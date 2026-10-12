"""bookings.py

The daily booking loop. For every hotel and stay date, the books hold three things. They are the
rooms on the books, the room revenue booked and the rate the hotel charges.

Before day 0's bookings, each stay date in the window is loaded with the bookings made before the
run starts. That load is a draw around normal_demand x curve(days out + 1) at the hotel's
starting rate. Then on each day from 0 to 149, every hotel and stay date in the window gets new
bookings. They are drawn around

    expected_demand x (curve today - curve yesterday)
    x (rate / comp median) ** -ELASTICITY

and capped at the rooms still unsold. Rates can change on days 0 to 59. A change applies from the
next day, and rates are frozen from day 60.

Every draw has its own random number, fixed by the seed before the run starts. The function
poisson_draw turns it into a Poisson count. A change to one rate changes only that stay date's
draws. A fixed-rate run and an agent run with the same seed therefore differ only where the agent
acted.

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
from hotel_market.demand import expected_demand, normal_demand
from hotel_market.schedule import HORIZON_DAYS
from hotel_market.shops import comp_median
from hotel_market.world import SIM_DAYS, Hotel, stay_window

ELASTICITY = 1.5  # bookings scale with (rate / comp median) ** -ELASTICITY
BOOKING_STREAM = 2  # keeps these draws apart from the rate-shop noise (stream 1)


def preload_mean(hotel: Hotel, stay_day: int, customer: Customer | None = None) -> float:
    """Rooms expected on the books for a stay date before day 0's bookings."""
    return normal_demand(hotel, stay_day) * (customer or demo()).curve(stay_day + 1)


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

    def __init__(self, seed: int, customer: Customer | None = None):
        self.seed = seed
        self.customer = customer or demo()
        hotels = self.customer.hotels
        rng = np.random.default_rng([seed, BOOKING_STREAM])
        self._preload_luck = rng.random((len(hotels), HORIZON_DAYS))
        self._daily_luck = rng.random((HORIZON_DAYS, len(hotels), HORIZON_DAYS))
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
        self.preload = np.zeros((len(hotels), HORIZON_DAYS), dtype=np.int64)
        self._preload()

    def _preload(self) -> None:
        """Bookings made before day 0: a draw around normal_demand x curve(days out + 1)."""
        window = stay_window(0)
        stays = np.array(window)
        for hotel in self.customer.hotels:
            i = hotel.row
            mean = np.array([preload_mean(hotel, s, self.customer) for s in window])
            rooms = np.minimum(poisson_draw(self._preload_luck[i, stays], mean), hotel.rooms)
            self.preload[i, stays] = rooms
            self.rooms[i, stays] = rooms
            self.revenue[i, stays] = rooms * self.rates[i, stays]

    def expected_new_bookings(
        self, hotel: Hotel, stay_day: int, day: int, median: float | None = None
    ) -> float:
        """The mean of a day's new bookings for a hotel and stay date. The competitor
        median is that day's shop, passed in when the caller already has it."""
        days_out = stay_day - day
        rate = self.rates[hotel.row, stay_day]
        if median is None:
            median = comp_median(day, hotel, stay_day, seed=self.seed, customer=self.customer)
        curve = self.customer.curve
        return (
            expected_demand(hotel, stay_day, day)
            * (curve(days_out) - curve(days_out + 1))
            * (rate / median) ** -ELASTICITY
        )

    def book(self, day: int) -> None:
        """Draw one day's new bookings for every hotel and stay date in the window."""
        window = stay_window(day)
        stays = np.array(window)
        for hotel in self.customer.hotels:
            i = hotel.row
            medians = [
                comp_median(day, hotel, s, seed=self.seed, customer=self.customer) for s in window
            ]
            mean = np.array(
                [self.expected_new_bookings(hotel, s, day, m) for s, m in zip(window, medians)]
            )
            wanted = poisson_draw(self._daily_luck[day, i, stays], mean)
            taken = np.minimum(wanted, hotel.rooms - self.rooms[i, stays])
            self.rooms[i, stays] += taken
            self.revenue[i, stays] += taken * self.rates[i, stays]
            self.daily_rooms[day, i, stays] = taken
            self.daily_rates[day, i, stays] = self.rates[i, stays]
            self.daily_medians[day, i, stays] = medians

    def set_rates(self, changes: dict[tuple[str, int], float]) -> None:
        """New rates by (hotel key, stay day). Called after a day's bookings, so
        they apply from the next day."""
        for (hotel_key, stay_day), rate in changes.items():
            self.rates[self.customer.hotel(hotel_key).row, stay_day] = rate

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


# Called after each day's bookings on days 0 to 59; returns new rates by
# (hotel key, stay day), which apply from the next day.
Decide = Callable[[int, Books], dict[tuple[str, int], float]]


def simulate(
    seed: int,
    decide: Decide | None = None,
    last_day: int = HORIZON_DAYS - 1,
    customer: Customer | None = None,
) -> Books:
    """Run the booking loop on days 0 to last_day (149 for a full run) and return the books.

    Without decide, every rate stays at the hotel's starting rate. Without a
    customer, the market is the demo market.
    """
    books = Books(seed, customer)
    for day in range(last_day + 1):
        books.book(day)
        if decide is not None and day < SIM_DAYS:
            books.set_rates(decide(day, books))
    return books


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the booking loop at fixed rates.")
    parser.add_argument("--seed", type=int, required=True)
    seed = parser.parse_args().seed
    books = simulate(seed)
    print(f"Fixed-rate run, seed {seed}, the demo market")
    print(f"{'':28}{'occupancy':>12}{'occupancy':>12}{'room revenue':>16}{'contribution':>16}")
    print(f"{'':28}{'stays 0-59':>12}{'stays 0-149':>12}{'stays 0-149':>16}{'stays 0-149':>16}")
    for hotel in books.customer.hotels:
        print(
            f"{hotel.name:28}{books.occupancy(hotel, range(SIM_DAYS)):12.1%}"
            f"{books.occupancy(hotel, range(HORIZON_DAYS)):12.1%}"
            f"{books.room_revenue(hotel):16,.0f}{books.contribution(hotel):16,.0f}"
        )
