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
    day_index,
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
    # The strip has a row for every day and hotel, with or without a flag.
    assert _rows(demo_file, "SELECT count(*) FROM strip") == [(SIM_DAYS * 4,)]


def test_the_reasons_come_from_the_recorded_live_run(demo_file):
    # The queued plans carry the model's reasons from tests/fixtures/live_seed7; the held flags
    # carry code's. The recorded run accepted every plan.
    recorded = {
        decision["reason"]
        for path in (ROOT / "tests" / "fixtures" / "live_seed7").glob("day*_*.json")
        for decision in json.loads(path.read_text())["decisions"]
    }
    queued = _rows(demo_file, "SELECT reason, reason_source, outcome FROM queue WHERE queued")
    assert len(queued) == 6 and len(recorded) == 6
    assert {reason for reason, _, _ in queued} == recorded
    assert {source for _, source, _ in queued} == {"model"}
    assert {outcome for _, _, outcome in queued} == {"accepted"}
    held = _rows(demo_file, "SELECT DISTINCT reason_source, outcome FROM queue WHERE NOT queued")
    assert held == [("code", "held")]
    assert recorded_run(7) == ROOT / "tests" / "fixtures" / "live_seed7"
    assert recorded_run(7, 4) == ROOT / "tests" / "fixtures" / "live_seed7_intraday"
    assert recorded_run(1) is None and recorded_run(1, 4) is None
    # The file says where its reasons came from, for the page's sidebar, and names its market.
    assert _rows(demo_file, "SELECT seed, reason_source, market FROM run") == [
        (7, "the model's, from the recorded live run", "demo")
    ]


