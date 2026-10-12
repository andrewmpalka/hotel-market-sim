"""stored.py

The agent's four sources read from stored tables, and the writers that fill them. The tables are
the ones sql/schema.sql defines, in a DuckDB file. Each is keyed by as_of_day, the day a row was
known on. The feeds are daily bookings, rate shops, schedule snapshots and events. The flags,
plans and decisions hold what the agent made of them.

Day -1 holds the position before the first day. A source answering as of a day reads only the
rows known by that day. The tables therefore keep the simulator's rule: nothing is used before
the day it became known.

write_snapshot() copies one day of any Sources into the feed tables. write_decisions() stores the
day's flags, plans and decisions. Both delete the day's rows first, so writing a day twice leaves
the tables as they were. state_before() gives an Agent the hold and the advice that earlier days
left. rate_changes_before() gives a simulator the accepted rates to play back. The hotel-market
run-day and replay commands (cli.py) drive them.

This module imports nothing from the simulator. A table-backed run knows the market only through
the tables and the customer file.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from hotel_market.customer import Customer, demo
from hotel_market.plan import HOLD, Entry
from hotel_market.sources import (
    BookingHistory,
    Bookings,
    Event,
    Events,
    RateShops,
    Schedules,
    Sources,
)
from hotel_market.world import HORIZON_DAYS, LOOKAHEAD_DAYS, Hotel, stay_window

SCHEMA_FILE = Path("sql") / "schema.sql"  # relative to the repository root
TABLES = (
    "daily_bookings",
    "rate_shops",
    "schedule_snapshots",
    "events",
    "flags",
    "plans",
    "decisions",
)
OPENING_DAY = -1  # the position before the first day: the opening rooms, shop and schedule

_COLUMNS = {
    "daily_bookings": ("as_of_day", "hotel", "stay_day", "rooms_taken", "rooms_on_books", "rate"),
    "rate_shops": ("as_of_day", "hotel", "stay_day", "competitor", "rate"),
    "schedule_snapshots": ("as_of_day", "stay_day", "seats"),
    "events": (
        "as_of_day",
        "name",
        "known_day",
        "start_day",
        "end_day",
        "hotels",
        "uplift",
        "comp_rate_raise",
    ),
    "flags": ("as_of_day", "hotel", "first_stay", "last_stay", "causes"),
    "plans": (
        "as_of_day",
        "hotel",
        "first_stay",
        "last_stay",
        "weekday",
        "candidate",
        "rates",
        "estimate",
        "versus_hold",
        "band_low",
        "band_high",
        "is_best",
    ),
    "decisions": (
        "as_of_day",
        "position",
        "hotel",
        "first_stay",
        "last_stay",
        "causes",
        "plan",
        "value_at_stake",
        "queued",
        "action",
        "reason",
        "reason_source",
        "elasticity",
        "elasticity_mode",
        "new_rates",
        "simulated",
        "event",
        "record",
    ),
}
# Columns that may be NULL: None is kept as NULL rather than becoming NaN.
_NULLABLE = {
    "plans": ("band_low", "band_high"),
    "decisions": ("plan", "value_at_stake", "elasticity", "elasticity_mode", "new_rates", "event"),
}


# ---- the file -------------------------------------------------------------


def schema_path() -> Path:
    """Where sql/schema.sql is: under the working directory, else the repository root."""
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        if (base / SCHEMA_FILE).exists():
            return base / SCHEMA_FILE
    raise FileNotFoundError(f"{SCHEMA_FILE} not found; run from the repository root")


def connect(path: Path | str, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """The tables in a DuckDB file, created from sql/schema.sql when they are missing."""
    connection = duckdb.connect(str(path), read_only=read_only)
    if not read_only:
        for statement in _statements(schema_path().read_text()):
            connection.execute(statement)
    return connection


def _statements(sql: str) -> list[str]:
    """The statements of a schema file, its comments dropped (it holds no string literals)."""
    code = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    return [statement for statement in code.split(";") if statement.strip()]


def _frame(connection, sql: str, parameters: list | None = None) -> pd.DataFrame:
    return connection.execute(sql, parameters or []).df()


# ---- the four sources, read from the tables ---------------------------------


class StoredBookings(Bookings):
    """daily_bookings, read as of a day."""

    def __init__(self, connection, customer: Customer):
        self.connection = connection
        self.hotels = customer.hotels
        self._rows = {hotel.key: hotel.row for hotel in self.hotels}

    def _row_index(self, frame: pd.DataFrame) -> np.ndarray:
        return frame["hotel"].map(self._rows).to_numpy(dtype=np.int64)

    def on_books(self, as_of_day: int) -> np.ndarray:
        frame = _frame(
            self.connection,
            "SELECT hotel, stay_day, CAST(SUM(rooms_taken) AS BIGINT) AS rooms "
            "FROM daily_bookings WHERE as_of_day <= ? GROUP BY hotel, stay_day",
            [as_of_day],
        )
        rooms = np.zeros((len(self.hotels), HORIZON_DAYS), dtype=np.int64)
        rooms[self._row_index(frame), frame["stay_day"].to_numpy()] = frame["rooms"].to_numpy()
        return rooms

    def rates(self, as_of_day: int) -> np.ndarray:
        frame = _frame(
            self.connection,
            "SELECT hotel, stay_day, rate FROM daily_bookings WHERE as_of_day = ?",
            [as_of_day],
        )
        rates = np.zeros((len(self.hotels), HORIZON_DAYS))
        rates[self._row_index(frame), frame["stay_day"].to_numpy()] = frame["rate"].to_numpy()
        return rates

    def history(self, as_of_day: int) -> BookingHistory:
        taken = np.zeros((as_of_day, len(self.hotels), HORIZON_DAYS), dtype=np.int64)
        rates = np.zeros((as_of_day, len(self.hotels), HORIZON_DAYS))
        frame = _frame(
            self.connection,
            "SELECT as_of_day, hotel, stay_day, rooms_taken, rate FROM daily_bookings "
            "WHERE as_of_day >= 0 AND as_of_day < ?",
            [as_of_day],
        )
        index = (
            frame["as_of_day"].to_numpy(),
            self._row_index(frame),
            frame["stay_day"].to_numpy(),
        )
        taken[index] = frame["rooms_taken"].to_numpy()
        rates[index] = frame["rate"].to_numpy()
        first = _frame(
            self.connection,
            "SELECT hotel, stay_day, rooms_taken FROM daily_bookings WHERE as_of_day = ?",
            [OPENING_DAY],
        )
        opening = np.zeros((len(self.hotels), HORIZON_DAYS), dtype=np.int64)
        opening[self._row_index(first), first["stay_day"].to_numpy()] = first[
            "rooms_taken"
        ].to_numpy()
        return BookingHistory(taken, rates, opening)


class StoredRateShops(RateShops):
    """rate_shops, one shop day at a time."""

    def __init__(self, connection, customer: Customer):
        self.connection = connection
        self.hotels = customer.hotels
        self._shops: dict[int, dict[tuple[str, int], dict[str, float]]] = {}

    def competitor_rates(self, shop_day: int, hotel: Hotel, stay_day: int) -> dict[str, float]:
        shop = self._shop(shop_day)
        if (hotel.key, stay_day) not in shop:
            raise LookupError(
                f"the tables hold no rate shop for {hotel.key}, stay date {stay_day}, "
                f"on day {shop_day}"
            )
        return dict(shop[(hotel.key, stay_day)])

    def _shop(self, shop_day: int) -> dict[tuple[str, int], dict[str, float]]:
        """The whole shop of a day, read once: {(hotel key, stay day): {competitor: rate}}."""
        if shop_day not in self._shops:
            frame = _frame(
                self.connection,
                "SELECT hotel, stay_day, competitor, rate FROM rate_shops WHERE as_of_day = ? "
                "ORDER BY hotel, stay_day, competitor",
                [shop_day],
            )
            shop: dict[tuple[str, int], dict[str, float]] = {}
            columns = (frame[name].tolist() for name in ("hotel", "stay_day", "competitor", "rate"))
            for hotel, stay_day, competitor, rate in zip(*columns):
                shop.setdefault((hotel, stay_day), {})[competitor] = rate
            self._shops[shop_day] = shop
        return self._shops[shop_day]

    def median_history(self, as_of_day: int) -> np.ndarray:
        medians = np.zeros((as_of_day, len(self.hotels), HORIZON_DAYS))
        if as_of_day <= 0:
            return medians
        # Only the nights in each day's window: the ones the hotel was selling that day.
        frame = _frame(
            self.connection,
            "SELECT as_of_day, hotel, stay_day, rate FROM rate_shops "
            "WHERE as_of_day >= 0 AND as_of_day < ? "
            "AND stay_day BETWEEN as_of_day AND as_of_day + ? "
            "ORDER BY as_of_day, hotel, stay_day, competitor",
            [as_of_day, LOOKAHEAD_DAYS - 1],
        )
        for hotel in self.hotels:
            rows = frame[frame["hotel"] == hotel.key]
            count = len(hotel.competitors)
            if len(rows) % count:
                raise ValueError(f"{hotel.key}: a shop with a competitor missing")
            rates = rows["rate"].to_numpy().reshape(-1, count)
            days = rows["as_of_day"].to_numpy()[::count]
            stays = rows["stay_day"].to_numpy()[::count]
            medians[days, hotel.row, stays] = _median(rates)
        return medians


def _median(values: np.ndarray) -> np.ndarray:
    """The median along the last axis, computed as statistics.median computes it."""
    ordered = np.sort(values, axis=-1)
    count = ordered.shape[-1]
    if count % 2:
        return ordered[..., count // 2]
    return (ordered[..., count // 2 - 1] + ordered[..., count // 2]) / 2


class StoredSchedules(Schedules):
    """schedule_snapshots: the seats arriving each day, as filed by a day."""

    def __init__(self, connection):
        self.connection = connection
        self._seats: dict[int, np.ndarray] = {}

    def seats(self, as_of_day: int) -> np.ndarray:
        if as_of_day not in self._seats:
            frame = _frame(
                self.connection,
                "SELECT stay_day, seats FROM schedule_snapshots WHERE as_of_day = ?",
                [as_of_day],
            )
            if frame.empty:
                raise LookupError(f"the tables hold no schedule snapshot for day {as_of_day}")
            seats = np.zeros(HORIZON_DAYS, dtype=np.int64)
            seats[frame["stay_day"].to_numpy()] = frame["seats"].to_numpy()
            self._seats[as_of_day] = seats
        return self._seats[as_of_day]


class StoredEvents(Events):
    """events: the calendar as of a day, read once per day asked about."""

    def __init__(self, connection):
        self.connection = connection
        self._known: dict[int, list[Event]] = {}

    def known(self, as_of_day: int) -> list[Event]:
        if as_of_day not in self._known:
            frame = _frame(
                self.connection,
                "SELECT name, known_day, start_day, end_day, hotels, uplift, comp_rate_raise "
                "FROM events WHERE as_of_day = ? ORDER BY known_day, name",
                [as_of_day],
            )
            self._known[as_of_day] = [
                Event(
                    row.name,
                    int(row.known_day),
                    int(row.start_day),
                    int(row.end_day),
                    tuple(row.hotels.split(",")),
                    float(row.uplift),
                    float(row.comp_rate_raise),
                )
                for row in frame.itertuples(index=False)
            ]
        return list(self._known[as_of_day])


def stored_sources(connection, customer: Customer | None = None) -> Sources:
    """The four sources, answering from the tables."""
    customer = customer or demo()
    return Sources(
        StoredBookings(connection, customer),
        StoredRateShops(connection, customer),
        StoredSchedules(connection),
        StoredEvents(connection),
    )


# ---- writing a day ------------------------------------------------------------


def write_snapshot(connection, day: int, feed: Sources, customer: Customer | None = None) -> None:
    """One day of the four feeds, copied from any sources into the feed tables. The
    day's rows are deleted first, so writing a day twice leaves the tables as they
    were. Day -1 (OPENING_DAY) writes the position before the first day."""
    hotels = (customer or demo()).hotels
    if day == OPENING_DAY:
        opening = feed.bookings.history(0).opening
        bookings = [
            (day, h.key, s, int(opening[h.row, s]), int(opening[h.row, s]), float(h.start_rate))
            for h in hotels
            for s in stay_window(0)
        ]
    else:
        on_books = feed.bookings.on_books(day)
        rates = feed.bookings.rates(day)
        taken = feed.bookings.history(day + 1).taken[day]
        bookings = [
            (day, h.key, s, int(taken[h.row, s]), int(on_books[h.row, s]), float(rates[h.row, s]))
            for h in hotels
            for s in stay_window(day)
        ]
    shops = [
        (day, h.key, s, competitor, float(rate))
        for h in hotels
        for s in range(max(day, 0), HORIZON_DAYS)
        for competitor, rate in feed.shops.competitor_rates(day, h, s).items()
    ]
    seats = feed.schedules.seats(day)
    snapshot = [(day, s, int(seats[s])) for s in range(HORIZON_DAYS)]
    events = [
        (
            day,
            e.name,
            e.known_day,
            e.start_day,
            e.end_day,
            ",".join(e.hotels),
            e.uplift,
            e.comp_rate_raise,
        )
        for e in feed.events.known(day)
    ]
    with _transaction(connection):
        _replace_day(connection, "daily_bookings", day, bookings)
        _replace_day(connection, "rate_shops", day, shops)
        _replace_day(connection, "schedule_snapshots", day, snapshot)
        _replace_day(connection, "events", day, events)


def write_decisions(connection, day: int, entries: list[Entry], advice: Iterable) -> None:
    """The day's flags, plans and decisions, replacing any stored for the day."""
    flags = [(day, e.hotel, e.first_stay, e.last_stay, ",".join(e.causes)) for e in entries]
    decisions = [
        _decision_row(day, position, record.to_json())
        for position, record in enumerate([*entries, *advice])
    ]
    with _transaction(connection):
        _replace_day(connection, "flags", day, flags)
        _replace_day(connection, "plans", day, plan_rows(entries))
        _replace_day(connection, "decisions", day, decisions)


