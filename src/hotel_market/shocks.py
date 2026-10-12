"""shocks.py

The two shocks that are not in schedule.py: a convention, and a rate cut by
two competitors. The two air shocks, filed on days 20 and 40, live in
schedule.py.

Each shock has the day it becomes known and the range of stay dates it affects. Every lookup
takes as_of_day and sees only the shocks known on or before that day. schedule.py uses the same
rule for flights.
"""

from __future__ import annotations

from dataclasses import dataclass

from hotel_market.sources import Event


@dataclass(frozen=True)
class RateCut:
    known_day: int  # the first shop day that shows the cut
    start_day: int  # first stay date affected
    end_day: int  # last stay date affected
    hotel: str  # key of the hotel whose comp set this is
    competitors: tuple[str, ...]  # names of the competitors that cut
    cut: float  # 0.20 means rates are 20% lower

    def covers(self, hotel_key: str, competitor: str, stay_day: int) -> bool:
        return (
            hotel_key == self.hotel
            and competitor in self.competitors
            and self.start_day <= stay_day <= self.end_day
        )


EVENTS = [
    # Announced on day 10: a convention on stay days 45 to 48 raises demand
    # 35% at the two downtown hotels, and their competitors raise rates 15%
    # on those nights. Its peak night is not set here: forecast.peak_night()
    # works it out from expected demand.
    Event(
        "Convention",
        known_day=10,
        start_day=45,
        end_day=48,
        hotels=("convention", "full-service"),
        uplift=0.35,
        comp_rate_raise=0.15,
    ),
]

RATE_CUTS = [
    # Shopped from day 30: the two cheapest competitors of the full-service
    # hotel cut their rates 20% for stay days 37 to 39.
    RateCut(
        known_day=30,
        start_day=37,
        end_day=39,
        hotel="full-service",
        competitors=("full-service comp 1", "full-service comp 2"),
        cut=0.20,
    ),
]


def events_as_of(as_of_day: int) -> list[Event]:
    """The events known on a simulation day."""
    return [e for e in EVENTS if e.known_day <= as_of_day]


def event_uplift(hotel_key: str, stay_day: int, as_of_day: int) -> float:
    """Demand uplift for a hotel and stay date from the events known on as_of_day.

    0 when no known event covers the date. Overlapping events add up.
    """
    return sum(e.uplift for e in events_as_of(as_of_day) if e.covers(hotel_key, stay_day))


def comp_rate_raise(hotel_key: str, stay_day: int, as_of_day: int) -> float:
    """Fractional raise in the rates of a hotel's competitors for a stay date,
    from the events known on as_of_day.

    0 when no known event covers the date. Overlapping events add up.
    """
    return sum(e.comp_rate_raise for e in events_as_of(as_of_day) if e.covers(hotel_key, stay_day))


def rate_cuts_as_of(as_of_day: int) -> list[RateCut]:
    """The competitor rate cuts that show in the rate shop on a simulation day."""
    return [c for c in RATE_CUTS if c.known_day <= as_of_day]


def rate_cut(hotel_key: str, competitor: str, stay_day: int, as_of_day: int) -> float:
    """Fractional cut in one competitor's rate for a stay date, as shopped on as_of_day.

    0 when no known cut covers it. Overlapping cuts add up.
    """
    return sum(
        c.cut for c in rate_cuts_as_of(as_of_day) if c.covers(hotel_key, competitor, stay_day)
    )
