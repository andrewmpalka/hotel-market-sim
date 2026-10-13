"""demo_data.py

The demo page's data. One command writes one DuckDB file with everything the page shows.

    hotel-market demo-data --seed 7              # writes demo.duckdb
    hotel-market demo-data --seed 7 --out FILE

The file holds the seven stored tables for days 0 to 59 (stored.py). The daily path writes them
with the recorded live run as the cache (tests/fixtures/live_seed7). The page therefore shows the
model's reasons, and it needs no API key. A request the recording does not cover stops the
command. For a seed with no recording, the template writes the reasons.

The file adds the tables the page reads as they are (sql/demo.sql): hotels, days, news,
stay_dates, queue, scorecard, outcome and gains. Code computes every figure in them and writes
every date as a calendar date with its day of the week and the day number in brackets. The page
(demo_page.py) formats and draws them and computes nothing. The scorecard holds the nights
already stayed as of the day, stay dates 0 to the day before. The outcome holds the result once
every stay date is complete, every booking through day 149. The gains are that result's
contribution difference by stay date. Each is given per hotel and for all the hotels together.
"""

from __future__ import annotations

import argparse
import itertools
import math
import shutil
import tempfile
from collections.abc import Iterable, Sequence
from datetime import timedelta
from pathlib import Path

from hotel_market import stored
from hotel_market.agent import Agent
from hotel_market.bookings import Books, simulate
from hotel_market.customer import Customer, demo
from hotel_market.detect import detect_numbers
from hotel_market.plan import DAY_NAMES, HOLD, PLAN_ORDER, Entry, WeekdayGroup
from hotel_market.schedule import SIM_START
from hotel_market.simulated import simulated_sources
from hotel_market.sources import Sources
from hotel_market.text import (
    dollars,
    percent_change,
    percent_change_range,
    versus_holding,
    versus_holding_at_end,
)
from hotel_market.world import HORIZON_DAYS, SIM_DAYS, Hotel, stay_window, weekday

DEMO_FILE = Path("demo.duckdb")  # where the command writes by default
DEMO_SCHEMA_FILE = Path("sql") / "demo.sql"  # the page's tables; relative to the root
RECORDED_RUNS = Path("tests") / "fixtures"  # live_seed7 holds the recorded run of seed 7
DEMO_TABLES = (
    "hotels", "days", "news", "stay_dates", "queue", "scorecard", "outcome", "gains"
)  # fmt: skip
NOTHING_NEW = "Nothing new became known today."
ALL = "all"  # the scorecard's key for the hotels together
MEASURES = ("Occupancy", "ADR", "RevPAR", "Room revenue", "Contribution")  # the tiles, in order
RATE_AXIS = (0.75, 1.25)  # the rate chart's y axis, as shares of the hotel's start rate
GAIN_TICK_DAYS = 28  # the small line labels every fourth Monday
NUMBER_WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")


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
    """Write the demo file for the seed: the stored tables for days 0 to 59 and the page's
    tables. Both runs book on to day 149, so the outcome is complete. Returns whether the reasons
    came from a recorded live run."""
    from hotel_market.cli import run_days  # here, because cli imports this module

    customer = customer or demo()
    for leftover in (out, out.with_name(out.name + ".wal")):
        if leftover.exists():
            leftover.unlink()
    recording = recorded_run(seed)
    rows: dict[str, list[tuple]] = {table: [] for table in DEMO_TABLES}
    rows["hotels"] = [
        (
            h.row,
            h.key,
            h.name,
            h.rooms,
            h.start_rate,
            *[share * h.start_rate for share in RATE_AXIS],
        )
        for h in customer.hotels
    ]
    rows["days"] = [
        (day, day_label(day), stay_span(*_ends(stay_window(day)))) for day in range(SIM_DAYS)
    ]
    figures: dict[tuple[int, str, str], tuple[float, ...]] = {}  # (day, scope, run) -> the five
    final: dict[str, Books] = {}

    def observe(day: int, books: Books, agent: Agent) -> None:
        feed = simulated_sources(books)
        table = detect_numbers(day, feed, customer)
        entries = [entry for entry in agent.entries if entry.day == day]
        for hotel in customer.hotels:
            own = [entry for entry in entries if entry.hotel == hotel.key]
            rows["news"] += _news_rows(day, hotel, feed, table, customer)
            rows["stay_dates"] += _stay_rows(day, hotel, table, own)
            rows["queue"] += _queue_rows(day, hotel, own, customer.min_value_at_stake)
        figures.update(_stayed(day, "agent", books, customer))
        final["agent"] = books

    def record_fixed(day: int, books: Books) -> dict[tuple[str, int], float]:
        figures.update(_stayed(day, "fixed", books, customer))
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
            HORIZON_DAYS - 1,
            out,
            cache_dir=cache_dir,
            client=Recorded() if recording is not None else None,
            customer=customer,
            observe=observe,
        )
    final["fixed"] = simulate(seed, record_fixed, customer=customer)
    rows["scorecard"] = _scorecard_rows(figures, customer)
    rows["outcome"] = _outcome_rows(final["agent"], final["fixed"], customer)
    rows["gains"] = _gain_rows(final["agent"], final["fixed"], customer)
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


