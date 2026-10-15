"""simulated.py

The simulator as the agent's four data sources. Each class answers for a day from what the
simulator knew on that day. The bookings come from the Books' daily log and the rate shops from
the shops the simulator used. The schedule and event records are as of that day. deciding() wraps
an Agent as the simulator's decide hook.

The sources are made for a day, the as_of_day the simulator is deciding, and for a tick of it.
Each copies what it will read when it is made, the log through that day and the seats and events
known by then, and holds nothing else: no Books, no Scenario and no draw of a later day, so a
decider cannot reach tomorrow through an attribute either. A question about a later day, or a
later tick of the day, raises ValueError, and every array they hand out is a copy, so nothing the
agent does reaches the simulator's own log. When they are made with no day, as a test may make
them, they copy the whole log and answer any day.

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
    passengers_by_day,
    seats_by_day,
)
from hotel_market.shocks import events_as_of
from hotel_market.shops import comp_median, comp_rates
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
from hotel_market.world import (
    EVENT_TICK,
    FILING_TICK,
    SHOP_TICK,
    SIM_DAYS,
    TICKS_PER_DAY,
    Hotel,
    arrival_tick,
)


def _through(as_of_day: int | None) -> int:
    """How many days of a daily log a source made for the day copies: through that day."""
    return HORIZON_DAYS if as_of_day is None else as_of_day + 1


class SimulatedBookings(Limited, Bookings):
    """The Books' daily log through the day, copied when the source is made, read as of a day."""

    def __init__(self, books: Books, as_of_day: int | None = None, as_of_tick: int | None = None):
        self.as_of_day = as_of_day
        self.as_of_tick = as_of_tick
        self.ticks = books.ticks
        self._preload = books.preload.copy()
        self._daily_rooms = books.daily_rooms[: _through(as_of_day)].copy()
        self._daily_rates = books.daily_rates[: _through(as_of_day)].copy()
        self._tick_rooms = books.tick_rooms[: _through(as_of_day)].copy()
        self._tick_rates = books.tick_rates[: _through(as_of_day)].copy()

    def on_books(self, as_of_day: int, as_of_tick: int | None = None) -> np.ndarray:
        self._known(as_of_day, as_of_tick)
        if self.ticks == 1:
            return self._preload + self._daily_rooms[: as_of_day + 1].sum(axis=0)
        if as_of_day < 0:
            return self._preload.copy()  # the opening position, before any day's bookings
        tick = self._tick(as_of_tick)
        return (
            self._preload
            + self._daily_rooms[:as_of_day].sum(axis=0)
            + self._tick_rooms[as_of_day, :tick].sum(axis=0)
        )

    def rates(self, as_of_day: int, as_of_tick: int | None = None) -> np.ndarray:
        self._known(as_of_day, as_of_tick)
        if self.ticks == 1:
            return self._daily_rates[as_of_day].copy()
        return self._tick_rates[as_of_day, self._tick(as_of_tick) - 1].copy()

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

    def __init__(self, books: Books, as_of_day: int | None = None, as_of_tick: int | None = None):
        self.as_of_day = as_of_day
        self.as_of_tick = as_of_tick
        self.ticks = books.ticks
        self._seed = books.seed
        self._react = books.react
        self._daily_rates = books.daily_rates[: _through(as_of_day)].copy()
        self._daily_medians = books.daily_medians[: _through(as_of_day)].copy()

    def _hotel_change(self, shop_day: int, hotel: Hotel, stay_day: int) -> float:
        return lagged_change(self._daily_rates, self._react, shop_day, hotel, stay_day)

    def _landed(self, shop_day: int, as_of_tick: int | None) -> int:
        """The shop a question on (shop_day, tick) sees: the day's own once it has landed, else the
        day before's, the previous value."""
        self._known(shop_day, as_of_tick)
        if self._tick(as_of_tick) >= arrival_tick(SHOP_TICK, self.ticks):
            return shop_day
        return max(shop_day - 1, -1)  # the opening shop, day -1, is the earliest there is

    def competitor_rates(
        self, shop_day: int, hotel: Hotel, stay_day: int, as_of_tick: int | None = None
    ) -> dict[str, float]:
        shop_day = self._landed(shop_day, as_of_tick)
        return comp_rates(
            shop_day,
            hotel,
            stay_day,
            seed=self._seed,
            hotel_change=self._hotel_change(shop_day, hotel, stay_day),
        )

    def median(
        self, shop_day: int, hotel: Hotel, stay_day: int, as_of_tick: int | None = None
    ) -> float:
        shop_day = self._landed(shop_day, as_of_tick)
        return comp_median(
            shop_day,
            hotel,
            stay_day,
            seed=self._seed,
            hotel_change=self._hotel_change(shop_day, hotel, stay_day),
        )

    def median_history(self, as_of_day: int) -> np.ndarray:
        self._known(as_of_day, before=True)
        return self._daily_medians[:as_of_day].copy()


