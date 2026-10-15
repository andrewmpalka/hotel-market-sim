"""simulated.py

The simulator as the agent's four data sources. Each class answers for a day from what the
simulator knew on that day. The bookings come from the Books' daily log and the rate shops from
the shops the simulator used. The schedule and event records are as of that day. deciding() wraps
an Agent as the simulator's decide hook.

The sources are made for a day, the as_of_day the simulator is deciding. Each copies what it will
read when it is made, the log through that day and the seats and events known by then, and holds
nothing else: no Books, no Scenario and no draw of a later day, so a decider cannot reach tomorrow
through an attribute either. A question about a later day raises ValueError, and every array they
hand out is a copy, so nothing the agent does reaches the simulator's own log. When they are made
with no day, as a test may make them, they copy the whole log and answer any day.

Run `python -m hotel_market.simulated --seed 7` to print the flags of a fixed-rate run.
"""

from __future__ import annotations

import argparse
from functools import lru_cache

import numpy as np
import pandas as pd

from hotel_market.agent import Agent
from hotel_market.bookings import Books, Decide, lagged_change, simulate
from hotel_market.customer import Customer, demo
from hotel_market.detect import AHEAD, PACE, Flag, detect_numbers, flags, pace_without_shock
from hotel_market.policy import PacePolicy
from hotel_market.schedule import (
    DEFAULT_SCENARIO,
    HORIZON_DAYS,
    Scenario,
    build_schedule,
    seats_by_day,
)
from hotel_market.shocks import events_as_of
from hotel_market.shops import comp_median, comp_rates, starting_median
from hotel_market.sources import (
    BookingHistory,
    Bookings,
    Event,
    Events,
    Limited,
    RateShops,
    Schedules,
    Sources,
)
from hotel_market.world import SIM_DAYS, Hotel


def _through(as_of_day: int | None) -> int:
    """How many days of a daily log a source made for the day copies: through that day."""
    return HORIZON_DAYS if as_of_day is None else as_of_day + 1


class SimulatedBookings(Limited, Bookings):
    """The Books' daily log through the day, copied when the source is made, read as of a day."""

    def __init__(self, books: Books, as_of_day: int | None = None):
        self.as_of_day = as_of_day
        self._preload = books.preload.copy()
        self._daily_rooms = books.daily_rooms[: _through(as_of_day)].copy()
        self._daily_rates = books.daily_rates[: _through(as_of_day)].copy()

    def on_books(self, as_of_day: int) -> np.ndarray:
        self._known(as_of_day)
        return self._preload + self._daily_rooms[: as_of_day + 1].sum(axis=0)

    def rates(self, as_of_day: int) -> np.ndarray:
        self._known(as_of_day)
        return self._daily_rates[as_of_day].copy()

    def history(self, as_of_day: int) -> BookingHistory:
        self._known(as_of_day, before=True)
        return BookingHistory(
            self._daily_rooms[:as_of_day].copy(),
            self._daily_rates[:as_of_day].copy(),
            self._preload.copy(),
        )


class SimulatedRateShops(Limited, RateShops):
    """The rate shops the simulator draws from the seed, and the log of the medians it used
    through the day, copied. With the reaction on, each shop carries the hotel's lagged change,
    read from the copied rates, so the agent sees the shop the simulator used."""

    def __init__(self, books: Books, as_of_day: int | None = None):
        self.as_of_day = as_of_day
        self._seed = books.seed
        self._customer = books.customer
        self._react = books.react
        self._daily_rates = books.daily_rates[: _through(as_of_day)].copy()
        self._daily_medians = books.daily_medians[: _through(as_of_day)].copy()
        self._starting: dict[tuple[int, int], float] = {}  # (hotel row, stay day) -> median

    def _hotel_change(self, shop_day: int, hotel: Hotel, stay_day: int) -> float:
        return lagged_change(self._daily_rates, self._react, shop_day, hotel, stay_day)

    def competitor_rates(self, shop_day: int, hotel: Hotel, stay_day: int) -> dict[str, float]:
        self._known(shop_day)
        return comp_rates(
            shop_day,
            hotel,
            stay_day,
            seed=self._seed,
            customer=self._customer,
            hotel_change=self._hotel_change(shop_day, hotel, stay_day),
        )

    def median(self, shop_day: int, hotel: Hotel, stay_day: int) -> float:
        self._known(shop_day)
        return comp_median(
            shop_day,
            hotel,
            stay_day,
            seed=self._seed,
            customer=self._customer,
            hotel_change=self._hotel_change(shop_day, hotel, stay_day),
        )

    def first_median(self, hotel: Hotel, stay_day: int) -> float:
        """The shop of day -1: no shock is known yet, and no rate has changed."""
        key = (hotel.row, stay_day)
        if key not in self._starting:
            self._starting[key] = starting_median(
                hotel, stay_day, seed=self._seed, customer=self._customer
            )
        return self._starting[key]

    def median_history(self, as_of_day: int) -> np.ndarray:
        self._known(as_of_day, before=True)
        return self._daily_medians[:as_of_day].copy()


