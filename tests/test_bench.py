"""bench.py: the oracle reviewer as a grader, the reviewer measures and the scripted client."""

import json
import math

import pytest

from hotel_market.agent import Agent, ElasticityMode
from hotel_market.bench import (
    OracleReviewer,
    ScriptedClient,
    accept_rate,
    decline_f1,
    decline_precision,
    decline_recall,
    declined,
    dollar_weighted_recall,
    invalid_answers,
    key,
    oracle_declines,
    oracle_labels,
    oracle_values,
    regret,
    retries,
)
from hotel_market.bookings import simulate
from hotel_market.customer import demo
from hotel_market.detect import AHEAD, flags
from hotel_market.model import SYSTEM, Measured, request_digest, request_for
from hotel_market.plan import (
    HOLD,
    Candidate,
    Entry,
    FlagNumbers,
    Range,
    StayDate,
    WeekdayGroup,
    entry_for,
)
from hotel_market.simulated import deciding

DEMO = demo()
SEED = 7


def _entry(day, first, gain, action=None, plan_rate=133.0, hotel="airport"):
    """A made-up queued entry worth `gain` over holding by its own estimate, accepted unless
    action is HOLD. Its one stay date has 10 rooms left against 1,000 rooms of demand, so
    every candidate sells those 10 and the oracle's loss from the plan is 10 x (140 - rate)."""
    group = WeekdayGroup(
        0,
        [
            Candidate(HOLD, {first: 140.0}, 1000.0),
            Candidate("lower 5%", {first: plan_rate}, 1000.0 + gain),
        ],
        stay_dates=[StayDate(first, 140.0, 140.0, 10, 1000.0)],
    )
    numbers = FlagNumbers(
        days_out=Range(0, 0),
        rooms_on_books=0,
        unsold_rooms=0,
        remaining_demand=0.0,
        pace_gap=0.0,
        seat_change=Range(0.0, 0.0),
        seat_revision=Range(0.0, 0.0),
        rate=Range(140.0, 140.0),
        comp_median=Range(140.0, 140.0),
        rate_vs_median=Range(0.0, 0.0),
        median_change=Range(0.0, 0.0),
        new_event=None,
    )
    entry = Entry(day, hotel, first, first, (AHEAD,), numbers, [group], minimum=250)
    entry.action = HOLD if action == HOLD else entry.plan
    return entry


# Four queued entries and one under the minimum. The reviewer declines A and B; the oracle
# would decline B and C. D is accepted by both, and E was never asked. B's plan cuts the
# rate to $133 and C's to $126, so the oracle's losses from accepting them are $70 and $140.
A = _entry(10, 40, 300.0, HOLD)
B = _entry(10, 41, 600.0, HOLD)
C = _entry(20, 42, 1000.0, plan_rate=126.0)
D = _entry(20, 43, 400.0)
E = _entry(20, 44, 100.0)
ENTRIES = [A, B, C, D, E]
ORACLE = {key(B), key(C)}


def test_regret_is_the_oracle_arms_change_minus_the_arms_change():
    assert regret(32899.0, 8438.0) == pytest.approx(24461.0)
    assert regret(100.0, 120.0) == pytest.approx(-20.0)


def test_accept_rate_counts_accepted_queued_plans():
    assert not E.queued and declined(ENTRIES) == {key(A), key(B)}
    assert accept_rate(ENTRIES) == pytest.approx(2 / 4)
    assert math.isnan(accept_rate([E]))


