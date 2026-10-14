"""shops.py

Rate shops: what each competitor charges for a stay date, as seen on a shop day. The module also
gives the median of each hotel's comp set. Rates are flat across the week, and the cost per occupied
room is fixed, so the best rate on a night that will not sell out is the same every day. Neither the
hotels' starting rates nor their competitors' rates therefore follow the day of the week.

    competitor rate = base rate x (1 + noise)
                      x (1 + event raise known by shop_day)
                      x (1 - rate cut known by shop_day)
                      + REACTION_SHARE x the hotel's change from its start rate

shop_day is the as_of_day of a rate shop. The noise is drawn once per competitor and stay date
from the run's seed. A comp median therefore moves only when a shock does, or when the hotel's
own rate moved and the reaction is on.

The reaction is opt-in (--react). The hotel's change is the one in force REACTION_LAG days
before the shop day, which the Books read from their daily log and pass in. Nothing is therefore
used before it is known. The default run passes no change, so its medians stay as they were.
"""

from __future__ import annotations

import statistics
from functools import lru_cache

import numpy as np

from hotel_market.customer import Customer, demo
from hotel_market.schedule import HORIZON_DAYS
from hotel_market.shocks import comp_rate_raise, rate_cut
from hotel_market.world import Hotel

NOISE = 0.03  # each competitor's rate is off by up to 3% either way
NOISE_STREAM = 1  # keeps these draws apart from other draws on the same seed
# With --react, each competitor moves this share of the hotel's change from its start rate ...
REACTION_SHARE = 0.5
# ... this many days after the change took effect, reading the hotel's rate in force that day.
REACTION_LAG = 3


@lru_cache(maxsize=None)
def _noise(seed: int, hotels: int, competitors: int) -> np.ndarray:
    """Noise for every hotel, competitor and stay date, drawn in one go for a seed."""
    rng = np.random.default_rng([seed, NOISE_STREAM])
    noise = rng.uniform(-NOISE, NOISE, size=(hotels, competitors, HORIZON_DAYS))
    noise.flags.writeable = False
    return noise


def comp_rates(
    shop_day: int,
    hotel: Hotel,
    stay_day: int,
    *,
    seed: int,
    customer: Customer | None = None,
    hotel_change: float = 0.0,
) -> dict[str, float]:
    """Each competitor's rate for a stay date, as shopped on shop_day. hotel_change is the hotel's
    change from its start rate that the competitors react to, in dollars. Each moves
    REACTION_SHARE of it. The caller passes the lagged change, or nothing for no reaction."""
    customer = customer or demo()
    competitors = max(len(h.competitors) for h in customer.hotels)
    noise = _noise(seed, len(customer.hotels), competitors)[hotel.row, :, stay_day]
    raise_ = 1 + comp_rate_raise(hotel.key, stay_day, shop_day)
    reaction = REACTION_SHARE * hotel_change
    return {
        comp.name: (
            comp.base_rate
            * raise_
            * (1 + noise[i])
            * (1 - rate_cut(hotel.key, comp.name, stay_day, shop_day))
            + reaction
        )
        for i, comp in enumerate(hotel.competitors)
    }


def comp_median(
    shop_day: int,
    hotel: Hotel,
    stay_day: int,
    *,
    seed: int,
    customer: Customer | None = None,
    hotel_change: float = 0.0,
) -> float:
    """The median rate of a hotel's comp set for a stay date, as shopped on shop_day, after the
    reaction to hotel_change (see comp_rates)."""
    rates = comp_rates(
        shop_day, hotel, stay_day, seed=seed, customer=customer, hotel_change=hotel_change
    )
    return statistics.median(rates.values())


def starting_median(
    hotel: Hotel, stay_day: int, *, seed: int, customer: Customer | None = None
) -> float:
    """The comp median's starting level for a stay date: the median with no shock and no reaction,
    which the seeded noise fixes. It is the shop of day -1, before any shock is known. The
    market's price response (demand.py) measures the median against it."""
    return comp_median(-1, hotel, stay_day, seed=seed, customer=customer)
