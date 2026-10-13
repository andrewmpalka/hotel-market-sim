"""demo_data.py

The demo page's data. One command writes one DuckDB file with everything the page shows.

    hotel-market demo-data --seed 7              # writes demo.duckdb
    hotel-market demo-data --seed 7 --out FILE

The file holds the seven stored tables for days 0 to 59 (stored.py). The daily path writes them
with the recorded live run as the cache (tests/fixtures/live_seed7). The page therefore shows the
model's reasons, and it needs no API key. A request the recording does not cover stops the
command. For a seed with no recording, the template writes the reasons.

The file adds five tables the page reads as they are (sql/demo.sql): hotels, news, stay_dates,
queue and scorecard. Code computes every figure in them. The page (demo_page.py) formats and
draws them and computes nothing. The scorecard is to date: every booking made through the day,
over stay dates 0 to 149, for the agent run and the fixed-rate run, and their difference.
"""

from __future__ import annotations

import argparse
import itertools
import shutil
import tempfile
from collections.abc import Iterable, Sequence
from pathlib import Path

from hotel_market import stored
from hotel_market.agent import Agent
from hotel_market.bookings import Books, simulate
from hotel_market.customer import Customer, demo
from hotel_market.detect import detect_numbers
from hotel_market.plan import HOLD, Entry
from hotel_market.simulated import simulated_sources
from hotel_market.sources import Sources
from hotel_market.text import (
    percent_change,
    percent_change_range,
    stay_range,
    versus_holding,
)
from hotel_market.world import HORIZON_DAYS, SIM_DAYS, Hotel

DEMO_FILE = Path("demo.duckdb")  # where the command writes by default
DEMO_SCHEMA_FILE = Path("sql") / "demo.sql"  # the page's five tables; relative to the root
RECORDED_RUNS = Path("tests") / "fixtures"  # live_seed7 holds the recorded run of seed 7
DEMO_TABLES = ("hotels", "news", "stay_dates", "queue", "scorecard")
NOTHING_NEW = "Nothing new became known today."


class Recorded:
    """A client that never answers: every request must be in the recorded run's cache."""

    def complete(self, system: str, prompt: str, schema: dict) -> str:
        raise LookupError(
            "the recorded run does not cover this request; record a live run of the seed again"
        )


def recorded_run(seed: int) -> Path | None:
    """The recorded live run of the seed, under tests/fixtures, or None when there is none. The
    folder is looked up under the working directory, then the repository root."""
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        folder = base / RECORDED_RUNS / f"live_seed{seed}"
        if folder.is_dir():
            return folder
    return None


def build(seed: int, out: Path = DEMO_FILE, customer: Customer | None = None) -> bool:
    """Write the demo file for the seed: the stored tables for days 0 to 59 and the page's five
    tables. Returns whether the reasons came from a recorded live run."""
    from hotel_market.cli import run_days  # here, because cli imports this module

    customer = customer or demo()
    for leftover in (out, out.with_name(out.name + ".wal")):
        if leftover.exists():
            leftover.unlink()
    recording = recorded_run(seed)
    rows: dict[str, list[tuple]] = {table: [] for table in DEMO_TABLES}
    rows["hotels"] = [(h.row, h.key, h.name, h.rooms) for h in customer.hotels]

    def observe(day: int, books: Books, agent: Agent) -> None:
        feed = simulated_sources(books)
        table = detect_numbers(day, feed, customer)
        entries = [entry for entry in agent.entries if entry.day == day]
        for hotel in customer.hotels:
            own = [entry for entry in entries if entry.hotel == hotel.key]
            rows["news"] += _news_rows(day, hotel, feed, table, customer)
            rows["stay_dates"] += _stay_rows(day, hotel, table, own)
            rows["queue"] += _queue_rows(day, hotel, own)
            rows["scorecard"].append(_scorecard_row(day, hotel, "agent", books))

    def record_fixed(day: int, books: Books) -> dict[tuple[str, int], float]:
        for hotel in customer.hotels:
            rows["scorecard"].append(_scorecard_row(day, hotel, "fixed", books))
        return {}

    with tempfile.TemporaryDirectory() as folder:
        cache_dir = Path(folder) / "cache"
        if recording is not None:
            shutil.copytree(
                recording, cache_dir / f"seed{seed}", ignore=shutil.ignore_patterns("*.jsonl")
            )
        run_days(
            seed,
            0,
            SIM_DAYS - 1,
            out,
            cache_dir=cache_dir,
            client=Recorded() if recording is not None else None,
            customer=customer,
            observe=observe,
        )
    simulate(seed, record_fixed, last_day=SIM_DAYS - 1, customer=customer)
    rows["scorecard"] += _delta_rows(rows["scorecard"])
    connection = stored.connect(out)
    try:
        for statement in stored._statements(demo_schema_path().read_text()):
            connection.execute(statement)
        for table in DEMO_TABLES:
            width = len(rows[table][0])
            connection.executemany(
                f"INSERT INTO {table} VALUES ({', '.join('?' * width)})", rows[table]
            )
    finally:
        connection.close()
    return recording is not None


def demo_schema_path() -> Path:
    """Where sql/demo.sql is: under the working directory, else the repository root."""
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        if (base / DEMO_SCHEMA_FILE).exists():
            return base / DEMO_SCHEMA_FILE
    raise FileNotFoundError(f"{DEMO_SCHEMA_FILE} not found; run from the repository root")