class SimulatedSchedules(Limited, Schedules):
    """The schedule as filed by each filing day through the day under the run's scenario, counted
    to arriving seats once per filing. It holds those counts and not the scenario, so a filing
    still to come is not in it."""

    def __init__(self, scenario: Scenario = DEFAULT_SCENARIO, as_of_day: int | None = None):
        self.as_of_day = as_of_day
        last = HORIZON_DAYS - 1 if as_of_day is None else as_of_day
        self._filed = {day: _seats(day, scenario) for day in (-1, *scenario.filing_days(last))}

    def seats(self, as_of_day: int) -> np.ndarray:
        self._known(as_of_day)
        return self._filed[max(day for day in self._filed if day <= as_of_day)]


@lru_cache(maxsize=None)
def _seats(filing_day: int, scenario: Scenario) -> np.ndarray:
    seats = seats_by_day(build_schedule(as_of_day=filing_day, scenario=scenario)).to_numpy()
    seats.flags.writeable = False
    return seats


class SimulatedEvents(Limited, Events):
    """The events announced by the day, copied from the calendar, so an event still to be
    announced is not in it."""

    def __init__(self, as_of_day: int | None = None):
        self.as_of_day = as_of_day
        self._events = events_as_of(HORIZON_DAYS if as_of_day is None else as_of_day)

    def known(self, as_of_day: int) -> list[Event]:
        self._known(as_of_day)
        return [event for event in self._events if event.known_day <= as_of_day]


def simulated_sources(books: Books, as_of_day: int | None = None) -> Sources:
    """The four sources, made for as_of_day from copies of what these books knew by then: a
    question about a later day is refused, and no attribute reaches the books. With no day they
    answer any day."""
    return Sources(
        SimulatedBookings(books, as_of_day),
        SimulatedRateShops(books, as_of_day),
        SimulatedSchedules(books.scenario, as_of_day),
        SimulatedEvents(as_of_day),
    )


def deciding(decider: Agent | PacePolicy) -> Decide:
    """The agent, or a rule such as the pace policy, as the simulator's decide hook. After each
    day's bookings it reads the day through the simulated sources and returns the rate changes
    for tomorrow."""

    def decide(day: int, books: Books) -> dict[tuple[str, int], float]:
        return decider.decide(day, simulated_sources(books, day))

    return decide


def watch(
    seed: int,
    customer: Customer | None = None,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
) -> tuple[Books, list[Flag], dict[int, pd.DataFrame]]:
    """A fixed-rate run that runs detect after each of days 0 to 59, under a scenario and with
    the churn when asked.

    Returns the books, every flag, and each day's detect numbers.
    """
    customer = customer or demo()
    tables: dict[int, pd.DataFrame] = {}
    found: list[Flag] = []

    def record(day: int, books: Books) -> dict:
        tables[day] = detect_numbers(day, simulated_sources(books, day), customer)
        found.extend(flags(day, tables[day], customer=customer))
        return {}

    books = simulate(seed, record, customer=customer, scenario=scenario, churn=churn)
    return books, found, tables


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print the flags of a fixed-rate run.")
    parser.add_argument("--seed", type=int, required=True)
    seed = parser.parse_args().seed
    books, found, tables = watch(seed)

    print(f"Fixed-rate run, seed {seed}. Occupancy for stay dates 0 to 59:")
    for hotel in books.customer.hotels:
        print(f"  {hotel.name:28}{books.occupancy(hotel, range(SIM_DAYS)):6.1%}")

    print(f"\nEvery flag on days 0 to 59 ({len(found)} flags):")
    print(f"  {'day':>3}  {'hotel':12}  {'stays':7}  causes")
    for flag in found:
        stays = f"{flag.first_stay}" + (
            f"-{flag.last_stay}" if flag.last_stay > flag.first_stay else ""
        )
        note = "  (no shock behind it)" if pace_without_shock(flag, tables[flag.day]) else ""
        print(f"  {flag.day:>3}  {flag.hotel:12}  {stays:7}  {', '.join(flag.causes)}{note}")

    pace = [f for f in found if set(f.causes) <= PACE]
    lonely = [f for f in pace if pace_without_shock(f, tables[f.day])]
    ahead = sum(1 for f in lonely if AHEAD in f.causes)
    stay_days = sum(f.last_stay - f.first_stay + 1 for f in lonely)
    print(
        f"\nPace flags: {len(pace)}. With no shock behind them: {len(lonely)} "
        f"({ahead} ahead, {len(lonely) - ahead} behind), covering {stay_days} stay-date-days."
    )
