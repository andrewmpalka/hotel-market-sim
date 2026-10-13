"""bench.py

A benchmark of the model as a reviewer.

Code computes every candidate and its estimate (plan.py). The model only accepts or declines each
queued plan (model.py). The question a benchmark can ask is therefore how well a reviewer
declines.

In the default mode the plan is scored with the simulator's own elasticity. Accepting every plan
is then right, and every reviewer ties there. In the modes with a wrong or a learned elasticity,
a plan is sometimes worth less than holding. Declining it is then right. The benchmark runs the
reviewers in those modes.

The oracle reviewer is the ceiling for a reviewer. It grades; it is not an agent. It cannot pick
a better candidate than the plan, and a single seed's draw can beat it. For each queued entry it
re-scores the plan and hold with ORACLE_ELASTICITY, the simulator's own value. It declines the
plan when hold scores at least as well. It stands in as the client the agent asks, so its
decisions drive a run of their own. The command tells it the simulator's demand bias, market
elasticity and reaction share when it builds it (cli.py). The oracle therefore stays the
simulator's truth at any of those settings. It treats the reaction as immediate, where the
simulator applies it with a lag.

It also labels the entries of any other run after the fact. Its answers are never cached and
record the source "oracle". A later live run in the same mode therefore cannot mistake them for
the model's. It imports from plan.py and agent.py, and nothing in the agent's path imports it.
The simulator's elasticity therefore never reaches a decision through it. tests/test_sources.py
checks its imports with the agent's modules.

The measures are regret, the accept rate, decline precision, recall, F1, dollar-weighted recall
and the recovered share. Each is a function whose docstring gives its formula. Two more read a
learn arm's queue: by_standard_error gives the decline rate by how little the elasticity was
pinned down, and on_recent_changes counts the plans shown on stay dates the run changed within
the previous fortnight, and the declines among them.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterable
from dataclasses import astuple, dataclass
from pathlib import Path

from hotel_market.agent import Agent
from hotel_market.customer import Customer, demo
from hotel_market.model import ClaudeClient, Client, Measured, request_digest
from hotel_market.plan import HOLD, ORACLE_ELASTICITY, Entry, rescored
from hotel_market.text import tens_of_dollars

Key = tuple[int, str, str]  # (day, hotel key, entry id): one queued entry of one run


def key(entry: Entry) -> Key:
    return (entry.day, entry.hotel, entry.id)


# ---- the oracle reviewer ----------------------------------------------------


def oracle_values(
    entry: Entry,
    customer: Customer | None = None,
    demand_bias: float = 1.0,
    market_elasticity: float = 0.0,
    reaction_share: float = 0.0,
) -> tuple[float, float]:
    """(hold, plan): the worth of holding and of the plan at ORACLE_ELASTICITY, summed over the
    weekdays the plan changes. The plan's own estimate may come from another elasticity. This scores
    the same candidates with the simulator's value. The demand bias, the market elasticity and the
    reaction share are the simulator's too: the command tells the oracle what the run does."""
    customer = customer or demo()
    hotel = customer.hotel(entry.hotel)
    cost = hotel.room_cost if customer.scores_contribution() else 0.0
    world = (demand_bias, market_elasticity, reaction_share)
    hold = plan = 0.0
    for group in entry.changed_weekdays:
        hold += rescored(group, group.hold, ORACLE_ELASTICITY, cost, *world)
        plan += rescored(group, group.best, ORACLE_ELASTICITY, cost, *world)
    return hold, plan


def oracle_declines(
    entry: Entry,
    customer: Customer | None = None,
    demand_bias: float = 1.0,
    market_elasticity: float = 0.0,
    reaction_share: float = 0.0,
) -> bool:
    """Whether the oracle declines the entry's plan. It does when hold scores at least as well
    at ORACLE_ELASTICITY and the simulator's demand bias, market elasticity and reaction."""
    hold, plan = oracle_values(entry, customer, demand_bias, market_elasticity, reaction_share)
    return hold >= plan