class SimulatedSchedules(Limited, Schedules):
    """The schedule as filed by each filing day through the day under the run's scenario, counted
    to arriving seats and passengers once per filing. It holds those counts and not the scenario,
    so a filing still to come is not in it."""

    def __init__(
        self,
        scenario: Scenario = DEFAULT_SCENARIO,
        as_of_day: int | None = None,
        as_of_tick: int | None = None,
        ticks: int = TICKS_PER_DAY,
    ):
        self.as_of_day = as_of_day
        self.as_of_tick = as_of_tick
        self.ticks = ticks
        last = HORIZON_DAYS - 1 if as_of_day is None else as_of_day
        self._filed = {day: _counts(day, scenario) for day in (-1, *scenario.filing_days(last))}

    def _filing(
        self, as_of_day: int, as_of_tick: int | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        """The schedule a question on (day, tick) sees: the day's filing once it has landed, else
        the schedule as filed by the day before."""
        self._known(as_of_day, as_of_tick)
        if self._tick(as_of_tick) < arrival_tick(FILING_TICK, self.ticks):
            as_of_day = max(as_of_day - 1, -1)  # the first schedule is the earliest there is
        return self._filed[max(day for day in self._filed if day <= as_of_day)]

    def seats(self, as_of_day: int, as_of_tick: int | None = None) -> np.ndarray:
        return self._filing(as_of_day, as_of_tick)[0]

    def passengers(self, as_of_day: int, as_of_tick: int | None = None) -> np.ndarray:
        return self._filing(as_of_day, as_of_tick)[1]


@lru_cache(maxsize=None)
def _counts(filing_day: int, scenario: Scenario) -> tuple[np.ndarray, np.ndarray]:
    """(seats, passengers) by stay day under the schedule as filed by a day, read-only."""
    schedule = build_schedule(as_of_day=filing_day, scenario=scenario)
    seats = seats_by_day(schedule).to_numpy()
    passengers = passengers_by_day(schedule).to_numpy()
    seats.flags.writeable = passengers.flags.writeable = False
    return seats, passengers


class SimulatedEvents(Limited, Events):
    """The events announced by the day, copied from the calendar, so an event still to be
    announced is not in it."""

    def __init__(
        self,
        as_of_day: int | None = None,
        as_of_tick: int | None = None,
        ticks: int = TICKS_PER_DAY,
    ):
        self.as_of_day = as_of_day
        self.as_of_tick = as_of_tick
        self.ticks = ticks
        self._events = events_as_of(HORIZON_DAYS if as_of_day is None else as_of_day)

    def known(self, as_of_day: int, as_of_tick: int | None = None) -> list[Event]:
        """The events announced by the day and landed by the tick: the day's own announcements
        land at the events' tick, before which the day before's calendar answers."""
        self._known(as_of_day, as_of_tick)
        if self._tick(as_of_tick) < arrival_tick(EVENT_TICK, self.ticks):
            as_of_day = max(as_of_day - 1, -1)
        return [event for event in self._events if event.known_day <= as_of_day]


def simulated_sources(
    books: Books, as_of_day: int | None = None, as_of_tick: int | None = None
) -> Sources:
    """The four sources, made for as_of_day, and for a tick of it, from copies of what these
    books knew by then: a question about a later day or tick is refused, and no attribute reaches
    the books. With no day they answer any day, and with no tick any tick of the day."""
    return Sources(
        SimulatedBookings(books, as_of_day, as_of_tick),
        SimulatedRateShops(books, as_of_day, as_of_tick),
        SimulatedSchedules(books.scenario, as_of_day, as_of_tick, books.ticks),
        SimulatedEvents(as_of_day, as_of_tick, books.ticks),
    )


def deciding(decider: Agent | PacePolicy) -> Decide:
    """The agent, or a rule such as the pace policy, as the simulator's decide hook. After each
    day's bookings it reads the day through the simulated sources and returns the rate changes
    for tomorrow. With several ticks a day it is called after each tick's bookings with the tick,
    reads the sources as of that tick, and returns the changes for the next tick."""

    def decide(day: int, books: Books, tick: int | None = None) -> dict[tuple[str, int], float]:
        if tick is None:
            return decider.decide(day, simulated_sources(books, day))
        return decider.decide(day, simulated_sources(books, day, tick), tick)

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
