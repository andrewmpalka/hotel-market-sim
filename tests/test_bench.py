"""bench.py: the oracle reviewer as a grader, the reviewer measures and the reviewers. It also
covers the pooled counts, the price table and the scripted client."""

import json
import math
from dataclasses import replace

import pytest

from hotel_market.agent import Agent, ElasticityMode
from hotel_market.bench import (
    ORACLE,
    PRICES,
    TEMPLATE,
    DeclineCounts,
    OracleReviewer,
    Reviewer,
    ScriptedClient,
    accept_rate,
    by_standard_error,
    cost,
    counted,
    decline_f1,
    decline_precision,
    decline_recall,
    declined,
    dollar_weighted_recall,
    failed_requests,
    invalid_answers,
    key,
    live,
    on_recent_changes,
    oracle,
    oracle_declines,
    oracle_labels,
    oracle_values,
    recovered_share,
    regret,
    retries,
)
from hotel_market.bookings import simulate
from hotel_market.customer import demo
from hotel_market.detect import AHEAD, flags
from hotel_market.model import MODELS, SYSTEM, ClaudeClient, Measured, request_digest, request_for
from hotel_market.plan import (
    HOLD,
    Candidate,
    Entry,
    FlagNumbers,
    Pricing,
    Range,
    StayDate,
    WeekdayGroup,
    entry_for,
)
from hotel_market.simulated import deciding

DEMO = demo()
SEED = 7


def _entry(day, first, gain, action=None, plan_rate=133.0, hotel="airport"):
    """A made-up queued entry worth `gain` over holding by its own estimate, accepted unless action
    is HOLD. Its one stay date has 10 rooms left against 1,000 rooms of demand. Every candidate
    therefore sells those 10, and the oracle's loss from the plan is 10 x (140 - rate)."""
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
LABELS = {key(B), key(C)}  # the labels the tests hand to the measures


def test_regret_is_the_oracle_arms_change_minus_the_arms_change():
    assert regret(32899.0, 8438.0) == pytest.approx(24461.0)
    assert regret(100.0, 120.0) == pytest.approx(-20.0)


def test_the_recovered_share_is_the_gain_over_the_template_as_a_share_of_the_oracles():
    # The template earned +11,989, the oracle +34,117 and the reviewer +20,510 on the same
    # seeds and mode: it recovered 39% of what a reviewer could.
    assert recovered_share(11989.0, 34117.0, 20510.0) == pytest.approx(8521 / 22128)
    assert recovered_share(11989.0, 34117.0, 34117.0) == 1.0  # the oracle itself
    assert recovered_share(11989.0, 34117.0, 11989.0) == 0.0  # accept-all
    assert recovered_share(100.0, 300.0, 50.0) == pytest.approx(-0.25)  # worse than accept-all
    assert math.isnan(recovered_share(35648.0, 35648.0, 35648.0))  # the true mode: no room


def test_accept_rate_counts_accepted_queued_plans():
    assert not E.queued and declined(ENTRIES) == {key(A), key(B)}
    assert accept_rate(ENTRIES) == pytest.approx(2 / 4)
    assert math.isnan(accept_rate([E]))


def test_decline_precision_recall_and_f1_against_the_oracle():
    # Of the reviewer's two declines the oracle shares one; of the oracle's two the reviewer
    # shares one.
    assert decline_precision(ENTRIES, LABELS) == pytest.approx(1 / 2)
    assert decline_recall(ENTRIES, LABELS) == pytest.approx(1 / 2)
    assert decline_f1(ENTRIES, LABELS) == pytest.approx(1 / 2)
    # The weight is the oracle's loss from accepting, hold minus plan at 1.5: $70 for B and
    # $140 for C, so the reviewer caught $70 of the $210 at stake.
    assert oracle_values(B) == pytest.approx((933.33, 863.33), abs=0.01)
    assert oracle_values(C) == pytest.approx((933.33, 793.33), abs=0.01)
    assert dollar_weighted_recall(ENTRIES, LABELS) == pytest.approx(70 / 210)
    # The plan's own value at stake is not the weight: by it the share would be 600 / 1,600.
    assert B.value_at_stake == 600 and C.value_at_stake == 1000