def test_decline_precision_recall_and_f1_against_the_oracle():
    # Of the reviewer's two declines the oracle shares one; of the oracle's two the reviewer
    # shares one.
    assert decline_precision(ENTRIES, ORACLE) == pytest.approx(1 / 2)
    assert decline_recall(ENTRIES, ORACLE) == pytest.approx(1 / 2)
    assert decline_f1(ENTRIES, ORACLE) == pytest.approx(1 / 2)
    # The weight is the oracle's loss from accepting, hold minus plan at 1.5: $70 for B and
    # $140 for C, so the reviewer caught $70 of the $210 at stake.
    assert oracle_values(B) == pytest.approx((933.33, 863.33), abs=0.01)
    assert oracle_values(C) == pytest.approx((933.33, 793.33), abs=0.01)
    assert dollar_weighted_recall(ENTRIES, ORACLE) == pytest.approx(70 / 210)
    # The plan's own value at stake is not the weight: by it the share would be 600 / 1,600.
    assert B.value_at_stake == 600 and C.value_at_stake == 1000


def test_the_measures_are_nan_when_nobody_declined():
    accepted = [C, D]
    assert math.isnan(decline_precision(accepted, ORACLE))  # the reviewer declined nothing
    assert math.isnan(decline_recall(ENTRIES, set()))  # the oracle declined nothing
    assert math.isnan(decline_f1(ENTRIES, set()))
    assert math.isnan(dollar_weighted_recall(ENTRIES, set()))
    assert decline_f1([A], {key(B)}) == 0.0  # both declined something, nothing in common


def test_invalid_answers_and_retries_are_counted():
    calls = [{"retries": 2, "invalid": False}, {"retries": 0, "invalid": True}, {}]
    assert invalid_answers(calls) == 1 and retries(calls) == 2


@pytest.fixture(scope="module")
def fixed_mode_run(tmp_path_factory):
    """Seed 7 priced at a wrong elasticity, fixed:1.0, with the template accepting every plan."""
    agent = Agent(SEED, tmp_path_factory.mktemp("cache"), elasticity=ElasticityMode("fixed", 1.0))
    simulate(SEED, deciding(agent))
    return agent


def test_the_oracle_declines_where_hold_scores_at_least_as_well(fixed_mode_run):
    labels = oracle_labels(fixed_mode_run.entries)
    queued = [e for e in fixed_mode_run.entries if e.queued]
    assert labels and len(labels) < len(queued)  # some plans are wrong at 1.5, not all
    for entry in queued:
        hold, plan = oracle_values(entry)
        assert oracle_declines(entry) == (hold >= plan) == (key(entry) in labels)
        # The plan's own estimate at 1.0 never changes the oracle's scores at 1.5.
        assert entry.pricing.elasticity == 1.0
    # A plan whose estimate at 1.5 falls to hold or below is one the oracle declines.
    declined_by_oracle = [e for e in queued if key(e) in labels]
    assert all(oracle_values(e)[1] <= oracle_values(e)[0] for e in declined_by_oracle)


def test_the_oracle_reviewer_accepts_every_queued_plan_in_true_mode(tmp_path):
    agent = Agent(SEED, tmp_path)
    agent.client = OracleReviewer(agent)
    books = simulate(SEED, deciding(agent))
    queued = [e for e in agent.entries if e.queued]
    assert queued and all(e.action != HOLD for e in queued)
    assert oracle_labels(agent.entries) == set()
    assert all(e.reason.endswith("so we take the plan.") for e in queued)
    # It decides what the template decides, so the run ends where the template run ends.
    change = sum(books.contribution(h) - simulate(SEED).contribution(h) for h in DEMO.hotels)
    assert change == pytest.approx(28818, abs=1)


@pytest.fixture(scope="module")
def oracle_fixed_run(tmp_path_factory):
    """Seed 7 at fixed:1.0 with the oracle deciding, and the cache dir it was given."""
    cache = tmp_path_factory.mktemp("oracle_cache")
    agent = Agent(SEED, cache, elasticity=ElasticityMode("fixed", 1.0))
    agent.client = OracleReviewer(agent)
    simulate(SEED, deciding(agent))
    return agent, cache


