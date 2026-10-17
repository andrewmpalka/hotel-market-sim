"""demo_data.py

The demo page's data. One command writes one DuckDB file with everything the page shows.

    hotel-market demo-data --seed 7              # writes demo.duckdb
    hotel-market demo-data --seed 7 --out FILE --customer customers/demo.toml
    hotel-market demo-data --seed 7 --ticks 4 --out demo4.duckdb
    hotel-market demo-data --seed 7 --customer customers/demo-intraday.toml --ticks 4 \
        --out demo-intraday.duckdb

The file holds the eight stored tables for days 0 to 59 (stored.py). It writes them with a
client that answers from the recorded live run wherever the recording holds the same request, so
the page shows the model's reasons, and it needs no API key. On the daily clock the recording is
tests/fixtures/live_seed7, the demo market's run. A file at several ticks a day reads
tests/fixtures/live_seed7_intraday, the demo-intraday market's run at four, whose records name
their tick. A request the recording does not cover, because the market, the clock or the world
changed, gets the template's answer, and the command prints one warning line naming the day and
the hotel. For a seed with no recording, the template writes every reason.

The file adds the tables the page reads as they are (sql/demo.sql): hotels, days, news,
stay_dates, queue, scorecard, outcome and gains, and a run table with the seed and the words for
where the reasons came from, which the sidebar shows. A queued plan's row also carries the
earlier changes on its stay dates as the stored request lists them, the read-back the page shows
under "Since the last change". Code computes every figure in them and writes
every date as a calendar date with its day of the week and the day number in brackets. The page
(demo_page.py) formats and draws them and computes nothing. The scorecard holds the nights
already stayed as of the day, stay dates 0 to the day before. The outcome holds the result once
every stay date is complete, every booking through day 149. The gains are that result's
contribution difference by stay date. Each is given per hotel and for all the hotels together.

With --ticks N the run is the finer clock's (world.py): each news line names the tick its feed
landed at, the queue holds each tick's flags under that tick, the chart rows are written per
tick as of it, a planned rate names the tick it was decided at, and on a day a filing or an
event lands the news adds, at the day's last tick, the first flag, the first accepted raise on
its stay dates and what they earned against the fixed-rate run. The run table carries the ticks
a day was cut into, so the page can offer a tick. At one tick a day the file reads as before,
every row at tick 1. The recorded run is at one tick a day, so on a finer clock the template
writes every reason.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import tempfile
from collections.abc import Iterable, Sequence
from datetime import timedelta
from pathlib import Path

from hotel_market import stored
from hotel_market.agent import Agent
from hotel_market.bookings import Books, simulate
from hotel_market.customer import Customer, demo, load
from hotel_market.detect import NEW_EVENT, SEATS_UP, detect_numbers, moment_index
from hotel_market.model import request_digest, template_decisions
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
RECORDED_RUNS = Path("tests") / "fixtures"  # live_seed7 and live_seed7_intraday: seed 7's runs
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
    """A client that answers from a recorded live run and falls back to the template. It is
    uncached, so it looks each request up itself: a record of the day and hotel, at any tick,
    that holds the same request gives the model's decisions under the name model. Otherwise the
    template's decisions answer under the name template, and one warning line names the day and
    the hotel.
    ask() reads the name after each answer, so each decision records its own source."""

    cached = False

    def __init__(self, recording: Path, customer: Customer):
        self.recording = recording
        self.keys = {hotel.name: hotel.key for hotel in customer.hotels}
        self.name = "model"
        self.fallbacks = 0  # the requests the recording did not cover

    def complete(self, system: str, prompt: str, schema: dict) -> str:
        request = json.loads(prompt)
        day, hotel = request["day"], request["hotel"]["name"]
        digest = request_digest(request)
        for path in sorted(self.recording.glob(f"day{day:03d}*_{self.keys[hotel]}.json")):
            record = json.loads(path.read_text())
            if record["request_digest"] == digest:
                self.name = "model"
                return json.dumps({"decisions": record["decisions"]})
        self.name = "template"
        self.fallbacks += 1
        print(
            f"Warning: the recorded run does not cover day {day} at {hotel}, so the template "
            f"answered."
        )
        return json.dumps({"decisions": template_decisions(request)})


def recorded_run(seed: int, ticks: int = 1) -> Path | None:
    """The recorded live run of the seed at the clock, under tests/fixtures, or None when there
    is none: live_seed7 on the daily clock, live_seed7_intraday on a finer one, where a record's
    name carries its tick, as the agent's cache names it. The folder is looked up under the
    working directory, then the repository root."""
    name = f"live_seed{seed}" + ("_intraday" if ticks > 1 else "")
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        folder = base / RECORDED_RUNS / name
        if folder.is_dir():
            return folder
    return None


def build(
    seed: int, out: Path = DEMO_FILE, customer: Customer | None = None, ticks: int = 1
) -> str:
    """Write the demo file for the seed: the stored tables for days 0 to 59 and the page's
    tables, on the daily clock or on `ticks` a day. Both runs book on to day 149, so the outcome
    is complete. Returns the words for where the reasons came from, as the file's run table and
    the sidebar say them."""
    from hotel_market.cli import run_days  # here, because cli imports this module

    customer = customer or demo()
    for leftover in (out, out.with_name(out.name + ".wal")):
        if leftover.exists():
            leftover.unlink()
    recording = recorded_run(seed, ticks)
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
    # (day, hotel) -> the news so far, each with the tick it landed at
    texts: dict[tuple[int, str], list[tuple[int, str, str]]] = {}
    entries_of: dict[tuple[int, str], list[Entry]] = {}  # (day, hotel) -> the day's entries so far

    def observe(day: int, books: Books, agent: Agent, tick: int = 1) -> None:
        """After each moment: the news its feeds brought, its queue and the chart rows as of it;
        at the day's last tick the scorecard."""
        feed = simulated_sources(books, day, tick if ticks > 1 else None)
        table = detect_numbers(day, feed, customer, tick=tick if ticks > 1 else None)
        for hotel in customer.hotels:
            own = [e for e in agent.entries if e.day == day and e.hotel == hotel.key]
            entries_of.setdefault((day, hotel.key), []).extend(own)
            texts.setdefault((day, hotel.key), []).extend(
                (tick, kind, text)
                for kind, text in _news_texts(day, hotel, feed, table, customer, tick, ticks)
            )
            asked = (day, hotel.key) if ticks == 1 else (day, tick, hotel.key)
            rows["queue"] += _queue_rows(
                day, hotel, own, customer.min_value_at_stake, tick, agent.asked.get(asked)
            )
            rows["stay_dates"] += _stay_rows(
                day, hotel, table, entries_of[(day, hotel.key)], ticks, tick
            )
        if tick == ticks:
            figures.update(_stayed(day, "agent", books, customer))
            final["agent"] = books

    def record_fixed(day: int, books: Books, tick: int = 1) -> dict[tuple[str, int], float]:
        if tick == ticks:  # the day's figures after its last tick
            figures.update(_stayed(day, "fixed", books, customer))
        return {}

    client = Recorded(recording, customer) if recording is not None else None
    with tempfile.TemporaryDirectory() as folder:  # the client is uncached, so nothing lands here
        run_days(
            seed,
            0,
            HORIZON_DAYS - 1,
            out,
            cache_dir=Path(folder) / "cache",
            client=client,
            customer=customer,
            observe=observe,
            ticks=ticks,
        )
    source = reason_source(recording, client.fallbacks if client is not None else 0)
    final["fixed"] = simulate(seed, record_fixed, customer=customer, ticks=ticks)
    if ticks > 1:
        _add_outcomes(texts, entries_of, final["agent"], final["fixed"], customer, ticks)
    for (day, key), found in texts.items():
        rows["news"] += [
            (day, key, tick, position, kind, text)
            for position, (tick, kind, text) in enumerate(found or [(1, "none", NOTHING_NEW)])
        ]
    rows["news"].sort()
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
        connection.execute(
            "CREATE TABLE IF NOT EXISTS run (seed INTEGER NOT NULL, "
            "reason_source VARCHAR NOT NULL, ticks INTEGER NOT NULL)"
        )
        connection.execute("INSERT INTO run VALUES (?, ?, ?)", [seed, source, ticks])
    finally:
        connection.close()
    return source


