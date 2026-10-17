"""tick_sweep.py

The template sweep on the daily clock and on a finer one, side by side.

    python scripts/tick_sweep.py --seeds 1 20              # one tick a day against four
    python scripts/tick_sweep.py --seeds 1 20 --ticks 2    # against two
    python scripts/tick_sweep.py --seeds 1 20 --customer customers/demo-intraday.toml \
        --event concert                                    # the concert announcement

Each seed runs twice with the template: at --ticks 1, the daily loop, and at the finer clock,
where the feeds land at ticks of the day and the agent runs after each tick (world.py). The
world is the same in both, and a fixed-rate run books the same rooms at either clock unless a
rush is in the file, so the two runs differ in when the agent saw the day's data and acted. The
script prints one markdown table with a row per clock: the mean contribution change a seed
against the fixed-rate run, its spread and range, the seeds ahead with the sign test's p, the
decisions made at a tick other than the day's last, the plans accepted among them, and, for the
day-20 filing, the seeds where a raise on the stay dates it changed was accepted and the mean lag
in ticks from the filing's tick to the first such raise. A line under the table gives the paired
difference, the finer clock's change minus the daily one's seed by seed, with its spread and the
sign test's p.

With --customer the market is that file's, and with --event the announcement of that event
replaces the filing: the lag runs from the tick the announcement lands at to the first accepted
raise on its stay dates at its hotels, and two more columns give the rooms booked on those stay
dates at those hotels from the announcement to the first raise, the day's moments through the
raise's, and the contribution on those stay dates against the fixed-rate run, each a mean over
the seeds. The decisions files go to a temporary folder, and no model is called.
"""

from __future__ import annotations

import argparse
import statistics
import tempfile
from pathlib import Path

from hotel_market.cli import run, sign_test, spread
from hotel_market.customer import Customer, demo, load
from hotel_market.detect import SEATS_UP, moment_index
from hotel_market.plan import HOLD
from hotel_market.schedule import DEFAULT_SCENARIO
from hotel_market.sources import Event
from hotel_market.world import FILING_TICK, SIM_DAYS, arrival_tick, news_tick

FILING_DAY = DEFAULT_SCENARIO.filing_days()[0]  # the day-20 filing, the new flights


def find_event(customer: Customer, name: str) -> Event:
    """The customer's event with this name, case aside."""
    for event in customer.events:
        if event.name.lower() == name.lower():
            return event
    raise SystemExit(f"{customer.name} has no event named {name!r}")


def filing_moment(customer: Customer, ticks: int) -> int:
    """The moment the day-20 filing lands at on this clock: the file's tick for it, else the
    filing slot."""
    tick = arrival_tick(dict(customer.filing_ticks).get(FILING_DAY, FILING_TICK), ticks)
    return moment_index(FILING_DAY, tick, ticks)


def seed_result(
    seed: int, ticks: int, out: Path, customer: Customer | None = None, event: Event | None = None
) -> dict:
    """One seed at one clock: the contribution change, the decisions and the accepted plans made
    at a tick other than the day's last, and the lag in ticks from the day-20 filing, or from the
    event's announcement, to the first accepted raise on the stay dates it changed, None when no
    such raise was accepted. With an event, also the rooms its hotels booked on its stay dates
    from the announcement to the first raise and the contribution on those stay dates against
    the fixed-rate run."""
    customer = customer or demo()
    out.mkdir(parents=True, exist_ok=True)
    fixed, books, agent = run(
        seed, out / f"seed{seed}.jsonl", out / "cache", customer=customer, ticks=ticks
    )
    change = sum(books.contribution(h) - fixed.contribution(h) for h in customer.hotels)
    off_last = [e for e in agent.entries if e.tick != ticks]
    found = {
        "seed": seed,
        "change": change,
        "off_last": len(off_last),
        "off_last_accepted": sum(e.action != HOLD for e in off_last),
    }
    if event is None:
        filing = filing_moment(customer, ticks)
        raises = [
            moment_index(e.day, e.tick, ticks)
            for e in agent.entries
            if e.action != HOLD
            and SEATS_UP in e.causes
            and "raise" in e.action
            and moment_index(e.day, e.tick, ticks) >= filing
        ]
        found["lag"] = min(raises) - filing if raises else None
        return found
    announced = moment_index(event.known_day, news_tick(event.known_tick, ticks, ticks), ticks)
    stays = list(range(event.start_day, event.end_day + 1))
    hotels = [customer.hotel(key) for key in event.hotels]
    raises = [
        moment_index(e.day, e.tick, ticks)
        for e in agent.entries
        if e.action != HOLD
        and "raise" in e.action
        and e.hotel in event.hotels
        and set(e.new_rates) & set(stays)
        and moment_index(e.day, e.tick, ticks) >= announced
    ]
    first = min(raises) if raises else None
    last = first if first is not None else moment_index(SIM_DAYS - 1, ticks, ticks)
    rooms = 0
    for moment in range(announced, last + 1):
        day, tick = divmod(moment, ticks)
        rooms += int(sum(books.tick_rooms[day, tick, h.row, stays].sum() for h in hotels))
    found["lag"] = first - announced if first is not None else None
    found["rooms_before_raise"] = rooms
    found["earned"] = sum(
        books.contribution(h, stays) - fixed.contribution(h, stays) for h in hotels
    )
    return found


