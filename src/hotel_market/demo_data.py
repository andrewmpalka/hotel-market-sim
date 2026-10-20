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
stay_dates, queue, scorecard, outcome and gains. It also adds a run table with the seed, the words
for where the reasons came from and the market's name, and a strip table for each moment: the
first news so far, the stay dates flagged, the plans accepted so far that day and their value at
stake together, the last three of which the page shows as tiles, and, when the day's news names
nights past the agent's window, a clause for the charts' heading saying how far the agent looks.
The news writes a whole percentage without its ".0", and an event's demand against normal, "three
times normal" when it is a whole multiple. A queued plan's row carries a
headline that leads with its value at stake, a line that gives the request's numbers for its stay
dates their dates, and the earlier changes on its stay dates as the stored request lists them, the
read-back the page shows under "Since our last change on these dates", once as written and once
with its day numbers as dates. Code computes every figure in them and writes every date as a
calendar date with its day of the week, "Thu 18 Feb"; the days table adds the day's number,
"day 10", which the page shows small. The page (demo_page.py) formats and draws them and computes
nothing. The scorecard holds the nights already stayed as of the day, stay dates 0 to the day
before. The outcome holds the result once every stay date is complete, every booking through day
149. The gains are that result's contribution difference by stay date. Each is given per hotel and
for all the hotels together.