def reason_source(recording: Path | None, fallbacks: int = 0) -> str:
    """Where the file's reasons came from, as the sidebar says it: the recorded run's, the
    template's, or the recorded run's where it covers the request and the template's for the
    rest."""
    if recording is None:
        return "the template's, as no run is recorded"
    if fallbacks:
        return (
            f"the model's where the recorded live run covers the request and the template's for "
            f"the {fallbacks} it does not"
        )
    return "the model's, from the recorded live run"


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


def _news_texts(
    day: int, hotel: Hotel, feed: Sources, table, customer: Customer, tick: int = 1, ticks: int = 1
) -> list[tuple[str, str]]:
    """What became known at a moment for the hotel, in plain words, as (kind, text) pairs. On a
    finer clock each names the tick its feed landed at, and the table is the moment's, so a move
    is since the previous tick."""
    at = f" at tick {tick} of {ticks}" if ticks > 1 else ""
    moment = (day, tick) if ticks > 1 else (day, None)
    texts: list[tuple[str, str]] = []
    for event in feed.events.known(*moment):
        if event.known_day == day and hotel.key in event.hotels and _landed(table, "new_event"):
            texts.append(
                (
                    "event",
                    f"An event, the {event.name.lower()}, was announced{at} for "
                    f"{stay_span(event.start_day, event.end_day)}. Demand there is "
                    f"{percent_change(event.uplift)}, and the comp set's rates are "
                    f"{percent_change(event.comp_rate_raise)}.",
                )
            )
    revision = feed.schedules.passenger_revision(*moment)
    for first, last in _runs(s for s in range(HORIZON_DAYS) if revision[s] != 0):
        texts.append(
            (
                "schedule",
                f"The airlines filed a schedule change{at}: arriving passengers are "
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
                f"{percent_change_range(changes[s] for s in range(first, last + 1))}{at} for "
                f"{stay_span(first, last)}.",
            )
        )
    return texts