def test_every_date_reads_as_a_calendar_date(demo_file):
    # Day 0 is Monday 4 January 2027 (schedule.SIM_START). The day's number is a column of its
    # own, which the page shows small under the title.
    assert stay_label(0) == "Mon 4 Jan" and stay_label(45) == "Thu 18 Feb"
    assert stay_span(46, 46) == "Fri 19 Feb"
    assert stay_span(45, 48) == "Thu 18 Feb to Sun 21 Feb"
    assert day_label(10) == "Thu 14 Jan 2027" and day_index(10) == "day 10"
    assert _rows(demo_file, "SELECT label, stay_window, index FROM days WHERE as_of_day = 10") == [
        ("Thu 14 Jan 2027", "Thu 14 Jan to Tue 13 Apr", "day 10")
    ]
    assert _rows(demo_file, "SELECT count(*) FROM days WHERE index <> 'day ' || as_of_day") == [
        (0,)
    ]
    labels = _rows(
        demo_file,
        "SELECT stay_day, label, tick FROM stay_dates "
        "WHERE as_of_day = 10 AND hotel = 'convention' AND stay_day IN (10, 14, 45) "
        "ORDER BY stay_day",
    )
    assert labels == [
        (10, "Thu 14 Jan", False),
        (14, "Mon 18 Jan", True),
        (45, "Thu 18 Feb", False),
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
    assert stays == [("Thu 18 Feb to Sun 21 Feb",)]
    # No stay label anywhere in the file carries a bracket.
    bracketed = (
        "SELECT (SELECT count(*) FROM stay_dates WHERE label LIKE '%[%') "
        "+ (SELECT count(*) FROM gains WHERE label LIKE '%[%') "
        "+ (SELECT count(*) FROM queue WHERE stays LIKE '%[%' OR headline LIKE '%[%') "
        "+ (SELECT count(*) FROM news WHERE text LIKE '%[%') "
        "+ (SELECT count(*) FROM days WHERE label LIKE '%[%' OR stay_window LIKE '%[%')"
    )
    assert _rows(demo_file, bracketed) == [(0,)]


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
    assert {row[3] for row in day10} == {"Mon 4 Jan to Wed 13 Jan"}
    counted = "SELECT DISTINCT night_count FROM scorecard WHERE as_of_day = 10"
    assert _rows(demo_file, counted) == [(10,)]
    assert all(row[4] == row[5] and row[6] == 0 and row[8] == "0" for row in day10)
    assert [row[7] for row in day10][:2] == ["76.1%", "$220.00"]
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
    # convention hotel, which changed no rate, and +19,796 for all four, over stay dates 0 to 149.
    outcome = _rows(
        demo_file,
        "SELECT hotel, title, nights, delta, delta_text FROM outcome "
        "WHERE measure = 'Contribution' ORDER BY hotel",
    )
    by_hotel = {row[0]: row for row in outcome}
    assert by_hotel["convention"][3] == 0
    assert by_hotel[ALL][3] == pytest.approx(19796, abs=1)
    assert by_hotel[ALL][1:3] == ("All four hotels", "Mon 4 Jan to Wed 2 Jun")
    assert _rows(demo_file, "SELECT DISTINCT night_count FROM outcome") == [(HORIZON_DAYS,)]
    assert by_hotel[ALL][4] == "+$19,796" and by_hotel["convention"][4] == "0"
    revenue = _rows(
        demo_file, f"SELECT delta_text FROM outcome WHERE hotel = '{ALL}' AND position = 3"
    )
    assert revenue == [("-$21,324",)]
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
    # falls short of holding. On day 10 the full-service hotel's convention plan beats holding by
    # less than the $250 minimum, so it is held short of the minimum.
    day30 = _rows(
        demo_file,
        "SELECT stays, causes, plan, outcome, alternative, alternative_text FROM queue "
        "WHERE as_of_day = 30 AND hotel = 'full-service' ORDER BY position",
    )
    assert day30[0] == (
        "Wed 10 Feb to Fri 12 Feb",
        "comp median down",
        "hold",
        "held",
        "raise 5% on Wed, Fri; lower halfway to the new median on Thu",
        "$10 less than holding",
    )
    short = _rows(
        demo_file,
        "SELECT plan, value, outcome, alternative, alternative_text FROM queue "
        "WHERE as_of_day = 10 AND hotel = 'full-service'",
    )
    [(plan, value, outcome, alternative, text)] = short
    assert outcome == "held" and 0 < value < 250 and alternative == plan == "raise 5% on Thu"
    gain, short = math.floor(value), math.ceil(250 - value)
    assert text == f"${gain} more than holding, ${short} short of the $250 minimum"
    queued = _rows(
        demo_file, "SELECT DISTINCT alternative, alternative_text FROM queue WHERE queued"
    )
    assert queued == [("", "")]


def test_a_queued_plan_carries_the_stored_requests_earlier_changes(demo_file):
    # Day 20 at the lifestyle hotel: the request's entry for stay date 75 lists the day-18 raise
    # with the rooms booked since, and the queue row carries that line as the request wrote it,
    # and again with its day numbers as dates for the page. No other queued row, the airport's
    # day-20 plan included, carries one, and a held flag was never asked, so it carries none
    # either.
    line = "day 18: raised 10% to $264 on Sat 75; since then 2 rooms booked against 1 expected"
    dated = (
        "Fri 22 Jan: raised 10% to $264 on Sat 20 Mar; since then 2 rooms booked against 1 expected"
    )
    rows = _rows(
        demo_file,
        "SELECT stays, since_last_change, since_last_change_text FROM queue "
        "WHERE as_of_day = 20 AND hotel = 'lifestyle' AND queued ORDER BY position",
    )
    assert [row for row in rows if row[1]] == [(stay_label(75), line, dated)]
    assert all(text == "" for _, since, text in rows if not since)
    [(stored,)] = _rows(
        demo_file,
        "SELECT request FROM decisions WHERE as_of_day = 20 AND hotel = 'lifestyle' AND queued "
        "AND first_stay = 75",
    )
    request = json.loads(stored)
    [listed] = [
        e["earlier_changes_on_these_dates"] for e in request["entries"] if e["id"] == "75-75"
    ]
    assert listed == [line]
    assert _rows(demo_file, "SELECT count(*) FROM queue WHERE since_last_change <> ''") == [(1,)]
    assert _rows(demo_file, "SELECT DISTINCT since_last_change FROM queue WHERE NOT queued") == [
        ("",)
    ]
    # Each queued row carries the digest of its request as the decisions table stores it.
    digests = (
        "SELECT DISTINCT request_digest FROM {} "
        "WHERE as_of_day = 20 AND hotel = 'lifestyle' AND queued"
    )
    queued = _rows(demo_file, digests.format("queue"))
    assert queued == _rows(demo_file, digests.format("decisions")) and len(queued) == 1
    assert _rows(demo_file, "SELECT DISTINCT request_digest FROM queue WHERE NOT queued") == [("",)]


def test_a_queued_plans_headline_leads_with_the_money(demo_file):
    # The value at stake to the nearest $10, as the request shows it, then the plan with its days
    # of the week written out, then its stay dates. A held flag has no headline.
    [(value, headline)] = _rows(
        demo_file,
        "SELECT value, headline FROM queue WHERE as_of_day = 20 AND hotel = 'lifestyle' "
        "AND stays = 'Sat 20 Mar'",
    )
    money = f"+${10 * round(value / 10):,}"
    assert headline == f"{money} over holding · raise 10% on Saturday · Sat 20 Mar"
    assert money == "+$730"
    # Two days join with "and", three or more with commas and a last "and".
    [(airport,)] = _rows(
        demo_file, "SELECT headline FROM queue WHERE as_of_day = 20 AND hotel = 'airport'"
    )
    assert airport == (
        "+$10,140 over holding · raise 5% on Tuesday and Friday; raise 10% on Monday, Wednesday, "
        "Thursday and Sunday · Tue 23 Feb to Fri 23 Apr"
    )
    assert _rows(demo_file, "SELECT DISTINCT headline FROM queue WHERE NOT queued") == [("",)]


def test_a_queued_plan_dates_the_requests_numbers_for_its_stay_dates(demo_file):
    # The reasons name stay dates by the request's numbers, so each queued plan's row gives
    # them the page's dates. A held flag has none.
    dated = dict(
        _rows(
            demo_file,
            "SELECT stays, stay_numbers_text FROM queue "
            "WHERE as_of_day = 20 AND hotel = 'lifestyle' AND queued",
        )
    )
    assert dated == {
        "Tue 23 Feb to Fri 19 Mar": "Stay dates 50 to 74 are Tue 23 Feb to Fri 19 Mar.",
        "Sat 20 Mar": "Stay date 75 is Sat 20 Mar.",
        "Sun 21 Mar to Fri 23 Apr": "Stay dates 76 to 109 are Sun 21 Mar to Fri 23 Apr.",
    }
    held = _rows(demo_file, "SELECT DISTINCT stay_numbers_text FROM queue WHERE NOT queued")
    assert held == [("",)]


def test_the_strip_counts_the_moments_flags_and_recommendations(demo_file):
    # Day 20 at the lifestyle hotel: the filing is the day's first news, the day's flags cover
    # the stay dates the charts band in red, and the three accepted plans' values add up.
    [(news, nights, count, money)] = _rows(
        demo_file,
        "SELECT news, nights_flagged, recommendations, value_at_stake FROM strip "
        "WHERE as_of_day = 20 AND hotel = 'lifestyle' AND as_of_tick = 1",
    )
    assert news.startswith("The airlines filed a schedule change")
    assert nights > 0 and count == 3
    values = _rows(
        demo_file,
        "SELECT value FROM queue WHERE as_of_day = 20 AND hotel = 'lifestyle' "
        "AND outcome = 'accepted'",
    )
    assert money == f"+${10 * round(sum(value for (value,) in values) / 10):,}"
    # Everywhere, the nights flagged are the stay dates the charts mark flagged at that moment.
    differ = _rows(
        demo_file,
        "SELECT count(*) FROM strip s WHERE nights_flagged <> (SELECT count(*) FROM stay_dates d "
        "WHERE d.as_of_day = s.as_of_day AND d.hotel = s.hotel AND d.as_of_tick = s.as_of_tick "
        "AND d.flagged)",
    )
    assert differ == [(0,)]
    # A day with no news, no flag and no plan.
    quiet = _rows(
        demo_file,
        "SELECT news, nights_flagged, recommendations, value_at_stake FROM strip "
        "WHERE as_of_day = 0 AND hotel = 'convention'",
    )
    assert quiet == [("Nothing new", 0, 0, "$0")]


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
            "An event, the convention, was announced for Thu 18 Feb to Sun 21 Feb. "
            "Demand there is up 35.0%, and the comp set's rates are up 15.0%.",
        ),
        (
            "comp set",
            "The comp set median is up 10.3% to 17.1% for Thu 18 Feb to Sun 21 Feb.",
        ),
    ]
    filings = _rows(
        demo_file,
        "SELECT DISTINCT as_of_day, text FROM news WHERE kind = 'schedule' ORDER BY as_of_day",
    )
    assert filings == [
        (
            20,
            "The airlines filed a schedule change: arriving passengers are up 12.8% to 23.0% "
            "for Tue 23 Feb to Wed 2 Jun.",
        ),
        (
            40,
            "The airlines filed a schedule change: arriving passengers are down 8.1% to 9.9% "
            "for Mon 15 Mar to Sun 4 Apr.",
        ),
    ]
    day30 = _rows(
        demo_file, "SELECT text FROM news WHERE as_of_day = 30 AND hotel = 'full-service'"
    )
    assert day30 == [("The comp set median is down 8.3% to 11.0% for Wed 10 Feb to Fri 12 Feb.",)]


