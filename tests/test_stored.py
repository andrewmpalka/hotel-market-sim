"""Module 12, stored.py: the four sources from stored tables, and the daily commands."""

import pytest

from hotel_market import stored
from hotel_market.bookings import simulate
from hotel_market.cli import format_entry, main, queue, replay_day, run, run_day, run_days
from hotel_market.customer import demo
from hotel_market.plan import HOLD
from hotel_market.simulated import simulated_sources
from hotel_market.world import SIM_DAYS

SEED = 7
DEMO = demo()


@pytest.fixture(scope="module")
def in_memory(tmp_path_factory):
    """The seed-7 run in memory with the template: its decisions file, books and agent."""
    folder = tmp_path_factory.mktemp("memory")
    _, books, agent = run(SEED, folder / "decisions.jsonl", folder / "cache")
    return folder / "decisions.jsonl", books, agent


@pytest.fixture(scope="module")
def through_tables(tmp_path_factory):
    """The same run, day by day through the stored tables: the DuckDB file."""
    folder = tmp_path_factory.mktemp("tables")
    run_days(SEED, 0, SIM_DAYS - 1, folder / "run.duckdb", cache_dir=folder / "cache")
    return folder / "run.duckdb"


def _dump(db) -> dict[str, list[tuple]]:
    connection = stored.connect(db, read_only=True)
    try:
        return {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY ALL").fetchall()
            for table in stored.TABLES
        }
    finally:
        connection.close()


def test_the_schema_is_seven_tables_each_keyed_by_as_of_day(tmp_path):
    connection = stored.connect(tmp_path / "new.duckdb")
    tables = connection.execute(
        "SELECT table_name FROM information_schema.tables ORDER BY table_name"
    ).fetchall()
    assert {name for (name,) in tables} == set(stored.TABLES)
    for table in stored.TABLES:
        columns = connection.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ? "
            "ORDER BY ordinal_position",
            [table],
        ).fetchall()
        assert columns[0] == ("as_of_day",), table
    connection.close()
    assert _dump(tmp_path / "new.duckdb") == {table: [] for table in stored.TABLES}


def test_a_60_day_run_through_the_tables_gives_the_same_decisions_file(in_memory, through_tables):
    file, _, _ = in_memory
    connection = stored.connect(through_tables, read_only=True)
    assert stored.decisions_file(connection) == file.read_text()
    assert stored.stored_days(connection) == list(range(SIM_DAYS))
    connection.close()


def test_the_stored_sources_answer_as_the_simulated_ones_do(in_memory, through_tables):
    _, books, _ = in_memory
    simulated = simulated_sources(books)
    connection = stored.connect(through_tables, read_only=True)
    sources = stored.stored_sources(connection)
    for day in (0, 20, 59):
        assert (sources.bookings.on_books(day) == simulated.bookings.on_books(day)).all()
        assert (sources.bookings.rates(day) == simulated.bookings.rates(day)).all()
        stored_history, history = sources.bookings.history(day), simulated.bookings.history(day)
        assert (stored_history.taken == history.taken).all()
        assert (stored_history.rates == history.rates).all()
        assert (stored_history.opening == history.opening).all()
        assert (sources.shops.median_history(day) == simulated.shops.median_history(day)).all()
        for hotel in DEMO.hotels:
            for stay_day in (day, day + 45, day + 89):
                assert sources.shops.competitor_rates(
                    day, hotel, stay_day
                ) == simulated.shops.competitor_rates(day, hotel, stay_day)
                assert sources.shops.median(day, hotel, stay_day) == simulated.shops.median(
                    day, hotel, stay_day
                )
                assert sources.shops.first_median(hotel, stay_day) == simulated.shops.first_median(
                    hotel, stay_day
                )
        assert (sources.schedules.seats(day) == simulated.schedules.seats(day)).all()
        assert dict(sources.schedules.seat_change(day)) == dict(
            simulated.schedules.seat_change(day)
        )
        assert dict(sources.schedules.seat_revision(day)) == dict(
            simulated.schedules.seat_revision(day)
        )
        assert sources.events.known(day) == simulated.events.known(day)
    connection.close()


def test_running_a_day_twice_leaves_the_tables_unchanged(through_tables):
    before = _dump(through_tables)
    run_day(SEED, 20, through_tables)
    assert _dump(through_tables) == before


def test_the_stored_state_is_what_the_earlier_decisions_left(in_memory, through_tables):
    _, _, agent = in_memory
    connection = stored.connect(through_tables, read_only=True)
    held, advised = stored.state_before(connection, 30)
    connection.close()
    expected_held = {}
    for entry in agent.entries:
        if entry.day < 30 and entry.action != HOLD:
            for stay_day in entry.new_rates:
                expected_held[(entry.hotel, stay_day)] = entry.day
    assert held == expected_held
    assert advised == {(a.hotel, a.event) for a in agent.advice if a.day < 30}


def test_replaying_a_past_day_reproduces_its_plans_exactly(in_memory, through_tables):
    _, _, agent = in_memory
    for day in (10, 20):
        entries, advice, differences = replay_day(day, through_tables)
        assert differences == []
        connection = stored.connect(through_tables, read_only=True)
        records = stored.records_on(connection, day)
        connection.close()
        assert [e.to_json() for e in entries] + [a.to_json() for a in advice] == records
        expected = [e for e in agent.entries if e.day == day]
        assert [format_entry(e) for e in queue(entries)] == [
            format_entry(e) for e in queue(expected)
        ]


def test_a_day_cannot_run_before_the_days_before_it(tmp_path):
    with pytest.raises(ValueError, match="holds no day 0"):
        run_day(SEED, 5, tmp_path / "empty.duckdb")


def test_the_daily_commands_run_a_day_and_replay_it(tmp_path, capsys):
    db = tmp_path / "run.duckdb"
    main(["run-day", "--seed", str(SEED), "--as-of", "1", "--from", "0", "--db", str(db)])
    out = capsys.readouterr().out
    assert "Day 1's feeds, flags, plans and decisions are in" in out
    main(["replay", "--as-of", "1", "--db", str(db)])
    out = capsys.readouterr().out
    assert out.startswith("Day 1 queue, rebuilt from the tables in")
    assert "The rebuilt plans match the stored plans." in out
    with pytest.raises(SystemExit):
        main(["run-day", "--seed", str(SEED), "--as-of", "60", "--db", str(db)])


def test_a_failed_day_write_rolls_the_earlier_tables_back(tmp_path, monkeypatch):
    """write_snapshot deletes and rewrites a day's rows table by table inside one transaction.
    When a later table's insert fails, the rollback gives the earlier table its day back."""
    db = tmp_path / "run.duckdb"
    run_days(SEED, 0, 2, db, cache_dir=tmp_path / "cache")
    feed = simulated_sources(simulate(SEED, last_day=2))
    original = stored._replace_day

    def failing(connection, table, day, rows):
        if table == "daily_bookings":
            original(connection, table, day, [])  # the day deleted and nothing written back
        elif table == "rate_shops":
            raise RuntimeError("the second table's insert failed")
        else:
            original(connection, table, day, rows)

    connection = stored.connect(db)
    try:
        day2 = "SELECT * FROM daily_bookings WHERE as_of_day = 2 ORDER BY ALL"
        before = connection.execute(day2).fetchall()
        assert before
        monkeypatch.setattr(stored, "_replace_day", failing)
        with pytest.raises(RuntimeError, match="second table"):
            stored.write_snapshot(connection, 2, feed)
        assert connection.execute(day2).fetchall() == before
        assert stored.stored_days(connection) == [0, 1, 2]
    finally:
        connection.close()
