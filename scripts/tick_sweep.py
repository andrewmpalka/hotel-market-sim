"""tick_sweep.py

The template sweep on the daily clock and on a finer one, side by side.

    python scripts/tick_sweep.py --seeds 1 20              # one tick a day against four
    python scripts/tick_sweep.py --seeds 1 20 --ticks 2    # against two

Each seed runs twice with the template: at --ticks 1, the daily loop, and at the finer clock,
where the feeds land at fixed ticks of the day and the agent runs after each tick (world.py). The
world is the same in both, and a fixed-rate run books the same rooms at either clock, so the two
runs differ only in when the agent saw the day's data and acted. The script prints one markdown
table with a row per clock: the mean contribution change a seed against the fixed-rate run, its
spread and range, the seeds ahead with the sign test's p, the decisions made at a tick other than
the day's last, the plans accepted among them, and, for the day-20 filing, the seeds where a raise
on the stay dates it changed was accepted and the mean lag in ticks from the filing's tick to the
first such raise. A line under the table gives the paired difference, the finer clock's change
minus the daily one's seed by seed, with its spread and the sign test's p. The decisions files go
to a temporary folder, and no model is called.
"""

from __future__ import annotations

import argparse
import statistics
import tempfile
from pathlib import Path

from hotel_market.cli import run, sign_test, spread
from hotel_market.customer import demo
from hotel_market.detect import SEATS_UP, moment_index
from hotel_market.plan import HOLD
from hotel_market.schedule import DEFAULT_SCENARIO
from hotel_market.world import FILING_TICK, arrival_tick

FILING_DAY = DEFAULT_SCENARIO.filing_days()[0]  # the day-20 filing, the new flights


def seed_result(seed: int, ticks: int, out: Path) -> dict:
    """One seed at one clock: the contribution change, the decisions and the accepted plans made
    at a tick other than the day's last, and the lag in ticks from the day-20 filing to the first
    accepted raise on the stay dates it changed, None when no such raise was accepted."""
    customer = demo()
    out.mkdir(parents=True, exist_ok=True)
    fixed, books, agent = run(seed, out / f"seed{seed}.jsonl", out / "cache", ticks=ticks)
    change = sum(books.contribution(h) - fixed.contribution(h) for h in customer.hotels)
    off_last = [e for e in agent.entries if e.tick != ticks]
    filing = moment_index(FILING_DAY, arrival_tick(FILING_TICK, ticks), ticks)
    raises = [
        moment_index(e.day, e.tick, ticks)
        for e in agent.entries
        if e.action != HOLD
        and SEATS_UP in e.causes
        and "raise" in e.action
        and moment_index(e.day, e.tick, ticks) >= filing
    ]
    return {
        "seed": seed,
        "change": change,
        "off_last": len(off_last),
        "off_last_accepted": sum(e.action != HOLD for e in off_last),
        "lag": min(raises) - filing if raises else None,
    }


def sweep(first: int, last: int, ticks: int, out: Path) -> dict:
    """One row of the table: the seeds at one clock, summed or averaged."""
    out.mkdir(parents=True, exist_ok=True)
    results = [seed_result(seed, ticks, out) for seed in range(first, last + 1)]
    lags = [r["lag"] for r in results if r["lag"] is not None]
    return {
        "ticks": ticks,
        "changes": [r["change"] for r in results],
        "off_last": sum(r["off_last"] for r in results),
        "off_last_accepted": sum(r["off_last_accepted"] for r in results),
        "raised": len(lags),
        "lag": statistics.mean(lags) if lags else None,
    }


def money(value: float) -> str:
    return f"{'-' if value < 0 else '+'}${abs(value):,.0f}"


def _number(value: float) -> str:
    return "n/a" if value != value else f"{value:,.0f}"


def _p(values: list[float]) -> str:
    p = sign_test(values)
    return "n/a" if p != p else ("<0.001" if p < 0.001 else f"{p:#.2g}")


def table(rows: list[dict]) -> str:
    """The rows as a markdown table, then the paired difference between the last row and the
    first, the finer clock's change minus the daily one's seed by seed."""
    lines = [
        "| Ticks a day | Mean change a seed | SD | SE | Range | Ahead | p | Decisions off the "
        "last tick | Accepted off the last tick | Seeds with a raise after the day-20 filing | "
        "Mean lag in ticks |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        changes = row["changes"]
        sd, se = spread(changes)
        lag = "n/a" if row["lag"] is None else f"{row['lag']:.2f}"
        lines.append(
            f"| {row['ticks']} | {money(statistics.mean(changes))} | {_number(sd)} | "
            f"{_number(se)} | {money(min(changes))} to {money(max(changes))} | "
            f"{sum(c > 0 for c in changes)} of {len(changes)} | {_p(changes)} | "
            f"{row['off_last']} | {row['off_last_accepted']} | {row['raised']} of "
            f"{len(changes)} | {lag} |"
        )
    first, last = rows[0], rows[-1]
    paired = [a - b for a, b in zip(last["changes"], first["changes"], strict=True)]
    sd, se = spread(paired)
    lines.append("")
    lines.append(
        f"Paired difference, {last['ticks']} ticks minus {first['ticks']}: mean "
        f"{money(statistics.mean(paired))} a seed (sd {_number(sd)}, se {_number(se)}), range "
        f"{money(min(paired))} to {money(max(paired))}, the finer clock ahead in "
        f"{sum(d > 0 for d in paired)} of {len(paired)} seeds, sign test p {_p(paired)}."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="The template sweep on the daily clock and on a finer one, side by side, as "
        "a markdown table with the paired difference."
    )
    parser.add_argument(
        "--seeds", type=int, nargs=2, default=(1, 20), metavar=("FIRST", "LAST"), help="the seeds"
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
        rows = [
            sweep(*args.seeds, ticks, Path(folder) / f"ticks-{ticks}") for ticks in (1, args.ticks)
        ]
    print(table(rows))


if __name__ == "__main__":
    main()
