"""Module 26, demo_data.py: the demo page's file, written by code from the recorded run."""

import json
import math
from pathlib import Path

import pytest

from hotel_market import stored
from hotel_market.bookings import simulate
from hotel_market.customer import DEMO_FILE, demo
from hotel_market.demo_data import (
    ALL,
    DEMO_TABLES,
    MEASURES,
    NOTHING_NEW,
    day_label,
    delta_text,
    figures,
    main,
    recorded_run,
    stay_label,
    stay_span,
    tiles,
    value_text,
)
from hotel_market.world import HORIZON_DAYS, SIM_DAYS

ROOT = Path(__file__).resolve().parents[1]


def _rows(path, sql, *parameters):
    connection = stored.connect(path, read_only=True)
    try:
        return connection.execute(sql, list(parameters)).fetchall()
    finally:
        connection.close()


def test_the_file_holds_the_stored_tables_for_every_day_and_the_pages_tables(demo_file):
    connection = stored.connect(demo_file, read_only=True)
    try:
        assert stored.stored_days(connection) == list(range(SIM_DAYS))
        counts = {
            t: connection.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in DEMO_TABLES
        }
    finally:
        connection.close()
    assert counts["hotels"] == 4 and counts["days"] == SIM_DAYS
    assert counts["stay_dates"] == SIM_DAYS * 4 * 90  # the window of each day
    assert counts["news"] >= SIM_DAYS * 4  # at least the "nothing new" row
    assert (
        counts["queue"] == _rows(demo_file, "SELECT count(*) FROM decisions WHERE simulated")[0][0]
    )
    # Five tiles for each hotel and for all together: on the days with a night stayed, and once.
    assert counts["scorecard"] == (SIM_DAYS - 1) * 5 * 5
    assert counts["outcome"] == 5 * 5
    assert counts["gains"] == 5 * HORIZON_DAYS


@pytest.mark.xfail(reason="world v2; re-record with make live-audit SEED=7", strict=True)
def test_the_reasons_come_from_the_recorded_live_run(demo_file):
    # The queued plans carry the model's reasons from tests/fixtures/live_seed7; the held flags
    # carry code's. The recorded run accepted every plan.
    recorded = {
        decision["reason"]
        for path in (ROOT / "tests" / "fixtures" / "live_seed7").glob("day*_*.json")
        for decision in json.loads(path.read_text())["decisions"]
    }
    queued = _rows(demo_file, "SELECT reason, reason_source, outcome FROM queue WHERE queued")
    assert len(queued) == 7 and len(recorded) == 7
    assert {reason for reason, _, _ in queued} == recorded
    assert {source for _, source, _ in queued} == {"model"}
    assert {outcome for _, _, outcome in queued} == {"accepted"}
    held = _rows(demo_file, "SELECT DISTINCT reason_source, outcome FROM queue WHERE NOT queued")
    assert held == [("code", "held")]
    assert recorded_run(7) == ROOT / "tests" / "fixtures" / "live_seed7"
    assert recorded_run(1) is None
    # The file says where its reasons came from, for the page's sidebar.
    assert _rows(demo_file, "SELECT seed, reason_source FROM run") == [
        (7, "the model's, from the recorded live run")
    ]  # until the recording covers world v2 this row names the template as well


def test_every_date_reads_as_a_calendar_date_with_its_day_number_in_brackets(demo_file):
    # Day 0 is Monday 4 January 2027 (schedule.SIM_START).
    assert stay_label(0) == "Mon 4 Jan [0]" and stay_label(45) == "Thu 18 Feb [45]"
    assert stay_span(46, 46) == "Fri 19 Feb [46]"
    assert stay_span(45, 48) == "Thu 18 Feb [45] to Sun 21 Feb [48]"
    assert day_label(10) == "Thu 14 Jan 2027 [day 10]"
    assert _rows(demo_file, "SELECT label, stay_window FROM days WHERE as_of_day = 10") == [
        ("Thu 14 Jan 2027 [day 10]", "Thu 14 Jan [10] to Tue 13 Apr [99]")
    ]
    labels = _rows(
        demo_file,
        "SELECT stay_day, label, tick FROM stay_dates "
        "WHERE as_of_day = 10 AND hotel = 'convention' AND stay_day IN (10, 14, 45) "
        "ORDER BY stay_day",
    )
    assert labels == [
        (10, "Thu 14 Jan [10]", False),
        (14, "Mon 18 Jan [14]", True),
        (45, "Thu 18 Feb [45]", False),
    ]
    # The x axis labels the Mondays of the window and nothing else.
    ticks = _rows(
        demo_file,
        "SELECT stay_day FROM stay_dates WHERE as_of_day = 10 AND hotel = 'convention' AND tick "
        "ORDER BY stay_day",
    )
    assert [stay for (stay,) in ticks] == list(range(14, 100, 7))
    stays = _rows(
        demo_file, "SELECT stays FROM queue WHERE as_of_day = 10 AND hotel = 'convention'"
    )
    assert stays == [("Thu 18 Feb [45] to Sun 21 Feb [48]",)]


