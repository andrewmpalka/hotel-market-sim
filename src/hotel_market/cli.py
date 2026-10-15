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
    hotel-market --seeds 1 20 --elasticity learn:1.0 --level
                                               the learning agent also scales its
                                               forecast by the fitted demand level
    hotel-market run-day --seed 7 --as-of 20   store day 20's feeds in hotel_market.duckdb,
                                               run the agent on the tables and store its
                                               flags, plans and decisions
    hotel-market replay --as-of 20             day 20's queue again, rebuilt from the
                                               stored tables alone
    hotel-market bench --seeds 1 3             the reviewers benchmarked: for each seed
                                               and mode the template, the oracle and each
                                               model decide the same queues
    hotel-market bench --seeds 1 20 --template the template and the oracle only, offline
    hotel-market --seeds 1 20 --demand-bias 0.9
                                               the simulator's demand multiplied by 0.9,
                                               which the agent never sees; the bench
                                               takes the option too
    hotel-market --seeds 1 20 --react          competitors follow the hotels' rate changes
                                               with a lag; the bench takes it too
    hotel-market --seeds 1 20 --react --market-elasticity 0.5
                                               the market's demand answers the comp
                                               median's level; the agent is told the value
    hotel-market --seeds 1 20 --scenario upgauge --churn
                                               another set of air-schedule filings, with
                                               weekly revisions below the threshold on top
    hotel-market --seeds 1 20 --policy pace    the agent's gain against a rule that prices
                                               on the pace flags, next to its gain against
                                               frozen rates

With ANTHROPIC_API_KEY set, the agent asks Claude. Otherwise a template writes the reasons. The
option --elasticity is true, fixed:X or learn:X. The default is true, where the agent prices with
the simulator's own value.

The options --cautious and --level apply to every learn arm of the command. The option
--customer names the market's file, customers/demo.toml by default. --target overrides its target,
"contribution" or "revenue". The option --demand-bias multiplies the simulator's demand in both
runs. The agent never receives it, and a biased run keeps its cache in a folder of its own. The
bench tells its oracle the bias, so the oracle stays the simulator's truth. The option --react
turns the competitors' reaction on in both runs (shops.py), and a reacting run keeps its cache in
a folder of its own too. The option --market-elasticity sets the market's response to the comp
median's level in both runs (demand.py). The agent is told it, every plan record carries it, and
the oracle re-scores with it and with the reaction's share, so it stays the ceiling. The option
--scenario picks the air schedule's filings (schedule.py), and --churn adds the seed's weekly
revisions below the detect threshold. Both keep their cache in folders of their own.

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
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

from hotel_market import stored
from hotel_market.agent import MIN_STAY, TRUE_MODE, Advice, Agent, ElasticityMode
from hotel_market.bench import (
    ORACLE,
    TEMPLATE,
    DeclineCounts,
    Reviewer,
    by_standard_error,
    cost,
    counted,
    invalid_answers,
    live,
    on_recent_changes,
    oracle,
    recovered_share,
    regret,
)
from hotel_market.bookings import Books, simulate
from hotel_market.customer import TARGETS, Customer, demo, demo_path, load
from hotel_market.demand import DEMAND_BIAS, MARKET_ELASTICITY
from hotel_market.detect import MEDIAN_DOWN, MEDIAN_UP, NEW_EVENT, PACE, SEATS_CUT, SEATS_UP
from hotel_market.estimate import Estimate, level_factor
from hotel_market.model import MODELS, ClaudeClient, Client
from hotel_market.plan import DAY_NAMES, HOLD, Entry, Pricing
from hotel_market.policy import POLICIES
from hotel_market.schedule import DEFAULT_SCENARIO, HORIZON_DAYS, SCENARIOS, Scenario
from hotel_market.shops import REACTION_LAG, REACTION_SHARE
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
# A reacting run reports the stay dates changed twice or more within this many days.
REPEAT_WINDOW = 14
MEDIAN_CAUSES = frozenset({MEDIAN_UP, MEDIAN_DOWN})
SEAT_CAUSES = frozenset({SEATS_UP, SEATS_CUT})  # the flags a filing raises

# ---- the three things the command can do ----------------------------------


def run(
    seed: int,
    out: Path = Path("decisions.jsonl"),
    cache_dir: Path = Path("cache"),
    client: Client | None = None,
    mode: ElasticityMode = TRUE_MODE,
    customer: Customer | None = None,
    demand_bias: float = DEMAND_BIAS,
    react: bool = False,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
) -> tuple[Books, Books, Agent]:
    """The fixed-rate run, the agent run, and the agent. Writes decisions.jsonl. The demand bias
    and the reaction go to both runs and never to the agent. The market elasticity goes to both
    runs and to the agent, which is told it. The scenario and the churn set the air schedule."""
    customer = customer or demo()
    world = _world(demand_bias, react, market_elasticity, scenario, churn)
    fixed = simulate(seed, customer=customer, **world)
    cache_dir = cache_root(cache_dir, demand_bias, react, market_elasticity, scenario, churn)
    agent = Agent(
        seed,
        cache_dir,
        client,
        elasticity=mode,
        customer=customer,
        market_elasticity=market_elasticity,
    )
    books = simulate(seed, deciding(agent), customer=customer, **world)
    out.write_text("".join(json.dumps(line) + "\n" for line in agent.log))
    return fixed, books, agent


