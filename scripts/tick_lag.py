"""tick_lag.py

The day-20 filing, or an event's announcement, on the daily clock and on four ticks a day, side
by side: five lines per clock.

    python scripts/tick_lag.py --seed 7
    python scripts/tick_lag.py --seed 7 --hotel airport --ticks 4
    python scripts/tick_lag.py --seed 7 --customer customers/demo-intraday.toml --event concert

For one seed and one hotel, the script runs the template at --ticks 1 and at the finer clock and
prints, for the day-20 filing, the tick the filing landed at, the tick the first flag with a seats
cause rose at, the tick the first raise with a seats cause was accepted at, the stay dates that
raise covered, and the contribution on those stay dates against the fixed-rate run. These are the
five facts the demo page's day-20 news line shows at four ticks a day (demo_data.py). With
--customer the market is that file's, and with --event the five lines follow that event's
announcement instead: the tick it landed at, the first flag with an event cause at the hotel, the
first accepted raise on the event's stay dates, those stay dates and what they earned. The hotel
is then the event's first unless --hotel names one. The decisions files go to a temporary folder,
and no model is called.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from hotel_market.cli import run
from hotel_market.customer import Customer, demo, load
from hotel_market.detect import NEW_EVENT, SEATS_UP, moment_index
from hotel_market.plan import HOLD, Entry
from hotel_market.schedule import DEFAULT_SCENARIO
from hotel_market.sources import Event
from hotel_market.world import FILING_TICK, arrival_tick, news_tick

FILING_DAY = DEFAULT_SCENARIO.filing_days()[0]  # the day-20 filing, the new flights
LINES = (
    "The filing landed at",
    "The first flag rose at",
    "The first raise was accepted at",
    "The stay dates it covered",
    "Contribution on them against the fixed-rate run",
)
EVENT_LINE = "The announcement landed at"  # the first line, for an event


def find_event(customer: Customer, name: str) -> Event:
    """The customer's event with this name, case aside."""
    for event in customer.events:
        if event.name.lower() == name.lower():
            return event
    raise SystemExit(f"{customer.name} has no event named {name!r}")


def facts(
    seed: int,
    hotel_key: str,
    ticks: int,
    out: Path,
    customer: Customer | None = None,
    event: Event | None = None,
) -> list[str]:
    """The five facts for one seed, hotel and clock, each as the page would say it: for the day-20
    filing, or for the event's announcement when one is given."""
    customer = customer or demo()
    hotel = customer.hotel(hotel_key)
    out.mkdir(parents=True, exist_ok=True)
    fixed, books, agent = run(
        seed, out / f"seed{seed}.jsonl", out / "cache", customer=customer, ticks=ticks
    )
    if event is None:
        day = FILING_DAY
        tick = arrival_tick(dict(customer.filing_ticks).get(day, FILING_TICK), ticks)
        cause, stays = SEATS_UP, None
    else:
        day = event.known_day
        tick = news_tick(event.known_tick, ticks, ticks)
        cause, stays = NEW_EVENT, set(range(event.start_day, event.end_day + 1))
    landed = moment_index(day, tick, ticks)

    def after(entry: Entry) -> bool:
        return entry.hotel == hotel_key and moment_index(entry.day, entry.tick, ticks) >= landed

    flagged = [e for e in agent.entries if after(e) and cause in e.causes]
    raised = [
        e
        for e in agent.entries
        if after(e)
        and e.action != HOLD
        and "raise" in e.action
        and (cause in e.causes if stays is None else bool(stays & set(e.new_rates)))
    ]
    found = [f"tick {tick} of {ticks} on day {day}"]
    if not flagged:
        return found + ["no flag rose", "no raise was accepted", "none", "none"]
    first = min(flagged, key=lambda e: moment_index(e.day, e.tick, ticks))
    found.append(f"tick {first.tick} of {ticks} on day {first.day}")
    if not raised:
        return found + ["no raise was accepted", "none", "none"]
    raise_ = min(raised, key=lambda e: moment_index(e.day, e.tick, ticks))
    covered = sorted(raise_.new_rates)
    earned = books.contribution(hotel, covered) - fixed.contribution(hotel, covered)
    found.append(f"tick {raise_.tick} of {ticks} on day {raise_.day}")
    found.append(f"{covered[0]} to {covered[-1]}" if len(covered) > 1 else str(covered[0]))
    found.append(f"{'-' if earned < 0 else '+'}${abs(round(earned)):,}")
    return found


def table(one: list[str], many: list[str], ticks: int, subject: str = "The day-20 filing") -> str:
    """The five lines side by side, as a markdown table. The subject heads the first column: the
    day-20 filing, or the event's announcement."""
    lines = [f"| {subject} | --ticks 1 | --ticks {ticks} |", "| --- | --- | --- |"]
    names = LINES if subject == "The day-20 filing" else (EVENT_LINE, *LINES[1:])
    for name, a, b in zip(names, one, many, strict=True):
        lines.append(f"| {name} | {a} | {b} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="The day-20 filing, or an event's announcement, on the daily clock and on a "
        "finer one, five lines each."
    )
    parser.add_argument("--seed", type=int, default=7, help="the seed (default 7)")
    parser.add_argument(
        "--hotel",
        help="the hotel's key (default airport, the demo's, or the event's first hotel)",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=4,
        metavar="N",
        help="the finer clock's ticks a day (default 4)",
    )
    parser.add_argument(
        "--customer",
        type=Path,
        metavar="FILE",
        help="the market's customer file (default: customers/demo.toml)",
    )
    parser.add_argument(
        "--event", metavar="NAME", help="follow this event's announcement instead of the filing"
    )
    args = parser.parse_args(argv)
    if args.ticks < 2:
        parser.error("--ticks: the finer clock has two ticks a day or more")
    customer = load(args.customer) if args.customer else demo()
    event = find_event(customer, args.event) if args.event else None
    hotel = args.hotel or ("airport" if event is None else event.hotels[0])
    with tempfile.TemporaryDirectory() as folder:
        one = facts(args.seed, hotel, 1, Path(folder) / "ticks-1", customer, event)
        many = facts(
            args.seed, hotel, args.ticks, Path(folder) / f"ticks-{args.ticks}", customer, event
        )
    subject = "The day-20 filing" if event is None else f"The {event.name.lower()} announcement"
    print(table(one, many, args.ticks, subject))


if __name__ == "__main__":
    main()
