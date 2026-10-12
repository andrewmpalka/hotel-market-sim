"""detect.py

What changed after each day's bookings, for every hotel and stay date in the window. It gives the
detect numbers and a flag where a number crosses its threshold.

    pace gap        rooms on the books - normal_demand x curve(days out)
    seat_change     arriving seats against the no-shock schedule (reason text only)
    seat_revision   arriving seats against yesterday's schedule
    rate vs median  the hotel's rate against its comp median
    median change   the comp median against yesterday's shop
    new event       an event that became known today and covers the date

A stay date is flagged in four cases. The first is a pace gap beyond a share of the hotel's rooms
and some standard deviations of booking noise. The second is a seat_revision beyond its threshold
either way. The third is a comp median that moved beyond its threshold since yesterday. The
fourth is an event that became known today.

On a stay date under the hold, a pace gap alone raises no flag. The thresholds and the hold
period are the customer's settings (customer.py). For the demo market they are 10% of rooms, 3
standard deviations, 5%, 5% and 7 days. Consecutive flagged stay dates of a hotel with the same
causes merge into one flag.

Everything here is read through the four sources (sources.py). The table also carries the
forecast's expected demand for each stay date, which is all the planner needs. `python -m
hotel_market.simulated --seed 7` prints the flags of a fixed-rate run.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from hotel_market.customer import Customer, demo
from hotel_market.forecast import expected_demand, normal_demand
from hotel_market.sources import Sources
from hotel_market.world import Hotel, stay_window

AHEAD, BEHIND = "ahead of pace", "behind pace"
SEATS_UP, SEATS_CUT = "seats up", "seats cut"
MEDIAN_UP, MEDIAN_DOWN = "comp median up", "comp median down"
NEW_EVENT = "event announced"
PACE = {AHEAD, BEHIND}


@dataclass(frozen=True)
class Flag:
    day: int
    hotel: str  # hotel key
    first_stay: int
    last_stay: int
    causes: tuple[str, ...]


def detect_numbers(day: int, sources: Sources, customer: Customer | None = None) -> pd.DataFrame:
    """The detect numbers for every hotel and stay date in the day's window, one row each. Each row
    carries the causes the stay date is flagged for."""
    customer = customer or demo()
    seats = sources.schedules.seat_change(day)
    revision = sources.schedules.seat_revision(day)
    announced = [e for e in sources.events.known(day) if e.known_day == day]
    on_books = sources.bookings.on_books(day)
    rates = sources.bookings.rates(day)
    rows = []
    for hotel in customer.hotels:
        i = hotel.row
        for stay_day in stay_window(day):
            on_pace = normal_demand(hotel, stay_day) * customer.curve(stay_day - day)
            median = sources.shops.median(day, hotel, stay_day)
            row = {
                "day": day,
                "hotel": hotel.key,
                "stay_day": stay_day,
                "days_out": stay_day - day,
                "rooms": int(on_books[i, stay_day]),
                "pace_gap": on_books[i, stay_day] - on_pace,
                "pace_threshold": max(
                    customer.pace_share * hotel.rooms, customer.pace_noise_sd * math.sqrt(on_pace)
                ),
                "expected_demand": expected_demand(hotel, stay_day, day, sources),
                "seat_change": seats[stay_day],
                "seat_revision": revision[stay_day],
                "rate": float(rates[i, stay_day]),
                "comp_median": median,
                "rate_vs_median": rates[i, stay_day] / median - 1,
                "median_change": median / sources.shops.median(day - 1, hotel, stay_day) - 1,
                "new_event": next(
                    (e.name for e in announced if e.covers(hotel.key, stay_day)), None
                ),
                "shock_known": shock_known(hotel, stay_day, day, sources),
            }
            row["causes"] = _causes(row, customer)
            rows.append(row)
    return pd.DataFrame(rows)


def _causes(row: dict, customer: Customer) -> tuple[str, ...]:
    found = []
    if row["pace_gap"] > row["pace_threshold"]:
        found.append(AHEAD)
    if row["pace_gap"] < -row["pace_threshold"]:
        found.append(BEHIND)
    if row["seat_revision"] >= customer.seat_threshold:
        found.append(SEATS_UP)
    if row["seat_revision"] <= -customer.seat_threshold:
        found.append(SEATS_CUT)
    if row["median_change"] >= customer.median_threshold:
        found.append(MEDIAN_UP)
    if row["median_change"] <= -customer.median_threshold:
        found.append(MEDIAN_DOWN)
    if row["new_event"]:
        found.append(NEW_EVENT)
    return tuple(found)


def flags(
    day: int,
    table: pd.DataFrame,
    held: Mapping[tuple[str, int], int] | None = None,
    customer: Customer | None = None,
) -> list[Flag]:
    """The day's flags, merging consecutive stay dates of a hotel with the same causes.

    held maps (hotel key, stay day) to the day an action on it was last
    accepted. On a stay date under the hold, a pace gap alone raises no flag;
    any shock cause lifts the hold.
    """
    held = held or {}
    hold_days = (customer or demo()).hold_days
    found = []
    for hotel_key, rows in table.groupby("hotel", sort=False):
        causes_by_stay = []
        for stay_day, causes in zip(rows["stay_day"].tolist(), rows["causes"].tolist()):
            if set(causes) <= PACE and _held(held, hotel_key, stay_day, day, hold_days):
                causes = ()  # a pace gap alone raises no flag under the hold
            causes_by_stay.append((stay_day, causes))
        for causes, run in itertools.groupby(causes_by_stay, key=lambda item: item[1]):
            if causes:
                stays = [stay_day for stay_day, _ in run]
                found.append(Flag(day, hotel_key, stays[0], stays[-1], causes))
    return found


def _held(
    held: Mapping[tuple[str, int], int], hotel_key: str, stay_day: int, day: int, hold_days: int
) -> bool:
    accepted = held.get((hotel_key, stay_day))
    return accepted is not None and 0 < day - accepted <= hold_days


def shock_known(hotel: Hotel, stay_day: int, as_of_day: int, sources: Sources) -> bool:
    """Whether a shock known by as_of_day moves demand or competitor rates for this hotel and stay
    date. That is true when the seats have changed or a known event covers the date. It is also
    true when today's comp median differs from the first shop.
    """
    return (
        sources.schedules.seat_change(as_of_day)[stay_day] != 0
        or any(e.covers(hotel.key, stay_day) for e in sources.events.known(as_of_day))
        or sources.shops.median(as_of_day, hotel, stay_day)
        != sources.shops.median(0, hotel, stay_day)
    )


def pace_without_shock(flag: Flag, table: pd.DataFrame) -> bool:
    """A pace flag with no known shock behind any of its stay dates."""
    rows = table[
        (table["hotel"] == flag.hotel) & table["stay_day"].between(flag.first_stay, flag.last_stay)
    ]
    return set(flag.causes) <= PACE and not rows["shock_known"].any()