def replay(
    seed: int,
    day: int,
    cache_dir: Path = Path("cache"),
    client: Client | None = None,
    mode: ElasticityMode = TRUE_MODE,
    customer: Customer | None = None,
    demand_bias: float = DEMAND_BIAS,
    react: bool = False,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
) -> tuple[list[Entry], list[Advice]]:
    """A day's entries and advice, rebuilt without a model call. They come from the cache when there
    is a client, else from the template.
    """
    customer = customer or demo()
    cache_dir = cache_root(cache_dir, demand_bias, react, market_elasticity, scenario, churn)
    agent = Agent(
        seed,
        cache_dir,
        client,
        replay=True,
        elasticity=mode,
        customer=customer,
        market_elasticity=market_elasticity,
    )
    world = _world(demand_bias, react, market_elasticity, scenario, churn)
    simulate(seed, deciding(agent), last_day=day, customer=customer, **world)
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
    observe: Callable[[int, Books, Agent], None] | None = None,
) -> tuple[list[Entry], list[Advice]]:
    """Days first to last through the stored tables, in one pass of the simulator.

    The simulator stands in for the hotel's feeds. It plays the days before `first` with the rate
    changes the tables already hold. On each day from `first` to `last`, its position is written to
    the feed tables as that day's snapshot. A fresh agent then picks up the state the stored
    decisions left and decides the day from the tables alone. Its flags, plans and decisions are
    written. observe, if given, sees each decided day's books and agent; the demo data uses it.
    Returns the last day's entries and advice.
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
        feed = simulated_sources(books, day)
        if day == 0:
            stored.write_snapshot(connection, stored.OPENING_DAY, feed, customer)
        stored.write_snapshot(connection, day, feed, customer)
        agent = Agent(seed, cache_dir, client, elasticity=mode, customer=customer)
        agent.resume(*stored.state_before(connection, day))
        changes = agent.decide(day, stored.stored_sources(connection, customer))
        stored.write_decisions(connection, day, agent.entries, agent.advice)
        outcome["entries"], outcome["advice"] = agent.entries, agent.advice
        if observe is not None:
            observe(day, books, agent)
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
    flags: int = 0  # the flags the run raised, one entry each
    pace_flags: int = 0  # those with a pace cause, ahead of or behind pace
    median_flags: int = 0  # those with a comp-median cause
    own_median_flags: int = 0  # react only: the comp-median flags the hotel's own change caused
    repeat_changes: int = 0  # stay dates changed twice or more within REPEAT_WINDOW days
    seat_flags: int = 0  # the flags with a seat cause
    filings: int = 0  # the days the airline filed something, through the last decided day
    control_change: float = 0.0  # --policy only: the rule's contribution change over fixed rates
    control_revenue_change: float = 0.0  # --policy only: the rule's room revenue change
    control_changes: int = 0  # --policy only: the (hotel, stay date) pairs the rule changed


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
    def flags(self) -> int:
        return sum(result.flags for result in self.seeds)

    @property
    def pace_flags(self) -> int:
        return sum(result.pace_flags for result in self.seeds)

    @property
    def median_flags(self) -> int:
        return sum(result.median_flags for result in self.seeds)

    @property
    def own_median_flags(self) -> int:
        return sum(result.own_median_flags for result in self.seeds)

    @property
    def repeat_changes(self) -> int:
        return sum(result.repeat_changes for result in self.seeds)

    @property
    def seat_flags(self) -> int:
        return sum(result.seat_flags for result in self.seeds)

    @property
    def control_changes(self) -> list[float]:
        """Each seed's change in the target for the rule-based control, against fixed rates."""
        if self.target == "contribution":
            return [result.control_change for result in self.seeds]
        return [result.control_revenue_change for result in self.seeds]

    @property
    def against_control(self) -> list[float]:
        """Each seed's change in the target against the rule-based control."""
        return [
            own - rule for own, rule in zip(self.target_changes, self.control_changes, strict=True)
        ]

    @property
    def filings(self) -> int:
        return sum(result.filings for result in self.seeds)

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
    demand_bias: float = DEMAND_BIAS,
    react: bool = False,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
    policy: str | None = None,
) -> list[ArmResult]:
    """Seeds first to last: one fixed-rate run per seed, and one agent run per seed, mode and
    reviewer. Each agent run is compared with the fixed-rate run. The arms come mode by mode, a
    reviewer at a time. Each arm has its own cache folder, because the agent is given the reviewer's
    model. Each seed keeps its entries, its call records and the oracle's labels on it. The demand
    bias and the reaction go to every run and to the oracle's labels, and never to the agent. The
    market elasticity goes to every run, to the agent and to the oracle's labels. The scenario and
    the churn set every run's schedule. With a policy, each seed also runs the rule-based control,
    and every seed result carries its change against fixed rates.
    """
    customer = customer or demo()
    hotels = customer.hotels
    cache_dir = cache_root(cache_dir, demand_bias, react, market_elasticity, scenario, churn)
    world = _world(demand_bias, react, market_elasticity, scenario, churn)
    truth = (demand_bias, market_elasticity, REACTION_SHARE if react else 0.0)  # the oracle's
    arms: dict[tuple[ElasticityMode, Reviewer], list[SeedResult]] = {
        (mode, reviewer): [] for mode in modes for reviewer in reviewers
    }
    for seed in range(first, last + 1):
        fixed = simulate(seed, customer=customer, **world)
        control = _control(seed, policy, fixed, customer, world)
        for mode, reviewer in arms:
            agent = Agent(
                seed,
                cache_dir,
                elasticity=mode,
                customer=customer,
                model=reviewer.model,
                market_elasticity=market_elasticity,
            )
            agent.client = reviewer.client_for(agent)
            books = simulate(seed, deciding(agent), customer=customer, **world)
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
                    DeclineCounts.of(agent.entries, customer, *truth),
                    flags=len(agent.entries),
                    pace_flags=sum(bool(PACE & set(entry.causes)) for entry in agent.entries),
                    median_flags=sum(
                        bool(MEDIAN_CAUSES & set(entry.causes)) for entry in agent.entries
                    ),
                    own_median_flags=own_median_flags(agent.entries, books),
                    repeat_changes=repeat_changes(agent.entries),
                    seat_flags=sum(bool(SEAT_CAUSES & set(e.causes)) for e in agent.entries),
                    filings=len(books.scenario.filing_days(SIM_DAYS - 1)),
                    **control,
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