def plan_rows(entries: list[Entry]) -> list[tuple]:
    """One plans row per entry, day of the week and candidate, with the exact numbers."""
    rows = []
    for entry in entries:
        for group in entry.weekdays:
            for candidate in group.candidates:
                low, high = candidate.band if candidate.band is not None else (None, None)
                rows.append(
                    (
                        entry.day,
                        entry.hotel,
                        entry.first_stay,
                        entry.last_stay,
                        group.weekday,
                        candidate.name,
                        json.dumps({str(s): r for s, r in sorted(candidate.rates.items())}),
                        float(candidate.estimate),
                        float(candidate.estimate - group.hold.estimate),
                        low,
                        high,
                        candidate is group.best,
                    )
                )
    return rows


def _decision_row(day: int, position: int, line: dict) -> tuple:
    """A decisions row from a decisions.jsonl line, for an entry or an advice."""
    pricing = line.get("elasticity") or {}
    return (
        day,
        position,
        line["hotel"],
        line["stays"][0],
        line["stays"][1],
        ",".join(line["causes"]),
        line.get("plan"),
        line["value_at_stake"],
        bool(line.get("queued", False)),
        line["action"],
        line["reason"],
        line.get("reason_source", "code"),
        pricing.get("elasticity"),
        pricing.get("mode"),
        json.dumps(line["new_rates"]) if line.get("new_rates") else None,
        bool(line["simulated"]),
        line.get("event"),
        json.dumps(line),
    )