# ---- the page's rows, one function per table ----------------------------------------------


def _news_rows(day: int, hotel: Hotel, feed: Sources, table, customer: Customer) -> list[tuple]:
    """What became known today for the hotel, in plain words: each event announced today that
    covers it, each schedule filing's stay dates, and each comp set move beyond the threshold."""
    texts: list[tuple[str, str]] = []
    for event in feed.events.known(day):
        if event.known_day == day and hotel.key in event.hotels:
            texts.append(
                (
                    "event",
                    f"An event, the {event.name.lower()}, was announced for "
                    f"{stay_range(event.start_day, event.end_day)}. Demand there is "
                    f"{percent_change(event.uplift)}, and the comp set's rates are "
                    f"{percent_change(event.comp_rate_raise)}.",
                )
            )
    revision = feed.schedules.seat_revision(day)
    for first, last in _runs(s for s in range(HORIZON_DAYS) if revision[s] != 0):
        texts.append(
            (
                "schedule",
                f"The airlines filed a schedule change: arriving seats are "
                f"{percent_change_range(revision[s] for s in range(first, last + 1))} for "
                f"{stay_range(first, last)}.",
            )
        )
    own = table[table["hotel"] == hotel.key]
    moved = own[own["median_change"].abs() >= customer.median_threshold]
    changes = dict(zip(moved["stay_day"].tolist(), moved["median_change"].tolist()))
    for first, last in _runs(changes):
        texts.append(
            (
                "comp set",
                f"The comp set median is "
                f"{percent_change_range(changes[s] for s in range(first, last + 1))} for "
                f"{stay_range(first, last)}.",
            )
        )
    if not texts:
        texts.append(("none", NOTHING_NEW))
    return [(day, hotel.key, position, kind, text) for position, (kind, text) in enumerate(texts)]


def _runs(stays: Iterable[int]) -> list[tuple[int, int]]:
    """Consecutive stay dates as (first, last) pairs."""
    ordered = sorted(stays)
    groups = itertools.groupby(enumerate(ordered), key=lambda pair: pair[1] - pair[0])
    return [(run[0][1], run[-1][1]) for _, group in groups for run in [list(group)]]


def _stay_rows(day: int, hotel: Hotel, table, entries: Sequence[Entry]) -> list[tuple]:
    """The chart's rows: the hotel's rate, the comp median, the rooms on the books and the
    rooms the pace curve expects, per stay date in the window, with the flag that covers it."""
    own = table[table["hotel"] == hotel.key]
    rows = []
    for record in own.to_dict("records"):
        stay = record["stay_day"]
        flag = next((e for e in entries if e.first_stay <= stay <= e.last_stay), None)
        rows.append(
            (
                day,
                hotel.key,
                stay,
                float(record["rate"]),
                float(record["comp_median"]),
                int(record["rooms"]),
                float(record["rooms"] - record["pace_gap"]),
                flag is not None,
                ", ".join(flag.causes) if flag is not None else "",
            )
        )
    return rows


def _queue_rows(day: int, hotel: Hotel, entries: Sequence[Entry]) -> list[tuple]:
    """The day's flags for the hotel: each plan, its value, its reason and what became of it."""
    rows = []
    for position, entry in enumerate(entries):
        if not entry.queued:
            outcome = "held"
        else:
            outcome = "declined" if entry.action == HOLD else "accepted"
        rows.append(
            (
                day,
                hotel.key,
                position,
                stay_range(entry.first_stay, entry.last_stay),
                ", ".join(entry.causes),
                entry.plan or HOLD,
                float(entry.value_at_stake),
                versus_holding(entry.value_at_stake),
                entry.reason,
                entry.reason_source,
                bool(entry.queued),
                outcome,
            )
        )
    return rows


def _scorecard_row(day: int, hotel: Hotel, run: str, books: Books) -> tuple:
    """The run's figures to date: every booking made through the day, stay dates 0 to 149."""
    stays = range(HORIZON_DAYS)
    return (
        day,
        hotel.key,
        run,
        books.occupancy(hotel, stays),
        books.average_rate(hotel, stays),
        books.revpar(hotel, stays),
        books.room_revenue(hotel, stays),
        books.contribution(hotel, stays),
    )


def _delta_rows(scorecard: list[tuple]) -> list[tuple]:
    """The agent run minus the fixed-rate run, figure by figure, per hotel and day."""
    by_key = {(day, hotel, run): figures for day, hotel, run, *figures in scorecard}
    return [
        (day, hotel, "delta", *[a - f for a, f in zip(figures, by_key[(day, hotel, "fixed")])])
        for (day, hotel, run), figures in by_key.items()
        if run == "agent"
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="hotel-market demo-data",
        description="Write the demo page's DuckDB file: the stored tables for days 0 to 59 and "
        "the page's tables, with the reasons from the recorded live run.",
    )
    parser.add_argument(
        "--seed", type=int, default=7, help="the seed (default 7, the recorded one)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEMO_FILE,
        metavar="FILE",
        help=f"the file (default {DEMO_FILE})",
    )
    args = parser.parse_args(argv)
    recorded = build(args.seed, args.out)
    source = "the recorded live run" if recorded else "the template, as no run is recorded"
    print(f"Wrote {args.out}: days 0 to {SIM_DAYS - 1} of seed {args.seed}, reasons from {source}.")


if __name__ == "__main__":
    main()