def _world(
    demand_bias: float,
    react: bool,
    market_elasticity: float,
    scenario: Scenario,
    churn: bool,
) -> dict:
    """The simulator's settings for a run, as simulate() takes them."""
    return {
        "demand_bias": demand_bias,
        "react": react,
        "market_elasticity": market_elasticity,
        "scenario": scenario,
        "churn": churn,
    }


def _control(seed: int, policy: str | None, fixed: Books, customer: Customer, world: dict) -> dict:
    """The rule-based control's run for a seed, as the SeedResult fields it fills: its change in
    contribution and in room revenue against the fixed-rate run, and the pairs it changed. Empty
    without a policy."""
    if policy is None:
        return {}
    rule = POLICIES[policy](customer)
    books = simulate(seed, deciding(rule), customer=customer, **world)
    hotels = customer.hotels
    return {
        "control_change": sum(books.contribution(h) - fixed.contribution(h) for h in hotels),
        "control_revenue_change": sum(
            books.room_revenue(h) - fixed.room_revenue(h) for h in hotels
        ),
        "control_changes": rule.changed,
    }


def cache_root(
    cache_dir: Path,
    demand_bias: float,
    react: bool = False,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
) -> Path:
    """Where a run's arm folders go. A demand bias other than the default, the reaction, another
    scenario or the churn changes every request. Such runs therefore get a folder of their own
    under the cache. The agent's own folder name never carries them, because the agent never sees
    them. A market elasticity other than the default adds a folder of its own, nested under
    those."""
    parts = []
    if demand_bias != DEMAND_BIAS:
        parts.append(f"demand-bias-{demand_bias:g}")
    if react:
        parts.append("react")
    if scenario.name != DEFAULT_SCENARIO.name:
        parts.append(f"scenario-{scenario.name}")
    if churn:
        parts.append("churn")
    root = Path(cache_dir) / "-".join(parts) if parts else Path(cache_dir)
    if market_elasticity != MARKET_ELASTICITY:
        root = root / f"market-{market_elasticity:g}"
    return root


def own_median_flags(entries: Iterable[Entry], books: Books) -> int:
    """The flags with a comp-median cause that the hotel's own rate change caused, through the
    reaction. The comp median moves on the shop day that first reads a new rate, REACTION_LAG
    days after it took effect. A flag counts when one of its stay dates read a new rate that
    day. Without the reaction nothing counts."""
    if not books.react:
        return 0
    found = 0
    for entry in entries:
        if not MEDIAN_CAUSES & set(entry.causes) or entry.day <= REACTION_LAG:
            continue
        row = books.customer.hotel(entry.hotel).row
        read, before = entry.day - REACTION_LAG, entry.day - REACTION_LAG - 1
        stays = range(entry.first_stay, entry.last_stay + 1)
        if any(
            books.daily_rates[read, row, s] != books.daily_rates[before, row, s]
            and books.daily_rates[before, row, s]
            for s in stays
        ):
            found += 1
    return found


def repeat_changes(entries: Iterable[Entry], window: int = REPEAT_WINDOW) -> int:
    """The (hotel, stay date) pairs whose rate the run changed twice or more within the window:
    two accepted changes at most `window` days apart."""
    days: dict[tuple[str, int], list[int]] = {}
    for entry in entries:
        if entry.action == HOLD:
            continue
        for stay_day in entry.new_rates:
            days.setdefault((entry.hotel, stay_day), []).append(entry.day)
    return sum(
        any(later - earlier <= window for earlier, later in zip(changed, changed[1:]))
        for changed in (sorted(found) for found in days.values())
    )


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
        + ([_bias_text(books)] if books.demand_bias != DEMAND_BIAS else [])
        + ([_react_text()] if books.react else [])
        + ([_market_text(books)] if books.market_elasticity else [])
        + ([_schedule_text(books)] if books.scenario != DEFAULT_SCENARIO else [])
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