def test_the_measures_are_nan_when_nobody_declined():
    accepted = [C, D]
    assert math.isnan(decline_precision(accepted, LABELS))  # the reviewer declined nothing
    assert math.isnan(decline_recall(ENTRIES, set()))  # the oracle declined nothing
    assert math.isnan(decline_f1(ENTRIES, set()))
    assert math.isnan(dollar_weighted_recall(ENTRIES, set()))
    assert decline_f1([A], {key(B)}) == 0.0  # both declined something, nothing in common


def test_decline_counts_pool_the_step_1_measures():
    # On one run the counts give the measures above, with the oracle's own labels: it would
    # decline every one of the four plans, since each cuts the rate, so A and B agree with it.
    labels = oracle_labels(ENTRIES)
    assert labels == {key(A), key(B), key(C), key(D)}
    counts = DeclineCounts.of(ENTRIES)
    assert (counts.queued, counts.accepted, counts.declined) == (4, 2, 2)
    assert (counts.oracle, counts.agreed) == (4, 2)
    assert counts.accept_rate == accept_rate(ENTRIES) == 0.5
    assert counts.precision == decline_precision(ENTRIES, labels) == 1.0
    assert counts.recall == decline_recall(ENTRIES, labels) == 0.5
    assert counts.f1 == pytest.approx(decline_f1(ENTRIES, labels))
    assert counts.dollar_recall == pytest.approx(dollar_weighted_recall(ENTRIES, labels))
    assert counts.loss == pytest.approx(70 + 70 + 140 + 70) and counts.caught == pytest.approx(140)
    # Two runs add: the counts double and the rates hold, so an arm pools its seeds.
    pooled = counts + counts
    assert pooled.queued == 8 and pooled.agreed == 4 and pooled.loss == pytest.approx(700)
    assert (pooled.accept_rate, pooled.precision, pooled.recall) == (0.5, 1.0, 0.5)
    assert pooled.dollar_recall == pytest.approx(counts.dollar_recall)
    # The nan rules are the functions': no decline, no precision; no oracle decline, no recall.
    empty = DeclineCounts.of([E])
    assert math.isnan(empty.accept_rate) and math.isnan(empty.precision)
    assert math.isnan(empty.recall) and math.isnan(empty.f1) and math.isnan(empty.dollar_recall)
    assert sum([counts, empty], DeclineCounts()) == counts


def test_the_three_kinds_of_reviewer_make_their_clients(tmp_path, monkeypatch):
    mode = ElasticityMode.parse("fixed:1.0")
    agent = Agent(SEED, tmp_path, elasticity=mode)
    assert TEMPLATE.client_for(agent) is None and TEMPLATE.model is None and not TEMPLATE.live
    oracle = ORACLE.client_for(agent)
    assert isinstance(oracle, OracleReviewer) and oracle.agent is agent and not ORACLE.live
    # A model: a measured Claude client, its calls beside the arm's own cache. Building the
    # client reads the key; nothing is sent.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-a-key")
    reviewer = live("claude-haiku-5-5")
    assert reviewer.live and reviewer.name == reviewer.model == "claude-haiku-5-5"
    haiku = Agent(SEED, tmp_path, elasticity=mode, model=reviewer.model)
    client = reviewer.client_for(haiku)
    assert isinstance(client, Measured) and isinstance(client.client, ClaudeClient)
    assert client.client.model == "claude-haiku-5-5" and client.model == "claude-haiku-5-5"
    assert client.path == haiku.cache_dir / "calls.jsonl"
    assert haiku.cache_dir.name == "seed7-fixed-1-claude-haiku-5-5"
    assert Reviewer("x", "x", lambda agent: None).live


