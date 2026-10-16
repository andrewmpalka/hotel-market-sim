"""world.py

The types a market is described with, and the calendar the simulation runs on. A Hotel carries
everything the agent and the simulator need to know about it: its rooms, starting rate, share of
guests arriving by air and rooms sold on a normal night. It also has its demand factors across the
week, booking curve, rate floor and ceiling, cost per occupied room and comp set. The hotels
themselves, and the rest of a market's settings, come from a customer file (customer.py).

Nothing here is random. The seed only matters once competitor rates and bookings are drawn.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import timedelta

import numpy as np

from hotel_market.schedule import HORIZON_DAYS, SIM_START

SIM_DAYS = 60  # the agent decides on days 0 to 59; bookings run on to day 149
LOOKAHEAD_DAYS = 90  # stay dates each hotel looks at on each simulation day
# The ticks a day is cut into: the agent runs after each, and a moment is (day, tick) with the
# ticks counted 1 to N. At 1, the default, a tick is the whole day and the loop is the daily one.
# --ticks N sets a run's value; the sources default a question to the last tick of its day.
TICKS_PER_DAY = 1
# With N ticks, each feed lands at a fixed tick of the day: bookings at every tick, the rate shop
# at tick 2, the airlines' filings at tick 3 and the events at tick 4, each at tick 1 when N is
# smaller than its slot. Until a feed lands, a question on a tick gets the previous value.
SHOP_TICK = 2
FILING_TICK = 3
EVENT_TICK = 4


@dataclass(frozen=True)
class Competitor:
    name: str
    base_rate: float  # before event and noise adjustments


@dataclass(frozen=True)
class Hotel:
    key: str  # short id for lookups and file names
    name: str
    rooms: int
    start_rate: float
    air_share: float  # share of guests who arrive by air
    base_occupancy: float  # share of rooms sold on a normal night
    weekday_factors: tuple[float, ...]  # demand factors, Monday to Sunday
    curve_days_out: tuple[float, ...]  # the booking curve's pinned days out, ascending from 0
    curve_share: tuple[
        float, ...
    ]  # the share of final bookings on the books at each; 1 on the night
    competitors: tuple[Competitor, ...]
    floor: float  # the lowest rate the hotel will set
    ceiling: float  # the highest
    room_cost: float  # cost to service one occupied room: housekeeping, supplies, commissions
    row: int  # the hotel's row in every array indexed by hotel

    def clamp(self, rate: float) -> float:
        """Keep a proposed rate between the hotel's floor and ceiling."""
        return min(max(rate, self.floor), self.ceiling)

    def curve(self, days_out):
        """Share of final bookings normally on the books this many days before arrival: linear
        between the pinned points and flat beyond the last."""
        return np.interp(days_out, self.curve_days_out, self.curve_share)

    def starting_median(self) -> float:
        """The comp set's median before any shock, reaction or noise: the median of its base rates,
        which the symmetric offsets put at the start rate. The market's price response and the
        agent's forecast measure the shopped median against it."""
        return statistics.median(c.base_rate for c in self.competitors)


def stay_window(day: int) -> range:
    """The stay dates a hotel looks at on a simulation day: that night and the next 89.

    That night is included because the booking curve reaches 100% at 0 days out. Some rooms are
    therefore booked on the day of arrival. After day 59 the window stops at stay date 149, the
    last day of the schedule.
    """
    return range(day, min(day + LOOKAHEAD_DAYS, HORIZON_DAYS))


def arrival_tick(slot: int, ticks: int = TICKS_PER_DAY) -> int:
    """The tick a feed with this slot lands at on a day of `ticks` ticks: its slot, or tick 1 when
    the day has fewer ticks than the slot."""
    return slot if slot <= ticks else 1


def weekday(day: int) -> int:
    """Day of the week of a simulation day. Monday is 0, as in schedule.py."""
    return (SIM_START + timedelta(days=day)).weekday()
