"""simulated.py

The simulator as the agent's four data sources. Each class answers for a day from what the
simulator knew on that day. The bookings come from the Books' daily log and the rate shops from
the shops the simulator used. The schedule and event records are as of that day. deciding() wraps
an Agent as the simulator's decide hook.

Run `python -m hotel_market.simulated --seed 7` to print the flags of a fixed-rate run.
"""

from __future__ import annotations

import argparse
from functools import lru_cache

import numpy as np
import pandas as pd

from hotel_market.agent import Agent
from hotel_market.bookings import Books, Decide, simulate
from hotel_market.customer import Customer, demo
from hotel_market.demand import last_filing
from hotel_market.detect import AHEAD, PACE, Flag, detect_numbers, flags, pace_without_shock
from hotel_market.schedule import build_schedule, seats_by_day
from hotel_market.shocks import events_as_of
from hotel_market.shops import comp_rates
from hotel_market.sources import (
    BookingHistory,
    Bookings,
    Event,
    Events,
    RateShops,
    Schedules,
    Sources,
)
from hotel_market.world import SIM_DAYS, Hotel


class SimulatedBookings(Bookings):
    """The Books' daily log, read as of a day."""

    def __init__(self, books: Books):
        self.books = books

    def on_books(self, as_of_day: int) -> np.ndarray:
        return self.books.preload + self.books.daily_rooms[: as_of_day + 1].sum(axis=0)

    def rates(self, as_of_day: int) -> np.ndarray:
        return self.books.daily_rates[as_of_day]

    def history(self, as_of_day: int) -> BookingHistory:
        return BookingHistory(
            self.books.daily_rooms[:as_of_day],
            self.books.daily_rates[:as_of_day],
            self.books.preload,
        )


class SimulatedRateShops(RateShops):
    """The rate shops the simulator draws from the seed, and the log of the medians it used. With
    the reaction on, each shop carries the Books' lagged hotel change, so the agent sees the
    shop the simulator used."""

    def __init__(self, books: Books):
        self.books = books

    def competitor_rates(self, shop_day: int, hotel: Hotel, stay_day: int) -> dict[str, float]:
        books = self.books
        return comp_rates(
            shop_day,
            hotel,
            stay_day,
            seed=books.seed,
            customer=books.customer,
            hotel_change=books.hotel_change(shop_day, hotel, stay_day),
        )

    def median(self, shop_day: int, hotel: Hotel, stay_day: int) -> float:
        return self.books.comp_median(shop_day, hotel, stay_day)

    def first_median(self, hotel: Hotel, stay_day: int) -> float:
        """The shop of day -1: no shock is known yet, and no rate has changed."""
        return self.books.starting_median(hotel, stay_day)

    def median_history(self, as_of_day: int) -> np.ndarray:
        return self.books.daily_medians[:as_of_day]


class SimulatedSchedules(Schedules):
    """The schedule as filed by a day, counted to arriving seats. The schedule only
    changes on filing days, so the seats are counted once per filing and reused."""

    def seats(self, as_of_day: int) -> np.ndarray:
        return _seats(last_filing(as_of_day))


@lru_cache(maxsize=None)
def _seats(filing_day: int) -> np.ndarray:
    seats = seats_by_day(build_schedule(as_of_day=filing_day)).to_numpy()
    seats.flags.writeable = False
    return seats


class SimulatedEvents(Events):
    def known(self, as_of_day: int) -> list[Event]:
        return events_as_of(as_of_day)


def simulated_sources(books: Books) -> Sources:
    """The four sources, answering from these books and their seed."""
    return Sources(
        SimulatedBookings(books), SimulatedRateShops(books), SimulatedSchedules(), SimulatedEvents()
    )


def deciding(agent: Agent) -> Decide:
    """The agent as the simulator's decide hook. After each day's bookings it reads the day through
    the simulated sources and returns the rate changes for tomorrow."""

    def decide(day: int, books: Books) -> dict[tuple[str, int], float]:
        return agent.decide(day, simulated_sources(books))

    return decide


def watch(
    seed: int, customer: Customer | None = None
) -> tuple[Books, list[Flag], dict[int, pd.DataFrame]]:
    """A fixed-rate run that runs detect after each of days 0 to 59.

    Returns the books, every flag, and each day's detect numbers.
    """
    customer = customer or demo()
    tables: dict[int, pd.DataFrame] = {}
    found: list[Flag] = []

    def record(day: int, books: Books) -> dict:
        tables[day] = detect_numbers(day, simulated_sources(books), customer)
        found.extend(flags(day, tables[day], customer=customer))
        return {}

    return simulate(seed, record, customer=customer), found, tables


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