def oracle_labels(
    entries: Iterable[Entry],
    customer: Customer | None = None,
    demand_bias: float = 1.0,
    market_elasticity: float = 0.0,
    reaction_share: float = 0.0,
) -> set[Key]:
    """The queued entries of a run whose plan the oracle declines."""
    world = (demand_bias, market_elasticity, reaction_share)
    return {key(e) for e in entries if e.queued and oracle_declines(e, customer, *world)}


class OracleReviewer:
    """The oracle as the client an agent asks. It answers each request from the day's entries, which
    the agent keeps in agent.today while it asks. It declines a plan when hold scores at least as
    well at the simulator's elasticity and demand bias. Code writes its reasons from the two
    scores. Nothing it answers is cached."""

    name = "oracle"
    cached = False

    def __init__(
        self,
        agent: Agent,
        demand_bias: float = 1.0,
        market_elasticity: float = 0.0,
        reaction_share: float = 0.0,
    ):
        self.agent = agent
        # The simulator's settings, as the command built the reviewer.
        self.demand_bias = demand_bias
        self.market_elasticity = market_elasticity
        self.reaction_share = reaction_share

    def complete(self, system: str, prompt: str, schema: dict) -> str:
        request = json.loads(prompt)
        customer = self.agent.customer
        hotel = next(h for h in customer.hotels if h.name == request["hotel"]["name"])
        today = {e.id: e for e in self.agent.today if e.hotel == hotel.key and e.queued}
        decisions = []
        world = (self.demand_bias, self.market_elasticity, self.reaction_share)
        for asked in request["entries"]:
            hold, plan = oracle_values(today[asked["id"]], customer, *world)
            choice = HOLD if hold >= plan else asked["plan"]
            reason = _oracle_reason(hold, plan, choice, *world)
            decisions.append({"id": asked["id"], "choice": choice, "reason": reason})
        return json.dumps({"decisions": decisions})


def _oracle_reason(
    hold: float,
    plan: float,
    choice: str,
    demand_bias: float = 1.0,
    market_elasticity: float = 0.0,
    reaction_share: float = 0.0,
) -> str:
    verdict = "we hold" if choice == HOLD else "we take the plan"
    truth = f"the simulator's elasticity of {ORACLE_ELASTICITY:g}"
    if demand_bias != 1.0:
        truth += f" and demand bias of {demand_bias:g}"
    if market_elasticity:
        truth += f", a market elasticity of {market_elasticity:g}"
    if reaction_share:
        truth += f", with competitors following {reaction_share:.0%} of a change"
    return (
        f"At {truth}, holding is estimated at {tens_of_dollars(hold)} and the plan at "
        f"{tens_of_dollars(plan)}, so {verdict}."
    )


class ScriptedClient:
    """A client for tests and offline runs. It answers a request from `answers`, a dict of request
    digest to decisions, when the digest is there. Otherwise it declines the entries whose Key is in
    `declines` and accepts every other plan, with a scripted reason. It plays a model. Its answers
    are cached and record the source "model". The record's model field, "scripted", tells them from
    a real model's."""

    def __init__(
        self,
        answers: dict[str, list[dict]] | None = None,
        declines: Iterable[Key] = (),
        model: str = "scripted",
        customer: Customer | None = None,
    ):
        self.answers = dict(answers or {})
        self.declines = set(declines)
        self.model = model
        self.customer = customer or demo()

    def complete(self, system: str, prompt: str, schema: dict) -> str:
        request = json.loads(prompt)
        decisions = self.answers.get(request_digest(request))
        if decisions is None:
            hotel = next(h for h in self.customer.hotels if h.name == request["hotel"]["name"])
            decisions = [self._decision(request["day"], hotel.key, e) for e in request["entries"]]
        return json.dumps({"decisions": decisions})

    def _decision(self, day: int, hotel: str, entry: dict) -> dict:
        choice = HOLD if (day, hotel, entry["id"]) in self.declines else entry["plan"]
        return {"id": entry["id"], "choice": choice, "reason": f"Scripted: {choice}."}


# ---- the reviewers ------------------------------------------------------------


