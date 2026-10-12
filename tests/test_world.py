"""Module 1: hotels, comp sets, rate limits and the calendar."""

import statistics

import pytest

from hotel_market.customer import demo
from hotel_market.schedule import HORIZON_DAYS, build_schedule, seats_by_day
from hotel_market.world import LOOKAHEAD_DAYS, SIM_DAYS, stay_window, weekday

DEMO = demo()

# The hotel table in CLAUDE.md: rooms, start rate, share arriving by air, base occupancy.
TABLE = {
    "Downtown convention hotel": (400, 220, 0.60, 0.75),
    "Downtown full-service hotel": (250, 190, 0.45, 0.75),
    "Lifestyle hotel": (120, 240, 0.50, 0.75),
    "Airport hotel": (150, 140, 0.80, 0.85),
}


def test_hotels_match_the_table():
    assert {
        h.name: (h.rooms, h.start_rate, h.air_share, h.base_occupancy) for h in DEMO.hotels
    } == TABLE


def test_each_occupied_room_costs_a_third_of_the_start_rate():
    for hotel in DEMO.hotels:
        assert hotel.room_cost == pytest.approx(hotel.start_rate / 3)
    assert DEMO.hotel("airport").room_cost == pytest.approx(46.67, abs=0.01)


def test_each_hotel_has_four_competitors_within_10_percent_of_its_rate():
    for hotel in DEMO.hotels:
        assert len(hotel.competitors) == 4
        for comp in hotel.competitors:
            assert abs(comp.base_rate / hotel.start_rate - 1) <= 0.10


def test_hotel_keys_and_competitor_names_are_unique():
    keys = [h.key for h in DEMO.hotels]
    names = [c.name for h in DEMO.hotels for c in h.competitors]
    assert len(set(keys)) == len(keys)
    assert len(set(names)) == len(names)


def test_comp_set_median_starts_at_the_hotels_own_rate():
    # Not in CLAUDE.md: an assumption made in world.py so that every hotel
    # starts priced at its market.
    for hotel in DEMO.hotels:
        median = statistics.median(c.base_rate for c in hotel.competitors)
        assert median == pytest.approx(hotel.start_rate)


def test_floor_is_70_percent_and_ceiling_is_140_percent_of_start_rate():
    for hotel in DEMO.hotels:
        assert hotel.floor == pytest.approx(0.70 * hotel.start_rate)
        assert hotel.ceiling == pytest.approx(1.40 * hotel.start_rate)


def test_clamp_keeps_a_rate_between_floor_and_ceiling():
    airport = DEMO.hotel("airport")  # start rate 140: floor 98, ceiling 196
    assert airport.clamp(50) == pytest.approx(98)
    assert airport.clamp(500) == pytest.approx(196)
    assert airport.clamp(150) == 150


def test_simulation_runs_days_0_to_59_and_each_day_sees_90_stay_dates():
    assert SIM_DAYS == 60
    for day in range(SIM_DAYS):
        window = stay_window(day)
        assert len(window) == LOOKAHEAD_DAYS == 90
        assert window[0] == day


def test_every_stay_date_seen_is_inside_the_schedule():
    assert stay_window(SIM_DAYS - 1)[-1] < HORIZON_DAYS


def test_after_day_59_the_window_stops_at_stay_date_149():
    assert stay_window(100) == range(100, 150)
    assert stay_window(149) == range(149, 150)


def test_weekday_agrees_with_the_schedule():
    # The schedule flies fewer seats on Tuesdays (1) and Saturdays (5).
    seats = seats_by_day(build_schedule(as_of_day=-1))
    low_days = [day for day in range(HORIZON_DAYS) if seats[day] < seats.max()]
    assert weekday(0) == 0  # day 0 is a Monday
    assert low_days == [day for day in range(HORIZON_DAYS) if weekday(day) in (1, 5)]
