"""cli.py

The hotel-market command (also `python -m hotel_market`). It runs the simulation twice with one
seed. The first run has fixed rates, and in the second the agent decides after each of days 0 to
59. It writes decisions.jsonl and prints each day's queue sorted by value at stake. It ends with
room revenue and contribution per hotel for both runs over stay dates 0 to 149. The same table
follows over only the hotel and stay-date pairs where the agent changed a rate.

    hotel-market --seed 7                      both runs
    hotel-market --seed 7 --replay 20          day 20's queue again, from the cache
    hotel-market --seed 7 --template           the template, even with an API key set
    hotel-market --seeds 1 20                  seeds 1 to 20, with the template
    hotel-market --seed 7 --elasticity learn:1.0
                                               the agent learns its elasticity from the
                                               bookings, starting from 1.0
    hotel-market --seeds 1 20 --elasticity true --elasticity learn:1.0
                                               one arm per mode, side by side
    hotel-market --seeds 1 20 --elasticity learn:1.0 --cautious
                                               the learning agent acts only where a
                                               change beats holding one standard
                                               error either side of its estimate
    hotel-market run-day --seed 7 --as-of 20   store day 20's feeds in hotel_market.duckdb,
                                               run the agent on the tables and store its
                                               flags, plans and decisions
    hotel-market replay --as-of 20             day 20's queue again, rebuilt from the
                                               stored tables alone
    hotel-market bench --seeds 1 3             the reviewers benchmarked: for each seed
                                               and mode the template, the oracle and each
                                               model decide the same queues
    hotel-market bench --seeds 1 20 --template the template and the oracle only, offline

With ANTHROPIC_API_KEY set, the agent asks Claude. Otherwise a template writes the reasons. The
option --elasticity is true, fixed:X or learn:X. The default is true, where the agent prices with
the simulator's own value.

The option --cautious applies to every learn arm of the command. The option --customer names the
market's file, customers/demo.toml by default. The option --target overrides its target,
"contribution" or "revenue".

The bench command (bench.py) runs the fixed-rate run once per seed. It then runs one agent run
per mode and reviewer, each in its own cache folder. It prints one table per mode with a row per
reviewer, then a ranking over the mismatched modes.

The two daily commands run the agent one day at a time against the tables of sql/schema.sql
(stored.py). The command run-day plays the simulator to the day with the rate changes already
stored. It writes the day's feeds, runs the agent on the tables and writes its rows. Running a
day twice leaves the tables as they were. The command replay rebuilds a day's plans from the
tables alone, with the actions the stored decisions record. It checks them against the stored
plans.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

from hotel_market import stored
from hotel_market.agent import MIN_STAY, TRUE_MODE, Advice, Agent, ElasticityMode
from hotel_market.bench import (
    ORACLE,
    TEMPLATE,
    DeclineCounts,
    Reviewer,
    cost,
    counted,
    invalid_answers,
    live,
    recovered_share,
    regret,
)
from hotel_market.bookings import Books, simulate
from hotel_market.customer import TARGETS, Customer, demo, demo_path, load
from hotel_market.detect import NEW_EVENT, SEATS_UP
from hotel_market.estimate import Estimate
from hotel_market.model import MODELS, ClaudeClient, Client
from hotel_market.plan import DAY_NAMES, HOLD, Entry, Pricing
from hotel_market.schedule import HORIZON_DAYS
from hotel_market.simulated import deciding, simulated_sources
from hotel_market.text import capitalize_first, money_range, pace_text, percent_range, stay_range
from hotel_market.world import SIM_DAYS, Hotel

REPORT_DAYS = (10, 20, 30, 40, 59)  # the days a sweep reports a learn arm's estimates for
# The causes that mark a plan as raised by the convention or the new flights; a sweep
# reports the gain on those plans apart from the rest.
SHOCK_PLAN_CAUSES = frozenset({NEW_EVENT, SEATS_UP})
DAILY_COMMANDS = ("run-day", "replay")  # the commands that work through the stored tables
DEFAULT_DB = Path("hotel_market.duckdb")  # where they keep the tables
# The bench's default modes: two where the code's elasticity is wrong, and the true one.
BENCH_MODES = ("fixed:1.0", "fixed:2.0", "true")

# ---- the three things the command can do ----------------------------------


def run(
    seed: int,
    out: Path = Path("decisions.jsonl"),
    cache_dir: Path = Path("cache"),
    client: Client | None = None,
    mode: ElasticityMode = TRUE_MODE,
    customer: Customer | None = None,
) -> tuple[Books, Books, Agent]:
    """The fixed-rate run, the agent run, and the agent. Writes decisions.jsonl."""
    customer = customer or demo()
    fixed = simulate(seed, customer=customer)
    agent = Agent(seed, cache_dir, client, elasticity=mode, customer=customer)
    books = simulate(seed, deciding(agent), customer=customer)
    out.write_text("".join(json.dumps(line) + "\n" for line in agent.log))
    return fixed, books, agent


def replay(
    seed: int,
    day: int,
    cache_dir: Path = Path("cache"),
    client: Client | None = None,
    mode: ElasticityMode = TRUE_MODE,
    customer: Customer | None = None,
) -> tuple[list[Entry], list[Advice]]:
    """A day's entries and advice, rebuilt without a model call. They come from the cache when there
    is a client, else from the template.
    """
    customer = customer or demo()
    agent = Agent(seed, cache_dir, client, replay=True, elasticity=mode, customer=customer)
    simulate(seed, deciding(agent), last_day=day, customer=customer)
    return (
        [entry for entry in agent.entries if entry.day == day],
        [advice for advice in agent.advice if advice.day == day],
    )


# ---- the daily commands: the agent against stored tables ------------------


def run_days(
    seed: int,
    first: int,
    last: int,
    db: Path = DEFAULT_DB,
    cache_dir: Path = Path("cache"),
    client: Client | None = None,
    mode: ElasticityMode = TRUE_MODE,
    customer: Customer | None = None,
) -> tuple[list[Entry], list[Advice]]:
    """Days first to last through the stored tables, in one pass of the simulator.

    The simulator stands in for the hotel's feeds. It plays the days before `first` with the rate
    changes the tables already hold. On each day from `first` to `last`, its position is written to
    the feed tables as that day's snapshot. A fresh agent then picks up the state the stored
    decisions left and decides the day from the tables alone. Its flags, plans and decisions are
    written. Returns the last day's entries and advice.
    """
    customer = customer or demo()
    connection = stored.connect(db)
    missing = sorted(set(range(first)) - set(stored.stored_days(connection)))
    if missing:
        connection.close()
        raise ValueError(
            f"{db} holds no day {missing[0]}; the days before {first} must be run first"
        )
    earlier = stored.rate_changes_before(connection, first)
    outcome: dict[str, list] = {"entries": [], "advice": []}

    def decide(day: int, books: Books) -> dict[tuple[str, int], float]:
        if day < first:
            return earlier.get(day, {})
        feed = simulated_sources(books)
        if day == 0:
            stored.write_snapshot(connection, stored.OPENING_DAY, feed, customer)
        stored.write_snapshot(connection, day, feed, customer)
        agent = Agent(seed, cache_dir, client, elasticity=mode, customer=customer)
        agent.resume(*stored.state_before(connection, day))
        changes = agent.decide(day, stored.stored_sources(connection, customer))
        stored.write_decisions(connection, day, agent.entries, agent.advice)
        outcome["entries"], outcome["advice"] = agent.entries, agent.advice
        return changes

    try:
        simulate(seed, decide, last_day=last, customer=customer)
    finally:
        connection.close()
    return outcome["entries"], outcome["advice"]


def run_day(
    seed: int, day: int, db: Path = DEFAULT_DB, **settings
) -> tuple[list[Entry], list[Advice]]:
    """One day through the stored tables; the days before it must be there already."""
    return run_days(seed, day, day, db, **settings)


def replay_day(
    day: int,
    db: Path = DEFAULT_DB,
    mode: ElasticityMode = TRUE_MODE,
    customer: Customer | None = None,
) -> tuple[list[Entry], list[Advice], list[str]]:
    """A day's entries and advice rebuilt from the stored tables alone, with the actions the stored
    decisions record. The third value is how the rebuilt plans differ from the stored ones, empty
    when they match. Neither the simulator nor the model is involved, and nothing is written."""
    customer = customer or demo()
    connection = stored.connect(db, read_only=True)
    try:
        decided = stored.decided_on(connection, day)
        if day not in stored.stored_days(connection):
            raise LookupError(f"{db} holds no day {day}; run it first")
        agent = Agent(0, elasticity=mode, customer=customer)  # no cache: nothing is asked
        agent.resume(*stored.state_before(connection, day))
        sources = stored.stored_sources(connection, customer)
        entries = agent.plans_for(day, sources)
        for entry in entries:
            key = (entry.hotel, entry.first_stay, entry.last_stay)
            if key not in decided:
                raise LookupError(
                    f"{db} holds no decision for {entry.hotel} {entry.id} on day {day}"
                )
            entry.action, entry.reason, entry.reason_source = decided[key]
        advice = agent.advice_for(day, entries, sources)
        differences = stored.plan_differences(connection, day, entries)
    finally:
        connection.close()
    return entries, advice, differences


@dataclass(frozen=True)
class SeedResult:
    """One seed of a sweep: the agent run against the fixed-rate run, over stay dates 0 to 149."""

    seed: int
    contribution_change: float
    revenue_change: float
    rate_changes: int  # how many plans changed a rate
    estimated: float = 0.0  # what the accepted plans were estimated to earn over holding
    estimates: dict[tuple[int, str], Estimate] = field(default_factory=dict)  # learn only
    rejected_at_an_end: int = 0  # cautious only: candidates the band rejected
    shock_changes: int = 0  # plans raised by the convention or the new flights that changed a rate
    shock_gain: float = 0.0  # the target's change on the stay dates those plans changed
    other_changes: int = 0  # every other plan that changed a rate
    other_gain: float = 0.0  # the target's change on the stay dates only those changed
    entries: list[Entry] = field(default_factory=list)  # the run's entries, for the bench
    calls: list[dict] = field(default_factory=list)  # the arm's call records (model.Measured)
    counts: DeclineCounts = field(default_factory=DeclineCounts)  # the oracle's labels on the run


@dataclass(frozen=True)
class ArmResult:
    """One elasticity mode and one reviewer over the seeds of a sweep."""

    mode: ElasticityMode
    seeds: list[SeedResult]
    target: str = "contribution"  # what the agent scored on; wins and realised count it
    reviewer: Reviewer = TEMPLATE

    @property
    def changes(self) -> list[float]:
        return [result.contribution_change for result in self.seeds]

    @property
    def revenue_changes(self) -> list[float]:
        return [result.revenue_change for result in self.seeds]

    @property
    def target_changes(self) -> list[float]:
        """Each seed's change in the target: contribution, or room revenue."""
        return self.changes if self.target == "contribution" else self.revenue_changes

    @property
    def wins(self) -> int:
        """Seeds where the agent run earned more of the target than the fixed-rate run."""
        return sum(change > 0 for change in self.target_changes)

    @property
    def rate_changes(self) -> int:
        return sum(result.rate_changes for result in self.seeds)

    @property
    def estimated(self) -> float:
        return sum(result.estimated for result in self.seeds)

    @property
    def realised(self) -> float:
        return sum(self.target_changes)

    @property
    def rejected_at_an_end(self) -> int:
        return sum(result.rejected_at_an_end for result in self.seeds)

    @property
    def shock_changes(self) -> int:
        return sum(result.shock_changes for result in self.seeds)

    @property
    def shock_gain(self) -> float:
        return sum(result.shock_gain for result in self.seeds)

    @property
    def other_changes(self) -> int:
        return sum(result.other_changes for result in self.seeds)

    @property
    def other_gain(self) -> float:
        return sum(result.other_gain for result in self.seeds)

    def estimates_on(self, day: int, hotels: Sequence[Hotel]) -> dict[str, list[float]]:
        """Each hotel's learned elasticity on a day, one value per seed."""
        return {
            hotel.key: [result.estimates[(day, hotel.key)].elasticity for result in self.seeds]
            for hotel in hotels
        }

    @property
    def counts(self) -> DeclineCounts:
        """The decline counts pooled over the seeds."""
        return sum((result.counts for result in self.seeds), DeclineCounts())

    @property
    def calls(self) -> list[dict]:
        return [call for result in self.seeds for call in result.calls]