@contextmanager
def _transaction(connection) -> Iterator[None]:
    connection.begin()
    try:
        yield
    except BaseException:
        connection.rollback()
        raise
    connection.commit()


def _replace_day(connection, table: str, day: int, rows: list[tuple]) -> None:
    """Delete the day's rows of a table and insert these instead."""
    connection.execute(f"DELETE FROM {table} WHERE as_of_day = ?", [day])
    if not rows:
        return
    columns = _COLUMNS[table]
    frame = pd.DataFrame(rows, columns=columns)
    for column in columns:
        # Text goes over as plain objects, which every DuckDB release reads; NULL stays
        # None rather than becoming NaN.
        if pd.api.types.is_string_dtype(frame[column]) or column in _NULLABLE.get(table, ()):
            frame[column] = frame[column].astype(object).where(frame[column].notna(), None)
    connection.register("_rows", frame)
    names = ", ".join(columns)
    connection.execute(f"INSERT INTO {table} ({names}) SELECT {names} FROM _rows")
    connection.unregister("_rows")


# ---- reading a run back ---------------------------------------------------------


def stored_days(connection) -> list[int]:
    """The days whose feeds are in the tables, in order; the opening day is left out."""
    frame = _frame(
        connection,
        "SELECT DISTINCT as_of_day FROM daily_bookings WHERE as_of_day >= 0 ORDER BY as_of_day",
    )
    return [int(day) for day in frame["as_of_day"]]