def test_a_flag_from_pace_alone_says_why_in_the_news(demo_file, demo_file_intraday):
    """Pace is no feed, so the news names the nights a pace flag covers: on convention day 44
    three nights run ahead of the usual pace. No moment with a flagged night says that nothing
    new became known, on either clock."""
    pace = "Bookings are running ahead of the usual pace for Thu 18 Feb, Sun 21 Feb and Fri 26 Mar."
    assert _rows(
        demo_file, "SELECT kind, text FROM news WHERE as_of_day = 44 AND hotel = 'convention'"
    ) == [("pace", pace)]
    unexplained = (
        "SELECT count(*) FROM strip s WHERE nights_flagged > 0 AND NOT EXISTS (SELECT 1 FROM news "
        "n WHERE n.as_of_day = s.as_of_day AND n.hotel = s.hotel AND n.as_of_tick <= s.as_of_tick "
        "AND n.kind <> 'none')"
    )
    assert _rows(demo_file, unexplained) == [(0,)]
    assert _rows(demo_file_intraday, unexplained) == [(0,)]


def test_the_chart_rows_mark_the_flagged_stay_dates_and_carry_the_planned_rate(demo_file):
    flagged = _rows(
        demo_file,
        "SELECT stay_day, rate, rooms_on_books > 0, pace > 0, causes, flag, planned_rate "
        "FROM stay_dates "
        "WHERE as_of_day = 20 AND hotel = 'airport' AND flag = '50-109' ORDER BY stay_day",
    )
    assert [row[0] for row in flagged] == list(range(50, 110))
    assert {row[1] for row in flagged} == {140.0} and all(row[3] for row in flagged)  # pace > 0
    assert {row[4] for row in flagged} == {"seats up"}
    assert {row[5] for row in flagged} == {"50-109"}
    # The accepted plan raises 5% on Tue and Fri and 10% on Mon, Wed, Thu and Sun; Sat holds at
    # the current rate. Day 50 is a Tuesday.
    assert [row[6] for row in flagged][:7] == pytest.approx([147, 154, 154, 147, 140, 154, 154])
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