def sweep(
    first: int,
    last: int,
    cache_dir: Path = Path("cache"),
    modes: Sequence[ElasticityMode] = (TRUE_MODE,),
    customer: Customer | None = None,
    reviewers: Sequence[Reviewer] = (TEMPLATE,),
) -> list[ArmResult]:
    """Seeds first to last: one fixed-rate run per seed, and one agent run per seed, mode and
    reviewer. Each agent run is compared with the fixed-rate run. The arms come mode by mode, a
    reviewer at a time. Each arm has its own cache folder, because the agent is given the
    reviewer's model. Each seed keeps its entries, its call records and the oracle's labels on
    it.
    """
    customer = customer or demo()
    hotels = customer.hotels
    arms: dict[tuple[ElasticityMode, Reviewer], list[SeedResult]] = {
        (mode, reviewer): [] for mode in modes for reviewer in reviewers
    }
    for seed in range(first, last + 1):
        fixed = simulate(seed, customer=customer)
        for mode, reviewer in arms:
            agent = Agent(seed, cache_dir, elasticity=mode, customer=customer, model=reviewer.model)
            agent.client = reviewer.client_for(agent)
            books = simulate(seed, deciding(agent), customer=customer)
            accepted = [entry for entry in agent.entries if entry.action != HOLD]
            shock = [entry for entry in accepted if SHOCK_PLAN_CAUSES & set(entry.causes)]
            other = [entry for entry in accepted if entry not in shock]
            shock_pairs = {(e.hotel, s) for e in shock for s in e.new_rates}
            other_pairs = {(e.hotel, s) for e in other for s in e.new_rates} - shock_pairs
            arms[(mode, reviewer)].append(
                SeedResult(
                    seed,
                    sum(books.contribution(h) - fixed.contribution(h) for h in hotels),
                    sum(books.room_revenue(h) - fixed.room_revenue(h) for h in hotels),
                    len(accepted),
                    sum(entry.value_at_stake for entry in accepted),
                    dict(agent.estimates),
                    sum(entry.rejected_at_an_end for entry in agent.entries),
                    len(shock),
                    _gain_on(fixed, books, shock_pairs, hotels, customer.target),
                    len(other),
                    _gain_on(fixed, books, other_pairs, hotels, customer.target),
                    list(agent.entries),
                    _calls(agent),
                    DeclineCounts.of(agent.entries, customer),
                )
            )
    return [
        ArmResult(mode, results, customer.target, reviewer)
        for (mode, reviewer), results in arms.items()
    ]