def test_the_scorecard_counts_the_nights_already_stayed(demo_file):
    # Day 0 has no night stayed, so no rows. On day 10 the nights are stay dates 0 to 9, and
    # nothing has changed yet, so every change is "0", which the tile shows with no arrow.
    assert _rows(demo_file, "SELECT count(*) FROM scorecard WHERE as_of_day = 0") == [(0,)]
    day10 = _rows(
        demo_file,
        "SELECT position, measure, title, nights, agent, fixed, delta, value_text, delta_text "
        "FROM scorecard WHERE as_of_day = 10 AND hotel = 'convention' ORDER BY position",
    )
    assert [row[:2] for row in day10] == list(enumerate(MEASURES))
    assert {row[2] for row in day10} == {"Downtown convention hotel"}
    assert {row[3] for row in day10} == {"Mon 4 Jan [0] to Wed 13 Jan [9]"}
    assert all(row[4] == row[5] and row[6] == 0 and row[8] == "0" for row in day10)
    assert [row[7] for row in day10][:2] == ["74.0%", "$220.00"]
    # The figures are the Books measures over those nights, at fixed rates on day 10.
    books = simulate(7, last_day=9)
    hotel = demo().hotel("convention")
    stays = range(10)
    assert day10[0][4] == pytest.approx(books.occupancy(hotel, stays))
    assert day10[1][4] == pytest.approx(books.average_rate(hotel, stays))
    assert day10[2][4] == pytest.approx(books.revpar(hotel, stays))
    assert day10[3][4] == pytest.approx(books.room_revenue(hotel, stays))
    assert day10[4][4] == pytest.approx(books.contribution(hotel, stays))
    # The four hotels together: the sums first, then the ratios.
    together = _rows(
        demo_file,
        "SELECT measure, agent, title FROM scorecard "
        f"WHERE as_of_day = 10 AND hotel = '{ALL}' ORDER BY position",
    )
    assert {row[2] for row in together} == {"All four hotels"}
    revenue = sum(books.room_revenue(h, stays) for h in demo().hotels)
    available = sum(h.rooms * len(stays) for h in demo().hotels)
    assert together[3][1] == pytest.approx(revenue)
    assert together[2][1] == pytest.approx(revenue / available)
    mismatch = _rows(
        demo_file, "SELECT count(*) FROM scorecard WHERE abs(agent - fixed - delta) > 1e-6"
    )
    assert mismatch == [(0,)]


def test_the_outcome_is_the_result_once_every_stay_date_is_complete(demo_file):
    # Both runs book on to day 149, so the outcome is the README's seed-7 table: nothing for the
    # convention hotel, which changed no rate, and +17,154 for all four, over stay dates 0 to 149.
    outcome = _rows(
        demo_file,
        "SELECT hotel, title, nights, delta, delta_text FROM outcome "
        "WHERE measure = 'Contribution' ORDER BY hotel",
    )
    by_hotel = {row[0]: row for row in outcome}
    assert by_hotel["convention"][3] == 0
    assert by_hotel[ALL][3] == pytest.approx(17154, abs=1)
    assert by_hotel[ALL][1:3] == ("All four hotels", "Mon 4 Jan [0] to Wed 2 Jun [149]")
    assert by_hotel[ALL][4] == "+$17,154" and by_hotel["convention"][4] == "0"
    revenue = _rows(
        demo_file, f"SELECT delta_text FROM outcome WHERE hotel = '{ALL}' AND position = 3"
    )
    assert revenue == [("-$32,646",)]
    # The gains by stay date add up to the outcome, and the convention dates carry the hotel's.
    sums = _rows(demo_file, "SELECT hotel, sum(difference) FROM gains GROUP BY hotel")
    for hotel, total in sums:
        assert total == pytest.approx(by_hotel[hotel][3])
    convention = _rows(
        demo_file,
        "SELECT sum(difference) FROM gains "
        "WHERE hotel = 'convention' AND stay_day BETWEEN 45 AND 48",
    )
    assert convention[0][0] == pytest.approx(by_hotel["convention"][3])
    ticks = _rows(demo_file, f"SELECT stay_day FROM gains WHERE hotel = '{ALL}' AND tick")
    assert [stay for (stay,) in ticks] == [0, 28, 56, 84, 112, 140]