def _landed(table, column: str) -> bool:
    """Whether the moment's detect numbers mark anything in a column: an event announced at this
    tick shows in new_event, so an event known since an earlier tick is not news again."""
    return bool(table[column].notna().any())


def _add_outcomes(
    texts: dict, entries_of: dict, agent: Books, fixed: Books, customer: Customer, ticks: int
) -> None:
    """On a finer clock, after each hotel's news of a filing or an event announced that day: the
    tick the first flag with that cause rose, the tick the first raise was accepted on its stay
    dates, those stay dates and what they earned against the fixed-rate run; or that no raise
    was accepted. The line lands at the day's last tick, as it reads the whole day."""
    for (day, key), found in texts.items():
        hotel = customer.hotel(key)
        causes = []
        if any(kind == "schedule" for _, kind, _ in found):
            causes.append((SEATS_UP, "the stay dates the filing changed", None))
        for event in customer.events:
            if event.known_day == day and key in event.hotels:
                causes.append((NEW_EVENT, f"the {event.name.lower()}'s stay dates", event))
        for cause, what, event in causes:
            flagged = [e for e in entries_of.get((day, key), []) if cause in e.causes]
            if event is None:
                raised = [e for e in flagged if e.action != HOLD and "raise" in e.action]
            else:
                stays = set(range(event.start_day, event.end_day + 1))
                raised = [
                    e
                    for e in entries_of.get((day, key), [])
                    if e.action != HOLD and "raise" in e.action and stays & set(e.new_rates)
                ]
            if not flagged:
                text = f"No flag rose on {what}."
            elif not raised:
                first = min(flagged, key=lambda e: moment_index(e.day, e.tick, ticks))
                text = (
                    f"The first flag rose at tick {first.tick} of {ticks}; no raise was accepted "
                    f"on {what}."
                )
            else:
                first = min(flagged, key=lambda e: moment_index(e.day, e.tick, ticks))
                raise_ = min(raised, key=lambda e: moment_index(e.day, e.tick, ticks))
                stays = sorted(raise_.new_rates)
                measure = (
                    Books.contribution if customer.scores_contribution() else Books.room_revenue
                )
                earned = measure(agent, hotel, stays) - measure(fixed, hotel, stays)
                text = (
                    f"The first flag rose at tick {first.tick} of {ticks}, and the first raise "
                    f"was accepted at tick {raise_.tick} of {ticks} for "
                    f"{stay_span(stays[0], stays[-1])}; those stay dates earned "
                    f"{'-' if earned < 0 else '+'}${abs(round(earned)):,} against the fixed-rate "
                    f"run."
                )
            found.append((ticks, "decision", text))


