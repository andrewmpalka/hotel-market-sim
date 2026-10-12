"""demand.py

The simulator's demand: the rooms a hotel sells for a stay date at its
starting rate, given what is known on as_of_day.

    rooms x base occupancy x day-of-week factor
    x (1 + air share x seat_change for that stay date)
    x (1 + event uplift, from events known by as_of_day)

normal_demand leaves out seats and events. The agent never reads this
module: its own demand model is forecast.py, which uses the same formula
from the feeds, the known limit that the agent's demand model is right by
construction.

Run `python -m hotel_market.demand` to print normal demand as occupancy by day of week.
"""

from __future__ import annotations

from functools import lru_cache
from types import MappingProxyType

from hotel_market.customer import demo
from hotel_market.schedule import AIR_SHOCKS, seat_change
from hotel_market.shocks import event_uplift
from hotel_market.world import Hotel, weekday


def dow_factor(hotel: Hotel, stay_day: int) -> float:
    return hotel.weekday_factors[weekday(stay_day)]


def normal_demand(hotel: Hotel, stay_day: int) -> float:
    """Rooms a hotel expects to sell for a stay date with no seat change and no event."""
    return hotel.rooms * hotel.base_occupancy * dow_factor(hotel, stay_day)


def expected_demand(hotel: Hotel, stay_day: int, as_of_day: int) -> float:
    """Rooms a hotel expects to sell for a stay date, given what is known on as_of_day."""
    return (
        normal_demand(hotel, stay_day)
        * (1 + hotel.air_share * known_seat_change(as_of_day)[stay_day])
        * (1 + event_uplift(hotel.key, stay_day, as_of_day))
    )


def last_filing(as_of_day: int) -> int:
    """The last day on or before as_of_day when an airline filed a change, or -1 if none.

    The schedule only changes on filing days, so every day has the same seats
    as the last filing day before it. That lets seat_change and seat_revision,
    which build two schedules each, run once per filing instead of once a day.
    """
    return max((s.known_day for s in AIR_SHOCKS if s.known_day <= as_of_day), default=-1)


def known_seat_change(as_of_day: int) -> MappingProxyType[int, float]:
    """seat_change(as_of_day) as a read-only {stay day: change}, built once per filing."""
    return _seat_change(last_filing(as_of_day))


@lru_cache(maxsize=None)
def _seat_change(as_of_day: int) -> MappingProxyType[int, float]:
    return MappingProxyType(seat_change(as_of_day).to_dict())


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
