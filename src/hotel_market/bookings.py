"""bookings.py

The daily booking loop. For every hotel and stay date, the books hold three things: the rooms on the
books, the room revenue booked and the rate the hotel charges.

Before day 0's bookings, each stay date in the window is loaded with the bookings made before the
run starts. That load is a draw around normal_demand x curve(days out + 1) at the hotel's
starting rate. Then on each day from 0 to 149, every hotel and stay date in the window gets new
bookings. They are drawn around

    expected_demand x (curve today - curve yesterday)
    x (rate / comp median) ** -ELASTICITY

and capped at the rooms still unsold. Rates can change on days 0 to 59. A change applies from the
next day, and rates are frozen from day 60. A demand bias other than 1.0 multiplies the preload
and every day's expected demand (demand.py). The agent never sees it.

With the reaction on (--react), each day's rate shop is given the hotel's change from its start
rate as it stood REACTION_LAG days earlier, read from the daily log (shops.py). The competitors
move REACTION_SHARE of it. The reaction is off by default, and a fixed-rate run never changes a
rate, so the fixed-rate run is the same with it on.

Each day's expected demand is scaled by (the comp median shopped that day / its starting
level) ** -market_elasticity (demand.py), at the customer file's market elasticity unless a run
sets another with --market-elasticity.

Every draw has its own random number, fixed by the seed before the run starts. The function
poisson_draw turns it into a Poisson count. A change to one rate changes only that stay date's
draws. A fixed-rate run and an agent run with the same seed therefore differ only where the agent
acted.

With N ticks a day (--ticks), each day's count is still drawn once, at the day's first tick and
the rate then in force, and each booking is assigned to a tick with the hotel's own stream, so a
fixed-rate run books the same rooms per hotel and stay date at every N. A rate changed at tick t
applies from tick t+1: the bookings still to come that day are thinned, or topped up, in
proportion to the simulator's demand response at the new rate, (new / old) ** -ELASTICITY.

The books also keep a daily log of what each draw took, at what rate and against which competitor
median. The agent can learn from the bookings it has seen (estimate.py). It reads nothing it did
not know on the day.

Run `python -m hotel_market.bookings --seed 7` for occupancy and revenue at fixed rates.
"""

from __future__ import annotations

import argparse
import math
from collections.abc import Callable, Sequence

import numpy as np

from hotel_market.customer import Customer, demo
from hotel_market.demand import DEMAND_BIAS, expected_demand, normal_demand
from hotel_market.schedule import DEFAULT_SCENARIO, HORIZON_DAYS, Scenario, with_churn
from hotel_market.shops import REACTION_LAG, comp_median
from hotel_market.world import SIM_DAYS, TICKS_PER_DAY, Hotel, shop_landings, stay_window

ELASTICITY = 1.5  # bookings scale with (rate / comp median) ** -ELASTICITY
BOOKING_STREAM = (
    2  # keeps these draws apart from the rate-shop noise (stream 1); the hotel's key joins it
)
TICK_STREAM = 4  # the split of a day's bookings over its ticks; the hotel's key and the day join it


def preload_mean(hotel: Hotel, stay_day: int, demand_bias: float = DEMAND_BIAS) -> float:
    """Rooms expected on the books for a stay date before day 0's bookings: normal demand times
    the hotel's curve at the days out plus one. The curve is flat beyond its last point, so a
    stay date past the window holds the share the hotel books that far ahead."""
    return normal_demand(hotel, stay_day, demand_bias) * hotel.curve(stay_day + 1)


def poisson_draw(u: np.ndarray, mean: np.ndarray) -> np.ndarray:
    """The Poisson count that each random number u stands for. It is the smallest k with P(X <= k)
    >= u, where X is Poisson with the given mean.

        With u uniform between 0 and 1 this is an exact Poisson draw. A bigger mean
        never gives a smaller count for the same u.
    """
    u = np.asarray(u, dtype=float)
    mean = np.asarray(mean, dtype=float)
    if np.any(mean > 700):
        raise ValueError("means above 700 make exp(-mean) underflow")
    count = np.zeros(mean.shape, dtype=np.int64)
    p = np.exp(-mean)  # P(X = 0)
    cdf = p.copy()
    # Far past any u below 1. It stops float rounding in cdf from looping forever.
    limit = mean + 12 * np.sqrt(mean) + 20
    todo = u > cdf
    while todo.any():
        count[todo] += 1
        p[todo] *= mean[todo] / count[todo]
        cdf[todo] += p[todo]
        todo &= (u > cdf) & (count < limit)
    return count


