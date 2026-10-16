"""sources.py

The boundary between the agent and whatever supplies its data. Four
interfaces, one per feed a revenue system reads: bookings, competitor rate
shops, air schedules and events. Every method takes the day it is asked on
and returns only what was known on that day. It also takes the tick of that
day, as_of_tick, which defaults to the day's last tick, so a question with no
tick means "after the whole day" and reads as it always did (world.TICKS_PER_DAY).

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

from hotel_market.world import TICKS_PER_DAY, Hotel


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
    def on_books(self, as_of_day: int, as_of_tick: int | None = None) -> np.ndarray:
        """Rooms on the books by [hotel row, stay day] after as_of_day's bookings through the
        tick, the whole day with no tick."""

    @abstractmethod
    def rates(self, as_of_day: int, as_of_tick: int | None = None) -> np.ndarray:
        """Each hotel's rate in force on as_of_day at the tick, by [hotel row, stay day]."""

    @abstractmethod
    def history(self, as_of_day: int) -> BookingHistory:
        """The bookings made before as_of_day, day by day."""


class RateShops(ABC):
    """The rate shops: what each competitor charged for a stay date, as shopped on a day."""

    @abstractmethod
    def competitor_rates(
        self, shop_day: int, hotel: Hotel, stay_day: int, as_of_tick: int | None = None
    ) -> dict[str, float]:
        """Each competitor's rate for a stay date, as shopped on shop_day and known by the
        tick."""

    def median(
        self, shop_day: int, hotel: Hotel, stay_day: int, as_of_tick: int | None = None
    ) -> float:
        """The median of the hotel's comp set for a stay date, as shopped on shop_day."""
        return statistics.median(
            self.competitor_rates(shop_day, hotel, stay_day, as_of_tick).values()
        )

    @abstractmethod
    def median_history(self, as_of_day: int) -> np.ndarray:
        """The comp medians shopped before as_of_day, by [shop day, hotel row, stay day]. It is 0
        where a stay date was not shopped that day."""

    def first_median(self, hotel: Hotel) -> float:
        """The comp median's starting level: its level with no shock, no reaction and no noise,
        which is the median of the comp set's base rates. The forecast measures the shopped
        median against it (forecast.py). A feed with its own starting level may override it."""
        return hotel.starting_median()


class Schedules(ABC):
    """The air schedule feed. It gives the seats arriving each day, as filed by a day, and the
    passengers they carry at each flight's load factor. It also gives the two changes in the
    passengers that the agent reads.
    """

    ticks: int = TICKS_PER_DAY  # the ticks of a day, so the revision knows the previous tick

    @abstractmethod
    def seats(self, as_of_day: int, as_of_tick: int | None = None) -> np.ndarray:
        """Arriving seats by stay day, from the schedule as filed by as_of_day and known by the
        tick. Day -1 is the first schedule known, before any filing in the run."""

    @abstractmethod
    def passengers(self, as_of_day: int, as_of_tick: int | None = None) -> np.ndarray:
        """Arriving passengers by stay day, from the schedule as filed by as_of_day and known by
        the tick: the seats at each flight's load factor (schedule.passengers_by_day). Day -1 is
        the first schedule known."""

    def passenger_change(
        self, as_of_day: int, as_of_tick: int | None = None
    ) -> Mapping[int, float]:
        """By stay day: the fractional change in arriving passengers, as filed by as_of_day and
        known by the tick, against the first schedule known."""
        return seat_fraction(self.passengers(as_of_day, as_of_tick), self.passengers(-1))

    def passenger_revision(
        self, as_of_day: int, as_of_tick: int | None = None
    ) -> Mapping[int, float]:
        """By stay day: the fractional change against the schedule known at the previous tick,
        which with one tick a day is the day before."""
        day, tick = previous_tick(as_of_day, as_of_tick, self.ticks)
        return seat_fraction(self.passengers(as_of_day, as_of_tick), self.passengers(day, tick))


def previous_tick(day: int, tick: int | None, ticks: int = TICKS_PER_DAY) -> tuple[int, int]:
    """The moment before (day, tick): the tick before on the same day, or the last tick of the
    day before. No tick means the day's last tick."""
    tick = ticks if tick is None else tick
    return (day, tick - 1) if tick > 1 else (day - 1, ticks)


def seat_fraction(after: np.ndarray, before: np.ndarray) -> Mapping[int, float]:
    """(after - before) / before by stay day, as a read-only mapping, for seats or passengers."""
    return MappingProxyType(dict(enumerate(((after - before) / before).tolist())))


class Events(ABC):
    """The events feed."""

    @abstractmethod
    def known(self, as_of_day: int, as_of_tick: int | None = None) -> list[Event]:
        """The events announced by as_of_day and known by the tick."""


@dataclass(frozen=True)
class Sources:
    """The four feeds the agent reads, as one bundle."""

    bookings: Bookings
    shops: RateShops
    schedules: Schedules
    events: Events


class Limited:
    """A source made for a day, and for a tick of it. It refuses a question about a later day, or
    a later tick of the same day, so an agent cannot read tomorrow or the rest of today through
    it even by mistake. Made with no day, as a test may make it, it answers any day. Made for a
    day with no tick, it answers any tick of that day. Both implementations mix it in."""

    as_of_day: int | None = None  # the day the source was made for; None answers any day
    as_of_tick: int | None = None  # the tick it was made for; None answers any tick of the day
    ticks: int = TICKS_PER_DAY  # the ticks of a day; a question with no tick means the last one

    def _known(self, day: int, tick: int | None = None, before: bool = False) -> None:
        """Refuse a day after as_of_day, or a tick after as_of_tick on that day. A question about
        the bookings before a day, as history() asks, may name the day after as_of_day, because
        today's bookings are in. A tick outside 1 to the day's ticks is an error."""
        tick = self._tick(tick)
        latest = day - 1 if before else day
        if self.as_of_day is not None and latest > self.as_of_day:
            raise ValueError(f"asked about day {day} on day {self.as_of_day}: it is not known yet")
        if self.as_of_day is None or self.as_of_tick is None or latest != self.as_of_day:
            return
        # A question about the bookings before tomorrow means the whole of today, which a source
        # made for an earlier tick of today does not know yet.
        later = self.ticks if before else tick
        if later > self.as_of_tick:
            raise ValueError(
                f"asked about tick {later} of day {latest} on tick {self.as_of_tick}: it is not "
                f"known yet"
            )

    def _tick(self, tick: int | None) -> int:
        """The tick a question means: the day's last tick when it names none."""
        if tick is None:
            return self.ticks
        if not 1 <= tick <= self.ticks:
            raise ValueError(f"tick {tick} is not 1 to {self.ticks}")
        return tick
