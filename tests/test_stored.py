"""Module 12, stored.py: the four sources from stored tables, and the daily commands."""

import json

import pytest

from hotel_market import stored
from hotel_market.agent import TRUE_MODE
from hotel_market.bookings import simulate
from hotel_market.cli import (
    ArmResult,
    SeedResult,
    format_entry,
    main,
    outcomes_of,
    queue,
    replay_day,
    run,
    run_day,
    run_days,
)
from hotel_market.customer import demo
from hotel_market.model import MODEL, prompt_digest, request_digest
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


def test_the_schema_is_eight_tables_each_keyed_by_its_day(tmp_path):
    connection = stored.connect(tmp_path / "new.duckdb")
    tables = connection.execute(
        "SELECT table_name FROM information_schema.tables ORDER BY table_name"
    ).fetchall()
    assert {name for (name,) in tables} == set(stored.TABLES) and len(stored.TABLES) == 8
    for table in stored.TABLES:
        columns = connection.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ? "
            "ORDER BY ordinal_position",
            [table],
        ).fetchall()
        # The feeds and the agent's output are keyed by the day they were known on; an outcome
        # by the day its plan was accepted, so the plan is one join away.
        assert columns[0] == (("decision_day",) if table == "outcomes" else ("as_of_day",)), table
        assert tuple(name for (name,) in columns) == stored._COLUMNS[table], table
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
                assert sources.shops.first_median(hotel) == simulated.shops.first_median(hotel)
        assert (sources.schedules.seats(day) == simulated.schedules.seats(day)).all()
        assert (sources.schedules.passengers(day) == simulated.schedules.passengers(day)).all()
        assert dict(sources.schedules.passenger_change(day)) == dict(
            simulated.schedules.passenger_change(day)
        )
        assert dict(sources.schedules.passenger_revision(day)) == dict(
            simulated.schedules.passenger_revision(day)
        )
        assert sources.events.known(day) == simulated.events.known(day)
    connection.close()


def test_each_decision_carries_its_request_its_answer_and_their_digests(
    in_memory, through_tables, tmp_path
):
    """A queued entry's row holds the request its hotel's queue was asked with, the answer and the
    request's digest. The template run has no prompt digest and no model; a model's cached
    record gives both. Held flags and advice carry NULLs."""
    _, _, agent = in_memory
    connection = stored.connect(through_tables, read_only=True)
    try:
        rows = connection.execute(
            "SELECT as_of_day, hotel, first_stay, last_stay, queued, simulated, request_digest, "
            "prompt_digest, model, request, answer FROM decisions ORDER BY as_of_day, position"
        ).fetchall()
    finally:
        connection.close()
    queued = [row for row in rows if row[4]]
    assert queued and all(row[6] and row[9] and row[10] for row in queued)
    assert {(row[7], row[8]) for row in queued} == {(None, None)}  # the template answered
    for day, hotel, first, last, _, _, digest, _, _, request, answer in queued:
        request, answer = json.loads(request), json.loads(answer)
        assert digest == request_digest(request) and request["day"] == day
        assert request["hotel"]["name"] == demo().hotel(hotel).name
        assert f"{first}-{last}" in {entry["id"] for entry in request["entries"]}
        assert {d["id"] for d in answer} == {entry["id"] for entry in request["entries"]}
        stored_request, _ = agent.asked[(day, hotel)]
        assert request == stored_request
    assert all(row[6:] == (None,) * 5 for row in rows if not row[4])
    # With a model answering, the cache record's prompt digest and model come along.
    from tests.test_cli import FakeClient

    db = tmp_path / "model.duckdb"
    run_days(SEED, 0, 20, db, cache_dir=tmp_path / "cache", client=FakeClient())
    connection = stored.connect(db, read_only=True)
    try:
        found = connection.execute(
            "SELECT DISTINCT prompt_digest, model FROM decisions WHERE queued"
        ).fetchall()
    finally:
        connection.close()
    assert found == [(prompt_digest(), MODEL)]