class Books:
    """Rooms on the books, room revenue and rates, by hotel and stay date.

    The arrays are indexed [hotel.row, stay day]. Creating the books draws
    every random number the run will use, then loads the bookings made
    before day 0. The market is the customer's; the demo market by default.
    """

    def __init__(
        self,
        seed: int,
        customer: Customer | None = None,
        demand_bias: float = DEMAND_BIAS,
        react: bool = False,
        market_elasticity: float | None = None,
        scenario: Scenario = DEFAULT_SCENARIO,
        churn: bool = False,
        ticks: int = TICKS_PER_DAY,
    ):
        self.seed = seed
        self.customer = customer or demo()
        self.ticks = ticks  # the ticks a day is cut into; the sources default to the last
        self.demand_bias = demand_bias  # multiplies the preload and every day's expected demand
        self.react = react  # whether competitors react to the hotels' rate changes
        # The market's response to the median's level: the customer file's unless the run set one.
        self.market_elasticity = (
            self.customer.market_elasticity if market_elasticity is None else market_elasticity
        )
        self.churn = churn  # whether the airline also files the seed's weekly revisions
        self.scenario = with_churn(scenario, seed) if churn else scenario  # the air schedule's
        # The customer file may land a filing at a tick of its own (simulated.py reads it).
        self.scenario = self.scenario.with_filing_ticks(dict(self.customer.filing_ticks))
        # The day's rate shops as (tick, slot) pairs; the day's draw shops at the first.
        self.shops = shop_landings(self.customer.shop_ticks, ticks)
        hotels = self.customer.hotels
        # Each hotel draws its luck from a stream keyed by its key, so a hotel added to the
        # customer file leaves every other hotel's bookings as they were.
        self._preload_luck = np.zeros((len(hotels), HORIZON_DAYS))
        self._daily_luck = np.zeros((HORIZON_DAYS, len(hotels), HORIZON_DAYS))
        for hotel in hotels:
            rng = np.random.default_rng([seed, BOOKING_STREAM, *hotel.key.encode()])
            self._preload_luck[hotel.row] = rng.random(HORIZON_DAYS)
            self._daily_luck[:, hotel.row, :] = rng.random((HORIZON_DAYS, HORIZON_DAYS))
        self.rooms = np.zeros((len(hotels), HORIZON_DAYS), dtype=np.int64)
        self.revenue = np.zeros((len(hotels), HORIZON_DAYS))
        # Every stay date starts at the hotel's start rate; the agent changes them from here.
        self.rates = np.array([[hotel.start_rate] * HORIZON_DAYS for hotel in hotels], dtype=float)
        # The daily log, indexed [day, hotel row, stay day]: the rooms each day's draw
        # took, the rate in force that day and the competitor median shopped that day.
        # Zero where a stay date was outside the day's window.
        self.daily_rooms = np.zeros((HORIZON_DAYS, len(hotels), HORIZON_DAYS), dtype=np.int64)
        self.daily_rates = np.zeros((HORIZON_DAYS, len(hotels), HORIZON_DAYS))
        self.daily_medians = np.zeros((HORIZON_DAYS, len(hotels), HORIZON_DAYS))
        # The same by tick, indexed [day, tick - 1, hotel row, stay day]: the rooms each tick's
        # bookings took and the rate in force at that tick. With one tick a day they are the
        # daily log.
        self.tick_rooms = np.zeros((HORIZON_DAYS, ticks, len(hotels), HORIZON_DAYS), dtype=np.int64)
        self.tick_rates = np.zeros((HORIZON_DAYS, ticks, len(hotels), HORIZON_DAYS))
        # The day's bookings still to come, by tick, and the mean and rate they were drawn at.
        self._planned = np.zeros((ticks, len(hotels), HORIZON_DAYS), dtype=np.int64)
        self._planned_mean = np.zeros((len(hotels), HORIZON_DAYS))
        self._planned_rate = np.zeros((len(hotels), HORIZON_DAYS))
        self._split_rng: dict[int, np.random.Generator] = {}  # by hotel row, for the day
        self.preload = np.zeros((len(hotels), HORIZON_DAYS), dtype=np.int64)
        self._preload()

    def _preload(self) -> None:
        """Bookings made before day 0 on every stay date of the horizon: a draw around
        normal_demand x the hotel's curve(days out + 1)."""
        for hotel in self.customer.hotels:
            i = hotel.row
            mean = np.array([preload_mean(hotel, s, self.demand_bias) for s in range(HORIZON_DAYS)])
            rooms = np.minimum(poisson_draw(self._preload_luck[i], mean), hotel.rooms)
            self.preload[i] = rooms
            self.rooms[i] = rooms
            self.revenue[i] = rooms * self.rates[i]

    def expected_new_bookings(
        self, hotel: Hotel, stay_day: int, day: int, median: float | None = None
    ) -> float:
        """The mean of a day's new bookings for a hotel and stay date. The competitor
        median is that day's shop, passed in when the caller already has it."""
        days_out = stay_day - day
        rate = self.rates[hotel.row, stay_day]
        if median is None:
            median = self.comp_median(day, hotel, stay_day)
        curve = hotel.curve
        ratio = median / hotel.starting_median() if self.market_elasticity else 1.0
        demand = expected_demand(
            hotel,
            stay_day,
            day,
            self.demand_bias,
            ratio,
            self.market_elasticity,
            self.scenario,
            self.customer,
        )
        return demand * (curve(days_out) - curve(days_out + 1)) * (rate / median) ** -ELASTICITY

    def hotel_change(self, day: int, hotel: Hotel, stay_day: int) -> float:
        """The hotel's change from its start rate that its competitors react to on a shop day
        (lagged_change over the daily log)."""
        return lagged_change(self.daily_rates, self.react, day, hotel, stay_day)

    def comp_median(self, day: int, hotel: Hotel, stay_day: int) -> float:
        """The comp median the run shops on a day, with the reaction when it is on: the day's
        first shop, which a cut known later that day is not in."""
        change = self.hotel_change(day, hotel, stay_day)
        tick, slot = self.shops[0]
        return comp_median(
            day,
            hotel,
            stay_day,
            seed=self.seed,
            hotel_change=change,
            customer=self.customer,
            slot=slot,
            shop_tick=tick,
            ticks=self.ticks,
        )

    def book(self, day: int, tick: int = 1) -> None:
        """Draw one day's new bookings for every hotel and stay date in the window. With several
        ticks a day, tick 1 draws the day's count and splits it over the ticks, and each tick
        then books its share."""
        window = stay_window(day)
        stays = np.array(window)
        for hotel in self.customer.hotels:
            i = hotel.row
            if tick == 1:
                medians = [self.comp_median(day, hotel, s) for s in window]
                mean = np.array(
                    [self.expected_new_bookings(hotel, s, day, m) for s, m in zip(window, medians)]
                )
                wanted = poisson_draw(self._daily_luck[day, i, stays], mean)
                self.daily_rates[day, i, stays] = self.rates[i, stays]
                self.daily_medians[day, i, stays] = medians
                if self.ticks == 1:
                    planned = wanted
                else:
                    self._planned_mean[i, stays] = mean
                    self._planned_rate[i, stays] = self.rates[i, stays]
                    self._split_rng[i] = np.random.default_rng(
                        [self.seed, TICK_STREAM, *hotel.key.encode(), day]
                    )
                    self._planned[:, i, stays] = self._split(self._split_rng[i], wanted)
                    planned = self._planned[0, i, stays]
            else:
                planned = self._planned[tick - 1, i, stays]
            taken = np.minimum(planned, hotel.rooms - self.rooms[i, stays])
            self.rooms[i, stays] += taken
            self.revenue[i, stays] += taken * self.rates[i, stays]
            self.daily_rooms[day, i, stays] += taken
            self.tick_rooms[day, tick - 1, i, stays] = taken
            self.tick_rates[day, tick - 1, i, stays] = self.rates[i, stays]

    def _split(self, rng: np.random.Generator, wanted: np.ndarray) -> np.ndarray:
        """Each stay date's bookings assigned to the day's ticks, one draw per booking from the
        hotel's own stream: a [tick, stay] array of counts that sums to `wanted` over the ticks."""
        return rng.multinomial(wanted, np.full(self.ticks, 1 / self.ticks)).T

    def set_rates(
        self, changes: dict[tuple[str, int], float], day: int | None = None, tick: int | None = None
    ) -> None:
        """New rates by (hotel key, stay day). Called after a day's bookings, so they apply from
        the next day. With several ticks, called after a tick's bookings with the day and tick,
        so a change applies from the next tick: the bookings still to come that day are thinned
        or topped up in proportion to the demand response at the new rate."""
        for (hotel_key, stay_day), rate in changes.items():
            hotel = self.customer.hotel(hotel_key)
            i = hotel.row
            if tick is not None and tick < self.ticks and day is not None:
                self._rebook(i, stay_day, rate, tick)
            self.rates[i, stay_day] = rate

    def _rebook(self, row: int, stay_day: int, rate: float, tick: int) -> None:
        """Thin or top up the stay date's bookings planned for the ticks after `tick`, in
        proportion to the demand response at the new rate against the rate they were drawn at."""
        old = self._planned_rate[row, stay_day]
        if not old or rate == old:
            return
        factor = (rate / old) ** -ELASTICITY
        rng = self._split_rng[row]
        later = self._planned[tick:, row, stay_day]
        if factor < 1:
            later[:] = rng.binomial(later, factor)
        else:
            extra = self._planned_mean[row, stay_day] / self.ticks * (factor - 1)
            later[:] += rng.poisson(extra, size=later.shape)
        self._planned_rate[row, stay_day] = rate

    def occupancy(self, hotel: Hotel, stays: Sequence[int]) -> float:
        """Rooms sold over rooms available, for a range of stay dates."""
        return self.rooms[hotel.row, list(stays)].sum() / (hotel.rooms * len(stays))

    def average_rate(self, hotel: Hotel, stays: Sequence[int] = range(HORIZON_DAYS)) -> float:
        """Room revenue over rooms sold: the average daily rate. nan when nothing was sold."""
        sold = self.rooms[hotel.row, list(stays)].sum()
        return self.room_revenue(hotel, stays) / float(sold) if sold else math.nan

    def revpar(self, hotel: Hotel, stays: Sequence[int] = range(HORIZON_DAYS)) -> float:
        """Room revenue over rooms available: revenue per available room."""
        return self.room_revenue(hotel, stays) / (hotel.rooms * len(stays))

    def room_revenue(self, hotel: Hotel, stays: Sequence[int] = range(HORIZON_DAYS)) -> float:
        """The rate in force on each booking day, summed over the rooms booked that day."""
        return float(self.revenue[hotel.row, list(stays)].sum())

    def contribution(self, hotel: Hotel, stays: Sequence[int] = range(HORIZON_DAYS)) -> float:
        """Room revenue minus the cost of servicing every room sold."""
        sold = self.rooms[hotel.row, list(stays)].sum()
        return self.room_revenue(hotel, stays) - float(sold) * hotel.room_cost