def test_the_tiles_texts_round_and_a_change_that_rounds_to_nothing_is_zero():
    assert [value_text(p, v) for p, v in enumerate((0.7405, 220, 162.912, 651640, 434426.67))] == [
        "74.1%", "$220.00", "$162.91", "$651,640", "$434,427"
    ]  # fmt: skip
    assert value_text(1, math.nan) == "n/a"
    assert delta_text(0, -0.0051) == "-0.5 pts" and delta_text(0, 0.0004) == "0"
    assert delta_text(1, 1.136) == "+$1.14" and delta_text(2, -0.004) == "0"
    assert delta_text(3, -35018.6) == "-$35,019" and delta_text(4, 0.4) == "0"
    rows = tiles((0.5, 200.0, 100.0, 1000.0, 600.0), (0.5, 199.0, 99.5, 990.0, 600.0))
    assert [row[1] for row in rows] == list(MEASURES)
    assert [row[6] for row in rows] == ["0", "+$1.00", "+$0.50", "+$10", "0"]
    books = simulate(7, last_day=0)
    hotel = demo().hotel("airport")
    assert figures(books, [hotel], range(1)) == pytest.approx(
        (
            books.occupancy(hotel, range(1)),
            books.average_rate(hotel, range(1)),
            books.revpar(hotel, range(1)),
            books.room_revenue(hotel, range(1)),
            books.contribution(hotel, range(1)),
        )
    )


def test_a_held_flag_names_the_best_alternative_and_how_far_it_fell_short(demo_file):
    # On day 30 the full-service hotel's comp set cut its rates for stay dates 37 to 39. No
    # change beats holding, so the flag is held, and the best change on each day of the week
    # falls short of holding. The same day's pace flag on stay date 46 has a plan that beats
    # holding by less than the $250 minimum, so it is held short of the minimum.
    day30 = _rows(
        demo_file,
        "SELECT stays, causes, plan, outcome, alternative, alternative_text FROM queue "
        "WHERE as_of_day = 30 AND hotel = 'full-service' ORDER BY position",
    )
    assert day30[0] == (
        "Wed 10 Feb [37] to Fri 12 Feb [39]",
        "comp median down",
        "hold",
        "held",
        "raise 5% on Wed, Thu, Fri",
        "$20 less than holding",
    )
    short = _rows(
        demo_file,
        "SELECT plan, value, outcome, alternative, alternative_text FROM queue "
        "WHERE as_of_day = 30 AND hotel = 'full-service' AND position = 1",
    )
    [(plan, value, outcome, alternative, text)] = short
    assert outcome == "held" and 0 < value < 250 and alternative == plan == "raise 5% on Fri"
    gain, short = math.floor(value), math.ceil(250 - value)
    assert text == f"${gain} more than holding, ${short} short of the $250 minimum"
    queued = _rows(
        demo_file, "SELECT DISTINCT alternative, alternative_text FROM queue WHERE queued"
    )
    assert queued == [("", "")]


def test_the_news_names_the_convention_the_filings_and_the_comp_set_cut(demo_file):
    day0 = _rows(demo_file, "SELECT DISTINCT text FROM news WHERE as_of_day = 0")
    assert day0 == [(NOTHING_NEW,)]
    day10 = _rows(
        demo_file,
        "SELECT kind, text FROM news "
        "WHERE as_of_day = 10 AND hotel = 'convention' ORDER BY position",
    )
    assert day10 == [
        (
            "event",
            "An event, the convention, was announced for Thu 18 Feb [45] to Sun 21 Feb [48]. "
            "Demand there is up 35.0%, and the comp set's rates are up 15.0%.",
        ),
        (
            "comp set",
            "The comp set median is up 13.7% to 18.8% for Thu 18 Feb [45] to Sun 21 Feb [48].",
        ),
    ]
    filings = _rows(
        demo_file,
        "SELECT DISTINCT as_of_day, text FROM news WHERE kind = 'schedule' ORDER BY as_of_day",
    )
    assert filings == [
        (
            20,
            "The airlines filed a schedule change: arriving seats are up 17.0% to 21.6% "
            "for Tue 23 Feb [50] to Wed 2 Jun [149].",
        ),
        (
            40,
            "The airlines filed a schedule change: arriving seats are down 7.9% to 9.7% "
            "for Mon 15 Mar [70] to Sun 4 Apr [90].",
        ),
    ]
    day30 = _rows(
        demo_file, "SELECT text FROM news WHERE as_of_day = 30 AND hotel = 'full-service'"
    )
    assert day30 == [
        ("The comp set median is down 9.0% to 11.1% for Wed 10 Feb [37] to Fri 12 Feb [39].",)
    ]


