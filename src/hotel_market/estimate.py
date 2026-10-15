"""estimate.py

The agent learns the price elasticity from the bookings it has seen, instead of assuming the
simulator's value.

Each (stay date, booking day) pair of a hotel is one observation. It holds the rooms that day's
bookings took and the hotel's rate that day, from the bookings feed, and the competitor median
shopped that day, from the rate shops. It also holds the baseline, the bookings expected at a rate
ratio of 1.

The baseline is the agent's own forecast as of the booking day. It is multiplied by the booking
curve's rise from the day before. The forecast (forecast.py) is normal demand with its weekday
factor, the seats and any event known by then. Under a market elasticity it also carries the
market's answer to that day's comp median, so the estimator and the forecast agree. Without the
term, the market's answer to a moved median reads as price response, and the fit drifts.

The model is a Poisson regression with the log of the baseline as an offset. It has an intercept
that absorbs errors in the demand level and a slope on log(rate / competitor median). The
elasticity is the negative of the slope. A learn:X --level agent feeds the intercept back: it
scales its forecast by exp(intercept) once the fit has enough observations (level_factor). The
baseline stays unscaled, so the intercept keeps measuring the level against the raw forecast.

A normal prior on the elasticity keeps the estimate sensible while the rate ratio has barely moved.
The prior is centred on the value the agent is given, with standard deviation PRIOR_SD. The ratio
has barely moved most of the time, because with flat rates it moves only when a shock moves a
competitor median or the agent changes a rate. The estimate is clamped to ELASTICITY_MIN to
ELASTICITY_MAX.

Three things are left out: every booking made on or after as_of_day, a stay date's observations from
the day it sold out, and the day-0 preload. Rooms, and not price, capped the sold-out bookings, and
the simulator draws the preload around normal demand x curve with no price response at all.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from hotel_market.forecast import ORACLE_MARKET_ELASTICITY, event_uplift, normal_demand
from hotel_market.sources import Sources
from hotel_market.world import HORIZON_DAYS, Hotel, stay_window

PRIOR_SD = 0.5  # the standard deviation of the normal prior on the elasticity
ELASTICITY_MIN = 0.5  # the estimate is clamped to this range
ELASTICITY_MAX = 3.0
# With --level the agent scales its forecast by exp(intercept), the fitted demand level against
# the baseline, once the fit has this many observations, clamped to this range.
LEVEL_OBSERVATIONS = 500
LEVEL_MIN = 0.5
LEVEL_MAX = 2.0


@dataclass(frozen=True)
class Observations:
    """One row per (stay date, booking day) the estimate may use, as arrays."""

    stay_days: np.ndarray
    booking_days: np.ndarray
    bookings: np.ndarray  # the rooms the day's draw took
    log_ratio: np.ndarray  # log(rate / competitor median) that day
    log_baseline: np.ndarray  # log of the bookings expected at a rate ratio of 1

    def __len__(self) -> int:
        return len(self.bookings)


@dataclass(frozen=True)
class Estimate:
    """What the fit says about a hotel's elasticity as of a day."""

    elasticity: float  # the fit's answer, clamped to the range
    standard_error: float  # from the curvature at the optimum, prior included
    observations: int
    prior: float
    intercept: float  # log of the demand level against the baseline; 0 when the baseline is right


def level_factor(estimate: Estimate) -> float:
    """The factor a --level agent scales its forecast by: exp(intercept), clamped to LEVEL_MIN
    to LEVEL_MAX. It is 1 until the fit has LEVEL_OBSERVATIONS observations, as the elasticity
    is held near its prior until the data say otherwise."""
    if estimate.observations < LEVEL_OBSERVATIONS:
        return 1.0
    return min(max(float(np.exp(estimate.intercept)), LEVEL_MIN), LEVEL_MAX)


def observations(
    sources: Sources,
    hotel: Hotel,
    as_of_day: int,
    market_elasticity: float = ORACLE_MARKET_ELASTICITY,
) -> Observations:
    """The observations the agent may use on as_of_day. They are the bookings made before that day,
    inside that day's window, and before the stay date sold out. The market elasticity is the
    run's, and the baseline carries its term."""
    i = hotel.row
    history = sources.bookings.history(as_of_day)
    rooms = history.taken[:, i, :]
    rates = history.rates[:, i, :]
    medians = sources.shops.median_history(as_of_day)[:, i, :]
    on_the_books = history.opening[i][None, :] + np.cumsum(rooms, axis=0)  # after each day
    keep = (rates > 0) & (on_the_books < hotel.rooms)
    booking_days, stay_days = np.nonzero(keep)
    return Observations(
        stay_days=stay_days,
        booking_days=booking_days,
        bookings=rooms[keep],
        log_ratio=np.log(rates[keep] / medians[keep]),
        log_baseline=np.log(_baselines(sources, hotel, as_of_day, market_elasticity)[keep]),
    )