def lagged_change(
    daily_rates: np.ndarray, react: bool, day: int, hotel: Hotel, stay_day: int
) -> float:
    """The hotel's change from its start rate that its competitors react to on a shop day: its
    rate in force REACTION_LAG days earlier, read from a daily log of rates. It is zero when the
    reaction is off, before that day exists, and where the stay date was outside that day's
    window."""
    if not react or day < REACTION_LAG:
        return 0.0
    rate = daily_rates[day - REACTION_LAG, hotel.row, stay_day]
    return float(rate - hotel.start_rate) if rate else 0.0


# Called after each day's bookings on days 0 to 59; returns new rates by
# (hotel key, stay day), which apply from the next day. With several ticks a day it is called
# after each tick's bookings with the tick as a third argument, and the rates apply from the
# next tick.
Decide = Callable[..., dict[tuple[str, int], float]]


def simulate(
    seed: int,
    decide: Decide | None = None,
    last_day: int = HORIZON_DAYS - 1,
    customer: Customer | None = None,
    demand_bias: float = DEMAND_BIAS,
    react: bool = False,
    market_elasticity: float | None = None,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
    ticks: int = TICKS_PER_DAY,
) -> Books:
    """Run the booking loop on days 0 to last_day (149 for a full run) and return the books.

    Without decide, every rate stays at the hotel's starting rate. Without a
    customer, the market is the demo market. The demand bias multiplies the
    simulator's demand, and nothing the agent reads carries it. With react, the
    competitors follow the hotels' rate changes (shops.py). The market elasticity
    is the market's response to the comp median's level (demand.py), the
    customer file's unless given. The scenario is the air schedule's filings,
    and churn adds the seed's weekly revisions. ticks is the clock the run's sources answer on.
    """
    books = Books(seed, customer, demand_bias, react, market_elasticity, scenario, churn, ticks)
    for day in range(last_day + 1):
        for tick in range(1, ticks + 1):
            books.book(day, tick)
            if decide is not None and day < SIM_DAYS:
                if ticks == 1:
                    books.set_rates(decide(day, books))
                else:
                    books.set_rates(decide(day, books, tick), day, tick)
    return books


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the booking loop at fixed rates.")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--demand-bias", type=float, default=DEMAND_BIAS, metavar="F")
    arguments = parser.parse_args()
    seed, demand_bias = arguments.seed, arguments.demand_bias
    books = simulate(seed, demand_bias=demand_bias)
    bias = f", demand bias {demand_bias:g}" if demand_bias != DEMAND_BIAS else ""
    print(f"Fixed-rate run, seed {seed}, the demo market{bias}")
    print(f"{'':28}{'occupancy':>12}{'occupancy':>12}{'room revenue':>16}{'contribution':>16}")
    print(f"{'':28}{'stays 0-59':>12}{'stays 0-149':>12}{'stays 0-149':>16}{'stays 0-149':>16}")
    for hotel in books.customer.hotels:
        print(
            f"{hotel.name:28}{books.occupancy(hotel, range(SIM_DAYS)):12.1%}"
            f"{books.occupancy(hotel, range(HORIZON_DAYS)):12.1%}"
            f"{books.room_revenue(hotel):16,.0f}{books.contribution(hotel):16,.0f}"
        )