def test_the_outcomes_hold_each_accepted_plans_nights_once_they_pass(in_memory, through_tables):
    """Once a night has passed, every accepted plan that changed its rate has an outcome row: the
    rooms sold and the room revenue of the in-memory run, the plan's estimate for that night, and
    what the rooms sold after the decision earned. Nights after the last day run have none."""
    _, books, agent = in_memory
    connection = stored.connect(through_tables, read_only=True)
    try:
        rows = connection.execute(
            "SELECT decision_day, hotel, stay_day, rooms_sold, room_revenue, estimated, realised "
            "FROM outcomes ORDER BY decision_day, hotel, stay_day"
        ).fetchall()
    finally:
        connection.close()
    expected = {}
    for entry in agent.entries:
        if entry.action == HOLD:
            continue
        for group in entry.changed_weekdays:
            for stay, estimate in group.best.estimates.items():
                if stay < SIM_DAYS:
                    expected[(entry.day, entry.hotel, stay)] = estimate
    assert expected and {row[:3] for row in rows} == set(expected)
    for decision_day, key, stay, sold, revenue, estimated, realised in rows:
        hotel = demo().hotel(key)
        assert sold == books.rooms[hotel.row, stay]
        assert revenue == pytest.approx(books.revenue[hotel.row, stay])
        assert estimated == pytest.approx(expected[(decision_day, key, stay)])
        after = books.daily_rooms[decision_day + 1 :, hotel.row, stay]
        rates = books.daily_rates[decision_day + 1 :, hotel.row, stay]
        assert realised == pytest.approx(float((after * (rates - hotel.room_cost)).sum()))
    # The plans table carries each candidate's estimate per night, summing to its estimate.
    connection = stored.connect(through_tables, read_only=True)
    try:
        plans = connection.execute("SELECT estimates, estimate FROM plans").fetchall()
    finally:
        connection.close()
    assert all(sum(json.loads(e).values()) == pytest.approx(total) for e, total in plans)


def test_the_sweeps_outcome_records_are_the_stored_outcomes_rows(in_memory, through_tables):
    """outcomes_of() gives the sweep, from a run's own books, the records write_outcomes() stores
    through the tables: the same nights with the same figures, for every night that has passed."""
    _, books, agent = in_memory
    records = outcomes_of(agent.entries, books, demo())
    assert records and any(o.stay_day >= SIM_DAYS for o in records)  # the run books on to 149
    passed = sorted(o for o in records if o.stay_day < SIM_DAYS)
    connection = stored.connect(through_tables, read_only=True)
    try:
        rows = connection.execute(
            "SELECT decision_day, hotel, stay_day, rooms_sold, room_revenue, estimated, realised "
            "FROM outcomes ORDER BY decision_day, hotel, stay_day"
        ).fetchall()
    finally:
        connection.close()
    assert len(rows) == len(passed)
    for row, record in zip(rows, passed):
        assert row[:4] == record[:4]
        assert row[4:] == pytest.approx(record[4:])
    # Per arm the sweep prints these summed: the estimates against what the rooms sold earned.
    arm = ArmResult(TRUE_MODE, [SeedResult(SEED, 0.0, 0.0, 0, outcomes=records)])
    assert arm.nights == len(records)
    assert arm.estimated_on_nights == pytest.approx(sum(o.estimated for o in records))
    assert arm.realised_on_nights == pytest.approx(sum(o.realised for o in records))