def _calls(agent: Agent) -> list[dict]:
    """The arm's call records that count. They come from the calls.jsonl in its cache folder, which
    every run of the arm appends to. Without the file, they are what a measured client kept in
    memory. bench.counted keeps one record per request. It keeps only a request whose answer the
    cache holds or that failed."""
    path = agent.cache_dir / "calls.jsonl"
    if path.exists():
        records = [json.loads(line) for line in path.read_text().splitlines() if line]
    else:
        records = list(getattr(agent.client, "calls", []))
    return counted(records, agent.cache_dir)


def _gain_on(
    fixed: Books,
    books: Books,
    pairs: set[tuple[str, int]],
    hotels: Sequence[Hotel],
    target: str = "contribution",
) -> float:
    """The agent run's gain in the target over the fixed-rate run, on (hotel key, stay day) pairs.
    The target is contribution, or room revenue under a revenue target.
    """
    measure = Books.contribution if target == "contribution" else Books.room_revenue
    total = 0.0
    for hotel in hotels:
        stays = sorted(stay for key, stay in pairs if key == hotel.key)
        total += measure(books, hotel, stays) - measure(fixed, hotel, stays)
    return total


# ---- the queue, as printed ------------------------------------------------


def queue(entries: list[Entry]) -> list[Entry]:
    """The entries whose plan is worth at least the minimum, highest value at stake first."""
    return sorted(
        (entry for entry in entries if entry.queued), key=lambda entry: -entry.value_at_stake
    )


def format_line(entry: Entry) -> str:
    """One line of a day's queue."""
    action = entry.action if entry.action != HOLD else f"hold (declined: {entry.plan})"
    return (
        f"  {entry.value_at_stake:>+10,.0f}  {entry.hotel:12}  {entry.id:>7}  "
        f"{', '.join(entry.causes):34}  {action}"
    )


def format_advice(advice: Advice) -> str:
    return f"  {'advice':>10}  {advice.hotel:12}  {advice.stay_day:>7}  {MIN_STAY} (not simulated)"


