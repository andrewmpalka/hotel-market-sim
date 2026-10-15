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
from hotel_market.schedule import passenger_revision
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
    assert _flagged(found, 20, SEATS_UP) == {key: set(range(50, 110)) for key in EVERY_HOTEL}
    assert _flagged(found, 40, SEATS_CUT) == {key: set(range(70, 91)) for key in EVERY_HOTEL}
    # The shop noise can flag a comp median on any day, so the shocks' flags are among them.
    median_up, median_down = _flagged(found, 10, MEDIAN_UP), _flagged(found, 30, MEDIAN_DOWN)
    assert all(convention <= median_up.get(key, set()) for key in DOWNTOWN)
    assert set(range(37, 40)) <= median_down.get("full-service", set())


def test_shock_causes_appear_only_on_the_days_shocks_become_known(run):
    # The passenger change stays up from day 20 on, but only the revision raises flags. A
    # comp-median cause can come from the shop noise on any day, so only the shocks' days are
    # pinned.
    _, found, _ = run
    causes = (NEW_EVENT, MEDIAN_UP, MEDIAN_DOWN, SEATS_UP, SEATS_CUT)
    days = {cause: {f.day for f in found if cause in f.causes} for cause in causes}
    assert (days[NEW_EVENT], days[SEATS_UP], days[SEATS_CUT]) == ({10}, {20}, {40})
    assert 10 in days[MEDIAN_UP] and 30 in days[MEDIAN_DOWN]


def test_detect_runs_after_each_of_days_0_to_59(run):
    _, _, tables = run
    assert sorted(tables) == list(range(SIM_DAYS))


@pytest.mark.parametrize("day", [19, 20, 21, 39, 40, 41])
def test_known_passenger_revision_matches_the_schedule(day):
    assert dict(SimulatedSchedules().passenger_revision(day)) == passenger_revision(day).to_dict()


def test_numbers_follow_the_definitions():
    books = Books(SEED)
    for day in range(31):
        books.book(day)
    table = detect_numbers(30, simulated_sources(books)).set_index(["hotel", "stay_day"])
    for hotel in DEMO.hotels:
        i = hotel.row
        for stay_day in (30, 38, 60, 119):
            row = table.loc[(hotel.key, stay_day)]
            on_pace = demand.normal_demand(hotel, stay_day) * hotel.curve(stay_day - 30)
            median = comp_median(30, hotel, stay_day, seed=SEED)
            assert row["rooms"] == books.rooms[i, stay_day]
            ratio = median / hotel.starting_median()
            assert row["expected_demand"] == pytest.approx(
                demand.expected_demand(hotel, stay_day, 30, 1.0, ratio, DEMO.market_elasticity)
            )
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
    s, t = simulated_sources(Books(SEED)), DEMO.median_threshold
    assert not shock_known(airport, 60, 19, s, t) and shock_known(airport, 60, 20, s, t)
    assert not shock_known(airport, 46, 25, s, t)  # convention is downtown only
    assert not shock_known(convention, 46, 9, s, t) and shock_known(convention, 46, 10, s, t)
    assert not shock_known(full_service, 38, 29, s, t) and shock_known(full_service, 38, 30, s, t)
    # The shop noise alone never reaches the threshold, so no other day or date counts.
    assert not any(shock_known(airport, s_, d, s, t) for d in range(0, 19) for s_ in range(d, 50))


def test_pace_causes_follow_the_gap_against_the_threshold(run):
    _, _, tables = run
    for table in tables.values():
        for gap, threshold, causes in zip(
            table["pace_gap"], table["pace_threshold"], table["causes"]
        ):
            assert (AHEAD in causes) == (gap > threshold)
            assert (BEHIND in causes) == (gap < -threshold)
    assert any(AHEAD in causes for table in tables.values() for causes in table["causes"])
    # Seed 7 never falls behind pace at fixed rates, so empty three stay dates by hand.
    books = Books(SEED)
    for day in range(11):
        books.book(day)
    convention = DEMO.hotel("convention")
    i = convention.row
    books.preload[i, 40:43] = 0
    books.daily_rooms[:, i, 40:43] = 0
    books.rooms[i, 40:43] = 0
    table = detect_numbers(10, simulated_sources(books))
    rows = table.set_index(["hotel", "stay_day"])
    for stay_day in (40, 41, 42):
        row = rows.loc[("convention", stay_day)]
        assert row["pace_gap"] < -row["pace_threshold"] and BEHIND in row["causes"]
    behind = [f for f in flags(10, table) if f.hotel == "convention" and BEHIND in f.causes]
    assert behind == [Flag(10, "convention", 40, 42, (BEHIND,))]


def test_a_detector_that_fires_on_any_revision_is_caught_by_the_churn():
    from hotel_market.schedule import DEFAULT_SCENARIO, with_churn
    from hotel_market.simulated import watch

    _, with_churn_flags, _ = watch(7, churn=True)
    _, plain_flags, _ = watch(7)

    def seat_days(found):
        return sorted({f.day for f in found if set(f.causes) & {SEATS_UP, SEATS_CUT}})

    # The churn files on eight more days, with a seat revision on some of them, and raises no
    # seat flag: the threshold holds them out, as it is meant to.
    assert seat_days(with_churn_flags) == seat_days(plain_flags) == [20, 40]
    revisions = SimulatedSchedules(with_churn(DEFAULT_SCENARIO, 7))
    moved = [day for day in range(7, 57, 7) if any(revisions.passenger_revision(day).values())]
    assert moved