With --ticks N the run is the finer clock's (world.py): each news line opens with the time its
feed landed at, the queue holds each tick's flags under that tick, a queued plan names the time
it was decided at and an accepted one the time it is in effect from, the next tick's, the chart
rows are written per tick as of it, a planned rate names the time it was decided at, the strip
counts the plans accepted at every tick of the day so far, and on a day a filing or an
event lands the news adds, at the day's last tick, the first flag, the first accepted raise on
its stay dates and what they earned against the fixed-rate run. At four ticks a day a time is the
tick's time of day, 08:00, 11:00, 14:00 or 17:00; on another finer clock it is "tick 2 of 3".
The run table carries the ticks a day was cut into, so the page can offer a tick. At one tick a
day the file reads as before, every row at tick 1. The recorded run is at one tick a day, so on a
finer clock the template writes every reason.
"""

from __future__ import annotations

import argparse
import calendar
import itertools
import json
import math
import re
import tempfile
from collections.abc import Iterable, Sequence
from datetime import timedelta
from pathlib import Path

from hotel_market import stored
from hotel_market.agent import Agent
from hotel_market.bookings import Books, simulate
from hotel_market.customer import Customer, demo, load
from hotel_market.detect import AHEAD, BEHIND, NEW_EVENT, SEATS_UP, detect_numbers, moment_index
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
from hotel_market.world import HORIZON_DAYS, SIM_DAYS, Hotel, news_tick, stay_window, weekday

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
_TIMES_OF_DAY = {1: "08:00", 2: "11:00", 3: "14:00", 4: "17:00"}  # each tick's, at four a day


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
        (day, day_label(day), stay_span(*_ends(stay_window(day))), day_index(day))
        for day in range(SIM_DAYS)
    ]
    strip: list[tuple] = []  # one row per moment and hotel: the tiles under the page's title
    figures: dict[tuple[int, str, str], tuple[float, ...]] = {}  # (day, scope, run) -> the five
    final: dict[str, Books] = {}
    # (day, hotel) -> the news so far, each with the tick it landed at
    texts: dict[tuple[int, str], list[tuple[int, str, str]]] = {}
    reach: dict[tuple[int, str], int] = {}  # (day, hotel) -> the last stay date its news names
    entries_of: dict[tuple[int, str], list[Entry]] = {}  # (day, hotel) -> the day's entries so far

    def observe(day: int, books: Books, agent: Agent, tick: int = 1) -> None:
        """After each moment: the news its feeds brought, its queue and the chart rows as of it;
        at the day's last tick the scorecard."""
        feed = simulated_sources(books, day, tick if ticks > 1 else None)
        table = detect_numbers(day, feed, customer, tick=tick if ticks > 1 else None)
        for hotel in customer.hotels:
            key = (day, hotel.key)
            own = [e for e in agent.entries if e.day == day and e.hotel == hotel.key]
            entries_of.setdefault(key, []).extend(own)
            found = _news_texts(day, hotel, feed, table, customer, tick, ticks) + _pace_texts(
                entries_of[key], tick, ticks
            )
            texts.setdefault(key, []).extend((tick, kind, _whole(text)) for kind, text, _ in found)
            reach[key] = max([reach.get(key, -1), *(last for *_, last in found)])
            asked = (day, hotel.key) if ticks == 1 else (day, tick, hotel.key)
            rows["queue"] += _queue_rows(
                day, hotel, own, customer.min_value_at_stake, tick, agent.asked.get(asked), ticks
            )
            rows["stay_dates"] += _stay_rows(
                day, hotel, table, entries_of[(day, hotel.key)], ticks, tick
            )
            strip.append(_strip_row(day, hotel, tick, texts[key], entries_of[key], reach[key]))
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
            "reason_source VARCHAR NOT NULL, ticks INTEGER NOT NULL, market VARCHAR NOT NULL)"
        )
        connection.execute(
            "INSERT INTO run VALUES (?, ?, ?, ?)", [seed, source, ticks, customer.name]
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS strip (as_of_day INTEGER NOT NULL, hotel VARCHAR NOT NULL, "
            "as_of_tick INTEGER NOT NULL, news VARCHAR NOT NULL, nights_flagged INTEGER NOT NULL, "
            "recommendations INTEGER NOT NULL, value_at_stake VARCHAR NOT NULL, "
            "horizon_text VARCHAR NOT NULL, PRIMARY KEY (as_of_day, hotel, as_of_tick))"
        )
        connection.executemany("INSERT INTO strip VALUES (?, ?, ?, ?, ?, ?, ?, ?)", strip)
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
    """A stay date as the page shows it: "Thu 18 Feb"."""
    date = SIM_START + timedelta(days=stay_day)
    return f"{date:%a} {date.day} {date:%b}"


def stay_span(first_stay: int, last_stay: int) -> str:
    """One stay date, or a run of them: "Thu 18 Feb to Sun 21 Feb"."""
    if first_stay == last_stay:
        return stay_label(first_stay)
    return f"{stay_label(first_stay)} to {stay_label(last_stay)}"


def day_label(day: int) -> str:
    """A simulation day as the title shows it: "Thu 14 Jan 2027"."""
    date = SIM_START + timedelta(days=day)
    return f"{date:%a} {date.day} {date:%b} {date.year}"


def day_index(day: int) -> str:
    """A simulation day's number as the page shows it small under the title: "day 10"."""
    return f"day {day}"


def _time(tick: int, ticks: int) -> str:
    """A tick as the page names it: its time of day at four ticks a day, "11:00", and "tick 2 of
    3" on any other finer clock."""
    return _TIMES_OF_DAY[tick] if ticks == len(_TIMES_OF_DAY) else f"tick {tick} of {ticks}"


def _at(time: str, sentence: str) -> str:
    """The sentence led by the time its news landed at, "At 11:00 the airlines filed ...", or as
    it is when there is no time, on the daily clock."""
    return f"At {time} {sentence[:1].lower()}{sentence[1:]}" if time else sentence


def _with_dates(line: str) -> str:
    """The stored request's line on earlier changes with its day numbers as dates: "day 18: raised
    10% to $264 on Sat 75" reads "Fri 22 Jan: raised 10% to $264 on Sat 20 Mar"."""
    days = "|".join(DAY_NAMES)
    return re.sub(
        rf"\bday (\d+):|\b(?:{days}) (\d+)\b",
        lambda found: f"{stay_label(int(found[1]))}:" if found[1] else stay_label(int(found[2])),
        line,
    )


def _ends(stays: Sequence[int]) -> tuple[int, int]:
    return stays[0], stays[-1]


# ---- the page's rows, one function per table ----------------------------------------------


def _news_texts(
    day: int, hotel: Hotel, feed: Sources, table, customer: Customer, tick: int = 1, ticks: int = 1
) -> list[tuple[str, str, int]]:
    """What became known at a moment for the hotel, in plain words, as (kind, text, last stay
    date it names) triples. On a finer clock each opens with the time its feed landed at, and the
    table is the moment's, so a move is since the previous tick. A scripted move is named for what
    it is: an event that only moves the competitors' rates reads as their raise, and a rate cut
    from the customer file as the cut with the median's move it makes, so the comp set line
    leaves out the nights either already explains. An event's demand reads against normal, "three
    times normal" when it is a whole multiple."""
    time = _time(tick, ticks) if ticks > 1 else ""
    moment = (day, tick) if ticks > 1 else (day, None)
    texts: list[tuple[str, str, int]] = []
    explained: set[int] = set()  # nights whose comp set move a line above already gives
    for event in feed.events.known(*moment):
        if event.known_day == day and hotel.key in event.hotels and _landed(table, "new_event"):
            span = stay_span(event.start_day, event.end_day)
            if event.uplift == 0 and event.comp_rate_raise:  # the competitors' move alone
                moved = "raised" if event.comp_rate_raise > 0 else "cut"
                sentence = (
                    f"The {hotel.name.lower()}'s competitors {moved} their rates "
                    f"{_percent(abs(event.comp_rate_raise))} for {span}."
                )
            else:
                sentence = (
                    f"An event, the {event.name.lower()}, was announced for {span}. Demand on "
                    f"those nights is {_demand(event.uplift)}, and the comp set's rates are "
                    f"{percent_change(event.comp_rate_raise)}."
                )
            texts.append(("event", _at(time, sentence), event.end_day))
            if event.comp_rate_raise:
                explained |= set(range(event.start_day, event.end_day + 1))
    own = table[table["hotel"] == hotel.key]
    median = dict(zip(own["stay_day"].tolist(), own["median_change"].tolist()))
    for cut in customer.rate_cuts:
        landed = cut.known_day == day and news_tick(cut.known_tick, ticks, 1) == tick
        if cut.hotel == hotel.key and landed:
            nights = range(cut.start_day, cut.end_day + 1)
            sentence = (
                f"{_competitors(len(cut.competitors))} cut their rates {_percent(cut.cut)} for "
                f"{stay_span(cut.start_day, cut.end_day)}"
            )
            change = [median[s] for s in nights if s in median]
            if any(change):  # the shop at this moment shows the cut
                sentence += f", so the comp set median is {_whole(percent_change_range(change))}"
            texts.append(("rate cut", _at(time, f"{sentence}."), cut.end_day))
            explained |= set(nights)
    revision = feed.schedules.passenger_revision(*moment)
    for first, last in _runs(s for s in range(HORIZON_DAYS) if revision[s] != 0):
        texts.append(
            (
                "schedule",
                _at(
                    time,
                    f"The airlines filed a schedule change: arriving passengers are "
                    f"{percent_change_range(revision[s] for s in range(first, last + 1))} for "
                    f"{stay_span(first, last)}.",
                ),
                last,
            )
        )
    moved = own[own["median_change"].abs() >= customer.median_threshold]
    changes = {
        stay: change
        for stay, change in zip(moved["stay_day"].tolist(), moved["median_change"].tolist())
        if stay not in explained
    }
    for first, last in _runs(changes):
        texts.append(
            (
                "comp set",
                _at(
                    time,
                    f"The comp set median is "
                    f"{percent_change_range(changes[s] for s in range(first, last + 1))} for "
                    f"{stay_span(first, last)}.",
                ),
                last,
            )
        )
    return texts


def _pace_texts(today: Sequence[Entry], tick: int, ticks: int) -> list[tuple[str, str, int]]:
    """The nights a flag covers because their bookings run ahead of or behind the usual pace,
    which no feed reports, as (kind, text, last stay date) triples: "Bookings are running ahead
    of the usual pace for Thu 18 Feb, Sun 21 Feb and Fri 26 Mar." A night is named once a day, at
    the first tick a pace flag covers it, and a list of more than three runs of nights ends "and
    2 more"."""
    time = _time(tick, ticks) if ticks > 1 else ""
    texts = []
    for cause, how in ((AHEAD, "ahead of"), (BEHIND, "behind")):
        now = _covered(e for e in today if e.tick == tick and cause in e.causes)
        new = now - _covered(e for e in today if e.tick < tick and cause in e.causes)
        spans = [stay_span(first, last) for first, last in _runs(new)]
        if len(spans) > 3:
            spans = [*spans[:3], f"{len(spans) - 3} more"]
        if spans:
            sentence = f"Bookings are running {how} the usual pace for {_listed(spans)}."
            texts.append(("pace", _at(time, sentence), max(new)))
    return texts


def _whole(text: str) -> str:
    """A text with each whole percentage written without its ".0": "up 35%", "8.3% to 11%"."""
    return text.replace(".0%", "%")


def _percent(fraction: float) -> str:
    """A share as a percentage to one decimal, a whole one without its ".0": "20%", "8.3%"."""
    return _whole(f"{fraction:.1%}")


def _demand(uplift: float) -> str:
    """An event's demand against normal: "three times normal" or "twice normal" when it is a whole
    multiple of it, else the change, "up 35%"."""
    times = 1 + uplift
    if times < 2 or times != round(times):
        return percent_change(uplift)
    count = round(times)
    word = NUMBER_WORDS[count] if count < len(NUMBER_WORDS) else str(count)
    return "twice normal" if count == 2 else f"{word} times normal"


def _competitors(count: int) -> str:
    """The competitors a scripted cut names, counted in words: "Two competitors"."""
    word = NUMBER_WORDS[count] if count < len(NUMBER_WORDS) else str(count)
    return f"{word.capitalize()} competitor{'' if count == 1 else 's'}"


def _covered(entries: Iterable[Entry]) -> set[int]:
    """The stay dates the entries cover."""
    return {stay for e in entries for stay in range(e.first_stay, e.last_stay + 1)}


def _listed(items: Sequence[str]) -> str:
    """Items in a sentence: "A", "A and B", "A, B and C"."""
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} and {items[-1]}"


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
                # the news names an event that only moves the competitors' rates by its nights
                what = f"the {event.name.lower()}'s stay dates" if event.uplift else ""
                what = what or stay_span(event.start_day, event.end_day)
                causes.append((NEW_EVENT, what, event))
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
                    f"The first flag rose at {_time(first.tick, ticks)}; no raise was accepted on "
                    f"{what}."
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
                    f"The first flag rose at {_time(first.tick, ticks)}, and the first raise was "
                    f"accepted at {_time(raise_.tick, ticks)} for "
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
    names the time its plan was decided at."""
    own = table[table["hotel"] == hotel.key]
    rows = []
    for record in own.to_dict("records"):
        stay = record["stay_day"]
        flag = next((e for e in reversed(entries) if e.first_stay <= stay <= e.last_stay), None)
        planned, decided_at = None, ""
        if flag is not None and flag.action != HOLD:
            planned = flag.new_rates.get(stay, float(record["rate"]))
            decided_at = _time(flag.tick, ticks) if ticks > 1 else ""
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
    ticks: int = 1,
) -> list[tuple]:
    """A moment's flags for the hotel: each plan, its value, its reason and what became of it. A
    held flag also carries the best alternative to holding and how far it fell short. A queued
    flag carries its headline, the earlier changes on its stay dates as the stored request lists
    them, again with dates for day numbers, the request's digest as the decisions table stores it,
    and the request's numbers for its stay dates with their dates. The request is the one the
    hotel's queue was asked with (`asked`), so the page shows what the last change did without
    computing it; a held flag was never asked. On a finer clock each tick's flags sit under their
    tick, in the agent's order, and a queued plan also names the time it was decided at and an
    accepted one the time it is in effect from."""
    request, answer = asked if asked else ({}, {})
    since = {
        entry["id"]: entry.get("earlier_changes_on_these_dates", [])
        for entry in request.get("entries", [])
    }
    digest = (answer.get("request_digest") or request_digest(request)) if asked else ""
    rows = []
    for position, entry in enumerate(entries):
        if not entry.queued:
            outcome = "held"
        else:
            outcome = "declined" if entry.action == HOLD else "accepted"
        alternative, short = _alternative(entry, minimum) if outcome == "held" else ("", "")
        changes = since.get(entry.id, []) if entry.queued else []
        line = "; ".join(changes)
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
                line,
                _with_dates(latest_changes(changes)),
                _headline(entry) if entry.queued else "",
                digest if entry.queued else "",
                _stay_numbers(entry) if entry.queued else "",
                _time(tick, ticks) if ticks > 1 and entry.queued else "",
                _in_effect(tick, ticks) if outcome == "accepted" else "",
            )
        )
    return rows


def _in_effect(tick: int, ticks: int) -> str:
    """When a plan accepted at a tick takes effect, the next tick's time, as the page adds it once
    the day has moved on: "in effect from 14:00". Empty on the daily clock and at the day's last
    tick, whose plans take effect the next day."""
    return f"in effect from {_time(tick + 1, ticks)}" if 1 < ticks and tick < ticks else ""


def latest_changes(changes: Sequence[str], keep: int = 3) -> str:
    """A plan's earlier changes as the page lists them under "Since our last change on these
    dates": the three made last, in the request's order, then how many more there are, "and 15
    earlier changes", or "and 15 more changes" when some were made the same day as one shown. The
    stored request keeps every one."""
    if len(changes) <= keep:
        return "; ".join(changes)
    made = [int(re.match(r"day (\d+):", change)[1]) for change in changes]  # the day it was made
    shown = sorted(sorted(range(len(changes)), key=lambda i: -made[i])[:keep])
    rest = [made[i] for i in range(len(changes)) if i not in shown]
    word = "earlier" if max(rest) < min(made[i] for i in shown) else "more"
    count = f"{len(rest)} {word} change{'' if len(rest) == 1 else 's'}"
    return f"{'; '.join(changes[i] for i in shown)}; and {count}"


def _stay_numbers(entry: Entry) -> str:
    """The request's numbers for a queued plan's stay dates with the page's dates, for a reason
    that names the nights by number: "Stay dates 50 to 74 are Tue 23 Feb to Fri 19 Mar."."""
    if entry.first_stay == entry.last_stay:
        return f"Stay date {entry.first_stay} is {stay_label(entry.first_stay)}."
    span = stay_span(entry.first_stay, entry.last_stay)
    return f"Stay dates {entry.first_stay} to {entry.last_stay} are {span}."


def _headline(entry: Entry) -> str:
    """A queued plan's first line: its value at stake, the plan with its days of the week written
    out, and its stay dates, "+$2,470 over holding · raise 10% on Thursday and Friday · Thu 4 Feb
    to Fri 5 Feb"."""
    return (
        f"{_money(entry.value_at_stake)} over holding · {_weekdays_in_full(entry.plan)} · "
        f"{stay_span(entry.first_stay, entry.last_stay)}"
    )


