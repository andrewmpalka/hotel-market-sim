"""Module 4: competitor rates, comp medians and each hotel's starting rate."""

import statistics

import pytest

from hotel_market import shops
from hotel_market.customer import demo
from hotel_market.schedule import HORIZON_DAYS
from hotel_market.shops import comp_median, comp_rates

DEMO = demo()

SEED = 7
DOWNTOWN = {h.key for h in DEMO.hotels if h.name.startswith("Downtown")}


def test_hotel_starts_level_with_its_comp_median():
    for hotel in DEMO.hotels:
        # Before noise, the comp median is exactly the hotel's start rate ...
        assert statistics.median(c.base_rate for c in hotel.competitors) == pytest.approx(
            hotel.start_rate
        )
        # ... and noise of up to 3% on each competitor moves the median at most 3%.
        for stay_day in range(HORIZON_DAYS):
            assert abs(comp_median(0, hotel, stay_day, seed=SEED) / hotel.start_rate - 1) <= 0.03


def test_competitor_rates_are_base_rate_x_noise_with_no_weekly_pattern():
    # Before any shock every rate is within 3% of the base rate, so no
    # day-of-week factor can be hiding in it.
    offsets = [
        rate / comp.base_rate - 1
        for hotel in DEMO.hotels
        for stay_day in range(HORIZON_DAYS)
        for comp, rate in zip(hotel.competitors, comp_rates(0, hotel, stay_day, seed=SEED).values())
    ]
    assert -0.03 <= min(offsets) < -0.02
    assert 0.02 < max(offsets) <= 0.03


def test_comp_median_moves_only_when_a_shock_becomes_known():
    # Noise is drawn once per competitor and stay date, so day-to-day moves come from shocks.
    moved = set()
    for hotel in DEMO.hotels:
        for stay_day in range(HORIZON_DAYS):
            medians = [comp_median(d, hotel, stay_day, seed=SEED) for d in range(HORIZON_DAYS)]
            moved |= {
                (d, hotel.key, stay_day)
                for d in range(1, HORIZON_DAYS)
                if medians[d] != medians[d - 1]
            }
    convention = {(10, key, s) for key in DOWNTOWN for s in range(45, 49)}
    rate_cut = {(30, "full-service", s) for s in range(37, 40)}
    assert moved == convention | rate_cut


def test_rates_depend_only_on_the_seed():
    hotel = DEMO.hotel("airport")
    first = [comp_rates(0, hotel, s, seed=SEED) for s in range(90)]
    shops._noise.cache_clear()  # draw the noise again from scratch
    assert [comp_rates(0, hotel, s, seed=SEED) for s in range(90)] == first
    assert [comp_rates(0, hotel, s, seed=SEED + 1) for s in range(90)] != first


def test_downtown_competitors_raise_rates_15_percent_on_convention_nights_from_shop_day_10():
    for hotel in DEMO.hotels:
        factor = 1.15 if hotel.key in DOWNTOWN else 1.0
        for stay_day in range(45, 49):
            before = comp_rates(9, hotel, stay_day, seed=SEED)
            after = comp_rates(10, hotel, stay_day, seed=SEED)
            assert after == pytest.approx({name: rate * factor for name, rate in before.items()})


def test_two_cheapest_full_service_competitors_cut_20_percent_from_shop_day_30():
    hotel = DEMO.hotel("full-service")
    factor = {
        "full-service comp 1": 0.80,
        "full-service comp 2": 0.80,
        "full-service comp 3": 1.00,
        "full-service comp 4": 1.00,
    }
    for stay_day in range(37, 40):
        before = comp_rates(29, hotel, stay_day, seed=SEED)
        after = comp_rates(30, hotel, stay_day, seed=SEED)
        assert after == pytest.approx({name: rate * factor[name] for name, rate in before.items()})
        # Big enough for detect.py's 5% comp median flag.
        drop = (
            comp_median(30, hotel, stay_day, seed=SEED)
            / comp_median(29, hotel, stay_day, seed=SEED)
            - 1
        )
        assert drop <= -0.05