def format_entry(entry: Entry, customer: Customer | None = None) -> str:
    """One queue entry in full, as the revenue manager reads it."""
    hotel = (customer or demo()).hotel(entry.hotel)
    numbers = entry.numbers
    return "\n".join(
        [
            f"Day {entry.day} | {hotel.name} | {stay_range(entry.first_stay, entry.last_stay)}",
            f"  What changed    {', '.join(entry.causes)}",
            f"  Seats           {percent_range(numbers.seat_revision)} against yesterday's "
            f"schedule, {percent_range(numbers.seat_change)} against the original",
            f"  Bookings        {numbers.rooms_on_books:,} rooms on the books, "
            f"{numbers.unsold_rooms:,} unsold, {pace_text(numbers.pace_gap)}",
            f"  Competitors     comp median {money_range(numbers.comp_median)}, our rate "
            f"{percent_range(numbers.rate_vs_median)} against it",
            f"  By day of week  {_weekday_summary(entry)}",
            f"  Elasticity      {_pricing_text(entry.pricing)}",
            f"  Action          {_action_text(entry, hotel)}",
            f"  Value at stake  ${entry.value_at_stake:,.0f} of contribution against holding",
            f"  Reason          {entry.reason}",
        ]
    )


def _weekday_summary(entry: Entry) -> str:
    """The best candidate for each day: "Mon raise 10% (+$2,867) | Tue hold | ...". Under
    the cautious rule, also what the change earns at the band's ends."""
    parts = []
    for group in entry.weekdays:
        part = f"{DAY_NAMES[group.weekday]} {group.best.name}"
        if group.best.name != HOLD:
            part += f" (+${group.gain:,.0f}"
            if group.cautious:
                low, _, high = group.gains(group.best)
                part += f", {low:+,.0f} to {high:+,.0f} across the band"
            part += ")"
        parts.append(part)
    return " | ".join(parts)


def _pricing_text(pricing: Pricing) -> str:
    """The elasticity the estimates assume, and where it came from."""
    if pricing.mode == "learn":
        text = (
            f"{pricing.elasticity:.2f}, learned from {pricing.observations:,} observations "
            f"(standard error {pricing.standard_error:.2f}, prior {pricing.prior:g})"
        )
        if pricing.cautious:
            low, high = pricing.band
            text += f"; cautious: a change must also win at {low:.2f} and at {high:.2f}"
        return text
    if pricing.mode == "fixed":
        return f"{pricing.elasticity:g}, fixed for the run"
    return f"{pricing.elasticity:g}, the simulator's own value"


def _action_text(entry: Entry, hotel: Hotel) -> str:
    if entry.action == HOLD:
        return f"Hold: the plan ({entry.plan}) was declined"
    changed = sorted(entry.new_rates)
    old = money_range(entry.current_rates[stay_day] for stay_day in changed)
    new = money_range(entry.new_rates.values())
    dates = f"{len(changed)} stay date{'s' if len(changed) != 1 else ''}"
    return (
        f"{capitalize_first(entry.plan)}: {old} becomes {new} on {dates}, "
        f"inside the ${hotel.floor:,.0f} to ${hotel.ceiling:,.0f} limits"
    )


# ---- the summary at the end -----------------------------------------------


@dataclass(frozen=True)
class Comparison:
    """Room revenue and contribution for both runs, for one hotel or for all four."""

    name: str
    fixed_revenue: float
    agent_revenue: float
    fixed_contribution: float
    agent_contribution: float

    @property
    def revenue_change(self) -> float:
        return self.agent_revenue - self.fixed_revenue

    @property
    def contribution_change(self) -> float:
        return self.agent_contribution - self.fixed_contribution


def changed_stays(agent: Agent) -> dict[str, list[int]]:
    """The stay dates whose rate the agent changed at least once, by hotel key."""
    pairs = {(e.hotel, s) for e in agent.entries if e.action != HOLD for s in e.new_rates}
    return {h.key: sorted(s for key, s in pairs if key == h.key) for h in agent.customer.hotels}


def summary(seed: int, fixed: Books, books: Books, agent: Agent) -> str:
    """Both runs compared over every stay date, then over only the ones the agent changed."""
    hotels = agent.customer.hotels
    changed = changed_stays(agent)
    pairs = sum(len(stays) for stays in changed.values())
    whole = [_compare(h.name, h, fixed, books, range(HORIZON_DAYS)) for h in hotels]
    touched = [
        _compare(f"{h.name} ({len(changed[h.key])})", h, fixed, books, changed[h.key])
        for h in hotels
    ]
    return "\n".join(
        _comparison_table(
            f"Room revenue and contribution over stay dates 0 to 149, seed {seed}", whole
        )
        + [""]
        + _comparison_table(
            f"The same, over only the {pairs} hotel and stay-date pairs where the agent "
            f"changed a rate (pairs per hotel in brackets)",
            touched,
        )
        + ["", _flag_counts(agent), _mode_text(agent)]
        + ([_target_text(agent)] if not agent.customer.scores_contribution() else [])
    )


def _compare(
    name: str, hotel: Hotel, fixed: Books, books: Books, stays: Sequence[int]
) -> Comparison:
    return Comparison(
        name,
        fixed.room_revenue(hotel, stays),
        books.room_revenue(hotel, stays),
        fixed.contribution(hotel, stays),
        books.contribution(hotel, stays),
    )


def _comparison_table(title: str, rows: list[Comparison]) -> list[str]:
    """One row per hotel plus a total, as lines of text."""
    rows = rows + [_total(rows)]
    width = max(len(row.name) for row in rows) + 2
    lines = [
        title,
        f"{'':{width}}{'room revenue':>40}{'contribution':>48}",
        f"{'':{width}}{'fixed rates':>14}{'agent':>14}{'change':>12}"
        f"{'fixed rates':>14}{'agent':>14}{'change':>20}",
    ]
    for row in rows:
        change = row.contribution_change
        percent = f" ({change / row.fixed_contribution:+.1%})" if row.fixed_contribution else ""
        lines.append(
            f"{row.name:{width}}"
            f"{row.fixed_revenue:>14,.0f}{row.agent_revenue:>14,.0f}{row.revenue_change:>+12,.0f}"
            f"{row.fixed_contribution:>14,.0f}{row.agent_contribution:>14,.0f}"
            f"{f'{change:+,.0f}{percent}':>20}"
        )
    return lines