def test_the_oracle_reviewer_drives_a_run_of_its_own_in_a_wrong_mode(oracle_fixed_run):
    agent, _ = oracle_fixed_run
    # Its declines are exactly its own labels on the entries it saw.
    assert declined(agent.entries) == oracle_labels(agent.entries) != set()
    assert decline_precision(agent.entries, oracle_labels(agent.entries)) == 1.0
    assert decline_recall(agent.entries, oracle_labels(agent.entries)) == 1.0
    held = [e for e in agent.entries if e.queued and e.action == HOLD]
    assert all(e.reason.endswith("so we hold.") and e.reason_source == "oracle" for e in held)


def test_an_oracle_run_writes_nothing_to_the_cache(oracle_fixed_run):
    # The oracle is uncached: a later live run in the same mode must never read its answers
    # as the model's, so its cache folder is never even created.
    agent, cache = oracle_fixed_run
    assert agent.cache_dir.name == "seed7-fixed-1" and not agent.cache_dir.exists()
    assert list(cache.iterdir()) == []
    assert {e.reason_source for e in agent.entries if e.queued} == {"oracle"}


# ---- the scripted client -------------------------------------------------------


def test_a_scripted_client_answers_from_its_dict_of_digests(day10):
    _, table = day10
    hotel = DEMO.hotel("convention")
    entries = [entry_for(10, f, table) for f in flags(10, table) if f.hotel == "convention"]
    request = request_for(10, hotel, entries)
    [asked] = request["entries"]
    scripted = [{"id": asked["id"], "choice": HOLD, "reason": "Scripted by the test."}]
    client = ScriptedClient({request_digest(request): scripted})
    assert json.loads(client.complete(SYSTEM, json.dumps(request), {}))["decisions"] == scripted
    # A request its dict does not hold is accepted unless its key is among the declines.
    [decision] = json.loads(ScriptedClient().complete(SYSTEM, json.dumps(request), {}))["decisions"]
    assert decision == {
        "id": asked["id"],
        "choice": asked["plan"],
        "reason": f"Scripted: {asked['plan']}.",
    }
    declining = ScriptedClient(declines={(10, "convention", asked["id"])})
    [decision] = json.loads(declining.complete(SYSTEM, json.dumps(request), {}))["decisions"]
    assert decision["choice"] == HOLD


def test_a_scripted_client_declines_chosen_plans_and_is_read_back(fixed_mode_run, tmp_path):
    # The first plan the oracle would decline in the fixed:1.0 run; the scripted client
    # declines that one and accepts the rest, measured, with its calls beside the cache.
    target = min(oracle_labels(fixed_mode_run.entries))
    mode = ElasticityMode.parse("fixed:1.0")
    client = Measured(ScriptedClient(declines={target}), tmp_path / "cache" / "calls.jsonl")
    agent = Agent(SEED, tmp_path / "cache", client=client, elasticity=mode)
    simulate(SEED, deciding(agent))
    assert declined(agent.entries) == {target}
    assert decline_precision(agent.entries, oracle_labels(agent.entries)) == 1.0
    # It plays a model: its answers are cached under its own model name, scripted.
    assert agent.model == "scripted" and agent.cache_dir.name == "seed7-fixed-1-scripted"
    records = [json.loads(p.read_text()) for p in sorted(agent.cache_dir.glob("day*_*.json"))]
    assert records and {(r["source"], r["model"]) for r in records} == {("model", "scripted")}
    assert {e.reason_source for e in agent.entries if e.queued} == {"model"}
    # One call record per cache file, each a valid first answer, in memory and in the file.
    assert len(client.calls) == len(records)
    assert {(c["asked"], c["retries"], c["invalid"]) for c in client.calls} == {
        ("scripted", 0, False)
    }
    lines = (tmp_path / "cache" / "calls.jsonl").read_text().splitlines()
    assert [json.loads(line) for line in lines] == client.calls
    # A replay with a client that would decline nothing reads the declines back from the cache.
    again = Agent(SEED, tmp_path / "cache", client=ScriptedClient(), replay=True, elasticity=mode)
    simulate(SEED, deciding(again))
    assert declined(again.entries) == {target}