def _bias_text(books: Books) -> str:
    return (
        f"The simulator multiplied its demand by {books.demand_bias:g} in both runs. The agent "
        f"never saw the factor, so its forecast was off by it."
    )


def _schedule_text(books: Books) -> str:
    base = books.scenario.name.removesuffix("+churn")
    churn = ", with the seed's weekly revisions filed on top" if books.churn else ""
    return f"The air schedule ran the {base} scenario{churn} in both runs."


def _market_text(books: Books) -> str:
    return (
        f"The market's demand moved with the comp median's level at an elasticity of "
        f"{books.market_elasticity:g} in both runs, and the agent was told the value."
    )


def _react_text() -> str:
    return (
        f"Competitors reacted in both runs: {REACTION_LAG} days after a hotel's rate changed, each "
        f"moved {REACTION_SHARE:.0%} of the change from the start rate."
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
        if mode.level:
            levels = ", ".join(
                f"{h.key} {level_factor(agent.estimates[(last, h.key)]):.2f}"
                for h in agent.customer.hotels
            )
            rule += (
                f", and scaling its forecast by the fitted demand level ({levels} on day {last})"
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
    if argv[:1] == ["demo-data"]:
        from hotel_market import demo_data  # here, because demo_data imports run_days

        demo_data.main(argv[1:])
        return
    args = _parse_args(argv)
    customer = _customer(args)
    world = (
        args.demand_bias,
        args.react,
        args.market_elasticity,
        SCENARIOS[args.scenario],
        args.churn,
    )
    if args.seeds:
        _print_sweep(*args.seeds, args.modes, customer, *world, policy=args.policy)
    elif args.replay is not None:
        client = _client(args.template)
        _print_replay(args.seed, args.replay, client, args.modes[0], customer, *world)
    else:
        _print_run(args.seed, _client(args.template), args.modes[0], customer, *world, args.policy)


def _customer(args: argparse.Namespace) -> Customer:
    customer = load(args.customer) if args.customer else demo()
    return replace(customer, target=args.target) if args.target else customer


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hotel-market",
        description="Run the hotel market with fixed rates and with the agent.",
        epilog="hotel-market run-day and hotel-market replay run the agent one day at a time "
        "against stored tables; see hotel-market run-day --help. hotel-market demo-data writes "
        "the demo page's file; see hotel-market demo-data --help.",
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
    parser.add_argument(
        "--level",
        action="store_true",
        help="in learn mode, scale the demand forecast by the fitted demand level once the fit "
        "has enough observations",
    )
    _add_world_options(parser)
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
    args.modes = _learn_flags(parser, args.elasticity or [TRUE_MODE], args.cautious, args.level)
    return args


def _learn_flags(
    parser: argparse.ArgumentParser, modes: list[ElasticityMode], cautious: bool, level: bool
) -> list[ElasticityMode]:
    """The modes with --cautious and --level set on every learn mode. Either flag without a learn
    mode is an error."""
    for flag, name in ((cautious, "--cautious"), (level, "--level")):
        if flag and not any(mode.kind == "learn" for mode in modes):
            parser.error(f"{name} applies to learn:X")
    return [
        replace(mode, cautious=mode.cautious or cautious, level=mode.level or level)
        if mode.kind == "learn"
        else mode
        for mode in modes
    ]


def _add_world_options(parser: argparse.ArgumentParser) -> None:
    """The simulator's settings for a run: the demand bias and the reaction, which the agent never
    sees, the market elasticity, which it is told, and the air schedule's scenario and churn."""
    parser.add_argument(
        "--demand-bias",
        dest="demand_bias",
        type=_factor,
        default=DEMAND_BIAS,
        metavar="F",
        help=f"multiply the simulator's demand by F, which the agent never sees "
        f"(default: {DEMAND_BIAS:g})",
    )
    share = f"{REACTION_SHARE:.0%}".replace("%", "%%")  # argparse reads % as a format
    parser.add_argument(
        "--react",
        action="store_true",
        help=f"competitors move {share} of a hotel's rate change {REACTION_LAG} days after it "
        f"(default: they never react)",
    )
    parser.add_argument(
        "--market-elasticity",
        dest="market_elasticity",
        type=_nonnegative,
        default=MARKET_ELASTICITY,
        metavar="E",
        help=f"the market's demand scales with (comp median / its starting level) ** -E, and "
        f"the agent is told E (default: {MARKET_ELASTICITY:g}, no market-level response)",
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS),
        default=DEFAULT_SCENARIO.name,
        metavar="NAME",
        help=f"the air schedule's filings: {', '.join(sorted(SCENARIOS))} "
        f"(default: {DEFAULT_SCENARIO.name})",
    )
    parser.add_argument(
        "--churn",
        action="store_true",
        help="the airline also files weekly revisions below the detect threshold, drawn from "
        "the seed (default: off)",
    )
    parser.add_argument(
        "--policy",
        choices=sorted(POLICIES),
        metavar="NAME",
        help=f"also run a rule-based control and report the gain against it: "
        f"{', '.join(sorted(POLICIES))} (default: none)",
    )


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
        subparser.add_argument(
            "--level", action="store_true", help="in learn mode, the fitted demand level fed back"
        )
        _add_customer_options(subparser)
    args = parser.parse_args(argv)
    if not 0 <= args.as_of < SIM_DAYS:
        parser.error(f"--as-of: the agent decides on days 0 to {SIM_DAYS - 1}")
    if args.command == "run-day" and args.first is not None and not 0 <= args.first <= args.as_of:
        parser.error("--from: a day from 0 to --as-of")
    [args.mode] = _learn_flags(parser, [args.elasticity], args.cautious, args.level)
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


def _nonnegative(text: str) -> float:
    """A market elasticity: a number, zero or more."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"{text} is negative; a market elasticity is zero or more")
    return value


def _factor(text: str) -> float:
    """A factor on the simulator's demand: a number above zero."""
    try:
        factor = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from None
    if not factor > 0:
        raise argparse.ArgumentTypeError(f"{text} is not above zero; a factor is positive")
    return factor


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


def _print_run(
    seed: int,
    client: Client | None,
    mode: ElasticityMode,
    customer: Customer,
    demand_bias: float = DEMAND_BIAS,
    react: bool = False,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
    policy: str | None = None,
) -> None:
    world = _world(demand_bias, react, market_elasticity, scenario, churn)
    fixed, books, agent = run(seed, client=client, mode=mode, customer=customer, **world)
    for day in sorted({entry.day for entry in agent.entries}):
        lines = _queue_lines(day, agent.entries, agent.advice)
        if lines:
            print("\n".join(lines))
    print()
    print(summary(seed, fixed, books, agent))
    if policy:
        control = _control(seed, policy, fixed, customer, world)
        own = sum(books.contribution(h) - fixed.contribution(h) for h in customer.hotels)
        print(
            f"The {policy} policy earned {control['control_change']:+,.0f} over fixed rates with "
            f"{control['control_changes']} stay dates changed, so against it the agent earned "
            f"{own - control['control_change']:+,.0f}."
        )


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
    seed: int,
    day: int,
    client: Client | None,
    mode: ElasticityMode,
    customer: Customer,
    demand_bias: float = DEMAND_BIAS,
    react: bool = False,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
) -> None:
    world = _world(demand_bias, react, market_elasticity, scenario, churn)
    entries, advice = replay(seed, day, client=client, mode=mode, customer=customer, **world)
    print(f"Day {day} queue, replayed from the cache (seed {seed})\n")
    blocks = [format_entry(e, customer) for e in queue(entries)]
    blocks += [format_advice(a) for a in advice]
    print("\n\n".join(blocks) or "Nothing in the queue.")