def _total(rows: list[Comparison]) -> Comparison:
    return Comparison(
        "All four hotels",
        sum(row.fixed_revenue for row in rows),
        sum(row.agent_revenue for row in rows),
        sum(row.fixed_contribution for row in rows),
        sum(row.agent_contribution for row in rows),
    )


def _flag_counts(agent: Agent) -> str:
    """How the flags ended: a rate change, or a hold for one of three reasons."""
    entries = agent.entries
    changed = sum(1 for e in entries if e.action != HOLD)
    declined = sum(1 for e in entries if e.queued and e.action == HOLD)
    under_minimum = sum(1 for e in entries if e.changed_weekdays and not e.queued)
    unbeaten = sum(1 for e in entries if not e.changed_weekdays)
    return (
        f"Days 0 to 59: {len(entries)} flags. {changed} changed a rate; "
        f"{unbeaten + under_minimum + declined} held ({unbeaten} where no change beat hold, "
        f"{under_minimum} worth under the minimum, {declined} declined by the model). "
        f"{len(agent.advice)} minimum-stay advice, not simulated."
    )


def _mode_text(agent: Agent) -> str:
    """How the agent priced its estimates, and in learn mode where its estimates ended."""
    mode = agent.elasticity
    if mode.kind == "fixed":
        return f"The agent priced every estimate with a fixed elasticity of {mode.value:g}."
    if mode.kind == "learn":
        last = max(day for day, _ in agent.estimates)
        ended = ", ".join(
            f"{h.key} {agent.estimates[(last, h.key)].elasticity:.2f} "
            f"(se {agent.estimates[(last, h.key)].standard_error:.2f})"
            for h in agent.customer.hotels
        )
        rule = (
            " and acting only where a change beat holding one standard error either side"
            if mode.cautious
            else ""
        )
        return (
            f"The agent learned its elasticity from the bookings, starting from {mode.value:g}"
            f"{rule}; on day {last} its estimates were {ended}."
        )
    return f"The agent priced every estimate with the simulator's own elasticity, {mode.value:g}."


def _target_text(agent: Agent) -> str:
    return (
        f"The agent scored every candidate on {agent.customer.target}, as the customer file "
        f"{agent.customer.name!r} asks; the fixed-rate comparison above reports both measures."
    )


# ---- the command line -----------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] and argv[0] in DAILY_COMMANDS:
        _daily_main(argv)
        return
    if argv[:1] == ["bench"]:
        _bench_main(argv[1:])
        return
    args = _parse_args(argv)
    customer = _customer(args)
    if args.seeds:
        _print_sweep(*args.seeds, args.modes, customer)
    elif args.replay is not None:
        _print_replay(args.seed, args.replay, _client(args.template), args.modes[0], customer)
    else:
        _print_run(args.seed, _client(args.template), args.modes[0], customer)


def _customer(args: argparse.Namespace) -> Customer:
    customer = load(args.customer) if args.customer else demo()
    return replace(customer, target=args.target) if args.target else customer


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hotel-market",
        description="Run the hotel market with fixed rates and with the agent.",
        epilog="hotel-market run-day and hotel-market replay run the agent one day at a time "
        "against stored tables; see hotel-market run-day --help.",
    )
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--seed", type=_seed)
    which.add_argument(
        "--seeds",
        type=_seed,
        nargs=2,
        metavar=("FIRST", "LAST"),
        help="run a range of seeds with the template and summarise the contribution change",
    )
    parser.add_argument(
        "--replay", type=int, metavar="DAY", help="print a day's queue from the cache"
    )
    parser.add_argument(
        "--template", action="store_true", help="use the template even if an API key is set"
    )
    parser.add_argument(
        "--elasticity",
        action="append",
        type=_mode,
        metavar="MODE",
        help="where the agent's elasticity comes from: true (the default), fixed:X or "
        "learn:X; with --seeds, repeat it to run one arm per mode",
    )
    parser.add_argument(
        "--cautious",
        action="store_true",
        help="in learn mode, change a rate only where the change beats holding one standard "
        "error either side of the estimate",
    )
    _add_customer_options(parser)
    args = parser.parse_args(argv)
    if args.seeds and args.seeds[0] > args.seeds[1]:
        parser.error("--seeds: FIRST must not be after LAST")
    if args.seed is not None and args.elasticity and len(args.elasticity) > 1:
        parser.error("--seed takes one --elasticity; --seeds takes several")
    if args.replay is not None and args.seed is None:
        parser.error("--replay needs --seed")
    if args.replay is not None and not 0 <= args.replay < SIM_DAYS:
        parser.error(f"--replay: the agent decides on days 0 to {SIM_DAYS - 1}")
    args.modes = args.elasticity or [TRUE_MODE]
    if args.cautious:
        if not any(mode.kind == "learn" for mode in args.modes):
            parser.error("--cautious applies to learn:X")
        args.modes = [
            replace(mode, cautious=True) if mode.kind == "learn" else mode for mode in args.modes
        ]
    return args


def _add_customer_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--customer",
        type=Path,
        metavar="FILE",
        help=f"the market's customer file (default: {demo_path_text()})",
    )
    parser.add_argument(
        "--target",
        choices=TARGETS,
        help="score candidates on this instead of what the customer file says",
    )


