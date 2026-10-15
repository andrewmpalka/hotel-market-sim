"""Module 3: the simulator's expected and normal demand."""

import pytest

from hotel_market.customer import demo
from hotel_market.demand import (
    DEMAND_BIAS,
    MARKET_ELASTICITY,
    expected_demand,
    known_passenger_change,
    normal_demand,
)
from hotel_market.schedule import (
    LOAD_FACTOR,
    RAMP_DAYS,
    RAMP_LOAD_FACTORS,
    UPGAUGE_SCENARIO,
    passenger_change,
)
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
    """Regression test: it rebuilds the formula from the same factors the code reads, so it
    catches a changed formula and cannot catch a wrong one."""
    base_occupancy = {"convention": 0.75, "full-service": 0.75, "lifestyle": 0.75, "airport": 0.85}
    for hotel in DEMO.hotels:
        for stay_day in range(14):
            expected = hotel.rooms * base_occupancy[hotel.key] * TABLE[hotel.key][weekday(stay_day)]
            assert normal_demand(hotel, stay_day) == pytest.approx(expected)


@pytest.mark.parametrize("as_of_day", [0, 9, 10, 19, 20, 21, 39, 40, 41, 59])
def test_expected_demand_follows_the_formula(as_of_day):
    """Regression test: it combines normal demand, the passenger change and the event uplift the
    way demand.py combines them, so it pins the formula rather than checking it against anything."""
    change = passenger_change(as_of_day)
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


def _ramped(seats: int, since: int) -> float:
    """The passengers a new route's seats carry this many days into its ramp."""
    opening, full = RAMP_LOAD_FACTORS
    return seats * (opening + (full - opening) * min(since, RAMP_DAYS) / RAMP_DAYS)


def test_new_flights_raise_demand_from_day_20():
    # Day 55 is a Sunday, five days into the new routes' ramp: their 720 seats carry
    # 720 x (0.60 + 0.25 x 5 / 90) passengers on top of a normal day's 4,244 x 0.80.
    change = _ramped(720, 5) / (4244 * LOAD_FACTOR)
    for hotel in DEMO.hotels:
        assert expected_demand(hotel, 55, as_of_day=19) == normal_demand(hotel, 55)
        ratio = expected_demand(hotel, 55, as_of_day=20) / normal_demand(hotel, 55)
        assert ratio == pytest.approx(1 + hotel.air_share * change)
    # The airport hotel moves most: 0.80 x 13.0% = 10.4%.
    airport = DEMO.hotel("airport")
    assert expected_demand(airport, 55, as_of_day=20) / normal_demand(airport, 55) == pytest.approx(
        1.104, abs=1e-3
    )


def test_route_cut_lowers_demand_from_day_40():
    # Day 80 is a Thursday, 30 days into the new routes' ramp: their 720 seats at the ramp load
    # factor, less the 480 cut at the mature one, leave passengers above a normal day's.
    change = (_ramped(720, 30) - 480 * LOAD_FACTOR) / (4244 * LOAD_FACTOR)
    for hotel in DEMO.hotels:
        assert expected_demand(hotel, 80, as_of_day=40) < expected_demand(hotel, 80, as_of_day=39)
        ratio = expected_demand(hotel, 80, as_of_day=40) / normal_demand(hotel, 80)
        assert ratio == pytest.approx(1 + hotel.air_share * change)


@pytest.mark.parametrize("as_of_day", [-1, 19, 20, 21, 39, 40, 41])
def test_known_passenger_change_matches_the_schedule(as_of_day):
    assert dict(known_passenger_change(as_of_day)) == passenger_change(as_of_day).to_dict()


def test_known_passenger_change_is_read_only():
    with pytest.raises(TypeError):
        known_passenger_change(20)[55] = 0.0


def test_the_demand_bias_multiplies_both_demands_and_is_1_by_default():
    assert DEMAND_BIAS == 1.0
    for hotel in DEMO.hotels:
        for stay_day in (0, 45, 100):
            assert normal_demand(hotel, stay_day) == normal_demand(hotel, stay_day, 1.0)
            assert normal_demand(hotel, stay_day, 0.9) == pytest.approx(
                0.9 * normal_demand(hotel, stay_day)
            )
            # The bias scales the whole formula, seats and events included.
            assert expected_demand(hotel, stay_day, 20, 1.1) == pytest.approx(
                1.1 * expected_demand(hotel, stay_day, 20)
            )


def test_the_market_elasticity_scales_demand_with_the_medians_level():
    # The default is 1.0, the customer file's value: a market-wide rise loses demand in
    # proportion. At 0.0 the level would move nothing.
    assert MARKET_ELASTICITY == 1.0 == DEMO.market_elasticity
    hotel = DEMO.hotel("convention")
    plain = expected_demand(hotel, 46, 10, market_elasticity=0.0)
    assert expected_demand(hotel, 46, 10, median_ratio=1.15, market_elasticity=0.0) == plain
    assert expected_demand(hotel, 46, 10, median_ratio=1.15) == pytest.approx(plain / 1.15)
    assert expected_demand(
        hotel, 46, 10, median_ratio=1.15, market_elasticity=0.5
    ) == pytest.approx(plain * 1.15**-0.5)
    assert expected_demand(hotel, 46, 10, 0.9, 1.15, 1.0) == pytest.approx(0.9 * plain / 1.15)


def test_a_scenario_changes_the_passengers_the_demand_reads():
    # An equipment change on a route that flew before the run keeps its load factor, so the
    # passenger change is the seat change.
    convention = DEMO.hotel("convention")
    assert known_passenger_change(15, UPGAUGE_SCENARIO)[52] == pytest.approx(270 / 4244)
    assert known_passenger_change(15)[52] == 0  # the default has filed nothing by day 15
    ratio = 1 + convention.air_share * 270 / 4244
    assert expected_demand(convention, 52, 15, scenario=UPGAUGE_SCENARIO) == pytest.approx(
        expected_demand(convention, 52, 15) * ratio
    )