def _print_sweep(
    first: int,
    last: int,
    modes: Sequence[ElasticityMode],
    customer: Customer,
    demand_bias: float = DEMAND_BIAS,
    react: bool = False,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
    policy: str | None = None,
) -> None:
    world = _world(demand_bias, react, market_elasticity, scenario, churn)
    arms = sweep(first, last, modes=modes, customer=customer, policy=policy, **world)
    print(
        f"Seeds {first} to {last}: the agent run against the fixed-rate run, stay dates 0 to 149, "
        f"template reasons, candidates scored on {customer.target}"
        f"{_world_suffix(demand_bias, react, market_elasticity, scenario, churn)}"
    )
    if len(arms) == 1:
        print("\n".join(_seed_table(arms[0])))
    else:
        print("\n".join(_arm_table(arms)))
    print()
    print("\n".join(_source_table(arms)))
    print()
    print("\n".join(_revision_table(arms)))
    if react:
        print()
        print("\n".join(_reaction_table(arms, market_elasticity=market_elasticity)))
    if policy:
        print()
        print("\n".join(_control_table(arms, policy)))
    for arm in arms:
        if arm.mode.kind == "learn":
            print()
            print("\n".join(_estimate_table(arm, customer.hotels)))
        if arm.mode.level:
            print()
            print("\n".join(_level_table(arm, customer.hotels)))


def _world_suffix(
    demand_bias: float,
    react: bool = False,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
) -> str:
    """What a sweep's or a bench's heading adds when the simulator's demand was biased, its
    competitors reacted, its market answered the comp median's level, or its air schedule ran
    another scenario or the churn."""
    text = ""
    if demand_bias != DEMAND_BIAS:
        text += f", the simulator's demand multiplied by {demand_bias:g} unseen by the agent"
    if react:
        text += ", competitors reacting to the hotels' rate changes"
    if market_elasticity != MARKET_ELASTICITY:
        text += f", the market answering the comp median at an elasticity of {market_elasticity:g}"
    if scenario.name != DEFAULT_SCENARIO.name:
        text += f", the {scenario.name} schedule scenario"
    if churn:
        text += ", the airline filing weekly revisions below the threshold"
    return text


