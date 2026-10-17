"""customer.py

Everything specific to one market, read from a customer file such as customers/demo.toml. The
file holds the hotels with their rooms, starting rates, demand pattern, booking curves and comp
sets. It also holds the cost share and rate limits. The detect thresholds, the hold period and
the minimum value at stake follow. The market's price response and the target the agent scores
candidates on, "contribution" or "revenue", complete it, with the market's calendar: the events
that lift some of its hotels, and the scripted cuts by some hotel's competitors (shocks.py looks
them up). customers/harbour.toml is a second market with three hotels of other shapes.

On a finer clock the file may also say when its news lands within the day: the market's
shop_ticks, one rate shop per tick named, each with its own noise; an event's or a cut's
known_tick; and a [[filings]] table giving a filing's known_day and the tick it lands at. Each
is optional, and a file without them lands its feeds where world.py's slots put them, so it
reads as it did. customers/demo-intraday.toml is the demo market with such news inside the day.

Both sides read it: the simulator to make the market, the agent to know its hotels and settings. The
constants of the simulator itself, the calendar, the elasticity, the noise, the schedule and the
shocks, stay in the code. The demo file is the default wherever no customer is given, so the demo
market runs with no arguments.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from hotel_market.sources import Event
from hotel_market.world import SHOP_TICK, Competitor, Hotel, RateCut

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
    market_elasticity: float  # the market's own price response, which a run may override
    events: tuple[Event, ...] = ()  # the events that lift some of the hotels, by the day announced
    rate_cuts: tuple[RateCut, ...] = ()  # scripted cuts by some hotel's competitors
    shop_ticks: tuple[int, ...] = (SHOP_TICK,)  # the ticks a day's rate shops land at, one each
    filing_ticks: tuple[tuple[int, int], ...] = ()  # (known day, tick) of filings landing off slot

    def hotel(self, key: str) -> Hotel:
        for hotel in self.hotels:
            if hotel.key == key:
                return hotel
        raise KeyError(f"no hotel with key {key!r}")

    def scores_contribution(self) -> bool:
        return self.target == "contribution"


def load(path: Path | str) -> Customer:
    """A customer from its TOML file."""
    with open(path, "rb") as handle:
        data = tomllib.load(handle)
    limits, detect, agent, market = data["limits"], data["detect"], data["agent"], data["market"]
    if data["target"] not in TARGETS:
        raise ValueError(f"{path}: target must be one of {TARGETS}, not {data['target']!r}")
    _validate(path, data)
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
        market_elasticity=market["elasticity"],
        events=tuple(Event(**_event(entry)) for entry in data.get("events", [])),
        rate_cuts=tuple(RateCut(**_rate_cut(entry)) for entry in data.get("rate_cuts", [])),
        shop_ticks=tuple(market.get("shop_ticks", (SHOP_TICK,))),
        filing_ticks=tuple((f["known_day"], f["tick"]) for f in data.get("filings", [])),
    )


def _event(entry: dict) -> dict:
    return {**entry, "hotels": tuple(entry["hotels"])}


def _rate_cut(entry: dict) -> dict:
    return {**entry, "competitors": tuple(entry["competitors"])}


def _validate(path: Path | str, data: dict) -> None:
    """The checks a market file must pass. Each error names the field and, for a hotel, the hotel.
    The market elasticity is zero or more, the shares lie between 0 and 1, the floor sits below
    the ceiling, and every hotel has seven weekday factors, positive rooms, a positive start rate
    and a booking curve that starts at 1 on the night and falls with the days out. An event names
    hotels of the market, and a rate cut names a hotel and competitors of its comp set. Every tick
    the file names, a shop's, a filing's or a piece of news's known_tick, is a whole number from
    1, and the market has at least one shop."""
    limits, detect = data["limits"], data["detect"]
    keys = {entry["key"]: entry for entry in data["hotels"]}
    shop_ticks = data["market"].get("shop_ticks", [SHOP_TICK])
    if not shop_ticks:
        raise ValueError(f"{path}: market.shop_ticks names no tick; a day has one shop or more")
    for tick in shop_ticks:
        _tick(path, "market.shop_ticks", tick)
    for filing in data.get("filings", []):
        _tick(path, f"the filing on day {filing['known_day']}", filing["tick"])
    for news in data.get("events", []) + data.get("rate_cuts", []):
        if "known_tick" in news:
            _tick(path, f"known_tick on day {news['known_day']}", news["known_tick"])
    for event in data.get("events", []):
        unknown = set(event["hotels"]) - set(keys)
        if unknown:
            raise ValueError(f"{path}: event {event['name']!r} names no hotel {sorted(unknown)}")
    for cut in data.get("rate_cuts", []):
        if cut["hotel"] not in keys:
            raise ValueError(f"{path}: rate cut names no hotel {cut['hotel']!r}")
        names = {comp["name"] for comp in keys[cut["hotel"]]["competitors"]}
        unknown = set(cut["competitors"]) - names
        if unknown:
            raise ValueError(
                f"{path}: rate cut at hotel {cut['hotel']!r} names no competitor {sorted(unknown)}"
            )
    if not data["market"]["elasticity"] >= 0:
        raise ValueError(
            f"{path}: market.elasticity must be zero or more, not {data['market']['elasticity']!r}"
        )
    for field in ("floor_share", "cost_share"):
        _share(path, limits, field)
    _share(path, detect, "pace_share")
    if not limits["floor_share"] < limits["ceiling_share"]:
        raise ValueError(
            f"{path}: floor_share {limits['floor_share']!r} must be below ceiling_share "
            f"{limits['ceiling_share']!r}"
        )
    for entry in data["hotels"]:
        key = entry["key"]
        _curve(path, key, entry["booking_curve"])
        if len(entry["weekday_factors"]) != 7:
            raise ValueError(
                f"{path}: hotel {key!r}: weekday_factors needs seven entries, Monday to Sunday, "
                f"not {len(entry['weekday_factors'])}"
            )
        for field in ("rooms", "start_rate"):
            if not entry[field] > 0:
                raise ValueError(
                    f"{path}: hotel {key!r}: {field} must be positive, not {entry[field]!r}"
                )
        for field in ("air_share", "base_occupancy"):
            _share(path, entry, field, hotel=key)


def _curve(path: Path | str, hotel: str, curve: dict) -> None:
    """A booking curve's days out ascend from 0 with one share each. The shares start at 1 on the
    night and never rise with the days out, so no day expects fewer than no bookings."""
    days_out, share = curve["days_out"], curve["share"]
    where = f"{path}: hotel {hotel!r}: booking_curve"
    if (
        len(days_out) != len(share)
        or days_out[0] != 0
        or any(b <= a for a, b in zip(days_out, days_out[1:]))
    ):
        raise ValueError(
            f"{where}.days_out must ascend from 0, with one share each, not {days_out!r}"
        )
    if share[0] != 1 or any(not 0 <= b <= a for a, b in zip(share, share[1:])):
        raise ValueError(
            f"{where}.share must start at 1 on the night and fall to 0 or more, not {share!r}"
        )


def _tick(path: Path | str, where: str, value) -> None:
    """A tick a market file names is a whole number from 1; the clock lands it (world.news_tick)."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{path}: {where}: a tick is a whole number from 1, not {value!r}")