def state_before(connection, day: int) -> tuple[dict[tuple[str, int], int], set[tuple[str, str]]]:
    """What the decisions before a day leave an agent. That is the stay dates under the hold, by the
    day of their last accepted change. It also holds the (hotel, event) pairs already advised."""
    frame = _frame(
        connection,
        "SELECT as_of_day, hotel, new_rates, simulated, event FROM decisions "
        "WHERE as_of_day < ? ORDER BY as_of_day, position",
        [day],
    )
    held: dict[tuple[str, int], int] = {}
    advised: set[tuple[str, str]] = set()
    for row in frame.itertuples(index=False):
        if not row.simulated:
            advised.add((row.hotel, row.event))
        elif isinstance(row.new_rates, str):  # NULL comes back as NaN, not None
            for stay_day in json.loads(row.new_rates):
                held[(row.hotel, int(stay_day))] = int(row.as_of_day)
    return held, advised


def rate_changes_before(connection, day: int) -> dict[int, dict[tuple[str, int], float]]:
    """The accepted rate changes of the days before a day, by day then (hotel key, stay day). The
    rates are the exact rates the plans table keeps."""
    frame = _frame(
        connection,
        "SELECT p.as_of_day, p.hotel, p.rates FROM plans p JOIN decisions d "
        "ON d.as_of_day = p.as_of_day AND d.hotel = p.hotel "
        "AND d.first_stay = p.first_stay AND d.last_stay = p.last_stay "
        "WHERE p.as_of_day < ? AND p.is_best AND p.candidate <> ? "
        "AND d.simulated AND d.action <> ? "
        "ORDER BY p.as_of_day, p.hotel, p.first_stay, p.weekday",
        [day, HOLD, HOLD],
    )
    changes: dict[int, dict[tuple[str, int], float]] = {}
    for row in frame.itertuples(index=False):
        for stay_day, rate in json.loads(row.rates).items():
            changes.setdefault(int(row.as_of_day), {})[(row.hotel, int(stay_day))] = rate
    return changes