def _daily_main(argv: list[str]) -> None:
    args = _parse_daily_args(argv)
    customer = _customer(args)
    if args.command == "run-day":
        first = args.as_of if args.first is None else args.first
        entries, advice = run_days(
            args.seed,
            first,
            args.as_of,
            args.db,
            client=_client(args.template),
            mode=args.mode,
            customer=customer,
        )
        print("\n".join(_queue_lines(args.as_of, entries, advice)) or f"Day {args.as_of}: no flags")
        print(f"\nDay {args.as_of}'s feeds, flags, plans and decisions are in {args.db}.")
        return
    entries, advice, differences = replay_day(args.as_of, args.db, args.mode, customer)
    print(f"Day {args.as_of} queue, rebuilt from the tables in {args.db}\n")
    blocks = [format_entry(e, customer) for e in queue(entries)]
    blocks += [format_advice(a) for a in advice]
    print("\n\n".join(blocks) or "Nothing in the queue.")
    if differences:
        print("\nThe rebuilt plans differ from the stored plans:")
        print("\n".join(f"  {line}" for line in differences))
        sys.exit(1)
    print("\nThe rebuilt plans match the stored plans.")


def _parse_daily_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hotel-market",
        description="Run the agent one day at a time against the stored tables (sql/schema.sql).",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    run_day_parser = commands.add_parser(
        "run-day",
        help="store a day's feeds, run the agent on the tables and store its flags, plans "
        "and decisions",
    )
    run_day_parser.add_argument(
        "--seed", type=_seed, required=True, help="the seed of the simulated feeds"
    )
    run_day_parser.add_argument(
        "--from",
        dest="first",
        type=int,
        metavar="DAY",
        help="also run every day from this one to --as-of, in one pass (the days before "
        "--as-of must otherwise be in the tables already)",
    )
    run_day_parser.add_argument(
        "--template", action="store_true", help="use the template even if an API key is set"
    )
    replay_parser = commands.add_parser(
        "replay", help="rebuild a day's plans from the stored tables alone and print its queue"
    )
    for subparser in (run_day_parser, replay_parser):
        subparser.add_argument(
            "--as-of", dest="as_of", type=int, required=True, metavar="DAY", help="the day"
        )
        subparser.add_argument(
            "--db",
            type=Path,
            default=DEFAULT_DB,
            metavar="FILE",
            help=f"the DuckDB file holding the tables (default: {DEFAULT_DB})",
        )
        subparser.add_argument(
            "--elasticity",
            type=_mode,
            metavar="MODE",
            default=TRUE_MODE,
            help="where the agent's elasticity comes from: true (the default), fixed:X or learn:X",
        )
        subparser.add_argument(
            "--cautious", action="store_true", help="in learn mode, the cautious rule"
        )
        _add_customer_options(subparser)
    args = parser.parse_args(argv)
    if not 0 <= args.as_of < SIM_DAYS:
        parser.error(f"--as-of: the agent decides on days 0 to {SIM_DAYS - 1}")
    if args.command == "run-day" and args.first is not None and not 0 <= args.first <= args.as_of:
        parser.error("--from: a day from 0 to --as-of")
    if args.cautious and args.elasticity.kind != "learn":
        parser.error("--cautious applies to learn:X")
    args.mode = replace(args.elasticity, cautious=True) if args.cautious else args.elasticity
    return args


def _seed(text: str) -> int:
    """A seed for the random streams: a whole number, zero or more."""
    try:
        seed = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a whole number") from None
    if seed < 0:
        raise argparse.ArgumentTypeError(f"{text} is negative; a seed is zero or more")
    return seed


def demo_path_text() -> str:
    """The demo file's path for the help text, or where it would be looked for."""
    try:
        return str(demo_path())
    except FileNotFoundError:
        return "customers/demo.toml"


