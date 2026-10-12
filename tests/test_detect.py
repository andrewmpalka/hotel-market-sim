"""Module 6: the detect numbers, the flags and the 7-day hold."""

import math

import pandas as pd
import pytest

from hotel_market import demand
from hotel_market.bookings import Books
from hotel_market.customer import demo
from hotel_market.detect import (
    AHEAD,
    BEHIND,
    MEDIAN_DOWN,
    MEDIAN_UP,
    NEW_EVENT,
    SEATS_CUT,
    SEATS_UP,
    Flag,
    detect_numbers,
    flags,
    shock_known,
)
from hotel_market.schedule import seat_revision
from hotel_market.shops import comp_median
from hotel_market.simulated import SimulatedSchedules, simulated_sources, watch
from hotel_market.world import SIM_DAYS

DEMO = demo()

SEED = 7
DOWNTOWN = {h.key for h in DEMO.hotels if h.name.startswith("Downtown")}
EVERY_HOTEL = {h.key for h in DEMO.hotels}


@pytest.fixture(scope="module")
def run():
    """A fixed-rate run with seed 7, with detect after each of days 0 to 59."""
    return watch(SEED)


def _flagged(found, day, cause):
    """{hotel key: stay dates} flagged for a cause on a day."""
    out = {}
    for f in found:
        if f.day == day and cause in f.causes:
            out.setdefault(f.hotel, set()).update(range(f.first_stay, f.last_stay + 1))
    return out


def _table(causes, hotel="airport", first_stay=10):
    """A made-up day of detect numbers with only the columns flags() reads."""
    return pd.DataFrame(
        {
            "hotel": hotel,
            "stay_day": range(first_stay, first_stay + len(causes)),
            "causes": causes,
        }
    )


def test_each_shock_flags_on_the_day_it_becomes_known(run):
    _, found, _ = run
    convention = set(range(45, 49))
    assert _flagged(found, 10, NEW_EVENT) == {key: convention for key in DOWNTOWN}
    assert _flagged(found, 10, MEDIAN_UP) == {key: convention for key in DOWNTOWN}
    assert _flagged(found, 20, SEATS_UP) == {key: set(range(50, 110)) for key in EVERY_HOTEL}
    assert _flagged(found, 30, MEDIAN_DOWN) == {"full-service": set(range(37, 40))}
    assert _flagged(found, 40, SEATS_CUT) == {key: set(range(70, 91)) for key in EVERY_HOTEL}


def test_shock_causes_appear_only_on_the_days_shocks_become_known(run):
    # seat_change stays up from day 20 on, but only seat_revision raises flags.
    _, found, _ = run
    causes = (NEW_EVENT, MEDIAN_UP, MEDIAN_DOWN, SEATS_UP, SEATS_CUT)
    days = {cause: {f.day for f in found if cause in f.causes} for cause in causes}
    assert days == {
        NEW_EVENT: {10},
        MEDIAN_UP: {10},
        MEDIAN_DOWN: {30},
        SEATS_UP: {20},
        SEATS_CUT: {40},
    }


def test_detect_runs_after_each_of_days_0_to_59(run):
    _, _, tables = run
    assert sorted(tables) == list(range(SIM_DAYS))


@pytest.mark.parametrize("day", [19, 20, 21, 39, 40, 41])
def test_known_seat_revision_matches_the_schedule(day):
    assert dict(SimulatedSchedules().seat_revision(day)) == seat_revision(day).to_dict()


def test_numbers_follow_the_definitions():
    books = Books(SEED)
    for day in range(31):
        books.book(day)
    table = detect_numbers(30, simulated_sources(books)).set_index(["hotel", "stay_day"])
    for hotel in DEMO.hotels:
        i = hotel.row
        for stay_day in (30, 38, 60, 119):
            row = table.loc[(hotel.key, stay_day)]
            on_pace = demand.normal_demand(hotel, stay_day) * DEMO.curve(stay_day - 30)
            median = comp_median(30, hotel, stay_day, seed=SEED)
            assert row["rooms"] == books.rooms[i, stay_day]
            assert row["expected_demand"] == demand.expected_demand(hotel, stay_day, 30)
            assert row["pace_gap"] == pytest.approx(books.rooms[i, stay_day] - on_pace)
            assert row["pace_threshold"] == pytest.approx(
                max(0.10 * hotel.rooms, 3 * math.sqrt(on_pace))
            )
            assert row["rate_vs_median"] == pytest.approx(books.rates[i, stay_day] / median - 1)
            assert row["median_change"] == pytest.approx(
                median / comp_median(29, hotel, stay_day, seed=SEED) - 1
            )


def test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd():
    books = Books(SEED)
    books.book(0)
    table = detect_numbers(0, simulated_sources(books))
    convention = table.query("hotel == 'convention'").set_index("stay_day")
    # Tonight (a Monday) on pace means 400 x 0.75 x 0.95 = 285 rooms: 3 x sqrt(285) = 50.6 beats 40.
    assert convention.loc[0, "pace_threshold"] == pytest.approx(3 * math.sqrt(285))
    # Sixty days out only 20% of 270 rooms are on pace: 3 x sqrt(54) = 22, so 40 rooms wins.
    assert convention.loc[60, "pace_threshold"] == pytest.approx(40)


def test_consecutive_stay_dates_with_the_same_causes_merge_into_one_flag():
    table = _table([(), (AHEAD,), (AHEAD,), (AHEAD, SEATS_UP), (AHEAD,), (), (BEHIND,)])
    assert flags(5, table) == [
        Flag(5, "airport", 11, 12, (AHEAD,)),
        Flag(5, "airport", 13, 13, (AHEAD, SEATS_UP)),
        Flag(5, "airport", 14, 14, (AHEAD,)),
        Flag(5, "airport", 16, 16, (BEHIND,)),
    ]


def test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags():
    assert DEMO.hold_days == 7
    table = _table([(AHEAD,), (AHEAD, SEATS_UP)])  # stay dates 10 and 11
    held = {("airport", 10): 13, ("airport", 11): 13}  # actions accepted on day 13
    # Day 20 is the 7th day of the hold: only the flag with a shock behind it stays.
    assert flags(20, table, held) == [Flag(20, "airport", 11, 11, (AHEAD, SEATS_UP))]
    # Day 21 is past the hold, so the pace flag is back.
    assert flags(21, table, held) == [
        Flag(21, "airport", 10, 10, (AHEAD,)),
        Flag(21, "airport", 11, 11, (AHEAD, SEATS_UP)),
    ]


def test_shock_known_follows_what_is_known_on_the_day():
    airport, convention, full_service = (
        DEMO.hotel(k) for k in ("airport", "convention", "full-service")
    )
    s = simulated_sources(Books(SEED))
    assert not shock_known(airport, 60, 19, s) and shock_known(airport, 60, 20, s)  # new flights
    assert not shock_known(airport, 46, 25, s)  # convention is downtown only
    assert not shock_known(convention, 46, 9, s) and shock_known(convention, 46, 10, s)
    assert not shock_known(full_service, 38, 29, s) and shock_known(full_service, 38, 30, s)