def test_a_models_cost_comes_from_the_price_table():
    assert set(PRICES) == set(MODELS)
    calls = [
        {"input_tokens": 1200, "output_tokens": 300},
        {"input_tokens": 800, "output_tokens": 200, "bad_attempt": True},  # paid for all the same
    ]
    assert cost(calls, "claude-opus-5-5") == pytest.approx((2000 * 4.00 + 500 * 20.00) / 1e6)
    assert cost(calls, "claude-haiku-5-5") == pytest.approx((2000 * 0.10 + 500 * 0.50) / 1e6)
    assert cost([], "claude-sonnet-5-5") == 0.0
    assert math.isnan(cost(calls, "scripted"))


def test_a_call_a_fallback_model_answered_is_priced_at_that_model():
    # The API's fallback can answer with another model than the one asked; the record names it.
    calls = [
        {"model": "claude-opus-5-5", "input_tokens": 1000, "output_tokens": 100},
        {
            "model": "claude-sonnet-5-5",
            "input_tokens": 1000,
            "output_tokens": 100,
            "fallback": True,
        },
        {"input_tokens": 1000, "output_tokens": 100},  # no model field: priced at the one asked
    ]
    opus, sonnet = (1000 * 4.00 + 100 * 20.00) / 1e6, (1000 * 2.00 + 100 * 10.00) / 1e6
    assert cost(calls, "claude-opus-5-5") == pytest.approx(opus + sonnet + opus)
    assert cost(calls, "claude-haiku-5-5") == pytest.approx(
        opus + sonnet + (1000 * 0.10 + 100 * 0.50) / 1e6
    )
    assert math.isnan(cost([{"model": "scripted", "input_tokens": 1}], "claude-opus-5-5"))


def test_a_duplicate_call_record_is_counted_once(tmp_path):
    # An arm's calls.jsonl is appended across runs while its cache can be deleted, so a rerun
    # after deleting the cache writes a second record for the same request. The report keeps
    # the last record per digest, and only a digest whose cache file is present or that failed.
    folder = tmp_path / "seed7-fixed-1"
    folder.mkdir()
    (folder / "day010_convention.json").write_text(json.dumps({"request_digest": "a"}))
    first = {"request_digest": "a", "input_tokens": 1000, "output_tokens": 100}
    again = {"request_digest": "a", "input_tokens": 1100, "output_tokens": 110}  # the rerun
    gone = {"request_digest": "b", "input_tokens": 1000, "output_tokens": 100}  # cache deleted
    failed = {"request_digest": "c", "input_tokens": 300, "output_tokens": 0, "failed": True}
    older = {"input_tokens": 500, "output_tokens": 50}  # from before the digest field
    records = [first, gone, older, failed, again]
    merged = {**again, "bad_attempt": 0, "retries": 0}  # the two clean runs of one request
    assert counted(records, folder) == [older, merged, failed]
    assert cost(counted(records, folder), "claude-opus-5-5") == pytest.approx(
        ((1100 + 300 + 500) * 4.00 + (110 + 0 + 50) * 20.00) / 1e6
    )
    assert counted(records, tmp_path / "missing") == [older, failed]


