"""Module 2: the convention and the competitor rate cut."""

import statistics

import pytest

from hotel_market.customer import demo
from hotel_market.shocks import (
    EVENTS,
    RATE_CUTS,
    comp_rate_raise,
    event_uplift,
    events_as_of,
    rate_cut,
    rate_cuts_as_of,
)

DEMO = demo()

DOWNTOWN = {h.key for h in DEMO.hotels if h.name.startswith("Downtown")}
CONVENTION_NIGHTS = range(45, 49)
CUT_NIGHTS = range(37, 40)


def _cuts(stay_day, as_of_day):
    """Every competitor whose rate is cut for a stay date, with the size of the cut."""
    cuts = {
        c.name: rate_cut(h.key, c.name, stay_day, as_of_day)
        for h in DEMO.hotels
        for c in h.competitors
    }
    return {name: cut for name, cut in cuts.items() if cut}


def test_convention_is_not_known_before_day_10():
    assert events_as_of(9) == []
    for hotel in DEMO.hotels:
        for stay_day in CONVENTION_NIGHTS:
            assert event_uplift(hotel.key, stay_day, as_of_day=9) == 0


def test_convention_raises_downtown_demand_35_percent_on_days_45_to_48_from_day_10():
    assert len(DOWNTOWN) == 2
    for as_of_day in (10, 59):
        for key in DOWNTOWN:
            for stay_day in CONVENTION_NIGHTS:
                assert event_uplift(key, stay_day, as_of_day) == pytest.approx(0.35)
            assert event_uplift(key, 44, as_of_day) == 0
            assert event_uplift(key, 49, as_of_day) == 0


def test_convention_leaves_the_other_hotels_alone():
    for hotel in DEMO.hotels:
        if hotel.key not in DOWNTOWN:
            for stay_day in CONVENTION_NIGHTS:
                assert event_uplift(hotel.key, stay_day, as_of_day=59) == 0


def test_downtown_competitors_raise_rates_15_percent_on_convention_nights_from_day_10():
    for hotel in DEMO.hotels:
        for stay_day in CONVENTION_NIGHTS:
            assert comp_rate_raise(hotel.key, stay_day, as_of_day=9) == 0
            expected = 0.15 if hotel.key in DOWNTOWN else 0
            assert comp_rate_raise(hotel.key, stay_day, as_of_day=10) == pytest.approx(expected)
    for key in DOWNTOWN:
        assert comp_rate_raise(key, 44, as_of_day=10) == 0
        assert comp_rate_raise(key, 49, as_of_day=10) == 0


def test_rate_cut_is_not_shopped_before_day_30():
    assert rate_cuts_as_of(29) == []
    for stay_day in CUT_NIGHTS:
        assert _cuts(stay_day, as_of_day=29) == {}


def test_two_full_service_competitors_cut_20_percent_on_days_37_to_39_from_day_30():
    expected = {"full-service comp 1": 0.20, "full-service comp 2": 0.20}
    for as_of_day in (30, 59):
        for stay_day in CUT_NIGHTS:
            assert _cuts(stay_day, as_of_day) == pytest.approx(expected)
        assert _cuts(36, as_of_day) == {}
        assert _cuts(40, as_of_day) == {}


def test_the_cut_moves_the_full_service_comp_median_by_5_percent_or_more():
    # 5% is the comp median threshold that detect.py will flag (CLAUDE.md, module 6).
    hotel = DEMO.hotel("full-service")

    def median(as_of_day):
        return statistics.median(
            c.base_rate * (1 - rate_cut(hotel.key, c.name, 38, as_of_day))
            for c in hotel.competitors
        )

    assert median(30) / median(29) - 1 <= -0.05


def test_shocks_name_hotels_and_competitors_that_exist():
    for event in EVENTS:
        assert set(event.hotels) <= {h.key for h in DEMO.hotels}
    for cut in RATE_CUTS:
        assert set(cut.competitors) <= {c.name for c in DEMO.hotel(cut.hotel).competitors}