def _baselines(
    sources: Sources,
    hotel: Hotel,
    as_of_day: int,
    market_elasticity: float = ORACLE_MARKET_ELASTICITY,
) -> np.ndarray:
    """The bookings expected at a rate ratio of 1, by [booking day, stay day], for the days before
    as_of_day. Each is the forecast as known on the booking day (forecast.expected_demand, with
    the market term at that day's comp median) times the booking curve's rise. It is zero outside
    each day's window."""
    curve = hotel.curve
    normal = np.array([normal_demand(hotel, stay_day) for stay_day in range(HORIZON_DAYS)])
    baselines = np.zeros((as_of_day, HORIZON_DAYS))
    for day in range(as_of_day):
        stays = np.array(stay_window(day))
        seats = sources.schedules.seat_change(day)
        seat_factor = 1 + hotel.air_share * np.array([seats[s] for s in stays])
        uplift = 1 + np.array([event_uplift(hotel, s, day, sources) for s in stays])
        rise = curve(stays - day) - curve(stays - day + 1)
        baselines[day, stays] = normal[stays] * seat_factor * uplift * rise
    if market_elasticity:
        # The comp medians shopped on each booking day, over each stay date's starting level,
        # where the day's window shopped the date; the forecast uses the same ratio.
        medians = sources.shops.median_history(as_of_day)[:, hotel.row, :]
        first = np.array([sources.shops.first_median(hotel, s) for s in range(HORIZON_DAYS)])
        ratio = np.ones_like(baselines)
        shopped = medians > 0
        ratio[shopped] = (medians / first[None, :])[shopped]
        baselines *= ratio**-market_elasticity
    return baselines


def estimate_elasticity(
    sources: Sources,
    hotel: Hotel,
    as_of_day: int,
    prior: float,
    market_elasticity: float = ORACLE_MARKET_ELASTICITY,
) -> Estimate:
    """The hotel's elasticity as of a day, from the bookings made before it, with the run's market
    elasticity in the baseline."""
    data = observations(sources, hotel, as_of_day, market_elasticity)
    intercept, slope, standard_error = fit(data, prior)
    return Estimate(
        elasticity=min(max(-slope, ELASTICITY_MIN), ELASTICITY_MAX),
        standard_error=standard_error,
        observations=len(data),
        prior=prior,
        intercept=intercept,
    )


def fit(data: Observations, prior: float) -> tuple[float, float, float]:
    """The Poisson regression: (intercept, slope, standard error of the slope).

    Maximises the log-likelihood plus the log of the normal prior on the elasticity by Newton's
    method. The prior is -slope ~ N(prior, PRIOR_SD ** 2). The objective is concave, so every
    step improves it once the step is short enough. The steps are halved only to guard against
    overshooting far from the optimum. The standard error comes from the curvature at the
    optimum, prior included. With no observations it is PRIOR_SD.
    """
    y, x, offset = data.bookings, data.log_ratio, data.log_baseline
    precision = 1 / PRIOR_SD**2
    if len(y) == 0:
        return 0.0, -prior, PRIOR_SD

    def objective(a: float, b: float) -> float:
        linear = offset + a + b * x
        return float(y @ linear - np.exp(linear).sum() - 0.5 * precision * (b + prior) ** 2)

    def curvature(a: float, b: float) -> np.ndarray:
        mu = np.exp(offset + a + b * x)
        return -np.array(
            [[mu.sum(), (x * mu).sum()], [(x * mu).sum(), (x * x * mu).sum() + precision]]
        )

    a, b = 0.0, -prior
    value = objective(a, b)
    for _ in range(100):
        mu = np.exp(offset + a + b * x)
        gradient = np.array([(y - mu).sum(), (x * (y - mu)).sum() - precision * (b + prior)])
        step = np.linalg.solve(curvature(a, b), -gradient)
        scale = 1.0
        while True:
            trial = objective(a + scale * step[0], b + scale * step[1])
            if trial >= value or scale < 1e-8:
                break
            scale /= 2
        if trial < value:
            break  # no step improves the objective: this is the optimum to machine precision
        a, b, value = a + scale * step[0], b + scale * step[1], trial
        if np.abs(scale * step).max() < 1e-10:
            break
    covariance = np.linalg.inv(-curvature(a, b))
    return a, b, float(np.sqrt(covariance[1, 1]))
