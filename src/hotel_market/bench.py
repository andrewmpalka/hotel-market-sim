"""bench.py

A benchmark of the model as a reviewer.

Code computes every candidate and its estimate (plan.py), and the model only
accepts or declines each queued plan (model.py), so the question a benchmark
can ask is how well a reviewer declines. In the default mode the plan is scored
with the simulator's own elasticity and accepting every plan is right, so every
reviewer ties there. In the modes where the agent prices with a wrong or a
learned elasticity, a plan is sometimes worth less than holding, and declining
it is right. The benchmark runs the reviewers in those modes.

The oracle reviewer is the ceiling for a reviewer: a grader, not an agent. It
cannot pick a better candidate than the plan, and a single seed's draw can beat
it. For each queued entry it re-scores the plan and hold with ORACLE_ELASTICITY,
the simulator's own value, and declines the plan when hold scores at least as
well. It stands in as the client the agent asks, so its decisions drive a run
of their own, and it labels the entries of any other run after the fact. Its
answers are never cached and record the source "oracle", so a later live run in
the same mode cannot mistake them for the model's. It imports from plan.py and
agent.py and nothing in the agent's path imports it, so the simulator's
elasticity never reaches a decision through it; tests/test_sources.py checks
its imports with the agent's modules.

The measures follow a fraud benchmark's four detection measures, with a decline
standing for a block: decline precision, decline recall, their F1 and a
dollar-weighted recall, plus the regret of an arm against the oracle's arm and
the accept rate. Each is a function whose docstring gives its formula.

A Reviewer names what decides an arm of the benchmark: the template, the
oracle or a model behind a measured Claude client, each with its own cache
folder. cli.py's sweep() runs one arm per mode and reviewer and keeps each
seed's entries, call records and DeclineCounts, the counts behind the measures
pooled over the seeds, and the bench command prints them. PRICES turns an
arm's tokens into a list-price cost. A ScriptedClient plays a model offline:
it answers from a dict of request digest to decisions, or declines the entries
it is told to and accepts the rest, and it is cached under the model name
"scripted", so the whole benchmark runs without a key.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterable
from dataclasses import astuple, dataclass

from hotel_market.agent import Agent
from hotel_market.customer import Customer, demo
from hotel_market.model import ClaudeClient, Client, Measured, request_digest
from hotel_market.plan import HOLD, ORACLE_ELASTICITY, Entry, rescored
from hotel_market.text import tens_of_dollars

Key = tuple[int, str, str]  # (day, hotel key, entry id): one queued entry of one run


def key(entry: Entry) -> Key:
    return (entry.day, entry.hotel, entry.id)


# ---- the oracle reviewer ----------------------------------------------------


def oracle_values(entry: Entry, customer: Customer | None = None) -> tuple[float, float]:
    """(hold, plan): what holding and the plan are worth at ORACLE_ELASTICITY, summed over
    the days of the week the plan changes. The plan's own estimate may have been made at
    another elasticity; this is the same candidates scored with the simulator's value."""
    customer = customer or demo()
    hotel = customer.hotel(entry.hotel)
    cost = hotel.room_cost if customer.scores_contribution() else 0.0
    hold = plan = 0.0
    for group in entry.changed_weekdays:
        hold += rescored(group, group.hold, ORACLE_ELASTICITY, cost)
        plan += rescored(group, group.best, ORACLE_ELASTICITY, cost)
    return hold, plan


def oracle_declines(entry: Entry, customer: Customer | None = None) -> bool:
    """Whether the oracle declines the entry's plan: hold scores at least as well as the
    plan at ORACLE_ELASTICITY."""
    hold, plan = oracle_values(entry, customer)
    return hold >= plan


def oracle_labels(entries: Iterable[Entry], customer: Customer | None = None) -> set[Key]:
    """The queued entries of a run whose plan the oracle declines."""
    return {key(e) for e in entries if e.queued and oracle_declines(e, customer)}


class OracleReviewer:
    """The oracle as the client an agent asks: it answers each request from the day's
    entries, which the agent keeps in agent.today while it asks, and declines a plan when
    hold scores at least as well at the simulator's elasticity. Its reasons are written
    by code from the two scores, as the rules require. Nothing it answers is cached."""

    name = "oracle"
    cached = False

    def __init__(self, agent: Agent):
        self.agent = agent

    def complete(self, system: str, prompt: str, schema: dict) -> str:
        request = json.loads(prompt)
        customer = self.agent.customer
        hotel = next(h for h in customer.hotels if h.name == request["hotel"]["name"])
        today = {e.id: e for e in self.agent.today if e.hotel == hotel.key and e.queued}
        decisions = []
        for asked in request["entries"]:
            hold, plan = oracle_values(today[asked["id"]], customer)
            choice = HOLD if hold >= plan else asked["plan"]
            decisions.append(
                {"id": asked["id"], "choice": choice, "reason": _oracle_reason(hold, plan, choice)}
            )
        return json.dumps({"decisions": decisions})