@pytest.fixture(scope="module")
def demo_file_4(tmp_path_factory):
    """The demo file of seed 7 at four ticks a day."""
    from hotel_market.demo_data import build

    out = tmp_path_factory.mktemp("ticks") / "demo4.duckdb"
    source = build(7, out, ticks=4)
    return out, source


def test_at_four_ticks_the_news_names_each_feeds_tick_and_the_filings_outcome(demo_file_4):
    """At four ticks a day each news line opens with the time of day its feed landed at, the
    filing day adds the first flag, the first accepted raise, its stay dates and what they earned
    against the fixed-rate run, the queue holds every tick's flags, a planned rate names its time,
    and the template writes every reason, because the recording at this clock is the intraday
    market's and none of its requests is this market's."""
    out, source = demo_file_4
    assert source.startswith("the model's where the recorded live run covers the request and the")
    assert source.endswith("it does not")
    assert _rows(out, "SELECT seed, reason_source FROM run") == [(7, source)]
    day20 = _rows(
        out,
        "SELECT kind, text FROM news WHERE as_of_day = 20 AND hotel = 'airport' ORDER BY position",
    )
    assert day20[0] == (
        "schedule",
        "At 14:00 the airlines filed a schedule change: arriving passengers are up 12.8% "
        "to 23.0% for Tue 23 Feb to Wed 2 Jun.",
    )
    kinds = [kind for kind, _ in day20]
    assert "decision" in kinds
    decision = next(text for kind, text in day20 if kind == "decision")
    assert decision.startswith(
        "The first flag rose at 14:00, and the first raise was accepted at 14:00 for "
    )
    assert "those stay dates earned " in decision and "against the fixed-rate run." in decision
    day10 = _rows(
        out,
        "SELECT kind, text FROM news WHERE as_of_day = 10 AND hotel = 'convention' "
        "ORDER BY position",
    )
    # The shop lands at tick 2 and the event at tick 4; the event's day closes with its outcome.
    assert [kind for kind, _ in day10] == ["comp set", "event", "decision"]
    assert day10[0][1].startswith("At 11:00 the comp set median is")
    assert day10[1][1].startswith("At 17:00 an event, the convention, was announced for")
    assert day10[2][1].startswith("The first flag rose at 17:00")
    assert _rows(out, "SELECT count(*) FROM news WHERE text LIKE '%tick%'") == [(0,)]
    assert _rows(out, "SELECT DISTINCT text FROM news WHERE as_of_day = 0") == [(NOTHING_NEW,)]
    assert _rows(out, "SELECT COUNT(*) FROM news WHERE text = ?", NOTHING_NEW)[0][0] <= SIM_DAYS * 4
    planned = _rows(
        out,
        "SELECT DISTINCT decided_at FROM stay_dates WHERE as_of_day = 20 AND hotel = 'airport' "
        "AND planned_rate IS NOT NULL",
    )
    assert planned == [("14:00",)]
    assert _rows(out, "SELECT DISTINCT decided_at FROM stay_dates WHERE planned_rate IS NULL") == [
        ("",)
    ]
    queued = _rows(out, "SELECT DISTINCT reason_source FROM queue WHERE queued")
    assert queued == [("template",)]
    positions = _rows(
        out,
        "SELECT position FROM queue WHERE as_of_day = 20 AND hotel = 'airport' ORDER BY position",
    )
    assert [p for (p,) in positions] == list(range(len(positions)))
    ticks = _rows(out, "SELECT DISTINCT as_of_tick FROM decisions ORDER BY 1")
    assert ticks == [(1,), (2,), (3,), (4,)]