def _control_table(arms: list[ArmResult], policy: str, named: bool = False) -> list[str]:
    """Each arm against the rule-based control, next to its gain against fixed rates: the mean
    changes, each with its standard deviation and standard error across the seeds, the seeds ahead
    of the rule with the sign test's p, and the rule's own mean change and pairs changed."""
    reviewer_heading = f"{'reviewer':20}" if named else ""
    lines = [
        f"Against the {policy} policy, which prices with no estimate and no model: each arm's "
        f"mean change against fixed rates and against the policy, with the policy's own change",
        f"{'elasticity':18}{reviewer_heading}{'vs fixed':>12}{'vs the rule':>13}{'sd':>10}"
        f"{'se':>9}{'ahead of it':>13}{'p':>8}{'rule vs fixed':>15}{'sd':>10}{'se':>9}"
        f"{'rule changes':>14}",
    ]
    for arm in arms:
        reviewer = f"{arm.reviewer.name:20}" if named else ""
        against = arm.against_control
        sd, se = spread(against)
        rule_sd, rule_se = spread(arm.control_changes)
        lines.append(
            f"{str(arm.mode):18}{reviewer}{statistics.mean(arm.target_changes):>+12,.0f}"
            f"{statistics.mean(against):>+13,.0f}{_number(sd):>10}{_number(se):>9}"
            f"{f'{sum(change > 0 for change in against)}/{len(against)}':>13}{_p(against):>8}"
            f"{statistics.mean(arm.control_changes):>+15,.0f}{_number(rule_sd):>10}"
            f"{_number(rule_se):>9}{sum(result.control_changes for result in arm.seeds):>14}"
        )
    return lines


def _revision_table(arms: list[ArmResult], named: bool = False) -> list[str]:
    """The air schedule's filings and the flags they raised, summed over the seeds: the filing days
    through the last decided day, the flags with a seat cause and the rate changes."""
    reviewer_heading = f"{'reviewer':20}" if named else ""
    lines = [
        "The air schedule's filings through day 59 and the seat flags they raised, summed over "
        "the seeds",
        f"{'elasticity':18}{reviewer_heading}{'filings':>9}{'seat flags':>12}{'rate changes':>14}",
    ]
    for arm in arms:
        reviewer = f"{arm.reviewer.name:20}" if named else ""
        lines.append(
            f"{str(arm.mode):18}{reviewer}{arm.filings:>9}{arm.seat_flags:>12}"
            f"{arm.rate_changes:>14}"
        )
    return lines


def _reaction_table(
    arms: list[ArmResult], named: bool = False, market_elasticity: float = MARKET_ELASTICITY
) -> list[str]:
    """What the reaction did in each arm: the comp-median flags, those the hotels' own changes
    caused, and the stay dates changed twice or more within REPEAT_WINDOW days. The bench names
    each arm's reviewer, and the heading names the market elasticity."""
    reviewer_heading = f"{'reviewer':20}" if named else ""
    lines = [
        f"With competitors reacting (market elasticity {market_elasticity:g}): the comp-median "
        f"flags the hotels' own changes caused, the stay dates changed twice or more within "
        f"{REPEAT_WINDOW} days, and the plans shown on dates changed within the previous "
        f"{REPEAT_WINDOW} days, with the declines among them",
        f"{'elasticity':18}{reviewer_heading}{'median flags':>14}{'own changes':>13}"
        f"{'rate changes':>14}{'changed twice':>15}{'recent shown':>14}{'recent held':>13}",
    ]
    for arm in arms:
        reviewer = f"{arm.reviewer.name:20}" if named else ""
        shown = held = 0
        for result in arm.seeds:
            seed_shown, seed_held = on_recent_changes(result.entries, REPEAT_WINDOW)
            shown, held = shown + seed_shown, held + seed_held
        lines.append(
            f"{str(arm.mode):18}{reviewer}{arm.median_flags:>14}{arm.own_median_flags:>13}"
            f"{arm.rate_changes:>14}{arm.repeat_changes:>15}{shown:>14}{held:>13}"
        )
    return lines


def _standard_error_table(arm: ArmResult) -> list[str]:
    """A learn arm's decline rate by the standard error of its plans' pricing, pooled over the
    seeds: one row per group of STANDARD_ERROR_EDGES."""
    entries = [entry for result in arm.seeds for entry in result.entries]
    lines = [
        f"Elasticity {arm.mode}, {arm.reviewer.name}: the decline rate by the standard error of "
        f"the plan's elasticity, pooled over the seeds",
        f"{'standard error':>16}{'queued':>9}{'declined':>10}{'rate':>7}",
    ]
    for label, queued, declined, rate in by_standard_error(entries):
        lines.append(f"{label:>16}{queued:>9}{declined:>10}{_rate(rate):>7}")
    return lines