@dataclass(frozen=True)
class Reviewer:
    """One reviewer of the queued plans, as a sweep arm names it: the template, the oracle or a
    model. `model` is the model the arm asks, or None when it asks none. The agent takes it, so
    the arm's cache folder names it. `make` builds the client once the agent exists. The oracle
    reads the agent's entries, and a measured client writes its calls beside the agent's cache. A
    make of None is the template.
    """

    name: str
    model: str | None = None
    make: Callable[[Agent], Client | None] | None = None

    def client_for(self, agent: Agent) -> Client | None:
        return None if self.make is None else self.make(agent)

    @property
    def live(self) -> bool:
        """Whether the arm asks a model, so its calls, tokens, latency and cost are reported."""
        return self.model is not None


TEMPLATE = Reviewer("template")
ORACLE = Reviewer("oracle", make=OracleReviewer)


def oracle(
    demand_bias: float = 1.0, market_elasticity: float = 0.0, reaction_share: float = 0.0
) -> Reviewer:
    """The oracle reviewer told the simulator's demand bias, market elasticity and reaction share.
    At the defaults it is ORACLE. The command builds it, the way ORACLE_ELASTICITY names the
    simulator's elasticity for it."""
    if (demand_bias, market_elasticity, reaction_share) == (1.0, 0.0, 0.0):
        return ORACLE
    return Reviewer(
        "oracle",
        make=lambda agent: OracleReviewer(agent, demand_bias, market_elasticity, reaction_share),
    )


def live(model: str) -> Reviewer:
    """A model as a reviewer. Its measured Claude client appends its calls to calls.jsonl in the
    arm's cache folder. A rerun that reads the cache adds nothing to the file.
    """
    return Reviewer(
        model, model, lambda agent: Measured(ClaudeClient(model), agent.cache_dir / "calls.jsonl")
    )


# List prices in dollars per million tokens, (input, output), from Anthropic's pricing page,
# https://platform.claude.com/docs/en/about-claude/pricing, read on 2026-10-12. Haiku 5.5 is
# priced for prompts up to 100,000 tokens, which every request here is far under. Prompt
# caching is off, so the cache token counts in a call record cost nothing.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


def counted(records: Iterable[dict], folder: Path) -> list[dict]:
    """The call records of an arm that count. There is one per request digest. A digest counts only
    when its answer is in the arm's cache folder or its record is marked failed. A digest's
    records merge into one.

    The merged record takes its outcome, tokens and time from the last record. It sums
    bad_attempt and retries over all of them. A request that failed in one run and answered in a
    rerun therefore keeps every bad attempt. A record with no digest, from before the field, is
    kept as it is.
    """
    cached = set()
    if folder.exists():
        for path in folder.glob("day*_*.json"):
            cached.add(json.loads(path.read_text()).get("request_digest"))
    undigested, merged = [], {}
    for record in records:
        digest = record.get("request_digest")
        if digest is None:
            undigested.append(record)
        elif digest in merged:
            earlier = merged[digest]
            merged[digest] = {
                **record,
                "bad_attempt": int(earlier.get("bad_attempt", 0))
                + int(record.get("bad_attempt", 0)),
                "retries": int(earlier.get("retries", 0)) + int(record.get("retries", 0)),
            }
        else:
            merged[digest] = record
    return undigested + [
        r for r in merged.values() if r.get("failed") or r["request_digest"] in cached
    ]


def cost(calls: Iterable[dict], model: str) -> float:
    """The list-price cost of the calls in dollars at the model's PRICES. Every attempt's input
    and output tokens count, since each was paid for. nan for a model not in the table."""
    if model not in PRICES:
        return math.nan
    input_price, output_price = PRICES[model]
    calls = list(calls)
    tokens_in = sum(int(call.get("input_tokens", 0)) for call in calls)
    tokens_out = sum(int(call.get("output_tokens", 0)) for call in calls)
    return (tokens_in * input_price + tokens_out * output_price) / 1_000_000


# ---- the measures -------------------------------------------------------------


def regret(oracle_change: float, change: float) -> float:
    """Regret = the oracle arm's realised target change - the arm under test's, on the same seed and
    mode. It is positive when the reviewer left money behind and negative when it beat the
    oracle.
    """
    return oracle_change - change


