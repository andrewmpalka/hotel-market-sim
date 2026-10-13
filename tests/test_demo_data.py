"""Module 26, demo_data.py: the demo page's file, written by code from the recorded run."""

import json
from pathlib import Path

import pytest

from hotel_market import stored
from hotel_market.demo_data import DEMO_TABLES, NOTHING_NEW, main, recorded_run
from hotel_market.world import SIM_DAYS

ROOT = Path(__file__).resolve().parents[1]


def _rows(path, sql, *parameters):
    connection = stored.connect(path, read_only=True)
    try:
        return connection.execute(sql, list(parameters)).fetchall()
    finally:
        connection.close()


def test_the_file_holds_the_stored_tables_for_every_day_and_the_pages_five(demo_file):
    connection = stored.connect(demo_file, read_only=True)
    try:
        assert stored.stored_days(connection) == list(range(SIM_DAYS))
        counts = {
            t: connection.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in DEMO_TABLES
        }
    finally:
        connection.close()
    assert counts["hotels"] == 4
    assert counts["scorecard"] == SIM_DAYS * 4 * 3  # a day, a hotel, and agent, fixed and delta
    assert counts["stay_dates"] == SIM_DAYS * 4 * 90  # the window of each day
    assert counts["news"] >= SIM_DAYS * 4  # at least the "nothing new" row
    assert (
        counts["queue"] == _rows(demo_file, "SELECT count(*) FROM decisions WHERE simulated")[0][0]
    )


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


def test_the_scorecard_is_to_date_and_the_delta_is_the_agent_run_minus_the_fixed_one(demo_file):
    # On day 0 nothing has changed yet. By day 59 the convention hotel's changed dates are all
    # past, so its contribution to date is the recorded run's +3,915 (README, seed 7). The other
    # hotels' changed dates still take bookings after day 59, so theirs are not final.
    day0 = _rows(
        demo_file,
        "SELECT max(abs(contribution)) FROM scorecard WHERE as_of_day = 0 AND run = 'delta'",
    )
    assert day0[0][0] == 0
    [(convention,)] = _rows(
        demo_file,
        "SELECT contribution FROM scorecard "
        "WHERE as_of_day = 59 AND hotel = 'convention' AND run = 'delta'",
    )
    assert convention == pytest.approx(3915, abs=1)
    mismatch = _rows(
        demo_file,
        "SELECT count(*) FROM scorecard a JOIN scorecard f USING (as_of_day, hotel) "
        "JOIN scorecard d USING (as_of_day, hotel) WHERE a.run = 'agent' AND f.run = 'fixed' "
        "AND d.run = 'delta' AND abs(a.contribution - f.contribution - d.contribution) > 1e-6",
    )
    assert mismatch[0][0] == 0
    [(occupancy, adr, revpar)] = _rows(
        demo_file,
        "SELECT occupancy, adr, revpar FROM scorecard "
        "WHERE as_of_day = 0 AND hotel = 'convention' AND run = 'fixed'",
    )
    assert 0 < occupancy < 1 and adr == 220 and revpar == pytest.approx(220 * occupancy)


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
            "An event, the convention, was announced for stay dates 45 to 48. "
            "Demand there is up 35.0%, and the comp set's rates are up 15.0%.",
        ),
        ("comp set", "The comp set median is up 15.0% for stay dates 45 to 48."),
    ]
    filings = _rows(
        demo_file,
        "SELECT DISTINCT as_of_day, text FROM news WHERE kind = 'schedule' ORDER BY as_of_day",
    )
    assert filings == [
        (
            20,
            "The airlines filed a schedule change: arriving seats are up 17.0% to 21.6% "
            "for stay dates 50 to 149.",
        ),
        (
            40,
            "The airlines filed a schedule change: arriving seats are down 7.9% to 9.7% "
            "for stay dates 70 to 90.",
        ),
    ]
    day30 = _rows(
        demo_file, "SELECT text FROM news WHERE as_of_day = 30 AND hotel = 'full-service'"
    )
    assert day30 == [("The comp set median is down 9.6% to 9.8% for stay dates 37 to 39.",)]


def test_the_chart_rows_mark_the_flagged_stay_dates(demo_file):
    flagged = _rows(
        demo_file,
        "SELECT stay_day, rate, comp_median > rate, rooms_on_books > 0, pace > 0, causes "
        "FROM stay_dates "
        "WHERE as_of_day = 10 AND hotel = 'convention' AND flagged ORDER BY stay_day",
    )
    assert [row[0] for row in flagged] == [45, 46, 47, 48]
    assert all(row[1:5] == (220.0, True, True, True) for row in flagged)
    assert {row[5] for row in flagged} == {"comp median up, event announced"}
    unflagged = _rows(demo_file, "SELECT DISTINCT causes FROM stay_dates WHERE NOT flagged")
    assert unflagged == [("",)]


def test_a_seed_with_no_recording_gets_the_templates_reasons(tmp_path, capsys):
    main(["--seed", "1", "--out", str(tmp_path / "one.duckdb")])
    assert "reasons from the template, as no run is recorded." in capsys.readouterr().out
    sources = _rows(
        tmp_path / "one.duckdb", "SELECT DISTINCT reason_source FROM queue WHERE queued"
    )
    assert sources == [("template",)]
