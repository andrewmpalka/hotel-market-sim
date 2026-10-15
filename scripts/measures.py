"""measures.py

The template sweep in a revenue manager's measures, per hotel, both runs, as two markdown tables.

    python scripts/measures.py --seeds 1 20

The first table gives each hotel's occupancy, average rate, RevPAR and share of sold-out nights
over stay dates 0 to 149, each the mean over the seeds, for the fixed-rate run and the agent run.
The second gives what the agent run gave up and saved a seed: the room nights, the room revenue,
the room cost saved on those nights and the contribution. It ends with the cost per occupied
room, as a share of the start rate, at which the hotel's gain would be zero. A hotel whose room
revenue rose gains at any cost, and its share prints below zero. The decisions files go to a
temporary folder, and no model is called.
"""

from __future__ import annotations

import argparse
import statistics
import tempfile
from pathlib import Path

import numpy as np

from hotel_market.cli import run
from hotel_market.customer import demo
from hotel_market.world import HORIZON_DAYS

STAYS = range(HORIZON_DAYS)


def sweep(first: int, last: int, out: Path) -> dict[str, dict]:
    """Per hotel key: the per-seed measures of both runs, and the totals the agent run gave up."""
    customer = demo()
    found = {
        h.key: {
            "fixed": {"occupancy": [], "rate": [], "revpar": [], "sold_out": []},
            "agent": {"occupancy": [], "rate": [], "revpar": [], "sold_out": []},
            "rooms": 0,
            "revenue": 0.0,
            "contribution": 0.0,
        }
        for h in customer.hotels
    }
    for seed in range(first, last + 1):
        fixed, books, _ = run(seed, out / f"seed{seed}.jsonl", out / "cache")
        for hotel in customer.hotels:
            own = found[hotel.key]
            for name, run_books in (("fixed", fixed), ("agent", books)):
                measures = own[name]
                measures["occupancy"].append(run_books.occupancy(hotel, STAYS))
                measures["rate"].append(run_books.average_rate(hotel))
                measures["revpar"].append(run_books.revpar(hotel))
                measures["sold_out"].append(
                    float(np.mean(run_books.rooms[hotel.row] >= hotel.rooms))
                )
            own["rooms"] += int(books.rooms[hotel.row].sum() - fixed.rooms[hotel.row].sum())
            own["revenue"] += books.room_revenue(hotel) - fixed.room_revenue(hotel)
            own["contribution"] += books.contribution(hotel) - fixed.contribution(hotel)
    return found


def money(value: float) -> str:
    return f"{'-' if value < 0 else '+'}${abs(value):,.0f}"


def measures_table(found: dict[str, dict]) -> str:
    """The first table: the four measures per hotel, both runs, each the mean over the seeds."""
    customer = demo()
    lines = [
        "| Hotel | Occupancy, fixed | Occupancy, agent | Average rate, fixed | Average rate, agent "
        "| RevPAR, fixed | RevPAR, agent | Sold-out nights, fixed | Sold-out nights, agent |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for hotel in customer.hotels:
        fixed, agent = found[hotel.key]["fixed"], found[hotel.key]["agent"]
        mean = statistics.mean
        lines.append(
            f"| {hotel.name} | {mean(fixed['occupancy']):.1%} | {mean(agent['occupancy']):.1%} "
            f"| ${mean(fixed['rate']):,.2f} | ${mean(agent['rate']):,.2f} "
            f"| ${mean(fixed['revpar']):,.2f} | ${mean(agent['revpar']):,.2f} "
            f"| {mean(fixed['sold_out']):.1%} | {mean(agent['sold_out']):.1%} |"
        )
    return "\n".join(lines)


def cost_table(found: dict[str, dict], seeds: int) -> str:
    """The second table: what the agent run gave up and saved a seed, and the cost share at which
    each hotel's gain is zero."""
    customer = demo()
    lines = [
        "| Hotel | Room nights given up a seed | Share of capacity | Room revenue change a seed "
        "| Room cost saved a seed | Contribution gained a seed "
        "| Cost share at which the gain is zero |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for hotel in customer.hotels:
        own = found[hotel.key]
        rooms, revenue, contribution = own["rooms"], own["revenue"], own["contribution"]
        # gain = revenue change - cost x room nights change; it is zero at cost = revenue / rooms
        share = (revenue / rooms) / hotel.start_rate if rooms else float("nan")
        capacity = seeds * HORIZON_DAYS * hotel.rooms
        lines.append(
            f"| {hotel.name} | {-rooms / seeds:,.0f} | {-rooms / capacity:.2%} "
            f"| {money(revenue / seeds)} | {money(-rooms * hotel.room_cost / seeds)} "
            f"| {money(contribution / seeds)} | {share:.1%} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="The template sweep in a revenue manager's measures, per hotel and both "
        "runs, as two markdown tables."
    )
    parser.add_argument(
        "--seeds", type=int, nargs=2, default=(1, 20), metavar=("FIRST", "LAST"), help="the seeds"
    )
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory() as folder:
        found = sweep(*args.seeds, Path(folder))
    print(measures_table(found))
    print()
    print(cost_table(found, args.seeds[1] - args.seeds[0] + 1))


if __name__ == "__main__":
    main()