def decided_on(connection, day: int) -> dict[tuple[str, int, int], tuple[str, str, str]]:
    """The action, reason and reason source recorded for each entry of a day, by
    (hotel key, first stay, last stay)."""
    frame = _frame(
        connection,
        "SELECT hotel, first_stay, last_stay, action, reason, reason_source FROM decisions "
        "WHERE as_of_day = ? AND simulated",
        [day],
    )
    return {
        (row.hotel, int(row.first_stay), int(row.last_stay)): (
            row.action,
            row.reason,
            row.reason_source,
        )
        for row in frame.itertuples(index=False)
    }


def records_on(connection, day: int) -> list[dict]:
    """The day's decisions.jsonl lines, in order."""
    frame = _frame(
        connection,
        "SELECT record FROM decisions WHERE as_of_day = ? ORDER BY position",
        [day],
    )
    return [json.loads(record) for record in frame["record"]]


def decisions_file(connection) -> str:
    """The whole decisions.jsonl, as the run command would have written it."""
    frame = _frame(connection, "SELECT record FROM decisions ORDER BY as_of_day, position")
    return "".join(record + "\n" for record in frame["record"])


def plan_differences(connection, day: int, entries: list[Entry]) -> list[str]:
    """How the plans rebuilt for a day differ from the stored ones; empty when they match."""
    columns = ", ".join(_COLUMNS["plans"][1:])
    stored = {
        tuple(row)
        for row in connection.execute(
            f"SELECT {columns} FROM plans WHERE as_of_day = ?", [day]
        ).fetchall()
    }
    rebuilt = {row[1:] for row in plan_rows(entries)}
    found = [f"stored but not rebuilt: {row}" for row in sorted(stored - rebuilt, key=str)]
    found += [f"rebuilt but not stored: {row}" for row in sorted(rebuilt - stored, key=str)]
    return found