def test_a_level_scales_one_hotels_pace_baseline_and_expected_demand(day10):
    from hotel_market.bookings import simulate
    from hotel_market.detect import detect_numbers
    from hotel_market.simulated import simulated_sources

    sources = simulated_sources(simulate(7, last_day=10))
    plain = detect_numbers(10, sources, DEMO)
    scaled = detect_numbers(10, sources, DEMO, levels={"airport": 0.9})
    airport, others = plain["hotel"] == "airport", plain["hotel"] != "airport"
    assert scaled.loc[airport, "expected_demand"].to_numpy() == pytest.approx(
        0.9 * plain.loc[airport, "expected_demand"].to_numpy()
    )
    # The pace gap is rooms minus the scaled baseline, so it rises by a tenth of the baseline.
    baseline = plain.loc[airport, "rooms"].to_numpy() - plain.loc[airport, "pace_gap"].to_numpy()
    assert scaled.loc[airport, "pace_gap"].to_numpy() == pytest.approx(
        plain.loc[airport, "pace_gap"].to_numpy() + 0.1 * baseline
    )
    for column in ("expected_demand", "pace_gap", "pace_threshold"):
        assert (scaled.loc[others, column].to_numpy() == plain.loc[others, column].to_numpy()).all()


def test_with_several_ticks_the_hold_is_measured_in_ticks_and_the_baseline_at_the_fractional_day():
    """A change accepted at (day, tick) holds the stay date for hold_days of ticks: at four ticks
    a day, 28 ticks. A hold recorded as a day alone counts from that day's last tick. The pace
    baseline at a tick is the curve at the fractional days out."""
    from hotel_market.detect import days_in, moment_index

    assert DEMO.hold_days == 7
    table = _table([(AHEAD,), (AHEAD, SEATS_UP)])  # stay dates 10 and 11
    held = {("airport", 10): (13, 2), ("airport", 11): (13, 2)}  # accepted at tick 2 of day 13
    # Tick 2 of day 20 is the 28th tick of the hold: only the flag with a shock behind it stays.
    assert flags(20, table, held, tick=2, ticks=4) == [
        Flag(20, "airport", 11, 11, (AHEAD, SEATS_UP), 2, 4)
    ]
    # Tick 3 of day 20 is past the hold, so the pace flag is back.
    assert flags(20, table, held, tick=3, ticks=4) == [
        Flag(20, "airport", 10, 10, (AHEAD,), 3, 4),
        Flag(20, "airport", 11, 11, (AHEAD, SEATS_UP), 3, 4),
    ]
    # A hold recorded by its day alone was accepted at that day's last tick.
    by_day = {("airport", 10): 13}
    assert flags(20, table, by_day, tick=4, ticks=4)[0].first_stay == 11
    assert flags(21, table, by_day, tick=1, ticks=4)[0].first_stay == 10
    assert moment_index(20, 2, 4) - moment_index(13, 2, 4) == 28 == DEMO.hold_days * 4
    assert moment_index(13, 1, 1) == 13  # with one tick a day the index is the day
    # The baseline: after tick 2 of 4, half the day's bookings are in.
    assert days_in(45, 10, 2, 4) == 45 - 10 + 0.5
    assert days_in(45, 10, 4, 4) == days_in(45, 10) == 35.0


def test_detect_numbers_at_a_tick_read_the_sources_as_of_that_tick():
    """At four ticks a day, the numbers at tick 2 of day 10 see the comp set's raise, which lands
    at tick 2, but not the convention, which lands at tick 4; the pace baseline is the curve at
    the fractional day."""
    from hotel_market.bookings import simulate
    from hotel_market.detect import days_in
    from hotel_market.forecast import normal_demand
    from hotel_market.simulated import simulated_sources

    books = simulate(7, last_day=10, ticks=4)
    hotel = DEMO.hotel("convention")
    at_1 = detect_numbers(10, simulated_sources(books, 10, 1), tick=1)
    at_2 = detect_numbers(10, simulated_sources(books, 10, 2), tick=2)
    at_4 = detect_numbers(10, simulated_sources(books, 10, 4), tick=4)

    def row(table, stay):
        return table[(table["hotel"] == hotel.key) & (table["stay_day"] == stay)].iloc[0]

    assert MEDIAN_UP not in row(at_1, 46)["causes"] and MEDIAN_UP in row(at_2, 46)["causes"]
    assert row(at_2, 46)["new_event"] is None and row(at_4, 46)["new_event"] == "Convention"
    assert MEDIAN_UP not in row(at_4, 46)["causes"]  # the median did not move since tick 3
    on_books = simulated_sources(books, 10, 2).bookings.on_books(10, 2)[hotel.row, 46]
    expected_gap = on_books - normal_demand(hotel, 46) * hotel.curve(days_in(46, 10, 2, 4))
    assert row(at_2, 46)["pace_gap"] == pytest.approx(expected_gap)
    assert set(at_2["tick"]) == {2}