def test_a_failed_record_followed_by_a_good_one_sums_its_attempts(tmp_path):
    # A request that failed in one run and answered in the rerun: the outcome, tokens and
    # time come from the last record, and the bad attempts and retries add up over both.
    folder = tmp_path / "seed8-claude-sonnet-5-5"
    folder.mkdir()
    (folder / "day020_airport.json").write_text(json.dumps({"request_digest": "a"}))
    failed = {
        "request_digest": "a",
        "input_tokens": 13632,
        "output_tokens": 408,
        "seconds": 7.4,
        "retries": 2,
        "bad_attempt": True,
        "failed": True,
        "error": "ValueError",
    }
    good = {**failed, "input_tokens": 9088, "output_tokens": 300, "seconds": 5.0, "retries": 1}
    good.update(failed=False, error=None)
    [record] = counted([failed, good], folder)
    assert record["failed"] is False and record["error"] is None
    assert record["input_tokens"] == 9088 and record["seconds"] == 5.0
    assert record["bad_attempt"] == 2 and record["retries"] == 3
    assert invalid_answers([record]) == 2 and retries([record]) == 3
    assert failed_requests([record]) == 0
    # In the other order the later failure is the outcome, and the attempts still add up.
    [record] = counted([good, failed], folder)
    assert record["failed"] is True and record["bad_attempt"] == 2 and record["retries"] == 3


def test_bad_attempts_failed_requests_and_retries_are_counted():
    calls = [
        {"retries": 2, "bad_attempt": True, "failed": False},  # answered on the third try
        {"retries": 0, "bad_attempt": True, "failed": True},  # a refusal: never answered
        {"retries": 0, "bad_attempt": False, "failed": False},
        {},  # a record from before the flags
    ]
    assert invalid_answers(calls) == 2 and failed_requests(calls) == 1 and retries(calls) == 2


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
    assert change == pytest.approx(19012, abs=1)


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


def test_the_oracle_reviewer_is_told_the_demand_bias(fixed_mode_run, tmp_path):
    # At 1.0 the command's oracle is ORACLE itself. At another bias it is a reviewer of its own,
    # whose client scales the remaining demand by the bias and names it in every reason.
    assert oracle(1.0) is ORACLE and oracle(0.9) is not ORACLE and oracle(0.9).name == "oracle"
    agent = Agent(SEED, tmp_path, elasticity=ElasticityMode("fixed", 1.0))
    client = oracle(0.9).client_for(agent)
    assert isinstance(client, OracleReviewer) and client.demand_bias == 0.9 and not client.cached
    queued = [e for e in fixed_mode_run.entries if e.queued]
    lower = 0
    for entry in queued:
        hold, plan = oracle_values(entry)
        hold_at, plan_at = oracle_values(entry, demand_bias=0.9)
        assert hold_at <= hold and plan_at <= plan  # fewer rooms to come are worth less
        lower += hold_at < hold
        assert oracle_declines(entry, demand_bias=0.9) == (hold_at >= plan_at)
    assert lower
    labels = oracle_labels(queued, demand_bias=0.9)
    assert labels == {key(e) for e in queued if oracle_declines(e, demand_bias=0.9)}
    assert DeclineCounts.of(fixed_mode_run.entries, demand_bias=0.9).oracle == len(labels)
    agent.client = client
    simulate(SEED, deciding(agent), last_day=10, demand_bias=0.9)
    reasons = [e.reason for e in agent.entries if e.queued]
    assert reasons and all(
        "of 1.5 and demand bias of 0.9, a market elasticity of 1, holding" in r for r in reasons
    )


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
    assert {(c["asked"], c["retries"], c["bad_attempt"], c["failed"]) for c in client.calls} == {
        ("scripted", 0, False, False)
    }
    lines = (tmp_path / "cache" / "calls.jsonl").read_text().splitlines()
    assert [json.loads(line) for line in lines] == client.calls
    # A replay with a client that would decline nothing reads the declines back from the cache.
    again = Agent(SEED, tmp_path / "cache", client=ScriptedClient(), replay=True, elasticity=mode)
    simulate(SEED, deciding(again))
    assert declined(again.entries) == {target}


