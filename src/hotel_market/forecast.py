"""forecast.py

The agent's own demand model. It is the rooms a hotel expects to sell for a stay date at its
starting rate. It uses what the feeds say on a day.

    rooms x base occupancy x weekday factor
    x (1 + air share x seat change for that stay date)
    x (1 + uplift of every known event that covers the date)

normal_demand leaves out seats and events, and pace is measured against it. The weekday factors,
base occupancy and air share are the hotel's own settings. The seat change comes from the schedule
feed and the events from the events feed. The simulator books with the same formula (demand.py), so
the agent's demand model is right by construction, which is the known limit. The agent never reads
demand.py.

The market's price response mirrors demand.py's term: expected demand times (the comp median as
shopped / its starting level) ** -market elasticity. ORACLE_MARKET_ELASTICITY is the run's value,
handed to the agent as ORACLE_ELASTICITY hands it the share elasticity (plan.py). The command sets
it, and every plan record carries it. The default is the customer file's 1.0.
"""

from __future__ import annotations

from hotel_market.sources import Event, Sources
from hotel_market.world import Hotel, weekday

# The market elasticity the agent prices with: the simulator's value, handed to it, 1.0 by
# default as the customer file records. The command sets the run's value, and the oracle
# reviewer is told the same one.
ORACLE_MARKET_ELASTICITY = 1.0


def weekday_factor(hotel: Hotel, stay_day: int) -> float:
    return hotel.weekday_factors[weekday(stay_day)]


def normal_demand(hotel: Hotel, stay_day: int) -> float:
    """Rooms a hotel expects to sell for a stay date with no seat change and no event."""
    return hotel.rooms * hotel.base_occupancy * weekday_factor(hotel, stay_day)


def event_uplift(hotel: Hotel, stay_day: int, as_of_day: int, sources: Sources) -> float:
    """The demand uplift of the known events that cover the date; they add up."""
    return sum(e.uplift for e in sources.events.known(as_of_day) if e.covers(hotel.key, stay_day))


def expected_demand(
    hotel: Hotel,
    stay_day: int,
    as_of_day: int,
    sources: Sources,
    market_elasticity: float = ORACLE_MARKET_ELASTICITY,
) -> float:
    """Rooms a hotel expects to sell for a stay date, from what the feeds say on as_of_day. With a
    market elasticity, the comp median's level against its start scales it."""
    demand = (
        normal_demand(hotel, stay_day)
        * (1 + hotel.air_share * sources.schedules.seat_change(as_of_day)[stay_day])
        * (1 + event_uplift(hotel, stay_day, as_of_day, sources))
    )
    if market_elasticity:
        ratio = sources.shops.median(as_of_day, hotel, stay_day) / sources.shops.first_median(
            hotel, stay_day
        )
        demand *= ratio**-market_elasticity
    return demand


def peak_night(
    hotel: Hotel,
    event: Event,
    sources: Sources,
    market_elasticity: float = ORACLE_MARKET_ELASTICITY,
) -> int:
    """The event night with the highest expected demand at a hotel, as of the day
    the event becomes known. Ties go to the earliest night."""
    nights = range(event.start_day, event.end_day + 1)
    return max(
        nights,
        key=lambda night: expected_demand(
            hotel, night, event.known_day, sources, market_elasticity
        ),
    )