def _runs(stays: Iterable[int]) -> list[tuple[int, int]]:
    """Consecutive stay dates as (first, last) pairs."""
    ordered = sorted(stays)
    groups = itertools.groupby(enumerate(ordered), key=lambda pair: pair[1] - pair[0])
    return [(run[0][1], run[-1][1]) for _, group in groups for run in [list(group)]]


def _stay_rows(
    day: int, hotel: Hotel, table, entries: Sequence[Entry], ticks: int = 1, tick: int = 1
) -> list[tuple]:
    """The charts' rows as of a moment: the hotel's rate, the comp median, the rooms on the books
    and the rooms the pace curve expects, per stay date in the window, with the flag that covers
    it and the rate an accepted plan sets. A plan's held days of the week keep the current rate.
    On a finer clock the flag is the last so far that day to cover the date, and a planned rate
    names the tick its plan was decided at."""
    own = table[table["hotel"] == hotel.key]
    rows = []
    for record in own.to_dict("records"):
        stay = record["stay_day"]
        flag = next((e for e in reversed(entries) if e.first_stay <= stay <= e.last_stay), None)
        planned, decided_at = None, ""
        if flag is not None and flag.action != HOLD:
            planned = flag.new_rates.get(stay, float(record["rate"]))
            decided_at = f"tick {flag.tick} of {ticks}" if ticks > 1 else ""
        rows.append(
            (
                day,
                hotel.key,
                tick,
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
                decided_at,
            )
        )
    return rows


def _queue_rows(
    day: int,
    hotel: Hotel,
    entries: Sequence[Entry],
    minimum: float,
    tick: int = 1,
    asked: tuple[dict, dict] | None = None,
) -> list[tuple]:
    """A moment's flags for the hotel: each plan, its value, its reason and what became of it. A
    held flag also carries the best alternative to holding and how far it fell short. A queued
    flag carries the earlier changes on its stay dates as the stored request lists them, the
    request the hotel's queue was asked with (`asked`), so the page shows what the last change
    did without computing it; a held flag was never asked. On a finer clock each tick's flags
    sit under their tick, in the agent's order."""
    request = asked[0] if asked else {}
    since = {
        entry["id"]: "; ".join(entry.get("earlier_changes_on_these_dates", []))
        for entry in request.get("entries", [])
    }
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
                tick,
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
                since.get(entry.id, "") if entry.queued else "",
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
    return customer.hotel(scope).name if scope != ALL else all_hotels(len(customer.hotels))


def all_hotels(count: int) -> str:
    """The title of a row for all the hotels together, "All four hotels"; ten or more read as
    a number."""
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
        "the page's tables, with the reasons from the recorded live run where it covers the "
        "request and from the template elsewhere.",
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
    parser.add_argument(
        "--customer",
        type=Path,
        metavar="FILE",
        help="the market's customer file (default: customers/demo.toml)",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=1,
        metavar="N",
        help="cut each day into N ticks, the feeds landing at fixed ticks and the agent running "
        "after each (default 1, the daily loop)",
    )
    args = parser.parse_args(argv)
    if args.ticks < 1:
        parser.error("--ticks: a day has one tick or more")
    source = build(args.seed, args.out, load(args.customer) if args.customer else None, args.ticks)
    clock = "" if args.ticks == 1 else f" at {args.ticks} ticks a day"
    print(
        f"Wrote {args.out}: days 0 to {SIM_DAYS - 1} of seed {args.seed}{clock}, reasons {source}."
    )


if __name__ == "__main__":
    main()