def recovered_share(template_change: float, oracle_change: float, change: float) -> float:
    """Recovered share = (the arm's mean realised change - the template's) / (the oracle's - the
    template's). Both are on the same seeds and mode.

    It is the share of the value a reviewer could recover over accept-all that this one did. The
    oracle's share is 1 and accept-all's is 0. A reviewer that lost money against accept-all is
    below 0. It is nan when the oracle and the template tie, as in the true mode. There is then
    nothing to recover.
    """
    room = oracle_change - template_change
    if room == 0:
        return math.nan
    return (change - template_change) / room


def reviewed(entries: Iterable[Entry]) -> list[Entry]:
    """The entries the reviewer saw: those whose plan was worth the minimum and was queued."""
    return [e for e in entries if e.queued]


def declined(entries: Iterable[Entry]) -> set[Key]:
    """The queued entries whose plan the reviewer declined, so that the action is hold."""
    return {key(e) for e in reviewed(entries) if e.action == HOLD}


def accept_rate(entries: Iterable[Entry]) -> float:
    """Accept rate = queued entries whose plan was accepted / queued entries. nan with no
    queued entry."""
    queued = reviewed(entries)
    if not queued:
        return math.nan
    return sum(e.action != HOLD for e in queued) / len(queued)


def decline_precision(entries: Iterable[Entry], oracle: set[Key]) -> float:
    """Decline precision = the reviewer's declines the oracle also declined / the reviewer's
    declines. nan when the reviewer declined nothing."""
    ours = declined(entries)
    if not ours:
        return math.nan
    return len(ours & oracle) / len(ours)


def decline_recall(entries: Iterable[Entry], oracle: set[Key]) -> float:
    """Decline recall = the oracle's declines the reviewer also declined / the oracle's
    declines. nan when the oracle declined nothing."""
    if not oracle:
        return math.nan
    return len(declined(entries) & oracle) / len(oracle)


def decline_f1(entries: Iterable[Entry], oracle: set[Key]) -> float:
    """F1 = 2 x precision x recall / (precision + recall). It is nan when either is nan and 0 when
    both are 0.
    """
    precision, recall = decline_precision(entries, oracle), decline_recall(entries, oracle)
    if math.isnan(precision) or math.isnan(recall):
        return math.nan
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def dollar_weighted_recall(
    entries: Iterable[Entry], oracle: set[Key], customer: Customer | None = None
) -> float:
    """Dollar-weighted decline recall = the loss over the plans both declined / the loss over every
    plan the oracle declined. The loss is the oracle's loss from accepting a plan: hold minus plan
    at ORACLE_ELASTICITY (oracle_values). It is not the plan's own value at stake. It is nan when
    the oracle declined nothing."""
    by_key = {key(e): e for e in reviewed(entries)}

    def loss(k: Key) -> float:
        hold, plan = oracle_values(by_key[k], customer)
        return hold - plan

    total = sum(loss(k) for k in oracle if k in by_key)
    if total == 0:
        return math.nan
    return sum(loss(k) for k in declined(entries) & oracle if k in by_key) / total


@dataclass(frozen=True)
class DeclineCounts:
    """The counts behind the measures for one run or several. Adding two sums the counts, so an
    arm's rates are pooled over its seeds and not averaged. The rates follow accept_rate,
    decline_precision, decline_recall, decline_f1 and dollar_weighted_recall above. They keep the
    same nan rules. The method of(entries) labels a run with the oracle after the fact.
    """

    queued: int = 0  # the plans the reviewer saw
    accepted: int = 0
    declined: int = 0
    oracle: int = 0  # the plans the oracle declines
    agreed: int = 0  # the plans both declined
    loss: float = 0.0  # the oracle's loss from accepting every plan it declines
    caught: float = 0.0  # that loss over the plans both declined

    @classmethod
    def of(
        cls,
        entries: Iterable[Entry],
        customer: Customer | None = None,
        demand_bias: float = 1.0,
        market_elasticity: float = 0.0,
        reaction_share: float = 0.0,
    ) -> DeclineCounts:
        queued = reviewed(entries)
        world = (demand_bias, market_elasticity, reaction_share)
        ours, labels = declined(queued), oracle_labels(queued, customer, *world)
        by_key = {key(e): e for e in queued}

        def loss(k: Key) -> float:
            hold, plan = oracle_values(by_key[k], customer, *world)
            return hold - plan

        return cls(
            len(queued),
            sum(e.action != HOLD for e in queued),
            len(ours),
            len(labels),
            len(ours & labels),
            sum(loss(k) for k in labels),
            sum(loss(k) for k in ours & labels),
        )

    def __add__(self, other: DeclineCounts) -> DeclineCounts:
        return DeclineCounts(*(a + b for a, b in zip(astuple(self), astuple(other))))

    @property
    def accept_rate(self) -> float:
        return self.accepted / self.queued if self.queued else math.nan

    @property
    def precision(self) -> float:
        return self.agreed / self.declined if self.declined else math.nan

    @property
    def recall(self) -> float:
        return self.agreed / self.oracle if self.oracle else math.nan

    @property
    def f1(self) -> float:
        precision, recall = self.precision, self.recall
        if math.isnan(precision) or math.isnan(recall):
            return math.nan
        return 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    @property
    def dollar_recall(self) -> float:
        return self.caught / self.loss if self.loss else math.nan


