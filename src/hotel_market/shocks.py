"""shocks.py

The lookups over the two kinds of shock a market's customer file holds: its events, such as a
convention, and the scripted rate cuts by some hotel's competitors. The two air shocks, filed on
days 20 and 40, live in schedule.py and are the simulator's.

Each shock has the day it becomes known and the range of stay dates it affects. Every lookup
takes as_of_day and sees only the shocks known on or before that day. schedule.py uses the same
rule for flights. Each lookup also takes the customer whose market it is; the demo market is the
default, as everywhere. On a finer clock a cut also has the tick of its known day from which a
shop shows it (world.news_tick), so a shop lookup may name the shop's tick. The event lookups
stay by the day, because the simulator's demand counts an event for the whole day it is announced
on, while the events feed (simulated.py) lands it at its tick.
"""

from __future__ import annotations

from hotel_market.customer import Customer, demo
from hotel_market.sources import Event
from hotel_market.world import TICKS_PER_DAY, RateCut, news_tick


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


def rate_cuts_as_of(
    as_of_day: int,
    customer: Customer | None = None,
    as_of_tick: int | None = None,
    ticks: int = TICKS_PER_DAY,
) -> list[RateCut]:
    """The market's competitor rate cuts that show in the rate shop on a simulation day, or in
    the shop at a tick of it: a cut known that day shows from its known_tick on, from the day's
    first shop when the file names none. With no tick the whole day's cuts show."""
    return [
        c
        for c in (customer or demo()).rate_cuts
        if c.known_day < as_of_day
        or (
            c.known_day == as_of_day
            and (as_of_tick is None or news_tick(c.known_tick, ticks, 1) <= as_of_tick)
        )
    ]


def rate_cut(
    hotel_key: str,
    competitor: str,
    stay_day: int,
    as_of_day: int,
    customer: Customer | None = None,
    as_of_tick: int | None = None,
    ticks: int = TICKS_PER_DAY,
) -> float:
    """Fractional cut in one competitor's rate for a stay date, as shopped on as_of_day, at the
    shop's tick when one is given.

    0 when no known cut covers it. Overlapping cuts add up.
    """
    return sum(
        c.cut
        for c in rate_cuts_as_of(as_of_day, customer, as_of_tick, ticks)
        if c.covers(hotel_key, competitor, stay_day)
    )
