"""shocks.py

The lookups over the two kinds of shock a market's customer file holds: its events, such as a
convention, and the scripted rate cuts by some hotel's competitors. The two air shocks, filed on
days 20 and 40, live in schedule.py and are the simulator's.

Each shock has the day it becomes known and the range of stay dates it affects. Every lookup
takes as_of_day and sees only the shocks known on or before that day. schedule.py uses the same
rule for flights. Each lookup also takes the customer whose market it is; the demo market is the
default, as everywhere.
"""

from __future__ import annotations

from hotel_market.customer import Customer, demo
from hotel_market.sources import Event
from hotel_market.world import RateCut


def events_as_of(as_of_day: int, customer: Customer | None = None) -> list[Event]:
    """The market's events known on a simulation day."""
    return [e for e in (customer or demo()).events if e.known_day <= as_of_day]


def event_uplift(
    hotel_key: str, stay_day: int, as_of_day: int, customer: Customer | None = None
) -> float:
    """Demand uplift for a hotel and stay date from the events known on as_of_day.

    0 when no known event covers the date. Overlapping events add up.
    """
    return sum(e.uplift for e in events_as_of(as_of_day, customer) if e.covers(hotel_key, stay_day))


def comp_rate_raise(
    hotel_key: str, stay_day: int, as_of_day: int, customer: Customer | None = None
) -> float:
    """Fractional raise in the rates of a hotel's competitors for a stay date,
    from the events known on as_of_day.

    0 when no known event covers the date. Overlapping events add up.
    """
    return sum(
        e.comp_rate_raise
        for e in events_as_of(as_of_day, customer)
        if e.covers(hotel_key, stay_day)
    )


def rate_cuts_as_of(as_of_day: int, customer: Customer | None = None) -> list[RateCut]:
    """The market's competitor rate cuts that show in the rate shop on a simulation day."""
    return [c for c in (customer or demo()).rate_cuts if c.known_day <= as_of_day]


def rate_cut(
    hotel_key: str,
    competitor: str,
    stay_day: int,
    as_of_day: int,
    customer: Customer | None = None,
) -> float:
    """Fractional cut in one competitor's rate for a stay date, as shopped on as_of_day.

    0 when no known cut covers it. Overlapping cuts add up.
    """
    return sum(
        c.cut
        for c in rate_cuts_as_of(as_of_day, customer)
        if c.covers(hotel_key, competitor, stay_day)
    )