# The standard errors that bound the groups of by_standard_error: a learn arm's queued plans
# are grouped by how little their elasticity was pinned down when the reviewer saw them.
STANDARD_ERROR_EDGES = (0.15, 0.25, 0.35)


def by_standard_error(
    entries: Iterable[Entry], edges: tuple[float, ...] = STANDARD_ERROR_EDGES
) -> list[tuple[str, int, int, float]]:
    """The decline rate of a reviewer's queued plans by the standard error of their pricing: one
    row per group as (label, queued, declined, rate), the groups bounded by the edges. A plan
    whose pricing has no standard error, as a fixed or true mode's has not, is left out. The
    rate is nan in an empty group."""
    bounds = (0.0, *edges, math.inf)
    rows = []
    for low, high in zip(bounds, bounds[1:]):
        if high == math.inf:
            label = f"{low:g} and over"
        elif low == 0.0:
            label = f"under {high:g}"
        else:
            label = f"{low:g} to {high:g}"
        group = [
            e
            for e in reviewed(entries)
            if e.pricing.standard_error is not None and low <= e.pricing.standard_error < high
        ]
        held = sum(e.action == HOLD for e in group)
        rows.append((label, len(group), held, held / len(group) if group else math.nan))
    return rows


def on_recent_changes(entries: Iterable[Entry], window: int = 14) -> tuple[int, int]:
    """(shown, declined): the queued plans whose stay dates the same run changed within the
    `window` days before the plan's day, and how many of those the reviewer declined. A plan on
    day d counts when an accepted plan of the same hotel changed one of its stay dates on a day
    from d - window to d - 1. That is the loop a reaction feeds: the competitors' answer to the
    hotel's own change raises a new flag on the same dates."""
    changed: dict[tuple[str, int], list[int]] = {}
    for entry in entries:
        if entry.action != HOLD:
            for stay_day in entry.new_rates:
                changed.setdefault((entry.hotel, stay_day), []).append(entry.day)
    shown = declined = 0
    for entry in reviewed(entries):
        recent = any(
            entry.day - window <= day < entry.day
            for stay_day in range(entry.first_stay, entry.last_stay + 1)
            for day in changed.get((entry.hotel, stay_day), ())
        )
        if recent:
            shown += 1
            declined += entry.action == HOLD
    return shown, declined


def invalid_answers(calls: Iterable[dict]) -> int:
    """How many call records had a bad attempt. A bad attempt is an SDK error, a refusal or an
    answer that failed model._check. It counts whether or not a retry then answered. A Measured
    client writes the records. A record that counted() merged over several runs counts each run
    that had one.
    """
    return sum(int(call.get("bad_attempt", 0)) for call in calls)


def failed_requests(calls: Iterable[dict]) -> int:
    """How many call records ended without an answer: the retries ran out, or the model refused.
    The agent's run stops at the first of these, so an arm with one has no result."""
    return sum(1 for call in calls if call.get("failed"))


def retries(calls: Iterable[dict]) -> int:
    """The retries over all call records: the sum of each record's retries field."""
    return sum(int(call.get("retries", 0)) for call in calls)
