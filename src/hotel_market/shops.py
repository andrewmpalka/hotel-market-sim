"""shops.py

Rate shops: what each competitor charges for a stay date, as seen on a shop day. The module also
gives the median of each hotel's comp set. Rates are flat across the week, and the cost per occupied
room is fixed, so the best rate on a night that will not sell out is the same every day. Neither the
hotels' starting rates nor their competitors' rates therefore follow the day of the week.

    competitor rate = base rate x (1 + noise)
                      x (1 + event raise known by shop_day)
                      x (1 - rate cut known by shop_day)
                      + REACTION_SHARE x the hotel's change from its start rate

The event raise and the rate cut are the market's, from its customer file (shocks.py).

shop_day is the as_of_day of a rate shop. The noise is drawn afresh for every shop day, competitor
and stay date, from a stream keyed by the run's seed, the hotel's key and the competitor's name,
so a hotel added to the customer file leaves every other hotel's shops as they were. A comp median
therefore moves a little every day and a lot only when a shock does, or when the hotel's own rate
moved and the reaction is on. The level the market measures a median against is the comp set's
base rates' median (Hotel.starting_median), which carries no noise.

A market may shop more than once a day (its shop_ticks, world.shop_landings). Each shop is named
by its slot, the tick the file put it at, and a slot other than SHOP_TICK draws its noise from a
stream of its own, so the shop at the default slot is the one shop the market had before. A cut
known that day shows in a shop from the cut's known_tick on, so a shop lookup names its tick.

The reaction is opt-in (--react). The hotel's change is the one in force REACTION_LAG days
before the shop day, which the Books read from their daily log and pass in. Nothing is therefore
used before it is known. The default run passes no change, so its medians stay as they were.
"""

from __future__ import annotations

import statistics
from functools import lru_cache

import numpy as np

from hotel_market.customer import Customer
from hotel_market.schedule import HORIZON_DAYS
from hotel_market.shocks import comp_rate_raise, rate_cut
from hotel_market.world import SHOP_TICK, TICKS_PER_DAY, Hotel

NOISE = 0.03  # each competitor's rate is off by up to 3% either way, drawn afresh on every shop day
NOISE_STREAM = (
    1  # apart from other draws on the seed; the hotel's key and competitor's name join it
)
# With --react, each competitor moves this share of the hotel's change from its start rate ...
REACTION_SHARE = 0.5
# ... this many days after the change took effect, reading the hotel's rate in force that day.
REACTION_LAG = 3


@lru_cache(maxsize=None)
def _noise(seed: int, hotel: str, competitor: str, slot: int = SHOP_TICK) -> np.ndarray:
    """One competitor's noise by [shop day + 1, stay date], for shop days -1 to the horizon's end,
    from a stream keyed by the hotel's key and its name, so no other draw moves its shops. A shop
    at a slot other than SHOP_TICK draws from a stream keyed by its slot too."""
    key = [seed, NOISE_STREAM, *hotel.encode(), 0, *competitor.encode()]
    rng = np.random.default_rng(key if slot == SHOP_TICK else [*key, slot])
    noise = rng.uniform(-NOISE, NOISE, size=(HORIZON_DAYS + 1, HORIZON_DAYS))
    noise.flags.writeable = False
    return noise


def comp_rates(
    shop_day: int,
    hotel: Hotel,
    stay_day: int,
    *,
    seed: int,
    hotel_change: float = 0.0,
    customer: Customer | None = None,
    slot: int = SHOP_TICK,
    shop_tick: int | None = None,
    ticks: int = TICKS_PER_DAY,
) -> dict[str, float]:
    """Each competitor's rate for a stay date, as shopped on shop_day. hotel_change is the hotel's
    change from its start rate that the competitors react to, in dollars. Each moves
    REACTION_SHARE of it. The caller passes the lagged change, or nothing for no reaction. The
    customer's events and rate cuts move the rates on the dates they cover. slot names the shop's
    noise stream, and shop_tick the tick of the day the shop lands at, which a cut known that day
    must be known by; with no tick every cut of the day shows."""
    raise_ = 1 + comp_rate_raise(hotel.key, stay_day, shop_day, customer)
    reaction = REACTION_SHARE * hotel_change
    return {
        comp.name: (
            comp.base_rate
            * raise_
            * (1 + _noise(seed, hotel.key, comp.name, slot)[shop_day + 1, stay_day])
            * (1 - rate_cut(hotel.key, comp.name, stay_day, shop_day, customer, shop_tick, ticks))
            + reaction
        )
        for comp in hotel.competitors
    }


def comp_median(
    shop_day: int,
    hotel: Hotel,
    stay_day: int,
    *,
    seed: int,
    hotel_change: float = 0.0,
    customer: Customer | None = None,
    slot: int = SHOP_TICK,
    shop_tick: int | None = None,
    ticks: int = TICKS_PER_DAY,
) -> float:
    """The median rate of a hotel's comp set for a stay date, as shopped on shop_day, after the
    reaction to hotel_change (see comp_rates)."""
    return statistics.median(
        comp_rates(
            shop_day,
            hotel,
            stay_day,
            seed=seed,
            hotel_change=hotel_change,
            customer=customer,
            slot=slot,
            shop_tick=shop_tick,
            ticks=ticks,
        ).values()
    )