def test_the_oracle_reviewer_is_told_the_market_elasticity_and_the_reaction(
    fixed_mode_run, tmp_path
):
    # Told nothing, the oracle scores at the market elasticity each plan was priced with.
    assert oracle(1.0, None, 0.0) is ORACLE and oracle(1.0, 0.5, 0.0) is not ORACLE
    assert oracle(1.0, 0.0, 0.0) is not ORACLE
    agent = Agent(SEED, tmp_path, elasticity=ElasticityMode("fixed", 1.0))
    client = oracle(1.0, 0.5, 0.5).client_for(agent)
    assert (client.demand_bias, client.market_elasticity, client.reaction_share) == (1.0, 0.5, 0.5)
    queued = [e for e in fixed_mode_run.entries if e.queued]
    raises = [e for e in queued if all(part.startswith("raise") for part in e.plan.split("; "))]
    assert raises
    # Told that competitors follow half of a raise, the oracle expects it to cost fewer rooms, so
    # a raise it declines with the reaction is one it declines without it too.
    for entry in raises:
        if oracle_declines(entry, reaction_share=0.5):
            assert oracle_declines(entry)
    labels = oracle_labels(queued, market_elasticity=0.5, reaction_share=0.5)
    counts = DeclineCounts.of(
        fixed_mode_run.entries, demand_bias=1.0, market_elasticity=0.5, reaction_share=0.5
    )
    assert counts.oracle == len(labels)
    agent.client = client
    simulate(SEED, deciding(agent), last_day=10, react=True, market_elasticity=0.5)
    reasons = [e.reason for e in agent.entries if e.queued]
    assert reasons and all(
        "a market elasticity of 0.5, with competitors following 50% of a change, holding" in r
        for r in reasons
    )


def _learned(day, first, action, standard_error, hotel="airport"):
    """A hand-built queued entry priced in learn mode with the given standard error."""
    entry = _entry(day, first, 400.0, action=action, hotel=hotel)
    pricing = Pricing(1.3, "learn", standard_error=standard_error, prior=1.0, observations=800)
    return replace(entry, pricing=pricing)


def test_the_decline_rate_by_standard_error_groups_a_learn_arms_queue():
    entries = [
        _learned(10, 40, HOLD, 0.10),
        _learned(10, 41, "lower 5%", 0.12),
        _learned(11, 42, HOLD, 0.20),
        _learned(12, 43, HOLD, 0.30),
        _learned(12, 44, "lower 5%", 0.30),
        _learned(13, 45, "lower 5%", 0.50),
        _entry(14, 46, 400.0, action=HOLD),  # a true-mode plan has no standard error: left out
    ]
    rows = by_standard_error(entries)
    assert [row[0] for row in rows] == [
        "under 0.15",
        "0.15 to 0.25",
        "0.25 to 0.35",
        "0.35 and over",
    ]
    assert [(queued, declined) for _, queued, declined, _ in rows] == [
        (2, 1),
        (1, 1),
        (2, 1),
        (1, 0),
    ]
    assert [round(rate, 2) for *_, rate in rows] == [0.5, 1.0, 0.5, 0.0]
    [(_, queued, declined, rate)] = by_standard_error(entries[:1], edges=())
    assert (queued, declined, rate) == (1, 1, 1.0)
    assert all(math.isnan(rate) for *_, rate in by_standard_error([]))


def test_the_plans_on_recently_changed_dates_are_counted_with_their_declines():
    # Day 10 changes stay 40. Day 20's plan on 40 is within 14 days of it; day 25's is not.
    # Day 20's declined plan on 41 is on an untouched date, so it is shown elsewhere.
    entries = [
        _entry(10, 40, 400.0, action="lower 5%"),
        _entry(20, 40, 400.0, action=HOLD),
        _entry(20, 41, 400.0, action=HOLD),
        _entry(22, 40, 400.0, action="lower 5%"),
        _entry(25, 40, 400.0, action="lower 5%"),
        _entry(30, 40, 400.0, action="lower 5%"),
    ]
    assert on_recent_changes(entries) == (4, 1)  # days 20, 22, 25 and 30; day 20 on 41 is not
    assert on_recent_changes(entries, window=5) == (2, 0)  # days 25 and 30 after day 22
    assert on_recent_changes([]) == (0, 0)
