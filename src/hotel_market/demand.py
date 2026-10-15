"""demand.py

The simulator's demand. It is the rooms a hotel sells for a stay date at its starting rate. It
uses what is known on as_of_day.

    rooms x base occupancy x day-of-week factor
    x (1 + air share x seat_change for that stay date)
    x (1 + event uplift, from events known by as_of_day)

normal_demand leaves out seats and events. The agent never reads this module. Its own demand model
is forecast.py, which uses the same formula from the feeds. At the default demand bias the agent's
demand model is therefore right by construction, which is a known limit.

DEMAND_BIAS multiplies both functions. The command sets it with --demand-bias, and the booking
loop passes it to every draw. The agent never receives it, so at a bias other than 1.0 its
forecast is wrong by that factor. The error is in the demand level alone.

MARKET_ELASTICITY is the market's own price response. Expected demand is multiplied by (the comp
median as shopped that day / the median's starting level for that stay date) ** -MARKET_ELASTICITY.
The starting level is the median with no shock and no reaction (shops.starting_median). The
default is 1.0, a market-wide rate rise losing demand in proportion, which the customer file
records and the command's --market-elasticity overrides. The agent is told the run's value
(forecast.py), as it is told the share elasticity.

Run `python -m hotel_market.demand` to print normal demand as occupancy by day of week.
"""

from __future__ import annotations

from functools import lru_cache
from types import MappingProxyType

from hotel_market.customer import demo
from hotel_market.schedule import DEFAULT_SCENARIO, Scenario, seat_change
from hotel_market.shocks import event_uplift
from hotel_market.world import Hotel, weekday

# A factor on the simulator's demand that the agent never sees; --demand-bias sets it per run.
DEMAND_BIAS = 1.0
# The market's price response: demand scales with (comp median / its starting level) ** -this.
# 1.0 because a market-wide rate rise should lose demand in proportion; the demo customer file
# records the same value, and a run's --market-elasticity overrides it. At 0.0 only the hotel's
# rate against the median would move bookings, so a matched raise would be free.
MARKET_ELASTICITY = 1.0


def dow_factor(hotel: Hotel, stay_day: int) -> float:
    return hotel.weekday_factors[weekday(stay_day)]


def normal_demand(hotel: Hotel, stay_day: int, demand_bias: float = DEMAND_BIAS) -> float:
    """Rooms a hotel expects to sell for a stay date with no seat change and no event. The
    demand bias multiplies it."""
    return hotel.rooms * hotel.base_occupancy * dow_factor(hotel, stay_day) * demand_bias


def expected_demand(
    hotel: Hotel,
    stay_day: int,
    as_of_day: int,
    demand_bias: float = DEMAND_BIAS,
    median_ratio: float = 1.0,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
) -> float:
    """Rooms a hotel expects to sell for a stay date, given what is known on as_of_day. The
    demand bias multiplies it. median_ratio is the comp median as shopped over its starting
    level, and the market elasticity scales demand by median_ratio ** -market_elasticity. The
    scenario is the air schedule's filings."""
    return (
        normal_demand(hotel, stay_day, demand_bias)
        * (1 + hotel.air_share * known_seat_change(as_of_day, scenario)[stay_day])
        * (1 + event_uplift(hotel.key, stay_day, as_of_day))
        * median_ratio**-market_elasticity
    )


def last_filing(as_of_day: int, scenario: Scenario = DEFAULT_SCENARIO) -> int:
    """The last day on or before as_of_day when an airline filed a change, or -1 if none.

    The schedule changes only on filing days. Every day therefore has the same seats as the last
    filing day before it. The functions seat_change and seat_revision build two schedules each,
    so they run once per filing instead of once a day.
    """
    return max((s.known_day for s in scenario.shocks if s.known_day <= as_of_day), default=-1)


def known_seat_change(
    as_of_day: int, scenario: Scenario = DEFAULT_SCENARIO
) -> MappingProxyType[int, float]:
    """seat_change(as_of_day) as a read-only {stay day: change}, built once per filing."""
    return _seat_change(last_filing(as_of_day, scenario), scenario)


@lru_cache(maxsize=None)
def _seat_change(as_of_day: int, scenario: Scenario) -> MappingProxyType[int, float]:
    return MappingProxyType(seat_change(as_of_day, scenario).to_dict())


if __name__ == "__main__":
    print("Normal demand as occupancy: base occupancy x day-of-week factor")
    days = range(7)  # day 0 is a Monday, so days 0 to 6 run Monday to Sunday
    names = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    print(f"{'':28}" + "".join(f"{names[weekday(d)]:>8}" for d in days) + f"{'Week':>8}")
    for hotel in demo().hotels:
        occupancy = [normal_demand(hotel, d) / hotel.rooms for d in days]
        print(
            f"{hotel.name:28}"
            + "".join(f"{o:8.2%}" for o in occupancy)
            + f"{sum(occupancy) / len(occupancy):8.2%}"
        )
