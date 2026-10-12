"""Module 9, estimate.py: the agent learns the elasticity from the bookings it has seen."""

import numpy as np
import pytest

from hotel_market import bookings, estimate
from hotel_market.agent import Agent, ElasticityMode
from hotel_market.bookings import Books, simulate
from hotel_market.customer import demo
from hotel_market.estimate import (
    ELASTICITY_MAX,
    ELASTICITY_MIN,
    PRIOR_SD,
    Observations,
    estimate_elasticity,
    fit,
    observations,
)
from hotel_market.forecast import expected_demand
from hotel_market.simulated import deciding, simulated_sources
from hotel_market.world import stay_window

DEMO = demo()

SEED = 7
PRIOR = 1.5
# The estimate lands within this many standard errors of the truth. The standard error is
# the fit's posterior standard deviation, prior included, and the model is the simulator's
# own booking formula, so (estimate - truth) / standard error behaves like a standard
# normal draw: three standard errors fails about one check in 370 by chance. The twelve
# checks below are one fixed draw each, so they either always pass or always fail; the
# largest |z| measured was 1.6, on seeds 7 and 3.
TOLERANCE_SE = 3


@pytest.fixture(scope="module")
def fixed():
    """A fixed-rate run with seed 7."""
    return simulate(SEED)


@pytest.fixture(scope="module")
def learned(tmp_path_factory):
    """Seed-7 learn:1.5 agent runs with the simulator's elasticity at 1.0, 1.5 and 2.0."""
    runs = {}
    for true in (1.0, 1.5, 2.0):
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(bookings, "ELASTICITY", true)
            cache = tmp_path_factory.mktemp("cache")
            agent = Agent(SEED, cache, elasticity=ElasticityMode("learn", PRIOR))
            runs[true] = simulate(SEED, deciding(agent))
    return runs


def _made_up(elasticity, n=4000, seed=1):
    """Observations drawn by hand around a known elasticity, with no sell-outs."""
    rng = np.random.default_rng(seed)
    log_ratio = rng.uniform(-0.15, 0.15, n)
    log_baseline = np.log(rng.uniform(2, 12, n))
    taken = rng.poisson(np.exp(log_baseline - elasticity * log_ratio))
    return Observations(np.zeros(n, int), np.zeros(n, int), taken, log_ratio, log_baseline)


def test_the_day_59_estimate_recovers_the_simulators_elasticity(learned):
    for true, books in learned.items():
        for hotel in DEMO.hotels:
            found = estimate_elasticity(simulated_sources(books), hotel, 59, PRIOR)
            assert found.observations > 5000
            assert abs(found.elasticity - true) <= TOLERANCE_SE * found.standard_error
            assert found.standard_error < PRIOR_SD  # the bookings taught it something


@pytest.fixture(scope="module")
def answered(tmp_path_factory):
    """A seed-7 learn:1.5 run with competitors reacting and a market elasticity of 1.0, the
    agent told the value."""
    cache = tmp_path_factory.mktemp("cache")
    agent = Agent(SEED, cache, elasticity=ElasticityMode("learn", PRIOR), market_elasticity=1.0)
    return simulate(SEED, deciding(agent), react=True, market_elasticity=1.0)


def test_the_day_59_estimate_recovers_the_elasticity_under_a_market_response(answered):
    # With the market's answer in the baseline, the fit lands on the truth as it does at zero.
    # Without it, the market's answer to a moved median reads as price response, and the
    # estimates drift: up where the hotel's own raises moved the median, down on the convention
    # nights, where the competitors' raise did.
    sources = simulated_sources(answered)
    error_with_term = error_without = 0.0
    for hotel in DEMO.hotels:
        found = estimate_elasticity(sources, hotel, 59, PRIOR, market_elasticity=1.0)
        assert found.observations > 5000
        assert abs(found.elasticity - bookings.ELASTICITY) <= TOLERANCE_SE * found.standard_error
        error_with_term += abs(found.elasticity - bookings.ELASTICITY) / found.standard_error
        plain = estimate_elasticity(sources, hotel, 59, PRIOR)
        error_without += abs(plain.elasticity - bookings.ELASTICITY) / plain.standard_error
    assert error_without > 2 * error_with_term


def test_the_baseline_is_the_forecast_with_the_market_term_times_the_curves_rise(answered):
    sources = simulated_sources(answered)
    hotel = DEMO.hotel("convention")
    data = observations(sources, hotel, 59, market_elasticity=1.0)
    for k in range(0, len(data), 997):
        day, stay = int(data.booking_days[k]), int(data.stay_days[k])
        rise = DEMO.curve(stay - day) - DEMO.curve(stay - day + 1)
        forecast = expected_demand(hotel, stay, day, sources, 1.0) * rise
        assert np.exp(data.log_baseline[k]) == pytest.approx(forecast)
    # At a market elasticity of 0 the baseline is the plain forecast, as before.
    plain = observations(sources, hotel, 59)
    k = 5
    day, stay = int(plain.booking_days[k]), int(plain.stay_days[k])
    rise = DEMO.curve(stay - day) - DEMO.curve(stay - day + 1)
    assert np.exp(plain.log_baseline[k]) == pytest.approx(
        expected_demand(hotel, stay, day, sources) * rise
    )