# ---- dates in words --------------------------------------------------------------------------


def stay_label(stay_day: int) -> str:
    """A stay date as the page shows it: "Thu 18 Feb [45]"."""
    date = SIM_START + timedelta(days=stay_day)
    return f"{date:%a} {date.day} {date:%b} [{stay_day}]"


def stay_span(first_stay: int, last_stay: int) -> str:
    """One stay date, or a run of them: "Thu 18 Feb [45] to Sun 21 Feb [48]"."""
    if first_stay == last_stay:
        return stay_label(first_stay)
    return f"{stay_label(first_stay)} to {stay_label(last_stay)}"


def day_label(day: int) -> str:
    """A simulation day as the title shows it: "Thu 14 Jan 2027 [day 10]"."""
    date = SIM_START + timedelta(days=day)
    return f"{date:%a} {date.day} {date:%b} {date.year} [day {day}]"


def _ends(stays: Sequence[int]) -> tuple[int, int]:
    return stays[0], stays[-1]


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
                    f"{stay_span(event.start_day, event.end_day)}. Demand there is "
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
                f"{stay_span(first, last)}.",
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
                f"{stay_span(first, last)}.",
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
    """The charts' rows: the hotel's rate, the comp median, the rooms on the books and the
    rooms the pace curve expects, per stay date in the window, with the flag that covers it and
    the rate an accepted plan sets. A plan's held days of the week keep the current rate."""
    own = table[table["hotel"] == hotel.key]
    rows = []
    for record in own.to_dict("records"):
        stay = record["stay_day"]
        flag = next((e for e in entries if e.first_stay <= stay <= e.last_stay), None)
        planned = None
        if flag is not None and flag.action != HOLD:
            planned = flag.new_rates.get(stay, float(record["rate"]))
        rows.append(
            (
                day,
                hotel.key,
                stay,
                stay_label(stay),
                weekday(stay) == 0,
                float(record["rate"]),
                float(record["comp_median"]),
                int(record["rooms"]),
                float(record["rooms"] - record["pace_gap"]),
                flag is not None,
                ", ".join(flag.causes) if flag is not None else "",
                flag.id if flag is not None else "",
                planned,
            )
        )
    return rows


def _queue_rows(day: int, hotel: Hotel, entries: Sequence[Entry], minimum: float) -> list[tuple]:
    """The day's flags for the hotel: each plan, its value, its reason and what became of it. A
    held flag also carries the best alternative to holding and how far it fell short."""
    rows = []
    for position, entry in enumerate(entries):
        if not entry.queued:
            outcome = "held"
        else:
            outcome = "declined" if entry.action == HOLD else "accepted"
        alternative, short = _alternative(entry, minimum) if outcome == "held" else ("", "")
        rows.append(
            (
                day,
                hotel.key,
                position,
                stay_span(entry.first_stay, entry.last_stay),
                ", ".join(entry.causes),
                entry.plan or HOLD,
                float(entry.value_at_stake),
                versus_holding(entry.value_at_stake),
                entry.reason,
                entry.reason_source,
                bool(entry.queued),
                outcome,
                alternative,
                short,
            )
        )
    return rows


def _alternative(entry: Entry, minimum: float) -> tuple[str, str]:
    """The best alternative to holding a flag, and how it compares. A flag held under the minimum
    has a plan that beats holding; the text says by how much, to the dollar, and how far it falls
    short of the minimum. A flag where no change beats holding gets the best change on each day of
    the week, and the text says how far that falls short of holding."""
    if entry.plan:
        gain = entry.value_at_stake
        short = f"{dollars(math.ceil(minimum - gain))} short of the {dollars(minimum)} minimum"
        return entry.plan, f"{dollars(math.floor(gain))} more than holding, {short}"
    best = {group.weekday: _best_change(group) for group in entry.weekdays}
    behind = sum(best[g.weekday].estimate - g.hold.estimate for g in entry.weekdays)
    return changes_text(best), versus_holding_at_end(behind)


def _best_change(group: WeekdayGroup):
    """The candidate with the highest estimate among the changes, hold left out."""
    return max(group.candidates[1:], key=lambda candidate: candidate.estimate)


def changes_text(by_weekday: dict) -> str:
    """Changes in words, in the plan's order: "raise 5% on Wed, Fri; lower 5% on Thu"."""
    parts = []
    for action in PLAN_ORDER:
        days = [
            DAY_NAMES[wd]
            for wd, candidate in sorted(by_weekday.items())
            if candidate.name == action
        ]
        if days:
            parts.append(f"{action} on {', '.join(days)}")
    return "; ".join(parts)


