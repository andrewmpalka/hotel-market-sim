"""median_path.py

The comp median's path on one hotel's stay dates, shop day by shop day, next to the hotel's own
rate, from a template run of one seed.

    python scripts/median_path.py --seed 7 --react --hotel convention --stays 45 48 --days 8 20

The run is the hotel-market command's template run for the seed in the true mode, with the
simulator settings given (--react, --demand-bias and --market-elasticity). It makes no model
call and writes nothing. The table has one row per shop day. For each stay date it shows the
hotel's rate in force that day and the comp median shopped that day. A rate change the agent
accepted shows as a new rate from the next day. With --react the median follows it REACTION_LAG
days later. The last lines give the rooms each stay date sold by the end of the run, in the
agent run and in the fixed-rate run.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from hotel_market.agent import Agent
from hotel_market.bookings import Books, simulate
from hotel_market.customer import Customer, demo
from hotel_market.demand import DEMAND_BIAS, MARKET_ELASTICITY
from hotel_market.plan import HOLD
from hotel_market.shops import REACTION_LAG, REACTION_SHARE
from hotel_market.simulated import deciding

Row = tuple[int, list[tuple[float, float]]]  # (shop day, [(hotel rate, comp median) per stay])


def median_path(
    seed: int,
    hotel_key: str,
    stays: Sequence[int],
    days: Sequence[int],
    react: bool = False,
    demand_bias: float = DEMAND_BIAS,
    customer: Customer | None = None,
    market_elasticity: float = MARKET_ELASTICITY,
) -> tuple[list[Row], Agent, Books, Books]:
    """The rows of the table from a template run to the last day asked for, with the agent, the
    books of that run and the books of the fixed-rate run."""
    customer = customer or demo()
    agent = Agent(seed, customer=customer, market_elasticity=market_elasticity)
    world = {"demand_bias": demand_bias, "react": react, "market_elasticity": market_elasticity}
    books = simulate(seed, deciding(agent), last_day=max(days), customer=customer, **world)
    fixed = simulate(seed, last_day=max(days), customer=customer, **world)
    row = customer.hotel(hotel_key).row
    rows = [
        (
            day,
            [
                (float(books.daily_rates[day, row, s]), float(books.daily_medians[day, row, s]))
                for s in stays
            ],
        )
        for day in days
    ]
    return rows, agent, books, fixed


def lines_for(
    seed: int,
    hotel_key: str,
    stays: Sequence[int],
    days: Sequence[int],
    react: bool,
    demand_bias: float = DEMAND_BIAS,
    market_elasticity: float = MARKET_ELASTICITY,
) -> list[str]:
    rows, agent, books, fixed = median_path(
        seed,
        hotel_key,
        stays,
        days,
        react=react,
        demand_bias=demand_bias,
        market_elasticity=market_elasticity,
    )
    hotel = books.customer.hotel(hotel_key)
    world = (
        f"competitors moving {REACTION_SHARE:.0%} of a change {REACTION_LAG} days after it"
        if react
        else "competitors never reacting"
    )
    world += f", market elasticity {market_elasticity:g}"
    found = [
        f"Seed {seed}, {hotel.name}, template run, {world}. For each stay date: the hotel's rate "
        f"in force on the shop day and the comp median shopped that day.",
        f"{'day':>4}" + "".join(f"{f'stay {s}':>22}" for s in stays),
        f"{'':>4}" + "".join(f"{'rate':>11}{'median':>11}" for _ in stays),
    ]
    for day, cells in rows:
        found.append(
            f"{day:>4}" + "".join(f"{rate:>11,.2f}{median:>11,.2f}" for rate, median in cells)
        )
    changes = [
        f"Day {e.day}: {e.action} on stays {e.first_stay} to {e.last_stay}, new rates "
        + ", ".join(f"{s}: {r:,.2f}" for s, r in sorted(e.new_rates.items()) if s in stays)
        for e in agent.entries
        if e.hotel == hotel_key and e.action != HOLD and set(e.new_rates) & set(stays)
    ]
    found.append("")
    found.append("The agent's accepted changes on these stay dates:")
    found.extend(changes or ["none"])
    found.append("")
    found.append(f"Rooms sold by day {max(days)}, the agent run and the fixed-rate run:")
    found.extend(
        f"stay {s}: {int(books.rooms[hotel.row, s])} / {int(fixed.rooms[hotel.row, s])}"
        for s in stays
    )
    return found


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Print the comp median's path on a hotel's stay dates next to its own rate."
    )
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--hotel", required=True, metavar="KEY", help="the hotel's key")
    parser.add_argument(
        "--stays", type=int, nargs=2, required=True, metavar=("FIRST", "LAST"), help="stay dates"
    )
    parser.add_argument(
        "--days", type=int, nargs=2, required=True, metavar=("FIRST", "LAST"), help="shop days"
    )
    parser.add_argument("--react", action="store_true", help="competitors react (shops.py)")
    parser.add_argument(
        "--demand-bias", dest="demand_bias", type=float, default=DEMAND_BIAS, metavar="F"
    )
    parser.add_argument(
        "--market-elasticity",
        dest="market_elasticity",
        type=float,
        default=MARKET_ELASTICITY,
        metavar="E",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    stays = range(args.stays[0], args.stays[1] + 1)
    days = range(args.days[0], args.days[1] + 1)
    lines = lines_for(
        args.seed, args.hotel, stays, days, args.react, args.demand_bias, args.market_elasticity
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