def _weekdays_in_full(plan: str) -> str:
    """The plan with each run of days of the week written out: two joined by "and", three or more
    by commas and a last "and". "raise 10% on Thu, Fri" reads "raise 10% on Thursday and
    Friday"."""
    days = "|".join(DAY_NAMES)

    def full(found: re.Match) -> str:
        names = [calendar.day_name[DAY_NAMES.index(day)] for day in found[0].split(", ")]
        return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"

    return re.sub(rf"\b(?:{days})(?:, (?:{days}))*\b", full, plan)


def _money(value: float) -> str:
    """A value at stake as the headline and the strip write it, to the nearest $10 as the request
    shows it: "+$2,470", or "$0"."""
    tens = 10 * round(value / 10)
    return f"+{dollars(tens)}" if tens > 0 else dollars(tens)


def _strip_row(
    day: int,
    hotel: Hotel,
    tick: int,
    news: Sequence[tuple],
    today: Sequence[Entry],
    reach: int = -1,
) -> tuple:
    """The tiles under the page's title at a moment: the first news so far, or "Nothing new"; the
    stay dates the day's flags so far cover, which the charts shade; and the plans accepted so far
    that day with their value at stake together, "$0" when there is none. On the daily clock the
    day so far is its one tick. When the day's news so far names a stay date past the agent's
    window (`reach`), a clause for the charts' heading says how far the agent looks: "The agent
    looks 90 nights ahead, to Fri 23 Apr."."""
    nights = {stay for entry in today for stay in range(entry.first_stay, entry.last_stay + 1)}
    accepted = [entry.value_at_stake for entry in today if entry.queued and entry.action != HOLD]
    first = news[0][2] if news else "Nothing new"
    window = stay_window(day)
    ahead = f"The agent looks {len(window)} nights ahead, to {stay_label(window[-1])}."
    return (
        day,
        hotel.key,
        tick,
        first,
        len(nights),
        len(accepted),
        _money(sum(accepted)),
        ahead if reach > window[-1] else "",
    )


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
        nights = stay_span(0, day - 1)  # the day's count of nights, stay dates 0 to day - 1
        rows += [
            (day, scope, _title(scope, customer), nights, day, *tile)
            for tile in tiles(agent, fixed)
        ]
    return rows


def _outcome_rows(agent: Books, fixed: Books, customer: Customer) -> list[tuple]:
    """The result once every stay date is complete, per hotel and for all together."""
    stays = range(HORIZON_DAYS)
    scopes = [(h.key, [h]) for h in customer.hotels] + [(ALL, list(customer.hotels))]
    return [
        (scope, _title(scope, customer), stay_span(0, HORIZON_DAYS - 1), HORIZON_DAYS, *tile)
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
    """A figure as its tile shows it: occupancy to a tenth of a percent, a whole one without its
    ".0", ADR and RevPAR to the cent, revenue and contribution to the dollar."""
    if math.isnan(value):
        return "n/a"
    if position == 0:
        return _percent(value)
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
