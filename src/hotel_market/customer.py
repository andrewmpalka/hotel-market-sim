"""customer.py

Everything specific to one market, read from a customer file such as customers/demo.toml. The
file holds the hotels with their rooms, starting rates, demand pattern and comp sets. It also
holds the cost share and rate limits. The detect thresholds, the hold period and the minimum
value at stake follow. The booking curve and the target the agent scores candidates on,
"contribution" or "revenue", complete it.

Both sides read it: the simulator to make the market, the agent to know its hotels and settings.
The constants of the simulator itself stay in the code. They are the calendar, the elasticity,
the noise, the schedule and the shocks. The demo file is the default wherever no customer is
given, so the demo market runs with no arguments.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from hotel_market.world import Competitor, Hotel

TARGETS = ("contribution", "revenue")  # what the agent may score candidates on
DEMO_FILE = Path("customers") / "demo.toml"  # the demo market, relative to the repository root
CUSTOMER_VARIABLE = "HOTEL_MARKET_CUSTOMER"  # names the default customer file, when set


@dataclass(frozen=True)
class Customer:
    """One market's own description and settings."""

    name: str
    target: str  # one of TARGETS
    hotels: tuple[Hotel, ...]
    floor_share: float
    ceiling_share: float
    cost_share: float
    pace_share: float
    pace_noise_sd: float
    seat_threshold: float
    median_threshold: float
    hold_days: int
    min_value_at_stake: float
    curve_days_out: tuple[float, ...]
    curve_share: tuple[float, ...]

    def hotel(self, key: str) -> Hotel:
        for hotel in self.hotels:
            if hotel.key == key:
                return hotel
        raise KeyError(f"no hotel with key {key!r}")

    def curve(self, days_out):
        """Share of final bookings normally on the books this many days before arrival."""
        return np.interp(days_out, self.curve_days_out, self.curve_share)

    def scores_contribution(self) -> bool:
        return self.target == "contribution"


def load(path: Path | str) -> Customer:
    """A customer from its TOML file."""
    with open(path, "rb") as handle:
        data = tomllib.load(handle)
    limits, detect, agent, curve = (
        data["limits"],
        data["detect"],
        data["agent"],
        data["booking_curve"],
    )
    if data["target"] not in TARGETS:
        raise ValueError(f"{path}: target must be one of {TARGETS}, not {data['target']!r}")
    hotels = tuple(
        _hotel(row, entry, limits["floor_share"], limits["ceiling_share"], limits["cost_share"])
        for row, entry in enumerate(data["hotels"])
    )
    if len({hotel.key for hotel in hotels}) != len(hotels):
        raise ValueError(f"{path}: hotel keys must be unique")
    if len({hotel.name for hotel in hotels}) != len(hotels):  # a request names its hotel
        raise ValueError(f"{path}: hotel names must be unique")
    return Customer(
        name=data["name"],
        target=data["target"],
        hotels=hotels,
        floor_share=limits["floor_share"],
        ceiling_share=limits["ceiling_share"],
        cost_share=limits["cost_share"],
        pace_share=detect["pace_share"],
        pace_noise_sd=detect["pace_noise_sd"],
        seat_threshold=detect["seat_threshold"],
        median_threshold=detect["median_threshold"],
        hold_days=detect["hold_days"],
        min_value_at_stake=agent["min_value_at_stake"],
        curve_days_out=tuple(curve["days_out"]),
        curve_share=tuple(curve["share"]),
    )


def _hotel(row: int, entry: dict, floor_share: float, ceiling_share: float, cost_share: float):
    start_rate = entry["start_rate"]
    competitors = tuple(
        Competitor(comp["name"], start_rate * (1 + comp["offset"])) for comp in entry["competitors"]
    )
    return Hotel(
        key=entry["key"],
        name=entry["name"],
        rooms=entry["rooms"],
        start_rate=start_rate,
        air_share=entry["air_share"],
        base_occupancy=entry["base_occupancy"],
        weekday_factors=tuple(entry["weekday_factors"]),
        competitors=competitors,
        floor=floor_share * start_rate,
        ceiling=ceiling_share * start_rate,
        room_cost=cost_share * start_rate,
        row=row,
    )


def demo_path() -> Path:
    """Where the demo customer file is. It is the path in HOTEL_MARKET_CUSTOMER if that is set.
    Otherwise it is customers/demo.toml under the working directory, else under the repository
    root.
    """
    named = os.environ.get(CUSTOMER_VARIABLE)
    if named:
        return Path(named)
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        if (base / DEMO_FILE).exists():
            return base / DEMO_FILE
    raise FileNotFoundError(
        f"{DEMO_FILE} not found; run from the repository root, pass --customer, or set "
        f"{CUSTOMER_VARIABLE}"
    )


@lru_cache(maxsize=None)
def demo() -> Customer:
    """The demo market, loaded once. The default wherever no customer is given."""
    return load(demo_path())