def test_the_estimate_uses_no_booking_made_on_or_after_as_of_day(fixed):
    hotel = DEMO.hotel("airport")
    i = hotel.row
    before = estimate_elasticity(simulated_sources(fixed), hotel, 30, PRIOR)
    tampered = simulate(SEED)
    tampered.daily_rooms[30:, i, :] += 3
    tampered.daily_rates[30:, i, :] *= 1.2
    tampered.rooms[i, :] = 0
    assert estimate_elasticity(simulated_sources(tampered), hotel, 30, PRIOR) == before
    # A booking made the day before as_of_day does count.
    tampered.daily_rooms[29, i, 40:60] += 3
    assert estimate_elasticity(simulated_sources(tampered), hotel, 30, PRIOR) != before


def test_observations_stop_on_the_day_a_stay_date_sells_out():
    books = Books(SEED)
    for day in range(21):
        books.book(day)
    hotel = DEMO.hotel("lifestyle")
    i = hotel.row
    # Fill stay date 25 on day 15, and stay date 26 from the preload.
    on_the_books = books.preload[i, 25] + books.daily_rooms[:15, i, 25].sum()
    books.daily_rooms[15, i, 25] = hotel.rooms - on_the_books
    books.preload[i, 26] = hotel.rooms
    data = observations(simulated_sources(books), hotel, 21)
    assert data.booking_days[data.stay_days == 25].max() == 14
    assert not (data.stay_days == 26).any()
    assert (data.stay_days == 27).sum() == 21  # one per day it was in the window


def test_the_preload_is_not_an_observation():
    books = Books(SEED)
    hotel = DEMO.hotels[0]
    sources = simulated_sources(books)
    assert len(observations(sources, hotel, 0)) == 0
    books.book(0)
    data = observations(sources, hotel, 1)
    assert set(data.booking_days) == {0} and len(data) == len(stay_window(0))
    assert data.bookings.sum() == books.daily_rooms[0, 0].sum()
    assert data.bookings.sum() < books.rooms[0].sum()  # the preload is on the books, not here


def test_with_no_observations_the_estimate_is_the_prior():
    found = estimate_elasticity(simulated_sources(Books(SEED)), DEMO.hotels[0], 0, 1.2)
    assert found.observations == 0
    assert found.elasticity == 1.2 and found.standard_error == PRIOR_SD


def test_the_same_seed_gives_the_same_estimate(fixed):
    hotel = DEMO.hotel("convention")
    first = estimate_elasticity(simulated_sources(fixed), hotel, 45, PRIOR)
    assert estimate_elasticity(simulated_sources(simulate(SEED)), hotel, 45, PRIOR) == first
    assert estimate_elasticity(simulated_sources(simulate(SEED + 1)), hotel, 45, PRIOR) != first


def test_the_fit_recovers_a_known_elasticity_from_made_up_bookings():
    data = _made_up(1.8)
    intercept, slope, standard_error = fit(data, prior=1.0)
    assert abs(-slope - 1.8) <= TOLERANCE_SE * standard_error
    assert abs(intercept) < 0.05 and standard_error < 0.1  # the data outweigh the prior
    # The intercept absorbs a wrong demand level: a baseline half the true one.
    level_off = Observations(
        data.stay_days,
        data.booking_days,
        data.bookings,
        data.log_ratio,
        data.log_baseline - np.log(2),
    )
    intercept, slope_again, _ = fit(level_off, prior=1.0)
    assert intercept == pytest.approx(np.log(2), abs=0.05)
    assert slope_again == pytest.approx(slope, abs=0.01)


def test_the_prior_holds_the_estimate_when_the_ratio_never_moves():
    data = _made_up(1.8)
    flat = Observations(
        data.stay_days, data.booking_days, data.bookings, np.zeros(len(data)), data.log_baseline
    )
    _, slope, standard_error = fit(flat, prior=1.2)
    assert -slope == pytest.approx(1.2) and standard_error == pytest.approx(PRIOR_SD)


def test_the_estimate_is_clamped_to_the_range(monkeypatch, fixed):
    for true, limit in ((6.0, ELASTICITY_MAX), (0.05, ELASTICITY_MIN)):
        monkeypatch.setattr(estimate, "observations", lambda *args, true=true: _made_up(true))
        found = estimate_elasticity(simulated_sources(fixed), DEMO.hotels[0], 59, PRIOR)
        assert found.elasticity == limit and found.standard_error > 0