def test_at_one_tick_a_day_the_demo_file_has_no_tick_in_it(demo_file):
    """The daily clock's file reads as before: no tick words in the news, no decided-at or
    in-effect text, and the demo-data command takes --ticks with 1 as its default."""
    assert _rows(demo_file, "SELECT COUNT(*) FROM news WHERE text LIKE '%tick%'") == [(0,)]
    assert _rows(demo_file, "SELECT DISTINCT decided_at FROM stay_dates") == [("",)]
    assert _rows(demo_file, "SELECT DISTINCT decided_at, in_effect FROM queue") == [("", "")]
    assert _rows(demo_file, "SELECT DISTINCT kind FROM news WHERE kind = 'decision'") == []
    assert _rows(demo_file, "SELECT ticks FROM run") == [(1,)]
    for table in ("news", "stay_dates", "queue"):
        assert _rows(demo_file, f"SELECT DISTINCT as_of_tick FROM {table}") == [(1,)]


def test_the_intraday_file_holds_each_ticks_news_queue_and_chart_rows(demo_file_intraday):
    """On the intraday market at four ticks a day, the run table says four, each news row names
    the tick its news landed at, the queue holds each tick's flags under that tick, and the chart
    rows come once per tick as of it. On day 25 the lifestyle hotel's concert lands at tick 2,
    11:00, with the raise accepted at the same tick, the outcome line lands at tick 4, and tick 1
    has nothing yet; the day-20 filing lands at tick 1 and the day-45 repricing at tick 3. The
    reasons are the recorded intraday run's (tests/fixtures/live_seed7_intraday), which covers
    every request, so the concert's raise carries the model's reason."""
    out = demo_file_intraday
    assert _rows(out, "SELECT ticks FROM run") == [(4,)]
    assert _rows(out, "SELECT reason_source FROM run") == [
        ("the model's, from the recorded live run",)
    ]
    assert _rows(out, "SELECT DISTINCT reason_source FROM queue WHERE queued") == [("model",)]
    record = json.loads(
        (
            ROOT / "tests" / "fixtures" / "live_seed7_intraday" / "day025-t2_lifestyle.json"
        ).read_text()
    )
    reasons = _rows(
        out,
        "SELECT reason FROM queue WHERE as_of_day = 25 AND hotel = 'lifestyle' AND queued",
    )
    assert len(reasons) == 1 and reasons[0][0] in {d["reason"] for d in record["decisions"]}
    news = _rows(
        out,
        "SELECT as_of_tick, kind, text FROM news WHERE as_of_day = 25 AND hotel = 'lifestyle' "
        "ORDER BY position",
    )
    assert [(tick, kind) for tick, kind, _ in news] == [(2, "event"), (4, "decision")]
    assert news[0][2].startswith(
        "At 11:00 an event, the concert, was announced for Thu 4 Feb to Fri 5 Feb."
    )
    assert news[1][2].startswith(
        "The first flag rose at 11:00, and the first raise was accepted at 11:00 for "
        "Thu 4 Feb to Fri 5 Feb; those stay dates earned "
    )
    queue = _rows(
        out,
        "SELECT as_of_tick, position, plan, outcome FROM queue WHERE as_of_day = 25 AND "
        "hotel = 'lifestyle' ORDER BY as_of_tick, position",
    )
    assert queue == [(2, 0, "raise 10% on Thu, Fri", "accepted")]
    charts = _rows(
        out,
        "SELECT as_of_tick, COUNT(*), MAX(planned_rate), MAX(decided_at) FROM stay_dates "
        "WHERE as_of_day = 25 AND hotel = 'lifestyle' GROUP BY as_of_tick ORDER BY as_of_tick",
    )
    assert charts == [
        (1, 90, None, ""),
        (2, 90, 264.0, "11:00"),
        (3, 90, 264.0, "11:00"),
        (4, 90, 264.0, "11:00"),
    ]
    # The concert's plan leads with its money and names its time and when it is in effect from,
    # and the strip counts it from 11:00 on, as the day so far.
    assert _rows(
        out,
        "SELECT headline, decided_at, in_effect FROM queue WHERE as_of_day = 25 AND "
        "hotel = 'lifestyle'",
    ) == [
        (
            "+$2,470 over holding · raise 10% on Thursday and Friday · Thu 4 Feb to Fri 5 Feb",
            "11:00",
            "in effect from 14:00",
        )
    ]
    strip = _rows(
        out,
        "SELECT as_of_tick, nights_flagged, recommendations, value_at_stake FROM strip "
        "WHERE as_of_day = 25 AND hotel = 'lifestyle' ORDER BY as_of_tick",
    )
    assert strip == [
        (1, 0, 0, "$0"),
        (2, 2, 1, "+$2,470"),
        (3, 2, 1, "+$2,470"),
        (4, 2, 1, "+$2,470"),
    ]
    # A plan accepted at the day's last tick takes effect the next day, so it names no tick.
    assert _rows(
        out, "SELECT DISTINCT in_effect FROM queue WHERE as_of_tick = 4 OR outcome <> 'accepted'"
    ) == [("",)]
    assert _rows(out, "SELECT count(*) FROM strip") == [(60 * 4 * 4,)]
    landed = "SELECT as_of_tick FROM news WHERE as_of_day = ? AND hotel = ? AND kind = ?"
    assert _rows(out, landed, 20, "airport", "schedule") == [(1,)]
    assert _rows(out, landed, 45, "lifestyle", "event") == [(3,)]
    # Every tick of every day has its chart rows for every hotel, and a day with no news holds
    # one row saying so, at tick 1.
    assert _rows(out, "SELECT COUNT(DISTINCT (as_of_day, hotel, as_of_tick)) FROM stay_dates") == [
        (60 * 4 * 4,)
    ]
    assert _rows(out, "SELECT DISTINCT as_of_tick FROM news WHERE kind = 'none'") == [(1,)]