def _oracle_reason(hold: float, plan: float, choice: str) -> str:
    verdict = "we hold" if choice == HOLD else "we take the plan"
    return (
        f"At the simulator's elasticity of {ORACLE_ELASTICITY:g}, holding is estimated at "
        f"{tens_of_dollars(hold)} and the plan at {tens_of_dollars(plan)}, so {verdict}."
    )


class ScriptedClient:
    """A client for tests and offline runs. It answers a request from `answers`, a dict
    of request digest to decisions, when the digest is there. Otherwise it declines the
    entries whose Key is in `declines` and accepts every other plan, with a scripted
    reason. It plays a model: its answers are cached and record source "model", and the
    record's model field, "scripted", tells them from a real model's. An agent given it
    therefore keeps its cache in its own folder."""

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
    """One reviewer of the queued plans, as a sweep arm names it: the template, the oracle
    or a model. `model` is the model the arm asks, None when it asks none; the agent takes
    it, so the arm's cache folder names it. `make` builds the client once the agent exists,
    since the oracle reads the agent's entries and a measured client writes its calls beside
    the agent's cache; None is the template."""

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


def live(model: str) -> Reviewer:
    """A model as a reviewer: a measured Claude client whose calls are appended to calls.jsonl
    in the arm's cache folder, so that a rerun that reads the cache adds nothing to it."""
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
    """Regret = the realised target change of the arm that followed the oracle's decisions
    - the realised target change of the arm under test, on the same seed and mode. Positive
    when the reviewer left money behind, negative when it beat the oracle."""
    return oracle_change - change


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
    """F1 = 2 x precision x recall / (precision + recall). nan when either is nan, 0 when
    both are 0."""
    precision, recall = decline_precision(entries, oracle), decline_recall(entries, oracle)
    if math.isnan(precision) or math.isnan(recall):
        return math.nan
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def dollar_weighted_recall(
    entries: Iterable[Entry], oracle: set[Key], customer: Customer | None = None
) -> float:
    """Dollar-weighted decline recall = the oracle's loss from accepting, summed over the
    plans both the reviewer and the oracle declined / the same loss summed over every plan
    the oracle declined. The loss is hold minus plan at ORACLE_ELASTICITY (oracle_values),
    not the plan's own value at stake, which a wrong elasticity overstates. nan when the
    oracle declined nothing."""
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
    """The counts behind the measures for one run or several: adding two sums the counts, so
    that an arm's rates are pooled over its seeds rather than averaged. The rates follow
    accept_rate, decline_precision, decline_recall, decline_f1 and dollar_weighted_recall
    above, with the same nan rules. of(entries) labels a run with the oracle after the fact."""

    queued: int = 0  # the plans the reviewer saw
    accepted: int = 0
    declined: int = 0
    oracle: int = 0  # the plans the oracle declines
    agreed: int = 0  # the plans both declined
    loss: float = 0.0  # the oracle's loss from accepting every plan it declines
    caught: float = 0.0  # that loss over the plans both declined

    @classmethod
    def of(cls, entries: Iterable[Entry], customer: Customer | None = None) -> DeclineCounts:
        queued = reviewed(entries)
        ours, labels = declined(queued), oracle_labels(queued, customer)
        by_key = {key(e): e for e in queued}

        def loss(k: Key) -> float:
            hold, plan = oracle_values(by_key[k], customer)
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


def invalid_answers(calls: Iterable[dict]) -> int:
    """How many call records had a bad attempt: an SDK error, a refusal or an answer that failed
    model._check, whether or not a retry then answered. A Measured client writes the records."""
    return sum(1 for call in calls if call.get("bad_attempt"))


def failed_requests(calls: Iterable[dict]) -> int:
    """How many call records ended without an answer: the retries ran out, or the model refused.
    The agent's run stops at the first of these, so an arm with one has no result."""
    return sum(1 for call in calls if call.get("failed"))


def retries(calls: Iterable[dict]) -> int:
    """The retries over all call records: the sum of each record's retries field."""
    return sum(int(call.get("retries", 0)) for call in calls)
