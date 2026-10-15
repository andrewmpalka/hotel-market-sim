"""no_comp_raise.py

The template sweep with the convention's competitor raise set to zero, next to the shipped run.

    python scripts/no_comp_raise.py --seeds 1 20

The convention raises demand 35% at the two downtown hotels and, as shipped, their competitors'
rates 15% (shocks.py). This script runs the sweep twice, once as shipped and once with the raise
at 0.0 and the demand uplift unchanged, and prints one markdown table with a row per setting: the
mean contribution change a seed against the fixed-rate run, its range, the seeds ahead, the
accepted plans the convention raised, the gain on the stay dates those plans changed, and the
convention nights the two downtown hotels sold out at fixed rates. The Event is replaced in
shocks.EVENTS before each sweep and put back after it, so the simulator and the agent see the
same convention. The decisions files go to a temporary folder, and no model is called.
"""

from __future__ import annotations

import argparse
import statistics
import tempfile
from dataclasses import replace
from pathlib import Path

from hotel_market import shocks
from hotel_market.cli import _gain_on, run
from hotel_market.customer import demo
from hotel_market.detect import NEW_EVENT
from hotel_market.plan import HOLD


def sweep(first: int, last: int, comp_rate_raise: float, out: Path) -> dict:
    """One row of the table: the seeds' contribution changes, the accepted plans the convention
    raised with the gain on their stay dates, and the sold-out convention nights at fixed rates."""
    customer = demo()
    shipped = shocks.EVENTS[0]
    shocks.EVENTS[0] = replace(shipped, comp_rate_raise=comp_rate_raise)
    event = shocks.EVENTS[0]
    changes, plans, gain, sellouts = [], 0, 0.0, 0
    out.mkdir(parents=True, exist_ok=True)
    try:
        for seed in range(first, last + 1):
            fixed, books, agent = run(seed, out / f"seed{seed}.jsonl", out / "cache")
            changes.append(
                sum(books.contribution(h) - fixed.contribution(h) for h in customer.hotels)
            )
            raised = [e for e in agent.entries if e.action != HOLD and NEW_EVENT in e.causes]
            plans += len(raised)
            pairs = {(e.hotel, s) for e in raised for s in e.new_rates}
            gain += _gain_on(fixed, books, pairs, customer.hotels, customer.target)
            for key in event.hotels:
                hotel = customer.hotel(key)
                for stay in range(event.start_day, event.end_day + 1):
                    sellouts += int(fixed.rooms[hotel.row, stay] >= hotel.rooms)
    finally:
        shocks.EVENTS[0] = shipped
    seeds = last - first + 1
    nights = len(event.hotels) * (event.end_day - event.start_day + 1) * seeds
    return {
        "raise": comp_rate_raise,
        "mean": statistics.mean(changes),
        "low": min(changes),
        "high": max(changes),
        "ahead": sum(change > 0 for change in changes),
        "seeds": seeds,
        "plans": plans,
        "gain": gain / seeds,
        "sellouts": sellouts,
        "nights": nights,
    }


def money(value: float) -> str:
    return f"{'-' if value < 0 else '+'}${abs(value):,.0f}"


def table(rows: list[dict]) -> str:
    """The rows as a markdown table."""
    lines = [
        "| Competitors' raise | Mean change a seed | Range | Ahead | Convention plans accepted "
        "| Gain on their stay dates a seed | Convention nights sold out at fixed rates |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['raise']:.0%} | {money(row['mean'])} | {money(row['low'])} to "
            f"{money(row['high'])} | {row['ahead']} of {row['seeds']} | {row['plans']} | "
            f"{money(row['gain'])} | {row['sellouts']} of {row['nights']} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="The template sweep with the convention's competitor raise at zero, next to "
        "the shipped run, as a markdown table."
    )
    parser.add_argument(
        "--seeds", type=int, nargs=2, default=(1, 20), metavar=("FIRST", "LAST"), help="the seeds"
    )
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory() as folder:
        rows = [
            sweep(*args.seeds, raise_, Path(folder) / f"raise-{raise_:g}")
            for raise_ in (shocks.EVENTS[0].comp_rate_raise, 0.0)
        ]
    print(table(rows))


if __name__ == "__main__":
    main()