def _share(path: Path | str, table: dict, field: str, hotel: str | None = None) -> None:
    """A share lies between 0 and 1; the error names the field and the hotel when there is one."""
    value = table[field]
    if not 0 <= value <= 1:
        where = f"hotel {hotel!r}: " if hotel else ""
        raise ValueError(f"{path}: {where}{field} must lie between 0 and 1, not {value!r}")


def _hotel(row: int, entry: dict, floor_share: float, ceiling_share: float, cost_share: float):
    start_rate, curve = entry["start_rate"], entry["booking_curve"]
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
        curve_days_out=tuple(curve["days_out"]),
        curve_share=tuple(curve["share"]),
        competitors=competitors,
        floor=floor_share * start_rate,
        ceiling=ceiling_share * start_rate,
        room_cost=cost_share * start_rate,
        row=row,
    )


def demo_path() -> Path:
    """Where the demo customer file is. It is the path in HOTEL_MARKET_CUSTOMER if that is set.
    Otherwise it is customers/demo.toml under the repository this package is installed from. The
    working directory never counts, so a command run from one checkout cannot read another's
    file, and an installed package with no checkout needs the variable or --customer.
    """
    named = os.environ.get(CUSTOMER_VARIABLE)
    if named:
        return Path(named)
    root = Path(__file__).resolve().parents[2]
    if (root / DEMO_FILE).exists():
        return root / DEMO_FILE
    raise FileNotFoundError(
        f"{DEMO_FILE} not found under {root}; pass --customer, or set {CUSTOMER_VARIABLE}"
    )


@lru_cache(maxsize=None)
def demo() -> Customer:
    """The demo market, loaded once. The default wherever no customer is given."""
    return load(demo_path())
