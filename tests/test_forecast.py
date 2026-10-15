"""Module 10, forecast.py: the agent's demand model, which the simulator's demand matches
by construction for the demo market at the default demand bias and at no other."""

from dataclasses import replace

import pytest

from hotel_market import demand
from hotel_market.bookings import Books
from hotel_market.customer import demo
from hotel_market.forecast import (
    ORACLE_MARKET_ELASTICITY,
    expected_demand,
    normal_demand,
    peak_night,
)
from hotel_market.shocks import EVENTS
from hotel_market.simulated import simulated_sources
from hotel_market.sources import Event
from hotel_market.world import stay_window

DEMO = demo()


@pytest.fixture(scope="module")
def sources():
    return simulated_sources(Books(7))


@pytest.mark.parametrize("as_of_day", [0, 9, 10, 19, 20, 21, 39, 40, 41, 59])
def test_the_forecast_is_the_simulators_demand_for_the_demo_market(as_of_day, sources):
    for hotel in DEMO.hotels:
        for stay_day in stay_window(as_of_day):
            # The market term mirrors demand.py's: at every market elasticity, the default 1.0
            # included, the forecast equals the simulator's demand at the same median ratio.
            ratio = sources.shops.median(as_of_day, hotel, stay_day) / sources.shops.first_median(
                hotel, stay_day
            )
            forecast = expected_demand(hotel, stay_day, as_of_day, sources)
            assert forecast == pytest.approx(
                demand.expected_demand(hotel, stay_day, as_of_day, 1.0, ratio, 1.0)
            )
            assert forecast == expected_demand(hotel, stay_day, as_of_day, sources, 1.0)
            assert expected_demand(hotel, stay_day, as_of_day, sources, 0.0) == pytest.approx(
                demand.expected_demand(hotel, stay_day, as_of_day, market_elasticity=0.0)
            )
            # The demand bias is the simulator's alone: the forecast never carries it.
            assert forecast != demand.expected_demand(hotel, stay_day, as_of_day, 0.9, ratio, 1.0)
            assert expected_demand(hotel, stay_day, as_of_day, sources, 0.5) == pytest.approx(
                demand.expected_demand(hotel, stay_day, as_of_day, 1.0, ratio, 0.5)
            )
        assert normal_demand(hotel, as_of_day) == demand.normal_demand(hotel, as_of_day, 1.0)
        assert normal_demand(hotel, as_of_day) != demand.normal_demand(hotel, as_of_day, 0.9)


def test_convention_peak_night_is_its_busiest_night_as_of_day_10(sources):
    [convention] = EVENTS
    for key in convention.hotels:
        # Thursday 45 has the highest day-of-week factor of the four nights.
        assert peak_night(DEMO.hotel(key), convention, sources) == 45


def test_peak_night_uses_what_is_known_on_the_day_the_event_becomes_known(sources):
    # Airport hotel, nights 49 (a Monday) to 55: with no new flights, Monday 49
    # ties for the busiest night and wins as the earliest. Once the day-20
    # filing is known, Thursday 52 and Sunday 55 gain 17% seats and 52 wins.
    airport = DEMO.hotel("airport")
    event = Event(
        "Test",
        known_day=19,
        start_day=49,
        end_day=55,
        hotels=("airport",),
        uplift=0.0,
        comp_rate_raise=0.0,
    )
    assert peak_night(airport, event, sources) == 49
    assert peak_night(airport, replace(event, known_day=20), sources) == 52


def test_the_agents_market_elasticity_starts_at_1_and_lowers_demand_where_the_median_rose(sources):
    assert ORACLE_MARKET_ELASTICITY == 1.0 == DEMO.market_elasticity
    convention = DEMO.hotel("convention")
    # Before the convention is known the median is at its start, so the term is 1.
    assert expected_demand(convention, 46, 9, sources, 0.5) == expected_demand(
        convention, 46, 9, sources, 0.0
    )
    # From day 10 the competitors are 15% up on the convention nights, so the market term takes
    # a proportionate share of the demand by default and the square root of it at 0.5.
    plain = expected_demand(convention, 46, 10, sources, 0.0)
    assert expected_demand(convention, 46, 10, sources) == pytest.approx(plain / 1.15)
    assert expected_demand(convention, 46, 10, sources, 0.5) == pytest.approx(plain * 1.15**-0.5)