def test_the_chart_rows_mark_the_flagged_stay_dates_and_carry_the_planned_rate(demo_file):
    flagged = _rows(
        demo_file,
        "SELECT stay_day, rate, comp_median > rate, rooms_on_books > 0, pace > 0, causes, flag, "
        "planned_rate FROM stay_dates "
        "WHERE as_of_day = 10 AND hotel = 'full-service' AND flag = '45-48' ORDER BY stay_day",
    )
    assert [row[0] for row in flagged] == [45, 46, 47, 48]
    assert all(row[1:5] == (190.0, True, True, True) for row in flagged)
    assert {row[5] for row in flagged} == {"comp median up, event announced"}
    assert {row[6] for row in flagged} == {"45-48"}
    # The accepted plan raises 10% on Thu and 5% on Sat; Fri and Sun hold at the current rate.
    assert [row[7] for row in flagged] == pytest.approx([209, 190, 199.5, 190])
    unflagged = _rows(
        demo_file, "SELECT DISTINCT causes, flag, planned_rate FROM stay_dates WHERE NOT flagged"
    )
    assert unflagged == [("", "", None)]
    # A held flag has no planned rate.
    held = _rows(
        demo_file,
        "SELECT DISTINCT planned_rate FROM stay_dates "
        "WHERE as_of_day = 30 AND hotel = 'full-service' AND flagged",
    )
    assert held == [(None,)]
    axis = _rows(demo_file, "SELECT start_rate, rate_axis_low, rate_axis_high FROM hotels")
    assert all(
        low == pytest.approx(0.75 * rate) and high == pytest.approx(1.25 * rate)
        for rate, low, high in axis
    )


def test_a_request_the_recording_does_not_cover_gets_the_templates_answer_and_a_warning(
    tmp_path, capsys
):
    """The recorded run covers the shipped market at seed 7. In a market whose airport hotel has
    another name, that hotel's requests differ, so the template answers them and the command
    warns once per request; the other hotels keep the model's reasons, and the file says so."""
    market = tmp_path / "market.toml"
    market.write_text(
        (ROOT / DEMO_FILE).read_text().replace('name = "Airport hotel"', 'name = "Airport inn"')
    )
    main(["--seed", "7", "--out", str(tmp_path / "inn.duckdb"), "--customer", str(market)])
    out = capsys.readouterr().out
    assert (
        "Warning: the recorded run does not cover day 20 at Airport inn, so the template answered."
    ) in out
    # The recording is world v1's, so every request falls back until it is recorded again;
    # the file says for how many, and every queued row names the template.
    missed = out.count("Warning:")
    phrase = (
        "the model's where the recorded live run covers the request and the template's for "
        f"the {missed} it does not"
    )
    assert missed >= 1 and f"reasons {phrase}." in out
    assert _rows(tmp_path / "inn.duckdb", "SELECT seed, reason_source FROM run") == [(7, phrase)]
    sources = _rows(
        tmp_path / "inn.duckdb",
        "SELECT hotel, reason_source FROM queue WHERE queued ORDER BY as_of_day, hotel",
    )
    assert ("airport", "template") in sources
    assert {source for _, source in sources} <= {"model", "template"}
    stored = _rows(
        tmp_path / "inn.duckdb", "SELECT DISTINCT reason_source FROM decisions WHERE queued"
    )
    assert "template" in {source for (source,) in stored}


def test_a_seed_with_no_recording_gets_the_templates_reasons(tmp_path, capsys):
    main(["--seed", "1", "--out", str(tmp_path / "one.duckdb")])
    assert "reasons the template's, as no run is recorded." in capsys.readouterr().out
    sources = _rows(
        tmp_path / "one.duckdb", "SELECT DISTINCT reason_source FROM queue WHERE queued"
    )
    assert sources == [("template",)]
    assert _rows(tmp_path / "one.duckdb", "SELECT seed, reason_source FROM run") == [
        (1, "the template's, as no run is recorded")
    ]