def _mode(text: str) -> ElasticityMode:
    try:
        return ElasticityMode.parse(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def _client(template: bool) -> Client | None:
    """Claude when an API key is set and the template was not asked for; otherwise no client."""
    if template or not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    return ClaudeClient()


def _print_run(seed: int, client: Client | None, mode: ElasticityMode, customer: Customer) -> None:
    fixed, books, agent = run(seed, client=client, mode=mode, customer=customer)
    for day in sorted({entry.day for entry in agent.entries}):
        lines = _queue_lines(day, agent.entries, agent.advice)
        if lines:
            print("\n".join(lines))
    print()
    print(summary(seed, fixed, books, agent))


def _queue_lines(day: int, entries: list[Entry], advice: list[Advice]) -> list[str]:
    """A day's queue as the run prints it: a heading, then one line per queued entry and per advice.
    It is empty when the day has neither.
    """
    queued = queue([entry for entry in entries if entry.day == day])
    advised = [a for a in advice if a.day == day]
    if not queued and not advised:
        return []
    return (
        [f"Day {day} queue"]
        + [format_line(e) for e in queued]
        + [format_advice(a) for a in advised]
    )


def _print_replay(
    seed: int, day: int, client: Client | None, mode: ElasticityMode, customer: Customer
) -> None:
    entries, advice = replay(seed, day, client=client, mode=mode, customer=customer)
    print(f"Day {day} queue, replayed from the cache (seed {seed})\n")
    blocks = [format_entry(e, customer) for e in queue(entries)]
    blocks += [format_advice(a) for a in advice]
    print("\n\n".join(blocks) or "Nothing in the queue.")


def _print_sweep(
    first: int, last: int, modes: Sequence[ElasticityMode], customer: Customer
) -> None:
    arms = sweep(first, last, modes=modes, customer=customer)
    print(
        f"Seeds {first} to {last}: the agent run against the fixed-rate run, stay dates 0 to 149, "
        f"template reasons, candidates scored on {customer.target}"
    )
    if len(arms) == 1:
        print("\n".join(_seed_table(arms[0])))
    else:
        print("\n".join(_arm_table(arms)))
    print()
    print("\n".join(_source_table(arms)))
    for arm in arms:
        if arm.mode.kind == "learn":
            print()
            print("\n".join(_estimate_table(arm, customer.hotels)))


def _seed_table(arm: ArmResult) -> list[str]:
    """One arm, seed by seed, then the mean and range of both measures. The target's line adds the
    wins and the accepted plans' estimates against what they earned.
    """
    lines = [
        f"Elasticity {arm.mode}",
        f"{'seed':>4}{'contribution change':>22}{'revenue change':>18}{'rate changes':>15}",
        "",
    ]
    for r in arm.seeds:
        lines.insert(
            -1,
            f"{r.seed:>4}{r.contribution_change:>+22,.0f}{r.revenue_change:>+18,.0f}"
            f"{r.rate_changes:>15}",
        )
    outcome = (
        f"; higher than the fixed-rate run in {arm.wins} of {len(arm.seeds)} seeds. The accepted "
        f"plans were estimated to earn {arm.estimated:+,.0f} and earned {arm.realised:+,.0f}."
    )
    for name, changes in (("Contribution", arm.changes), ("Revenue", arm.revenue_changes)):
        lines.append(
            f"{name} change: mean {statistics.mean(changes):+,.0f}, range "
            f"{min(changes):+,.0f} to {max(changes):+,.0f}"
            + (outcome if name.lower() == arm.target else ".")
        )
    if arm.mode.cautious:
        lines.append(
            f"The cautious rule rejected {arm.rejected_at_an_end} candidates that were ahead "
            f"of hold at the estimate but lost to holding at one end of the band."
        )
    return lines


def _arm_table(arms: list[ArmResult]) -> list[str]:
    """Several arms side by side. Each row holds the mean change against the fixed-rate run, its
    range, the winning seeds and the rate changes. It also holds the estimates summed against the
    results and, for a cautious arm, the candidates its band rejected.
    """
    lines = [
        f"{'elasticity':18}{'mean change':>14}{'mean revenue':>14}{'range':>24}{'wins':>8}"
        f"{'rate changes':>14}{'estimated':>12}{'realised':>12}{'share':>8}"
        f"{'rejected at an end':>20}"
    ]
    for arm in arms:
        share = f"{arm.estimated / arm.realised:.2f}" if arm.realised else "n/a"
        rejected = str(arm.rejected_at_an_end) if arm.mode.cautious else "-"
        lines.append(
            f"{str(arm.mode):18}{statistics.mean(arm.changes):>+14,.0f}"
            f"{statistics.mean(arm.revenue_changes):>+14,.0f}"
            f"{f'{min(arm.changes):+,.0f} to {max(arm.changes):+,.0f}':>24}"
            f"{f'{arm.wins}/{len(arm.seeds)}':>8}{arm.rate_changes:>14}"
            f"{arm.estimated:>+12,.0f}{arm.realised:>+12,.0f}{share:>8}{rejected:>20}"
        )
    return lines


def _source_table(arms: list[ArmResult]) -> list[str]:
    """Where each arm's gain came from. The first group is the plans the convention and the new
    flights raised, and the second is every other plan. Each group shows its rate changes and the
    contribution change on the stay dates it changed, summed over the seeds.
    """
    lines = [
        "Where the gain came from: the plans raised by the convention and the new flights, "
        "then every other plan",
        f"{'elasticity':18}{'shock changes':>14}{'shock gain':>14}{'other changes':>14}"
        f"{'other gain':>14}",
    ]
    for arm in arms:
        lines.append(
            f"{str(arm.mode):18}{arm.shock_changes:>14}{arm.shock_gain:>+14,.0f}"
            f"{arm.other_changes:>14}{arm.other_gain:>+14,.0f}"
        )
    return lines


# ---- the bench --------------------------------------------------------------


def _bench_main(argv: list[str]) -> None:
    args = _parse_bench_args(argv)
    customer = _customer(args)
    reviewers = [TEMPLATE, ORACLE] + [live(model) for model in args.models]
    _print_bench(*args.seeds, args.modes, reviewers, customer)


def _parse_bench_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hotel-market bench",
        description="Benchmark the reviewers: for each seed and elasticity mode, the template, "
        "the oracle and each model decide the same queues, each against the fixed-rate run.",
    )
    parser.add_argument(
        "--seeds", type=_seed, nargs=2, metavar=("FIRST", "LAST"), required=True, help="the seeds"
    )
    parser.add_argument(
        "--elasticity",
        action="append",
        type=_mode,
        metavar="MODE",
        help=f"a mode to run every reviewer in; repeat it for several (default: "
        f"{', '.join(BENCH_MODES)})",
    )
    parser.add_argument(
        "--model",
        action="append",
        metavar="NAME",
        help=f"a model to review with; repeat it for several (default: {', '.join(MODELS)})",
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="the template and the oracle only, with no model, so the bench runs offline",
    )
    _add_customer_options(parser)
    args = parser.parse_args(argv)
    if args.seeds[0] > args.seeds[1]:
        parser.error("--seeds: FIRST must not be after LAST")
    if args.template and args.model:
        parser.error("--template runs no model; drop --model")
    args.modes = args.elasticity or [ElasticityMode.parse(text) for text in BENCH_MODES]
    args.models = [] if args.template else args.model or list(MODELS)
    if args.models and not os.environ.get("ANTHROPIC_API_KEY"):
        parser.error(
            "ANTHROPIC_API_KEY is not set; set it, or pass --template for the template and the "
            "oracle alone"
        )
    return args


def _print_bench(
    first: int,
    last: int,
    modes: Sequence[ElasticityMode],
    reviewers: Sequence[Reviewer],
    customer: Customer,
) -> None:
    arms = sweep(first, last, modes=modes, customer=customer, reviewers=reviewers)
    print(
        f"Seeds {first} to {last}: each reviewer against the fixed-rate run, stay dates 0 to 149, "
        f"candidates scored on {customer.target}. Regret is the oracle arm's mean change minus "
        f"the reviewer's; the rates are pooled over the seeds."
    )
    for mode in modes:
        print()
        print("\n".join(_bench_table(mode, [arm for arm in arms if arm.mode == mode])))
    print()
    mismatched = [mode for mode in modes if mode.kind != "true"]
    if mismatched:
        print(
            "\n".join(_ranking_table(mismatched, [arm for arm in arms if arm.mode in mismatched]))
        )
    else:
        print("No mismatched mode was run, so there is no ranking of the reviewers.")