def test_the_daily_commands_take_the_world_options(tmp_path, capsys):
    """run-day runs the simulator under the world its options describe, as the sweep does, and
    the agent is told the market elasticity; replay needs the same value to rebuild the plans."""
    db = tmp_path / "world.duckdb"
    main(
        ["run-day", "--seed", str(SEED), "--as-of", "12", "--from", "0", "--db", str(db)]
        + ["--react", "--market-elasticity", "0.5", "--demand-bias", "0.9", "--template"]
    )
    out = capsys.readouterr().out
    assert "feeds, flags, plans, decisions and outcomes are in" in out
    connection = stored.connect(db, read_only=True)
    try:
        records = stored.records_on(connection, 12)
        rooms = connection.execute(
            "SELECT SUM(rooms_taken) FROM daily_bookings WHERE as_of_day = 0"
        ).fetchone()[0]
    finally:
        connection.close()
    assert records and all(r["elasticity"]["market_elasticity"] == 0.5 for r in records)
    plain = simulate(SEED, last_day=0)
    assert rooms < plain.daily_rooms[0].sum()  # a tenth less demand booked fewer rooms
    # On day 10 the convention moved the comp medians, so the market term reaches the estimates:
    # told the run's value the replay rebuilds the plans, told the default it does not.
    assert replay_day(10, db, market_elasticity=0.5)[2] == []
    with pytest.raises(SystemExit):
        main(["replay", "--as-of", "10", "--db", str(db)])
    assert "The rebuilt plans differ from the stored plans" in capsys.readouterr().out


def test_running_a_day_twice_leaves_the_tables_unchanged(through_tables):
    before = _dump(through_tables)
    run_day(SEED, 20, through_tables)
    assert _dump(through_tables) == before


def test_the_stored_state_is_what_the_earlier_decisions_left(in_memory, through_tables):
    _, _, agent = in_memory
    connection = stored.connect(through_tables, read_only=True)
    held, advised, changes = stored.state_before(connection, 30)
    connection.close()
    expected_held = {}
    for entry in agent.entries:
        if entry.day < 30 and entry.action != HOLD:
            for stay_day in entry.new_rates:
                expected_held[(entry.hotel, stay_day)] = entry.day
    assert held == expected_held
    assert advised == {(a.hotel, a.event) for a in agent.advice if a.day < 30}
    # The accepted changes come back as the agent kept them: exact rates and expected rooms.
    kept = [c for found in agent.changes.values() for c in found if c.day < 30]
    assert changes and sorted(changes, key=str) == sorted(kept, key=str)


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
    assert "Day 1's feeds, flags, plans, decisions and outcomes are in" in out
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


def test_the_stored_sources_refuse_a_later_day_and_the_daily_commands_make_them_for_the_day(
    through_tables, monkeypatch
):
    """Made for a day, the stored sources refuse a question about a later day, as the simulated
    sources do, so a replay of day 10 cannot read the days after it. run-day and replay make the
    sources for the day they decide, and sources made with no day answer any day the tables hold."""
    connection = stored.connect(through_tables, read_only=True)
    try:
        sources = stored.stored_sources(connection, as_of_day=10)
        hotel = DEMO.hotels[0]
        assert sources.bookings.on_books(10).sum() > 0
        assert sources.bookings.history(11).taken.shape[0] == 11  # today's bookings are in
        for ask in (
            lambda: sources.bookings.on_books(34),
            lambda: sources.bookings.rates(11),
            lambda: sources.bookings.history(12),
            lambda: sources.shops.competitor_rates(11, hotel, 50),
            lambda: sources.shops.median(34, hotel, 46),
            lambda: sources.shops.median_history(12),
            lambda: sources.schedules.seats(20),
            lambda: sources.events.known(34),
        ):
            with pytest.raises(ValueError, match="on day 10"):
                ask()
        any_day = stored.stored_sources(connection)
        assert [e.name for e in any_day.events.known(34)] == ["Convention"]
    finally:
        connection.close()
    seen = []
    original = stored.stored_sources

    def spy(connection, customer=None, as_of_day=None, as_of_tick=None, ticks=1):
        seen.append(as_of_day)
        return original(connection, customer, as_of_day)

    monkeypatch.setattr(stored, "stored_sources", spy)
    replay_day(10, through_tables)
    run_day(SEED, 20, through_tables)
    assert seen == [10, 20]
