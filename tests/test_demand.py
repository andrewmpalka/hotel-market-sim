"""Module 3: the simulator's expected and normal demand."""

import pytest

from hotel_market.customer import demo
from hotel_market.demand import expected_demand, known_seat_change, normal_demand
from hotel_market.schedule import seat_change
from hotel_market.shocks import event_uplift
from hotel_market.world import stay_window, weekday

DEMO = demo()

# The day-of-week table in CLAUDE.md, Monday to Sunday.
DOWNTOWN = (0.95, 1.10, 1.10, 1.05, 0.90, 0.95, 0.80)
TABLE = {
    "convention": DOWNTOWN,
    "full-service": DOWNTOWN,
    "lifestyle": (0.85, 0.85, 0.90, 1.00, 1.20, 1.25, 0.90),
    "airport": (1.05, 0.90, 1.00, 1.05, 1.00, 0.85, 1.05),
}


def test_day_of_week_factors_match_the_table():
    assert {h.key: h.weekday_factors for h in DEMO.hotels} == TABLE


def test_normal_demand_is_rooms_x_base_occupancy_x_day_of_week_factor():
    base_occupancy = {"convention": 0.75, "full-service": 0.75, "lifestyle": 0.75, "airport": 0.85}
    for hotel in DEMO.hotels:
        for stay_day in range(14):
            expected = hotel.rooms * base_occupancy[hotel.key] * TABLE[hotel.key][weekday(stay_day)]
            assert normal_demand(hotel, stay_day) == pytest.approx(expected)


@pytest.mark.parametrize("as_of_day", [0, 9, 10, 19, 20, 21, 39, 40, 41, 59])
def test_expected_demand_follows_the_formula(as_of_day):
    change = seat_change(as_of_day)
    for hotel in DEMO.hotels:
        for stay_day in stay_window(as_of_day):
            formula = (
                normal_demand(hotel, stay_day)
                * (1 + hotel.air_share * change[stay_day])
                * (1 + event_uplift(hotel.key, stay_day, as_of_day))
            )
            assert expected_demand(hotel, stay_day, as_of_day) == pytest.approx(formula)


def test_nothing_changes_demand_before_day_10():
    for as_of_day in (0, 9):
        for hotel in DEMO.hotels:
            for stay_day in stay_window(as_of_day):
                assert expected_demand(hotel, stay_day, as_of_day) == normal_demand(hotel, stay_day)


def test_convention_raises_downtown_demand_35_percent_from_day_10():
    for hotel in DEMO.hotels:
        ratio = expected_demand(hotel, 46, as_of_day=10) / expected_demand(hotel, 46, as_of_day=9)
        assert ratio == pytest.approx(1.35 if hotel.name.startswith("Downtown") else 1.0)


def test_new_flights_raise_demand_from_day_20():
    # Day 55 is a Sunday: the 720 new seats are 17% on top of 4,244.
    for hotel in DEMO.hotels:
        assert expected_demand(hotel, 55, as_of_day=19) == normal_demand(hotel, 55)
        ratio = expected_demand(hotel, 55, as_of_day=20) / normal_demand(hotel, 55)
        assert ratio == pytest.approx(1 + hotel.air_share * 720 / 4244)
    # The airport hotel moves most: 0.80 x 17% = 13.6%.
    airport = DEMO.hotel("airport")
    assert expected_demand(airport, 55, as_of_day=20) / normal_demand(airport, 55) == pytest.approx(
        1.136, abs=1e-3
    )


def test_route_cut_lowers_demand_from_day_40():
    # Day 80 is a Thursday: 720 seats added and 480 cut leave seats 240 above 4,244.
    for hotel in DEMO.hotels:
        assert expected_demand(hotel, 80, as_of_day=40) < expected_demand(hotel, 80, as_of_day=39)
        ratio = expected_demand(hotel, 80, as_of_day=40) / normal_demand(hotel, 80)
        assert ratio == pytest.approx(1 + hotel.air_share * 240 / 4244)


@pytest.mark.parametrize("as_of_day", [-1, 19, 20, 21, 39, 40, 41])
def test_known_seat_change_matches_the_schedule(as_of_day):
    assert dict(known_seat_change(as_of_day)) == seat_change(as_of_day).to_dict()


def test_known_seat_change_is_read_only():
    with pytest.raises(TypeError):
        known_seat_change(20)[55] = 0.0
