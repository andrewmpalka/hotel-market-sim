"""tick_lag.py

The day-20 filing on the daily clock and on four ticks a day, side by side: five lines per clock.

    python scripts/tick_lag.py --seed 7
    python scripts/tick_lag.py --seed 7 --hotel airport --ticks 4

For one seed and one hotel, the script runs the template at --ticks 1 and at the finer clock and
prints, for the day-20 filing, the tick the filing landed at, the tick the first flag with a seats
cause rose at, the tick the first raise with a seats cause was accepted at, the stay dates that
raise covered, and the contribution on those stay dates against the fixed-rate run. These are the
five facts the demo page's day-20 news line shows at four ticks a day (demo_data.py). The
decisions files go to a temporary folder, and no model is called.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from hotel_market.cli import run
from hotel_market.customer import demo
from hotel_market.detect import SEATS_UP, moment_index
from hotel_market.plan import HOLD, Entry
from hotel_market.schedule import DEFAULT_SCENARIO
from hotel_market.world import FILING_TICK, arrival_tick

FILING_DAY = DEFAULT_SCENARIO.filing_days()[0]  # the day-20 filing, the new flights
LINES = (
    "The filing landed at",
    "The first flag rose at",
    "The first raise was accepted at",
    "The stay dates it covered",
    "Contribution on them against the fixed-rate run",
)


def facts(seed: int, hotel_key: str, ticks: int, out: Path) -> list[str]:
    """The five facts for one seed, hotel and clock, each as the page would say it."""
    customer = demo()
    hotel = customer.hotel(hotel_key)
    out.mkdir(parents=True, exist_ok=True)
    fixed, books, agent = run(seed, out / f"seed{seed}.jsonl", out / "cache", ticks=ticks)
    filing_tick = arrival_tick(FILING_TICK, ticks)
    filing = moment_index(FILING_DAY, filing_tick, ticks)

    def after_filing(entry: Entry) -> bool:
        return (
            entry.hotel == hotel_key
            and SEATS_UP in entry.causes
            and moment_index(entry.day, entry.tick, ticks) >= filing
        )

    flagged = [e for e in agent.entries if after_filing(e)]
    raised = [e for e in flagged if e.action != HOLD and "raise" in e.action]
    found = [f"tick {filing_tick} of {ticks} on day {FILING_DAY}"]
    if not flagged:
        return found + ["no flag rose", "no raise was accepted", "none", "none"]
    first = min(flagged, key=lambda e: moment_index(e.day, e.tick, ticks))
    found.append(f"tick {first.tick} of {ticks} on day {first.day}")
    if not raised:
        return found + ["no raise was accepted", "none", "none"]
    raise_ = min(raised, key=lambda e: moment_index(e.day, e.tick, ticks))
    stays = sorted(raise_.new_rates)
    earned = books.contribution(hotel, stays) - fixed.contribution(hotel, stays)
    found.append(f"tick {raise_.tick} of {ticks} on day {raise_.day}")
    found.append(f"{stays[0]} to {stays[-1]}" if len(stays) > 1 else str(stays[0]))
    found.append(f"{'-' if earned < 0 else '+'}${abs(round(earned)):,}")
    return found


def table(one: list[str], many: list[str], ticks: int) -> str:
    """The five lines side by side, as a markdown table."""
    lines = [f"| The day-20 filing | --ticks 1 | --ticks {ticks} |", "| --- | --- | --- |"]
    for name, a, b in zip(LINES, one, many, strict=True):
        lines.append(f"| {name} | {a} | {b} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="The day-20 filing on the daily clock and on a finer one, five lines each."
    )
    parser.add_argument("--seed", type=int, default=7, help="the seed (default 7)")
    parser.add_argument(
        "--hotel", default="airport", help="the hotel's key (default airport, the walkthrough's)"
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=4,
        metavar="N",
        help="the finer clock's ticks a day (default 4)",
    )
    args = parser.parse_args(argv)
    if args.ticks < 2:
        parser.error("--ticks: the finer clock has two ticks a day or more")
    with tempfile.TemporaryDirectory() as folder:
        one = facts(args.seed, args.hotel, 1, Path(folder) / "ticks-1")
        many = facts(args.seed, args.hotel, args.ticks, Path(folder) / f"ticks-{args.ticks}")
    print(table(one, many, args.ticks))


if __name__ == "__main__":
    main()
