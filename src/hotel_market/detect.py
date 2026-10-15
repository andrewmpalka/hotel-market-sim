"""detect.py

What changed after each day's bookings, for every hotel and stay date in the window. It gives the
detect numbers and a flag where a number crosses its threshold.

    pace gap        rooms on the books - normal_demand x curve(days out)
    passenger_change    arriving passengers against the no-shock schedule (reason text only)
    passenger_revision  arriving passengers against yesterday's schedule
    rate vs median  the hotel's rate against its comp median
    median change   the comp median against yesterday's shop
    new event       an event that became known today and covers the date

A stay date is flagged in four cases: a pace gap beyond a share of the hotel's rooms and some
standard deviations of booking noise, a passenger_revision beyond its threshold either way, a comp
median that moved beyond its threshold since yesterday, and an event that became known today.

With several ticks a day the numbers are read as of (day, tick). "Since yesterday" and "today"
then mean since the previous tick, so a feed raises its flag at the tick it lands, and the pace
baseline is the curve at the fractional day, days out plus the share of the day still to come.
With one tick a day, the default, nothing changes.

On a stay date under the hold, a pace gap alone raises no flag. The thresholds and the hold
period are the customer's settings (customer.py). For the demo market they are 10% of rooms, 3
standard deviations, 5%, 5% and 7 days, which with several ticks is 7 days' worth of ticks.
Consecutive flagged stay dates of a hotel with the same causes merge into one flag.

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
from hotel_market.forecast import ORACLE_MARKET_ELASTICITY, expected_demand, normal_demand
from hotel_market.sources import Sources, previous_tick
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
    tick: int = 1  # the tick of the day the flag rose on; 1 with one tick a day
    ticks: int = 1  # the ticks of that day


def detect_numbers(
    day: int,
    sources: Sources,
    customer: Customer | None = None,
    market_elasticity: float = ORACLE_MARKET_ELASTICITY,
    levels: Mapping[str, float] | None = None,
    tick: int | None = None,
) -> pd.DataFrame:
    """The detect numbers for every hotel and stay date in the day's window, one row each, as of
    the day's tick, the last with no tick. Each row carries the causes the stay date is flagged
    for. The market elasticity goes into the expected demand (forecast.py). levels maps a hotel
    key to the factor a --level agent scales its forecast by today; it scales the pace baseline
    and the expected demand alike."""
    customer = customer or demo()
    levels = levels or {}
    ticks = sources.bookings.ticks
    tick = ticks if tick is None else tick
    before = previous_tick(day, tick, ticks)  # the moment the changes are measured since
    passengers = sources.schedules.passenger_change(day, tick)
    revision = sources.schedules.passenger_revision(day, tick)
    known_before = {e.name for e in sources.events.known(*before)}
    announced = [e for e in sources.events.known(day, tick) if e.name not in known_before]
    on_books = sources.bookings.on_books(day, tick)
    rates = sources.bookings.rates(day, tick)
    rows = []
    for hotel in customer.hotels:
        i = hotel.row
        level = levels.get(hotel.key, 1.0)
        for stay_day in stay_window(day):
            on_pace = (
                normal_demand(hotel, stay_day)
                * hotel.curve(days_in(stay_day, day, tick, ticks))
                * level
            )
            median = sources.shops.median(day, hotel, stay_day, tick)
            row = {
                "day": day,
                "tick": tick,
                "hotel": hotel.key,
                "stay_day": stay_day,
                "days_out": stay_day - day,
                "rooms": int(on_books[i, stay_day]),
                "pace_gap": on_books[i, stay_day] - on_pace,
                "pace_threshold": max(
                    customer.pace_share * hotel.rooms, customer.pace_noise_sd * math.sqrt(on_pace)
                ),
                "expected_demand": level
                * expected_demand(hotel, stay_day, day, sources, market_elasticity, tick),
                "passenger_change": passengers[stay_day],
                "passenger_revision": revision[stay_day],
                "rate": float(rates[i, stay_day]),
                "comp_median": median,
                "rate_vs_median": rates[i, stay_day] / median - 1,
                "median_change": median
                / sources.shops.median(before[0], hotel, stay_day, before[1])
                - 1,
                "new_event": next(
                    (e.name for e in announced if e.covers(hotel.key, stay_day)), None
                ),
                "shock_known": shock_known(
                    hotel, stay_day, day, sources, customer.median_threshold, tick
                ),
            }
            row["causes"] = _causes(row, customer)
            rows.append(row)
    return pd.DataFrame(rows)


def days_in(stay_day: int, day: int, tick: int = 1, ticks: int = 1) -> float:
    """The days out at a moment, as the booking curve reads them: the whole days out plus the
    share of the day still to come after the tick. After the last tick it is the whole days out."""
    return stay_day - day + 1 - tick / ticks


def _causes(row: dict, customer: Customer) -> tuple[str, ...]:
    found = []
    if row["pace_gap"] > row["pace_threshold"]:
        found.append(AHEAD)
    if row["pace_gap"] < -row["pace_threshold"]:
        found.append(BEHIND)
    if row["passenger_revision"] >= customer.seat_threshold:
        found.append(SEATS_UP)
    if row["passenger_revision"] <= -customer.seat_threshold:
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
    held: Mapping[tuple[str, int], int | tuple[int, int]] | None = None,
    customer: Customer | None = None,
    tick: int | None = None,
    ticks: int = 1,
) -> list[Flag]:
    """The day's flags, merging consecutive stay dates of a hotel with the same causes.

    held maps (hotel key, stay day) to the day an action on it was last accepted, or to the
    (day, tick) with several ticks a day. On a stay date under the hold, a pace gap alone raises
    no flag; any shock cause lifts the hold. The hold is hold_days of ticks long.
    """
    held = held or {}
    hold_days = (customer or demo()).hold_days
    tick = ticks if tick is None else tick
    now = moment_index(day, tick, ticks)
    found = []
    for hotel_key, rows in table.groupby("hotel", sort=False):
        causes_by_stay = []
        for stay_day, causes in zip(rows["stay_day"].tolist(), rows["causes"].tolist()):
            if set(causes) <= PACE and _held(
                held, hotel_key, stay_day, now, hold_days * ticks, ticks
            ):
                causes = ()  # a pace gap alone raises no flag under the hold
            causes_by_stay.append((stay_day, causes))
        for causes, run in itertools.groupby(causes_by_stay, key=lambda item: item[1]):
            if causes:
                stays = [stay_day for stay_day, _ in run]
                found.append(Flag(day, hotel_key, stays[0], stays[-1], causes, tick, ticks))
    return found


def moment_index(day: int, tick: int = 1, ticks: int = 1) -> int:
    """A moment's place on the clock: the ticks before it since day 0. With one tick a day it is
    the day."""
    return day * ticks + tick - 1


def _held(
    held: Mapping[tuple[str, int], int | tuple[int, int]],
    hotel_key: str,
    stay_day: int,
    now: int,
    hold_ticks: int,
    ticks: int,
) -> bool:
    """Whether the stay date is under the hold at the moment `now`, a moment index. A hold
    recorded as a day alone was accepted at that day's last tick."""
    accepted = held.get((hotel_key, stay_day))
    if accepted is None:
        return False
    since = (
        moment_index(*accepted, ticks)
        if isinstance(accepted, tuple)
        else moment_index(accepted, ticks, ticks)
    )
    return 0 < now - since <= hold_ticks


def shock_known(
    hotel: Hotel,
    stay_day: int,
    as_of_day: int,
    sources: Sources,
    median_threshold: float,
    as_of_tick: int | None = None,
) -> bool:
    """Whether a shock known by as_of_day, at the tick, moves demand or competitor rates for this
    hotel and stay date. That is true when the passengers have changed, a known event covers the
    date or today's comp median sits the median threshold or more away from its starting level,
    which the shop noise alone never reaches.
    """
    median = sources.shops.median(as_of_day, hotel, stay_day, as_of_tick)
    return (
        sources.schedules.passenger_change(as_of_day, as_of_tick)[stay_day] != 0
        or any(e.covers(hotel.key, stay_day) for e in sources.events.known(as_of_day, as_of_tick))
        or abs(median / sources.shops.first_median(hotel) - 1) >= median_threshold
    )


def pace_without_shock(flag: Flag, table: pd.DataFrame) -> bool:
    """A pace flag with no known shock behind any of its stay dates."""
    rows = table[
        (table["hotel"] == flag.hotel) & table["stay_day"].between(flag.first_stay, flag.last_stay)
    ]
    return set(flag.causes) <= PACE and not rows["shock_known"].any()