def sweep(
    first: int,
    last: int,
    ticks: int,
    out: Path,
    customer: Customer | None = None,
    event: Event | None = None,
) -> dict:
    """One row of the table: the seeds at one clock, summed or averaged."""
    out.mkdir(parents=True, exist_ok=True)
    results = [seed_result(seed, ticks, out, customer, event) for seed in range(first, last + 1)]
    lags = [r["lag"] for r in results if r["lag"] is not None]
    row = {
        "ticks": ticks,
        "changes": [r["change"] for r in results],
        "off_last": sum(r["off_last"] for r in results),
        "off_last_accepted": sum(r["off_last_accepted"] for r in results),
        "raised": len(lags),
        "lag": statistics.mean(lags) if lags else None,
    }
    if event is not None:
        row["rooms_before_raise"] = statistics.mean(r["rooms_before_raise"] for r in results)
        row["earned"] = statistics.mean(r["earned"] for r in results)
    return row


def money(value: float) -> str:
    return f"{'-' if value < 0 else '+'}${abs(value):,.0f}"


def _number(value: float) -> str:
    return "n/a" if value != value else f"{value:,.0f}"


def _p(values: list[float]) -> str:
    p = sign_test(values)
    return "n/a" if p != p else ("<0.001" if p < 0.001 else f"{p:#.2g}")


def table(rows: list[dict], subject: str = "the day-20 filing") -> str:
    """The rows as a markdown table, then the paired difference between the last row and the
    first, the finer clock's change minus the daily one's seed by seed. The subject names what
    the lag is counted from; an event's rows carry the two columns of what its stay dates did."""
    with_event = "earned" in rows[0]
    lines = [
        "| Ticks a day | Mean change a seed | SD | SE | Range | Ahead | p | Decisions off the "
        f"last tick | Accepted off the last tick | Seeds with a raise after {subject} | "
        "Mean lag in ticks |"
        + (
            " Rooms booked on its stay dates before the first raise | Contribution on its stay "
            "dates against the fixed-rate run |"
            if with_event
            else ""
        ),
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
        + (" ---: | ---: |" if with_event else ""),
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
            + (
                f" {row['rooms_before_raise']:,.1f} | {money(row['earned'])} |"
                if with_event
                else ""
            )
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
    parser.add_argument(
        "--customer",
        type=Path,
        metavar="FILE",
        help="the market's customer file (default: customers/demo.toml)",
    )
    parser.add_argument(
        "--event",
        metavar="NAME",
        help="count the lag from this event's announcement instead of the day-20 filing, and "
        "add what its stay dates booked and earned",
    )
    args = parser.parse_args(argv)
    if args.ticks < 2:
        parser.error("--ticks: the finer clock has two ticks a day or more")
    customer = load(args.customer) if args.customer else demo()
    event = find_event(customer, args.event) if args.event else None
    with tempfile.TemporaryDirectory() as folder:
        rows = [
            sweep(*args.seeds, ticks, Path(folder) / f"ticks-{ticks}", customer, event)
            for ticks in (1, args.ticks)
        ]
    subject = "the day-20 filing" if event is None else f"the {event.name.lower()} announcement"
    print(table(rows, subject))


if __name__ == "__main__":
    main()