def _seed_table(arm: ArmResult) -> list[str]:
    """One arm, seed by seed, then the mean of both measures with its standard deviation and
    standard error across the seeds, and the range. The target's line adds the wins with the sign
    test's p, and the accepted plans' estimates against what they earned.
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
        f"; higher than the fixed-rate run in {arm.wins} of {len(arm.seeds)} seeds (sign test "
        f"p {_p(arm.target_changes)}). The accepted plans were estimated to earn "
        f"{arm.estimated:+,.0f} and earned {arm.realised:+,.0f}."
    )
    for name, changes in (("Contribution", arm.changes), ("Revenue", arm.revenue_changes)):
        lines.append(
            f"{name} change: mean {statistics.mean(changes):+,.0f} ({_sd_se(changes)}), range "
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
    """Several arms side by side. Each row holds the mean change against the fixed-rate run with
    its standard deviation and standard error across the seeds, its range, the winning seeds with
    the sign test's p and the rate changes. It also holds the estimates summed against the results
    and, for a cautious arm, the candidates its band rejected.
    """
    lines = [
        f"{'elasticity':18}{'mean change':>14}{'sd':>10}{'se':>9}{'mean revenue':>14}"
        f"{'range':>24}{'wins':>8}{'p':>8}{'rate changes':>14}{'estimated':>12}{'realised':>12}"
        f"{'share':>8}{'rejected at an end':>20}"
    ]
    for arm in arms:
        share = f"{arm.estimated / arm.realised:.2f}" if arm.realised else "n/a"
        rejected = str(arm.rejected_at_an_end) if arm.mode.cautious else "-"
        sd, se = spread(arm.changes)
        lines.append(
            f"{str(arm.mode):18}{statistics.mean(arm.changes):>+14,.0f}{_number(sd):>10}"
            f"{_number(se):>9}{statistics.mean(arm.revenue_changes):>+14,.0f}"
            f"{f'{min(arm.changes):+,.0f} to {max(arm.changes):+,.0f}':>24}"
            f"{f'{arm.wins}/{len(arm.seeds)}':>8}{_p(arm.target_changes):>8}{arm.rate_changes:>14}"
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
    share = REACTION_SHARE if args.react else 0.0
    truth = oracle(args.demand_bias, args.market_elasticity, share)
    reviewers = [TEMPLATE, truth] + [live(model) for model in args.models]
    _print_bench(
        *args.seeds,
        args.modes,
        reviewers,
        customer,
        args.demand_bias,
        args.react,
        args.market_elasticity,
        SCENARIOS[args.scenario],
        args.churn,
        args.policy,
    )


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
    parser.add_argument(
        "--cautious",
        action="store_true",
        help="in every learn mode run, the cautious rule, as the sweep applies it",
    )
    parser.add_argument(
        "--level",
        action="store_true",
        help="in every learn mode run, the fitted demand level fed back, as the sweep applies it",
    )
    _add_world_options(parser)
    _add_customer_options(parser)
    args = parser.parse_args(argv)
    if args.seeds[0] > args.seeds[1]:
        parser.error("--seeds: FIRST must not be after LAST")
    if args.template and args.model:
        parser.error("--template runs no model; drop --model")
    modes = args.elasticity or [ElasticityMode.parse(text) for text in BENCH_MODES]
    args.modes = _learn_flags(parser, modes, args.cautious, args.level)
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
    demand_bias: float = DEMAND_BIAS,
    react: bool = False,
    market_elasticity: float = MARKET_ELASTICITY,
    scenario: Scenario = DEFAULT_SCENARIO,
    churn: bool = False,
    policy: str | None = None,
) -> None:
    settings = _world(demand_bias, react, market_elasticity, scenario, churn)
    arms = sweep(
        first, last, modes=modes, customer=customer, reviewers=reviewers, policy=policy, **settings
    )
    world = _world_suffix(demand_bias, react, market_elasticity, scenario, churn)
    print(
        f"Seeds {first} to {last}: each reviewer against the fixed-rate run, stay dates 0 to 149, "
        f"candidates scored on {customer.target}{world}. Regret is the oracle arm's mean change "
        f"minus the reviewer's; the rates are pooled over the seeds."
    )
    for mode in modes:
        in_mode = [arm for arm in arms if arm.mode == mode]
        print()
        print("\n".join(_bench_table(mode, in_mode)))
        if mode.kind == "learn":
            for arm in in_mode:
                print()
                print("\n".join(_estimate_table(arm, customer.hotels, named=True)))
                if mode.level:
                    print()
                    print("\n".join(_level_table(arm, customer.hotels, named=True)))
                if arm.reviewer.live and arm.counts.declined:
                    print()
                    print("\n".join(_standard_error_table(arm)))
    if react:
        print()
        print("\n".join(_reaction_table(arms, named=True, market_elasticity=market_elasticity)))
    if churn or scenario.name != DEFAULT_SCENARIO.name:
        print()
        print("\n".join(_revision_table(arms, named=True)))
    if policy:
        print()
        print("\n".join(_control_table(arms, policy, named=True)))
    print()
    mismatched = [mode for mode in modes if mode.kind != "true"]
    if mismatched:
        print(
            "\n".join(_ranking_table(mismatched, [arm for arm in arms if arm.mode in mismatched]))
        )
    else:
        print("No mismatched mode was run, so there is no ranking of the reviewers.")


_BENCH_HEADER = (
    f"{'reviewer':20}{'mean change':>13}{'sd':>10}{'se':>9}{'range':>22}{'ahead':>8}{'p':>8}"
    f"{'flags':>7}{'pace':>6}"
    f"{'changes':>9}{'regret':>10}{'recovered':>11}"
    f"{'accept':>8}{'precision':>11}{'recall':>8}{'F1':>8}{'$ recall':>10}{'invalid':>9}"
    f"{'calls':>7}{'tokens in/out':>18}{'median s':>10}{'cost':>9}"
)


def _bench_table(mode: ElasticityMode, arms: list[ArmResult]) -> list[str]:
    """One mode's arms, a row per reviewer. Each row holds the mean realised change with its
    standard deviation and standard error across the seeds, its range, the seeds ahead of the
    fixed-rate run with the sign test's p, and the regret against the oracle arm. It counts the
    flags raised, those with a pace cause and the plans that changed a rate.

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
    sd, se = spread(changes)
    return (
        f"{arm.reviewer.name:20}{mean:>+13,.0f}{_number(sd):>10}{_number(se):>9}"
        f"{f'{min(changes):+,.0f} to {max(changes):+,.0f}':>22}"
        f"{f'{arm.wins}/{len(changes)}':>8}{_p(changes):>8}{arm.flags:>7}{arm.pace_flags:>6}"
        f"{arm.rate_changes:>9}{regret(oracle_mean, mean):>+10,.0f}"
        f"{_rate(recovered_share(statistics.mean(template.target_changes), oracle_mean, mean)):>11}"
        f"{_rate(counts.accept_rate):>8}{_rate(counts.precision):>11}{_rate(counts.recall):>8}"
        f"{_rate(counts.f1):>8}{_rate(counts.dollar_recall):>10}"
        f"{invalid_answers(calls) if is_live else '-':>9}{len(calls) if is_live else '-':>7}"
        f"{_tokens(calls) if is_live else '-':>18}{median if is_live else '-':>10}"
        f"{_cost(calls, arm.reviewer.model) if is_live else '-':>9}"
    )


