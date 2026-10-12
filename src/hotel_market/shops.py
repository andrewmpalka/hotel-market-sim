"""shops.py

Rate shops: what each competitor charges for a stay date, as seen on a shop
day, and the median of each hotel's comp set. Rates are flat across the
week: with a fixed cost per occupied room, the best rate on a night that
won't sell out is the same every day, so neither the hotels' starting rates
nor their competitors' follow the day of the week.

    competitor rate = base rate x (1 + noise)
                      x (1 + event raise known by shop_day)
                      x (1 - rate cut known by shop_day)

shop_day is the as_of_day of a rate shop. The noise is drawn once per
competitor and stay date from the run's seed, so a comp median only moves
when a shock does.
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


@lru_cache(maxsize=None)
def _noise(seed: int, hotels: int, competitors: int) -> np.ndarray:
    """Noise for every hotel, competitor and stay date, drawn in one go for a seed."""
    rng = np.random.default_rng([seed, NOISE_STREAM])
    noise = rng.uniform(-NOISE, NOISE, size=(hotels, competitors, HORIZON_DAYS))
    noise.flags.writeable = False
    return noise


def comp_rates(
    shop_day: int, hotel: Hotel, stay_day: int, *, seed: int, customer: Customer | None = None
) -> dict[str, float]:
    """Each competitor's rate for a stay date, as shopped on shop_day."""
    customer = customer or demo()
    competitors = max(len(h.competitors) for h in customer.hotels)
    noise = _noise(seed, len(customer.hotels), competitors)[hotel.row, :, stay_day]
    raise_ = 1 + comp_rate_raise(hotel.key, stay_day, shop_day)
    return {
        comp.name: (
            comp.base_rate
            * raise_
            * (1 + noise[i])
            * (1 - rate_cut(hotel.key, comp.name, stay_day, shop_day))
        )
        for i, comp in enumerate(hotel.competitors)
    }


def comp_median(
    shop_day: int, hotel: Hotel, stay_day: int, *, seed: int, customer: Customer | None = None
) -> float:
    """The median rate of a hotel's comp set for a stay date, as shopped on shop_day."""
    rates = comp_rates(shop_day, hotel, stay_day, seed=seed, customer=customer)
    return statistics.median(rates.values())