_BENCH_HEADER = (
    f"{'reviewer':20}{'mean change':>13}{'range':>22}{'ahead':>8}{'regret':>10}{'recovered':>11}"
    f"{'accept':>8}{'precision':>11}{'recall':>8}{'F1':>8}{'$ recall':>10}{'invalid':>9}"
    f"{'calls':>7}{'tokens in/out':>18}{'median s':>10}{'cost':>9}"
)


def _bench_table(mode: ElasticityMode, arms: list[ArmResult]) -> list[str]:
    """One mode's arms, a row per reviewer. Each row holds the mean realised change and its range.
    It holds the seeds ahead of the fixed-rate run and the regret against the oracle arm.

    It also holds the recovered share of the oracle's gain over the template's and the accept
    rate. Then come the decline precision, recall, F1 and dollar-weighted recall. The last
    columns are the calls with a bad attempt. For a model they add its calls, tokens, median
    latency and list-price cost.
    """
    oracle = next(arm for arm in arms if arm.reviewer.name == ORACLE.name)
    template = next(arm for arm in arms if arm.reviewer.name == TEMPLATE.name)
    lines = [f"Elasticity {mode}: each reviewer against the fixed-rate run", _BENCH_HEADER]
    lines += [_bench_row(arm, oracle, template) for arm in arms]
    return lines


def _ranking_table(modes: Sequence[ElasticityMode], arms: list[ArmResult]) -> list[str]:
    """The reviewers pooled over the mismatched modes, the highest mean change first."""
    names = list(dict.fromkeys(arm.reviewer.name for arm in arms))
    pooled = []
    for name in names:
        own = [arm for arm in arms if arm.reviewer.name == name]
        seeds = [result for arm in own for result in arm.seeds]
        pooled.append(ArmResult(modes[0], seeds, own[0].target, own[0].reviewer))
    oracle = next(arm for arm in pooled if arm.reviewer.name == ORACLE.name)
    template = next(arm for arm in pooled if arm.reviewer.name == TEMPLATE.name)
    ranked = sorted(pooled, key=lambda arm: -statistics.mean(arm.target_changes))
    lines = [
        f"Across the mismatched modes ({', '.join(str(mode) for mode in modes)}): each reviewer "
        f"pooled over those arms, the highest mean change first",
        f"{'rank':>4}  {_BENCH_HEADER}",
    ]
    lines += [
        f"{rank:>4}  {_bench_row(arm, oracle, template)}" for rank, arm in enumerate(ranked, 1)
    ]
    return lines


def _bench_row(arm: ArmResult, oracle: ArmResult, template: ArmResult) -> str:
    changes = arm.target_changes
    mean, oracle_mean = statistics.mean(changes), statistics.mean(oracle.target_changes)
    counts = arm.counts
    calls = arm.calls
    is_live = arm.reviewer.live
    seconds = [float(call.get("seconds", 0.0)) for call in calls]
    median = f"{statistics.median(seconds):.1f}" if seconds else "-"
    return (
        f"{arm.reviewer.name:20}{mean:>+13,.0f}"
        f"{f'{min(changes):+,.0f} to {max(changes):+,.0f}':>22}"
        f"{f'{arm.wins}/{len(changes)}':>8}{regret(oracle_mean, mean):>+10,.0f}"
        f"{_rate(recovered_share(statistics.mean(template.target_changes), oracle_mean, mean)):>11}"
        f"{_rate(counts.accept_rate):>8}{_rate(counts.precision):>11}{_rate(counts.recall):>8}"
        f"{_rate(counts.f1):>8}{_rate(counts.dollar_recall):>10}"
        f"{invalid_answers(calls) if is_live else '-':>9}{len(calls) if is_live else '-':>7}"
        f"{_tokens(calls) if is_live else '-':>18}{median if is_live else '-':>10}"
        f"{_cost(calls, arm.reviewer.model) if is_live else '-':>9}"
    )


def _rate(value: float) -> str:
    return "-" if math.isnan(value) else f"{value:.2f}"


def _tokens(calls: list[dict]) -> str:
    tokens_in = sum(int(call.get("input_tokens", 0)) for call in calls)
    tokens_out = sum(int(call.get("output_tokens", 0)) for call in calls)
    return f"{tokens_in:,}/{tokens_out:,}"


def _cost(calls: list[dict], model: str | None) -> str:
    dollars = cost(calls, model or "")
    return "n/a" if math.isnan(dollars) else f"${dollars:.2f}"


def _estimate_table(arm: ArmResult, hotels: Sequence[Hotel]) -> list[str]:
    """A learn arm's estimate per hotel on the report days, as mean (lowest to highest)
    across the seeds."""
    lines = [
        f"Elasticity {arm.mode}: the estimate each hotel priced with, mean (lowest to highest) "
        f"across the seeds",
        f"{'day':>4}" + "".join(f"{h.key:>20}" for h in hotels),
    ]
    for day in REPORT_DAYS:
        if not all((day, h.key) in r.estimates for r in arm.seeds for h in hotels):
            continue
        cells = []
        for values in arm.estimates_on(day, hotels).values():
            cells.append(f"{statistics.mean(values):.2f} ({min(values):.2f} to {max(values):.2f})")
        lines.append(f"{day:>4}" + "".join(f"{cell:>20}" for cell in cells))
    return lines


if __name__ == "__main__":
    main()