def _rate(value: float) -> str:
    return "-" if math.isnan(value) else f"{value:.2f}"


def spread(values: Sequence[float]) -> tuple[float, float]:
    """The standard deviation of the seeds' values and the standard error of their mean, both nan
    with fewer than two seeds."""
    if len(values) < 2:
        return math.nan, math.nan
    sd = statistics.stdev(values)
    return sd, sd / math.sqrt(len(values))


def sign_test(values: Sequence[float]) -> float:
    """The two-sided sign test on the seeds above zero: the chance that a fair coin gives a count at
    least as far from half as this one. A seed at exactly zero counts as not above. nan with no
    seeds."""
    n = len(values)
    if not n:
        return math.nan
    wins = sum(value > 0 for value in values)
    tail = min(_at_least(wins, n), _at_least(n - wins, n))  # P(X >= wins) and P(X <= wins)
    return min(1.0, 2 * tail)


def _at_least(count: int, n: int) -> float:
    """P(X >= count) for X binomial with n fair trials."""
    return sum(math.comb(n, k) for k in range(count, n + 1)) / 2**n


def _number(value: float) -> str:
    return "n/a" if math.isnan(value) else f"{value:,.0f}"


def _sd_se(values: Sequence[float]) -> str:
    sd, se = spread(values)
    return f"sd {_number(sd)}, se {_number(se)}"


def _p(values: Sequence[float]) -> str:
    """The sign test's p to two significant figures, "<0.001" below that."""
    p = sign_test(values)
    if math.isnan(p):
        return "n/a"
    return "<0.001" if p < 0.001 else f"{p:#.2g}"


def _tokens(calls: list[dict]) -> str:
    tokens_in = sum(int(call.get("input_tokens", 0)) for call in calls)
    tokens_out = sum(int(call.get("output_tokens", 0)) for call in calls)
    return f"{tokens_in:,}/{tokens_out:,}"


def _cost(calls: list[dict], model: str | None) -> str:
    dollars = cost(calls, model or "")
    return "n/a" if math.isnan(dollars) else f"${dollars:.2f}"


def _level_table(arm: ArmResult, hotels: Sequence[Hotel], named: bool = False) -> list[str]:
    """A level arm's forecast factor per hotel on the report days, as mean (lowest to highest)
    across the seeds: exp(intercept) once the fit has enough observations, else 1."""
    reviewer = f", {arm.reviewer.name}" if named else ""
    lines = [
        f"Elasticity {arm.mode}{reviewer}: the factor each hotel scaled its forecast by, mean "
        f"(lowest to highest) across the seeds",
        f"{'day':>4}" + "".join(f"{h.key:>20}" for h in hotels),
    ]
    for day in REPORT_DAYS:
        if not all((day, h.key) in r.estimates for r in arm.seeds for h in hotels):
            continue
        cells = []
        for hotel in hotels:
            values = [level_factor(r.estimates[(day, hotel.key)]) for r in arm.seeds]
            cells.append(f"{statistics.mean(values):.2f} ({min(values):.2f} to {max(values):.2f})")
        lines.append(f"{day:>4}" + "".join(f"{cell:>20}" for cell in cells))
    return lines


def _estimate_table(arm: ArmResult, hotels: Sequence[Hotel], named: bool = False) -> list[str]:
    """A learn arm's estimate per hotel on the report days, as mean (lowest to highest)
    across the seeds. The bench names the arm's reviewer in the heading."""
    reviewer = f", {arm.reviewer.name}" if named else ""
    lines = [
        f"Elasticity {arm.mode}{reviewer}: the estimate each hotel priced with, mean (lowest to "
        f"highest) across the seeds",
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