# ---- the scorecard: the nights stayed, the complete outcome and the gains by stay date -----


def _stayed(day: int, run: str, books: Books, customer: Customer) -> dict:
    """The run's figures over the nights already stayed as of the day, stay dates 0 to the day
    before, per hotel and for all together. Nothing on day 0."""
    stays = range(day)
    if not stays:
        return {}
    found = {(day, h.key, run): figures(books, [h], stays) for h in customer.hotels}
    found[(day, ALL, run)] = figures(books, customer.hotels, stays)
    return found


def figures(books: Books, hotels: Sequence[Hotel], stays: Sequence[int]) -> tuple[float, ...]:
    """Occupancy, ADR, RevPAR, room revenue and contribution over the hotels and stay dates
    together. For one hotel they are the Books measures; for several, the sums are taken first."""
    stays = list(stays)
    sold = sum(int(books.rooms[h.row, stays].sum()) for h in hotels)
    available = sum(h.rooms * len(stays) for h in hotels)
    revenue = sum(books.room_revenue(h, stays) for h in hotels)
    contribution = sum(books.contribution(h, stays) for h in hotels)
    adr = revenue / sold if sold else math.nan
    return (sold / available, adr, revenue / available, revenue, contribution)


def _scorecard_rows(found: dict, customer: Customer) -> list[tuple]:
    """One row per day, scope and measure, for the days with a night stayed."""
    rows = []
    for (day, scope, run), agent in found.items():
        if run != "agent":
            continue
        fixed = found[(day, scope, "fixed")]
        nights = stay_span(0, day - 1)
        rows += [
            (day, scope, _title(scope, customer), nights, *tile) for tile in tiles(agent, fixed)
        ]
    return rows


def _outcome_rows(agent: Books, fixed: Books, customer: Customer) -> list[tuple]:
    """The result once every stay date is complete, per hotel and for all together."""
    stays = range(HORIZON_DAYS)
    scopes = [(h.key, [h]) for h in customer.hotels] + [(ALL, list(customer.hotels))]
    return [
        (scope, _title(scope, customer), stay_span(0, HORIZON_DAYS - 1), *tile)
        for scope, hotels in scopes
        for tile in tiles(figures(agent, hotels, stays), figures(fixed, hotels, stays))
    ]


def _gain_rows(agent: Books, fixed: Books, customer: Customer) -> list[tuple]:
    """The contribution difference on each stay date, per hotel and for all together."""
    scopes = [(h.key, [h]) for h in customer.hotels] + [(ALL, list(customer.hotels))]
    rows = []
    for scope, hotels in scopes:
        for stay in range(HORIZON_DAYS):
            earned = sum(agent.contribution(h, [stay]) for h in hotels)
            held = sum(fixed.contribution(h, [stay]) for h in hotels)
            tick = stay % GAIN_TICK_DAYS == 0
            rows.append(
                (
                    scope,
                    _title(scope, customer),
                    stay,
                    stay_label(stay),
                    tick,
                    earned,
                    held,
                    earned - held,
                )
            )
    return rows


def _title(scope: str, customer: Customer) -> str:
    """The hotel's name, or "All four hotels"."""
    if scope != ALL:
        return customer.hotel(scope).name
    count = len(customer.hotels)
    word = NUMBER_WORDS[count] if count < len(NUMBER_WORDS) else str(count)
    return f"All {word} hotels"


def tiles(agent: Sequence[float], fixed: Sequence[float]) -> list[tuple]:
    """The five tiles: position, measure, the agent's figure, the fixed run's, their difference,
    and the two texts the tile shows."""
    return [
        (position, measure, a, f, a - f, value_text(position, a), delta_text(position, a - f))
        for position, (measure, a, f) in enumerate(zip(MEASURES, agent, fixed))
    ]


def value_text(position: int, value: float) -> str:
    """A figure as its tile shows it: occupancy to a tenth of a percent, ADR and RevPAR to the
    cent, revenue and contribution to the dollar."""
    if math.isnan(value):
        return "n/a"
    if position == 0:
        return f"{value:.1%}"
    if position in (1, 2):
        return f"${value:,.2f}"
    return f"${value:,.0f}"


def delta_text(position: int, delta: float) -> str:
    """A change as its tile shows it, at the tile's precision. Occupancy moves in points. A change
    that rounds to nothing is "0", which the tile shows with no arrow."""
    if math.isnan(delta):
        return "0"
    if position == 0:
        points = round(100 * delta, 1)
        return "0" if points == 0 else f"{points:+.1f} pts"
    if position in (1, 2):
        cents = round(delta, 2)
        return "0" if cents == 0 else f"{'-' if cents < 0 else '+'}${abs(cents):,.2f}"
    units = round(delta)
    return "0" if units == 0 else f"{'-' if units < 0 else '+'}${abs(units):,}"


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
