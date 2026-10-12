"""sources.py

The boundary between the agent and whatever supplies its data. Four
interfaces, one per feed a revenue system reads: bookings, competitor rate
shops, air schedules and events. Every method takes the day it is asked on
and returns only what was known on that day.

The agent's modules (detect, forecast, estimate, plan, model, agent) read data through these
interfaces and nothing else. tests/test_sources.py fails if one of them imports the simulator.
simulated.py implements the four with the simulator, and stored.py implements them from stored
tables.
"""

from __future__ import annotations

import statistics
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from hotel_market.world import Hotel


@dataclass(frozen=True)
class Event:
    """A demand event, as the events feed describes it."""

    name: str
    known_day: int  # the day the event is announced
    start_day: int  # first stay date affected
    end_day: int  # last stay date affected
    hotels: tuple[str, ...]  # keys of the hotels whose demand rises
    uplift: float  # 0.35 means demand is 35% higher
    comp_rate_raise: float  # 0.15 means those hotels' competitors charge 15% more

    def covers(self, hotel_key: str, stay_day: int) -> bool:
        return hotel_key in self.hotels and self.start_day <= stay_day <= self.end_day


@dataclass(frozen=True)
class BookingHistory:
    """The record of bookings before a day, as arrays indexed [day, hotel row, stay day]."""

    taken: np.ndarray  # the rooms each day's bookings took; 0 outside that day's window
    rates: np.ndarray  # the hotel's rate in force on each day; 0 outside that day's window
    opening: np.ndarray  # [hotel row, stay day]: the rooms on the books before day 0


class Bookings(ABC):
    """The property system: rooms on the books, the rates in force, and the record."""

    @abstractmethod
    def on_books(self, as_of_day: int) -> np.ndarray:
        """Rooms on the books by [hotel row, stay day] after as_of_day's bookings."""

    @abstractmethod
    def rates(self, as_of_day: int) -> np.ndarray:
        """Each hotel's rate in force on as_of_day, by [hotel row, stay day]."""

    @abstractmethod
    def history(self, as_of_day: int) -> BookingHistory:
        """The bookings made before as_of_day, day by day."""


class RateShops(ABC):
    """The rate shops: what each competitor charged for a stay date, as shopped on a day."""

    @abstractmethod
    def competitor_rates(self, shop_day: int, hotel: Hotel, stay_day: int) -> dict[str, float]:
        """Each competitor's rate for a stay date, as shopped on shop_day."""

    def median(self, shop_day: int, hotel: Hotel, stay_day: int) -> float:
        """The median of the hotel's comp set for a stay date, as shopped on shop_day."""
        return statistics.median(self.competitor_rates(shop_day, hotel, stay_day).values())

    @abstractmethod
    def median_history(self, as_of_day: int) -> np.ndarray:
        """The comp medians shopped before as_of_day, by [shop day, hotel row, stay day]. It is 0
        where a stay date was not shopped that day."""

    @abstractmethod
    def first_median(self, hotel: Hotel, stay_day: int) -> float:
        """The comp median's starting level for a stay date: its level with no shock and no
        reaction. The forecast measures the median against it (forecast.py)."""


class Schedules(ABC):
    """The air schedule feed. It gives the seats arriving each day, as filed by a day. It also gives
    the two changes the agent reads them as.
    """

    @abstractmethod
    def seats(self, as_of_day: int) -> np.ndarray:
        """Arriving seats by stay day, from the schedule as filed by as_of_day. Day -1 is
        the first schedule known, before any filing in the run."""

    def seat_change(self, as_of_day: int) -> Mapping[int, float]:
        """By stay day: the fractional change in arriving seats, as filed by as_of_day,
        against the first schedule known."""
        return seat_fraction(self.seats(as_of_day), self.seats(-1))

    def seat_revision(self, as_of_day: int) -> Mapping[int, float]:
        """By stay day: the fractional change against the schedule known the day before."""
        return seat_fraction(self.seats(as_of_day), self.seats(as_of_day - 1))


def seat_fraction(after: np.ndarray, before: np.ndarray) -> Mapping[int, float]:
    """(after - before) / before by stay day, as a read-only mapping."""
    return MappingProxyType(dict(enumerate(((after - before) / before).tolist())))


class Events(ABC):
    """The events feed."""

    @abstractmethod
    def known(self, as_of_day: int) -> list[Event]:
        """The events announced by as_of_day."""


@dataclass(frozen=True)
class Sources:
    """The four feeds the agent reads, as one bundle."""

    bookings: Bookings
    shops: RateShops
    schedules: Schedules
    events: Events
