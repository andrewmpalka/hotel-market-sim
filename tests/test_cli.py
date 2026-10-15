"""Module 8: the two runs, decisions.jsonl, the replay, the summary and the bench."""

import json
import math
import statistics
from dataclasses import replace

import numpy as np
import pytest

from hotel_market.agent import MIN_STAY, TRUE_MODE, Agent, ElasticityMode
from hotel_market.bench import (
    ORACLE,
    TEMPLATE,
    DeclineCounts,
    Reviewer,
    ScriptedClient,
    accept_rate,
    decline_f1,
    decline_precision,
    decline_recall,
    dollar_weighted_recall,
    key,
    oracle_labels,
    recovered_share,
)
from hotel_market.bookings import simulate
from hotel_market.cli import (
    BENCH_MODES,
    MEDIAN_CAUSES,
    NO_KEY_LINE,
    REPEAT_WINDOW,
    REPORT_DAYS,
    SEAT_CAUSES,
    SHOCK_PLAN_CAUSES,
    ArmResult,
    Comparison,
    SeedResult,
    _calls,
    _comparison_table,
    _gain_on,
    changed_stays,
    format_entry,
    main,
    own_median_flags,
    queue,
    repeat_changes,
    replay,
    run,
    summary,
    sweep,
)
from hotel_market.customer import demo
from hotel_market.detect import NEW_EVENT, PACE, SEATS_UP
from hotel_market.estimate import Estimate
from hotel_market.model import Measured
from hotel_market.plan import HOLD
from hotel_market.policy import PacePolicy
from hotel_market.schedule import DEFAULT_SCENARIO, UPGAUGE_SCENARIO
from hotel_market.simulated import deciding

DEMO = demo()

SEED = 7


class FakeClient:
    """Stands in for the model: accepts each plan and says so."""

    def complete(self, system, prompt, schema):
        entries = json.loads(prompt)["entries"]
        return json.dumps(
            {
                "decisions": [
                    {"id": e["id"], "choice": e["plan"], "reason": f"Fake reason for {e['id']}."}
                    for e in entries
                ]
            }
        )


class NoCalls:
    def complete(self, system, prompt, schema):
        raise AssertionError("the model was called")


@pytest.fixture(scope="module")
def first(tmp_path_factory):
    """A seed-7 run whose answers come from the fake model and land in the cache."""
    folder = tmp_path_factory.mktemp("first")
    fixed, books, agent = run(SEED, folder / "decisions.jsonl", folder / "cache", FakeClient())
    return folder, fixed, books, agent


def test_two_runs_with_the_same_seed_write_identical_decisions_files(first, tmp_path):
    folder, *_ = first
    run(SEED, tmp_path / "decisions.jsonl", tmp_path / "cache", FakeClient())
    assert (tmp_path / "decisions.jsonl").read_bytes() == (folder / "decisions.jsonl").read_bytes()


def test_a_rerun_reads_the_cache_first(first, tmp_path):
    folder, *_ = first
    run(SEED, tmp_path / "again.jsonl", folder / "cache", NoCalls())
    assert (tmp_path / "again.jsonl").read_bytes() == (folder / "decisions.jsonl").read_bytes()


def test_replaying_day_20_makes_no_model_call_and_prints_the_same_entries(first):
    folder, _, _, agent = first
    entries, _ = replay(SEED, 20, folder / "cache", client=NoCalls())
    original = [e for e in agent.entries if e.day == 20]
    assert queue(entries)
    assert [format_entry(e, DEMO) for e in queue(entries)] == [
        format_entry(e, DEMO) for e in queue(original)
    ]
    # The client is never called in a replay; these reasons can only be the cached model answers.
    assert all(e.reason.startswith("Fake reason") for e in queue(entries))
    # Without a client the same day is replayed with the template's reasons instead.
    from_template, _ = replay(SEED, 20, folder / "cache")
    assert [e.plan for e in queue(from_template)] == [e.plan for e in queue(entries)]
    assert not any(e.reason.startswith("Fake reason") for e in queue(from_template))


@pytest.mark.parametrize(
    "argv",
    [
        ["--seeds", "5", "3"],  # FIRST after LAST
        ["--seed", "-1"],  # a negative seed
        ["--seed", "seven"],  # not a number
        ["--seeds", "1", "5", "--replay", "20"],  # a replay needs one seed
        ["--seed", "7", "--replay", "60"],  # the agent decides on days 0 to 59
        ["--seed", "7", "--elasticity", "guess:1"],  # true, fixed:X or learn:X
        ["--seed", "7", "--elasticity", "true", "--elasticity", "learn:1"],  # one per seed
        ["--seed", "7", "--cautious"],  # cautious needs a learn mode
        ["--seed", "7", "--elasticity", "fixed:1.0", "--cautious"],
        ["--seeds", "1", "2", "--elasticity", "true", "--cautious"],
    ],
)
def test_the_command_rejects_bad_arguments(argv):
    with pytest.raises(SystemExit):
        main(argv)


def test_the_queue_holds_plans_worth_the_minimum_highest_value_first(first):
    _, _, _, agent = first
    for day in range(60):
        entries = queue([e for e in agent.entries if e.day == day])
        assert all(e.value_at_stake >= DEMO.min_value_at_stake for e in entries)
        values = [e.value_at_stake for e in entries]
        assert values == sorted(values, reverse=True)
    small = [e for e in agent.entries if e.changed_weekdays and not e.queued]
    assert small and not any(e in queue(agent.entries) for e in small)


def test_the_replay_command_prints_day_20s_queue(first, monkeypatch, capsys):
    folder, *_ = first
    monkeypatch.chdir(folder)
    main(["--seed", str(SEED), "--replay", "20"])
    out = capsys.readouterr().out
    assert "Day 20 | Airport hotel | stay dates 50 to 109" in out
    assert (
        "Raise 5% on Tue; raise 10% on Mon, Wed, Thu, Fri, Sun: "
        "$140 becomes $147 to $154 on 52 stay dates"
    ) in out
    assert "Value at stake" in out
    assert "Elasticity      1.5, the simulator's own value" in out


def test_a_run_with_no_key_says_so_and_names_the_template(monkeypatch, capsys, tmp_path):
    """Without a key the template accepts every plan. A run that did not ask for the template
    prints one line saying so, and every summary names who answered the queue."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # decisions.jsonl lands here
    main(["--seed", str(SEED)])
    out = capsys.readouterr().out
    assert out.startswith(NO_KEY_LINE + "\n")
    assert "0 declined by the template)." in out and "declined by the model" not in out
    main(["--seed", str(SEED), "--template"])
    out = capsys.readouterr().out
    assert NO_KEY_LINE not in out and "0 declined by the template)." in out


def test_the_summary_reports_revenue_and_contribution_for_both_runs(first):
    _, fixed, books, agent = first
    text = summary(SEED, fixed, books, agent)
    for hotel in DEMO.hotels:
        line = next(row for row in text.splitlines() if row.startswith(hotel.name))
        for value in (
            fixed.room_revenue(hotel),
            books.room_revenue(hotel),
            fixed.contribution(hotel),
            books.contribution(hotel),
        ):
            assert f"{value:,.0f}" in line
    assert "All four hotels" in text and "held" in text
    assert "0 declined by the model)." in text  # the fake model answered the queue
    # The total row's title counts the hotels of the market, so another market reads right.
    rows = [Comparison(f"hotel {i}", 1.0, 1.0, 1.0, 1.0) for i in range(5)]
    assert _comparison_table("t", rows)[-1].startswith("All five hotels")


def test_decisions_jsonl_has_one_line_per_flag_and_advice(first):
    folder, _, _, agent = first
    lines = [json.loads(row) for row in (folder / "decisions.jsonl").read_text().splitlines()]
    advice = [line for line in lines if not line["simulated"]]
    assert len(lines) == len(agent.entries) + len(advice)
    for line in lines:
        assert {
            "day",
            "hotel",
            "stays",
            "causes",
            "action",
            "reason",
            "value_at_stake",
            "simulated",
        } <= set(line)
    for line in lines:
        if line["simulated"]:
            assert {"numbers", "by_weekday", "plan", "new_rates"} <= set(line)
            assert (line["new_rates"] is None) == (line["action"] == HOLD)
            assert line["action"] in (HOLD, line["plan"])
    assert all(line["action"] == MIN_STAY and line["value_at_stake"] is None for line in advice)


def test_changed_stays_are_the_pairs_whose_rate_the_agent_changed(first):
    _, fixed, books, agent = first
    stays = changed_stays(agent)
    for hotel in DEMO.hotels:
        i = hotel.row
        moved = np.flatnonzero(books.rates[i] != fixed.rates[i]).tolist()
        assert stays[hotel.key] == moved
    assert sum(len(s) for s in stays.values()) > 0


def test_every_other_pair_books_the_same_in_both_runs(first):
    # One random number per draw: the runs differ only where the agent changed a rate.
    _, fixed, books, agent = first
    stays = changed_stays(agent)
    same = np.ones(fixed.rooms.shape, dtype=bool)
    for hotel_key, changed in stays.items():
        same[DEMO.hotel(hotel_key).row, changed] = False
    assert np.array_equal(books.rooms[same], fixed.rooms[same])
    assert np.array_equal(books.revenue[same], fixed.revenue[same])


def test_the_summary_compares_both_runs_on_the_changed_pairs(first):
    _, fixed, books, agent = first
    stays = changed_stays(agent)
    text = summary(SEED, fixed, books, agent)
    pairs = sum(len(s) for s in stays.values())
    assert f"over only the {pairs} hotel and stay-date pairs where the agent changed a rate" in text
    for hotel in DEMO.hotels:
        line = next(
            row
            for row in text.splitlines()
            if row.startswith(f"{hotel.name} ({len(stays[hotel.key])})")
        )
        for value in (
            fixed.room_revenue(hotel, stays[hotel.key]),
            books.room_revenue(hotel, stays[hotel.key]),
            fixed.contribution(hotel, stays[hotel.key]),
            books.contribution(hotel, stays[hotel.key]),
        ):
            assert f"{value:,.0f}" in line
    # Since every other pair books the same, the changes over the pairs are the whole change.
    for measure in ("room_revenue", "contribution"):
        total = sum(getattr(books, measure)(h) - getattr(fixed, measure)(h) for h in DEMO.hotels)
        on_pairs = sum(
            getattr(books, measure)(h, stays[h.key]) - getattr(fixed, measure)(h, stays[h.key])
            for h in DEMO.hotels
        )
        assert on_pairs == pytest.approx(total)


def test_the_sweep_gives_each_seeds_change_over_the_fixed_run(first, tmp_path):
    _, fixed, books, agent = first
    [arm] = sweep(SEED, SEED, tmp_path / "cache")
    [result] = arm.seeds
    assert arm.mode == TRUE_MODE and result.seed == SEED
    assert result.estimated == pytest.approx(
        sum(e.value_at_stake for e in agent.entries if e.action != HOLD)
    )
    # The template accepts every plan, as the fake model does, so the runs match.
    assert result.contribution_change == pytest.approx(
        sum(books.contribution(h) - fixed.contribution(h) for h in DEMO.hotels)
    )
    assert result.revenue_change == pytest.approx(
        sum(books.room_revenue(h) - fixed.room_revenue(h) for h in DEMO.hotels)
    )
    assert result.rate_changes == sum(1 for e in agent.entries if e.action != HOLD)
    # Every other pair books the same, so the gain on the changed pairs is the whole change,
    # in whichever measure the target names.
    pairs = {(e.hotel, s) for e in agent.entries if e.action != HOLD for s in e.new_rates}
    assert _gain_on(fixed, books, pairs, DEMO.hotels) == pytest.approx(result.contribution_change)
    assert _gain_on(fixed, books, pairs, DEMO.hotels, "revenue") == pytest.approx(
        result.revenue_change
    )


ROWS = [
    SeedResult(1, 100.4, -20.0, 3, 120.0, shock_changes=2, shock_gain=90.0, other_changes=1),
    SeedResult(2, -50.6, 15.0, 1, 30.0, other_changes=1, other_gain=-50.6),
    SeedResult(
        3, 10.0, 0.0, 2, 20.0, shock_changes=1, shock_gain=4.0, other_changes=1, other_gain=6.0
    ),
]


def test_the_seeds_command_prints_each_seed_and_the_mean_and_range(monkeypatch, capsys):
    monkeypatch.setattr(
        "hotel_market.cli.sweep",
        lambda first, last, modes, customer, **world: [ArmResult(TRUE_MODE, ROWS)],
    )
    main(["--seeds", "1", "3"])
    out = capsys.readouterr().out
    printed = [line.split() for line in out.splitlines() if line[:4].strip().isdigit()]
    assert printed == [["1", "+100", "-20", "3"], ["2", "-51", "+15", "1"], ["3", "+10", "+0", "2"]]
    # The mean of the unrounded changes: (100.4 - 50.6 + 10.0) / 3 = 19.93.
    # The standard deviation of the three changes is 76 and its standard error 44; two of three
    # seeds ahead is what a fair coin gives, so the sign test's p is 1.0.
    assert (
        "Contribution change: mean +20 (sd 76, se 44), range -51 to +100; "
        "higher than the fixed-rate run in 2 of 3 seeds (sign test p 1.0). "
        "The accepted plans were estimated to earn +170 and earned +60."
    ) in out
    assert "Revenue change: mean -2 (sd 18, se 10), range -20 to +15." in out
    assert "Where the gain came from" in out
    source, filings = [line.split() for line in out.splitlines() if line.startswith("true ")]
    assert source == ["true", "3", "+94", "3", "-45"]
    assert filings == ["true", "0", "0", "6"]  # the filings table: no filings in these rows


def test_a_revenue_target_arm_counts_wins_and_earnings_in_revenue(monkeypatch, capsys):
    arm = ArmResult(TRUE_MODE, ROWS, "revenue")
    assert arm.wins == 1 and arm.realised == pytest.approx(-5.0)
    monkeypatch.setattr(
        "hotel_market.cli.sweep",
        lambda first, last, modes, customer, **world: [arm],
    )
    main(["--seeds", "1", "3", "--target", "revenue"])
    out = capsys.readouterr().out
    assert "candidates scored on revenue" in out
    assert "Contribution change: mean +20 (sd 76, se 44), range -51 to +100." in out
    assert (
        "Revenue change: mean -2 (sd 18, se 10), range -20 to +15; higher than the fixed-rate run "
        "in 1 of 3 seeds (sign test p 1.0). The accepted plans were estimated to earn +170 and "
        "earned -5."
    ) in out


def test_the_seeds_command_prints_one_row_per_arm_and_a_learn_arms_estimates(monkeypatch, capsys):
    learn = ElasticityMode.parse("learn:1.0")
    found = {
        (day, h.key): Estimate(1.0 + 0.01 * day + 0.1 * i, 0.3, 90 * day, 1.0, 0.0)
        for day in REPORT_DAYS
        for i, h in enumerate(DEMO.hotels)
    }
    learned = [
        replace(r, estimates=found, rejected_at_an_end=rejected)
        for r, rejected in zip(ROWS, (2, 1, 0))
    ]
    cautious = replace(learn, cautious=True)
    arms = [ArmResult(TRUE_MODE, ROWS), ArmResult(cautious, learned)]
    monkeypatch.setattr(
        "hotel_market.cli.sweep",
        lambda first, last, modes, customer, **world: arms,
    )
    main(["--seeds", "1", "3", "--elasticity", "true", "--elasticity", "learn:1.0", "--cautious"])
    out = capsys.readouterr().out
    rows = [line.split() for line in out.splitlines() if line.startswith(("true", "learn:1"))]
    # The mean revenue change of the rows is (-20 + 15 + 0) / 3 = -1.67. After the mean change
    # come its standard deviation and standard error, and after the wins the sign test's p.
    assert rows[0] == [
        "true",
        "+20",
        "76",
        "44",
        "-2",
        "-51",
        "to",
        "+100",
        "2/3",
        "1.0",
        "6",
        "+170",
        "+60",
        "2.84",
        "-",
    ]
    assert rows[1][:2] == ["learn:1", "cautious"] and rows[1][2:] == rows[0][1:-1] + ["3"]
    assert rows[2] == ["true", "3", "+94", "3", "-45"]  # where the gain came from
    assert rows[3] == ["learn:1", "cautious", "3", "+94", "3", "-45"]
    assert "Elasticity learn:1 cautious: the estimate each hotel priced with" in out
    assert "  59" in out and "1.59 (1.59 to 1.59)" in out  # day 59, the convention hotel


def test_the_default_mode_still_gives_19012_on_seed_7(first):
    _, fixed, books, _ = first
    change = sum(books.contribution(h) - fixed.contribution(h) for h in DEMO.hotels)
    assert change == pytest.approx(19012, abs=1)


@pytest.mark.slow
def test_the_default_mode_still_gives_a_20_seed_mean_of_32899(tmp_path):
    [arm] = sweep(1, 20, tmp_path / "cache")
    assert statistics.mean(arm.changes) == pytest.approx(32899, abs=1)
    assert arm.wins == 20


# ---- the bench ------------------------------------------------------------------

TARGET = (10, "convention", "45-48")  # the convention's plan on day 10, queued in every seed
FIXED_1 = ElasticityMode.parse("fixed:1.0")


def _scripted() -> Reviewer:
    """A model that declines the convention's day-10 plan and accepts the rest, measured."""
    return Reviewer(
        "scripted",
        "scripted",
        lambda agent: Measured(ScriptedClient(declines={TARGET}), agent.cache_dir / "calls.jsonl"),
    )


@pytest.fixture(scope="module")
def bench_arms(tmp_path_factory):
    """Seeds 1 and 2 at fixed:1.0 with the template, the oracle and the scripted model."""
    cache = tmp_path_factory.mktemp("bench") / "cache"
    return cache, sweep(1, 2, cache, [FIXED_1], reviewers=[TEMPLATE, ORACLE, _scripted()])


def _same(a: float, b: float) -> bool:
    return (math.isnan(a) and math.isnan(b)) or a == pytest.approx(b)


def test_a_sweep_with_reviewers_keeps_each_arms_entries_calls_and_counts(bench_arms):
    cache, arms = bench_arms
    template, oracle, scripted = arms
    assert [arm.reviewer.name for arm in arms] == ["template", "oracle", "scripted"]
    assert {arm.mode for arm in arms} == {FIXED_1} and all(len(arm.seeds) == 2 for arm in arms)
    # The template declines nothing, the oracle's declines are its own labels, and the scripted
    # model declines the one plan in each seed.
    assert template.counts.declined == 0 and template.counts.accept_rate == 1.0
    assert oracle.counts.precision == oracle.counts.recall == 1.0 and oracle.counts.declined > 0
    assert scripted.counts.declined == 2
    for result in scripted.seeds:
        held = [e for e in result.entries if e.queued and e.action == HOLD]
        assert [key(e) for e in held] == [TARGET]
    # Each seed's counts are the step-1 measures on its own entries, labelled by the oracle,
    # and the arm's counts are their sum.
    for arm in arms:
        for result in arm.seeds:
            labels = oracle_labels(result.entries)
            counts = result.counts
            assert counts == DeclineCounts.of(result.entries)
            assert _same(counts.accept_rate, accept_rate(result.entries))
            assert _same(counts.precision, decline_precision(result.entries, labels))
            assert _same(counts.recall, decline_recall(result.entries, labels))
            assert _same(counts.f1, decline_f1(result.entries, labels))
            assert _same(counts.dollar_recall, dollar_weighted_recall(result.entries, labels))
        assert arm.counts == sum((r.counts for r in arm.seeds), DeclineCounts())
    # Only the scripted model wrote a cache, in its own folder, with its calls beside it: one
    # call record per cache file, read back from the file.
    assert sorted(p.name for p in cache.iterdir()) == [
        "seed1-fixed-1-scripted",
        "seed2-fixed-1-scripted",
    ]
    for result in scripted.seeds:
        folder = cache / f"seed{result.seed}-fixed-1-scripted"
        assert len(result.calls) == len(list(folder.glob("day*_*.json"))) > 0
        lines = (folder / "calls.jsonl").read_text().splitlines()
        assert result.calls == [json.loads(line) for line in lines]
    assert template.calls == [] and oracle.calls == []


def test_the_bench_command_prints_its_tables(bench_arms, monkeypatch, capsys):
    _, arms = bench_arms
    template, oracle, scripted = arms
    monkeypatch.setattr(
        "hotel_market.cli.sweep",
        lambda first, last, modes, customer, reviewers, **world: arms,
    )
    main(["bench", "--seeds", "1", "2", "--elasticity", "fixed:1.0", "--template"])
    out = capsys.readouterr().out
    assert "Elasticity fixed:1: each reviewer against the fixed-rate run" in out
    rows = {line.split()[0]: line.split() for line in out.splitlines() if line.strip()}

    def expected(arm, live_columns):
        mean = statistics.mean(arm.changes)
        oracle_mean, template_mean = (
            statistics.mean(oracle.changes),
            statistics.mean(template.changes),
        )
        counts = arm.counts
        rate = lambda value: "-" if math.isnan(value) else f"{value:.2f}"  # noqa: E731
        sd = statistics.stdev(arm.changes)
        return [
            arm.reviewer.name,
            f"{mean:+,.0f}",
            f"{sd:,.0f}",
            f"{sd / math.sqrt(2):,.0f}",
            f"{min(arm.changes):+,.0f}",
            "to",
            f"{max(arm.changes):+,.0f}",
            f"{arm.wins}/2",
            {2: "0.50", 1: "1.0", 0: "0.50"}[arm.wins],  # the sign test on two seeds
            str(arm.flags),
            str(arm.pace_flags),
            str(arm.rate_changes),
            f"{oracle_mean - mean:+,.0f}",
            rate(recovered_share(template_mean, oracle_mean, mean)),
            rate(counts.accept_rate),
            rate(counts.precision),
            rate(counts.recall),
            rate(counts.f1),
            rate(counts.dollar_recall),
        ] + live_columns

    assert rows["template"] == expected(template, ["-", "-", "-", "-", "-"])
    assert rows["oracle"] == expected(oracle, ["-", "-", "-", "-", "-"])
    # regret, recovered share, then precision, recall, F1 and $ recall: the oracle is its own
    # reference, and the template recovers nothing and declines nothing.
    assert rows["oracle"][12:14] == ["+0", "1.00"]
    assert rows["oracle"][15:19] == ["1.00", "1.00", "1.00", "1.00"]
    assert rows["template"][13] == "0.00" and rows["template"][15] == "-"
    assert rows["template"][16] == "0.00"
    # The scripted model is live: its calls, tokens, median latency and cost are printed; its
    # model is not in the price table, so the cost is n/a.
    calls = len(scripted.calls)
    assert rows["scripted"] == expected(scripted, ["0", str(calls), "0/0", "0.0", "n/a"])
    # The ranking pools the mismatched modes, here the one, the highest mean change first.
    assert "Across the mismatched modes (fixed:1)" in out
    ranked = [line.split() for line in out.splitlines() if line[:4].strip().isdigit()]
    by_change = sorted(arms, key=lambda arm: -statistics.mean(arm.changes))
    assert [row[:2] for row in ranked] == [
        [str(rank), arm.reviewer.name] for rank, arm in enumerate(by_change, 1)
    ]
    assert ranked[0][2:] == rows[ranked[0][1]][1:]


def test_a_sweep_counts_each_runs_flags_and_its_pace_flags(bench_arms):
    _, arms = bench_arms
    for arm in arms:
        for result in arm.seeds:
            assert result.flags == len(result.entries) > 0
            assert result.pace_flags == sum(bool(PACE & set(e.causes)) for e in result.entries)
            assert 0 < result.pace_flags <= result.flags
        assert arm.flags == sum(r.flags for r in arm.seeds)
        assert arm.pace_flags == sum(r.pace_flags for r in arm.seeds)


def test_a_demand_bias_goes_to_both_runs_and_never_to_the_agent(tmp_path):
    fixed, books, agent = run(
        SEED, tmp_path / "d.jsonl", tmp_path / "cache", FakeClient(), demand_bias=0.9
    )
    assert fixed.demand_bias == books.demand_bias == 0.9
    assert fixed.rooms.sum() < simulate(SEED).rooms.sum()
    # The agent's folder sits under one for the bias, and nothing it wrote names the bias.
    assert agent.cache_dir == tmp_path / "cache" / "demand-bias-0.9" / "seed7"
    assert not hasattr(agent, "demand_bias") and "bias" not in json.dumps(agent.log)
    assert "The simulator multiplied its demand by 0.9 in both runs." in summary(
        SEED, fixed, books, agent
    )
    plain, _, plain_agent = run(SEED, tmp_path / "p.jsonl", tmp_path / "cache", FakeClient())
    assert plain.demand_bias == 1.0 and plain_agent.cache_dir == tmp_path / "cache" / "seed7"
    assert "multiplied its demand" not in summary(SEED, plain, plain, plain_agent)


def test_a_reacting_run_goes_to_both_runs_and_never_to_the_agent(tmp_path):
    fixed, books, agent = run(
        SEED, tmp_path / "d.jsonl", tmp_path / "cache", FakeClient(), react=True
    )
    assert fixed.react and books.react
    # The fixed-rate run never changes a rate, so the reaction leaves it as it is.
    assert np.array_equal(fixed.rooms, simulate(SEED).rooms)
    assert agent.cache_dir == tmp_path / "cache" / "react" / "seed7"
    assert not hasattr(agent, "react") and "react" not in json.dumps(agent.log)
    assert "Competitors reacted in both runs: 3 days after" in summary(SEED, fixed, books, agent)
    both = run(
        SEED, tmp_path / "b.jsonl", tmp_path / "cache", FakeClient(), demand_bias=0.9, react=True
    )[2]
    assert both.cache_dir == tmp_path / "cache" / "demand-bias-0.9-react" / "seed7"


def test_a_reacting_sweep_counts_its_own_median_flags_and_the_repeat_changes(first, tmp_path):
    _, _, books, agent = first
    assert own_median_flags(agent.entries, books) == 0  # no reaction, so nothing counts
    accepted = next(e for e in agent.entries if e.action != HOLD)
    soon, later = (
        replace(accepted, day=accepted.day + REPEAT_WINDOW),
        replace(accepted, day=accepted.day + REPEAT_WINDOW + 1),
    )
    assert repeat_changes([accepted, soon]) == len(accepted.new_rates)
    assert repeat_changes([accepted, later]) == 0 and repeat_changes([accepted]) == 0
    assert REPEAT_WINDOW == 14
    [arm] = sweep(SEED, SEED, tmp_path / "cache", react=True)
    [result] = arm.seeds
    assert result.median_flags == sum(bool(MEDIAN_CAUSES & set(e.causes)) for e in result.entries)
    assert 0 < result.own_median_flags <= result.median_flags
    assert result.repeat_changes == repeat_changes(result.entries) > 0
    assert arm.own_median_flags == result.own_median_flags
    assert arm.repeat_changes == result.repeat_changes and arm.median_flags == result.median_flags


def test_a_market_elasticity_goes_to_both_runs_and_to_the_agent(tmp_path):
    fixed, books, agent = run(
        SEED, tmp_path / "d.jsonl", tmp_path / "cache", FakeClient(), market_elasticity=0.5
    )
    assert fixed.market_elasticity == books.market_elasticity == agent.market_elasticity == 0.5
    assert agent.cache_dir == tmp_path / "cache" / "market-0.5" / "seed7"
    plans = [line for line in agent.log if "elasticity" in line]
    assert plans and all(line["elasticity"]["market_elasticity"] == 0.5 for line in plans)
    assert "at an elasticity of 0.5 in both runs" in summary(SEED, fixed, books, agent)
    # A run at 0.0 keeps its cache apart too, because the customer file's value is 1.0.
    zero = run(SEED, tmp_path / "z.jsonl", tmp_path / "cache", FakeClient(), market_elasticity=0.0)
    assert zero[2].cache_dir == tmp_path / "cache" / "market-0" / "seed7"
    nested = run(
        SEED,
        tmp_path / "n.jsonl",
        tmp_path / "cache",
        FakeClient(),
        demand_bias=0.9,
        react=True,
        market_elasticity=0.5,
    )[2]
    assert nested.cache_dir == tmp_path / "cache" / "demand-bias-0.9-react" / "market-0.5" / "seed7"
    # Given no value, both runs and the agent take the customer file's, in the plain folder.
    plain, _, plain_agent = run(SEED, tmp_path / "p.jsonl", tmp_path / "cache", FakeClient())
    assert plain.market_elasticity == DEMO.market_elasticity == 1.0
    assert plain_agent.cache_dir == tmp_path / "cache" / "seed7"
    assert all(
        line["elasticity"]["market_elasticity"] == 1.0
        for line in plain_agent.log
        if "elasticity" in line
    )
    assert "at an elasticity of 1 in both runs" in summary(SEED, plain, plain, plain_agent)


def test_a_scenario_and_the_churn_go_to_both_runs(tmp_path):
    fixed, books, agent = run(
        SEED, tmp_path / "d.jsonl", tmp_path / "cache", FakeClient(), scenario=UPGAUGE_SCENARIO
    )
    assert fixed.scenario is UPGAUGE_SCENARIO and books.scenario is UPGAUGE_SCENARIO
    assert agent.cache_dir == tmp_path / "cache" / "scenario-upgauge" / "seed7"
    text = summary(SEED, fixed, books, agent)
    assert "The air schedule ran the upgauge scenario in both runs." in text
    fixed, books, agent = run(
        SEED, tmp_path / "c.jsonl", tmp_path / "cache", FakeClient(), churn=True
    )
    assert books.churn and books.scenario.name == "default+churn"
    assert fixed.scenario == books.scenario and not fixed.scenario == DEFAULT_SCENARIO
    assert agent.cache_dir == tmp_path / "cache" / "churn" / "seed7"
    assert "with the seed's weekly revisions filed on top" in summary(SEED, fixed, books, agent)
    [arm] = sweep(SEED, SEED, tmp_path / "cache", churn=True)
    [result] = arm.seeds
    assert result.filings == arm.filings == 10
    assert result.seat_flags == sum(bool(SEAT_CAUSES & set(e.causes)) for e in result.entries) > 0


@pytest.mark.slow
def test_the_churn_and_the_upgauge_runs_pin_their_headline(tmp_path):
    """The template arms with the churn and with the upgauge scenario end where the recorded
    runs ended, so the filings table stays pinned."""
    [churned] = sweep(1, 20, tmp_path / "cache", churn=True)
    assert statistics.mean(churned.changes) == pytest.approx(34974, abs=1)
    assert (churned.filings, churned.seat_flags, churned.rate_changes) == (200, 173, 184)
    [upgauged] = sweep(1, 20, tmp_path / "cache", scenario=UPGAUGE_SCENARIO)
    assert statistics.mean(upgauged.changes) == pytest.approx(21083, abs=1)
    assert (upgauged.filings, upgauged.seat_flags, upgauged.rate_changes) == (40, 182, 177)


def test_a_policy_runs_the_rule_based_control_beside_each_arm(tmp_path, capsys):
    [arm] = sweep(SEED, SEED, tmp_path / "cache", policy="pace")
    [result] = arm.seeds
    rule = PacePolicy()
    fixed, books = simulate(SEED), simulate(SEED, deciding(rule))
    assert result.control_change == pytest.approx(
        sum(books.contribution(h) - fixed.contribution(h) for h in DEMO.hotels)
    )
    assert result.control_changes == rule.changed > 0
    assert arm.against_control == [
        pytest.approx(result.contribution_change - result.control_change)
    ]
    [plain] = sweep(SEED, SEED, tmp_path / "cache")
    assert plain.seeds[0].control_change == 0.0 and plain.seeds[0].control_changes == 0
    main(["--seed", str(SEED), "--template", "--policy", "pace"])
    out = capsys.readouterr().out
    assert "The pace policy earned" in out and "so against it the agent earned" in out


def test_the_command_and_the_bench_take_a_demand_bias(monkeypatch, capsys):
    seen = {}

    def fake_sweep(
        first,
        last,
        modes,
        customer,
        reviewers=(TEMPLATE,),
        demand_bias=1.0,
        react=False,
        market_elasticity=None,
        scenario=DEFAULT_SCENARIO,
        churn=False,
        policy=None,
    ):
        seen["bias"], seen["reviewers"], seen["react"] = demand_bias, list(reviewers), react
        seen["market"], seen["scenario"], seen["churn"] = market_elasticity, scenario, churn
        seen["policy"] = policy
        return [ArmResult(mode, ROWS, reviewer=r) for mode in modes for r in reviewers]

    monkeypatch.setattr("hotel_market.cli.sweep", fake_sweep)
    main(["--seeds", "1", "3", "--demand-bias", "0.9"])
    out = capsys.readouterr().out
    assert seen["bias"] == 0.9 and "multiplied by 0.9 unseen by the agent" in out
    main(
        ["bench", "--seeds", "1", "3", "--template", "--elasticity", "learn:1.0", "--cautious"]
        + ["--demand-bias", "1.1"]
    )
    out = capsys.readouterr().out
    assert seen["bias"] == 1.1 and "multiplied by 1.1 unseen by the agent" in out
    template, oracle_arm = seen["reviewers"]
    assert template is TEMPLATE and oracle_arm is not ORACLE and oracle_arm.name == "oracle"
    assert "Elasticity learn:1 cautious: each reviewer" in out
    assert "Elasticity learn:1 cautious, oracle: the estimate each hotel priced with" in out
    # The default is 1.0, where the oracle is ORACLE itself; a bias must be above zero, and
    # --cautious needs a learn mode, as on the sweep.
    main(["bench", "--seeds", "1", "3", "--template", "--elasticity", "fixed:1.0"])
    assert seen["bias"] == 1.0 and seen["reviewers"][1] is ORACLE and not seen["react"]
    # --react goes to the sweep on both commands, and each then prints the reaction table.
    main(["--seeds", "1", "3", "--react"])
    out = capsys.readouterr().out
    assert seen["react"] and "competitors reacting to the hotels' rate changes" in out
    # The heading names the customer file's value when the command set none.
    assert "With competitors reacting (market elasticity 1): the comp-median flags" in out
    assert "recent shown" in out and "recent held" in out
    main(["bench", "--seeds", "1", "3", "--template", "--elasticity", "fixed:1.0", "--react"])
    out = capsys.readouterr().out
    assert seen["react"] and "With competitors reacting" in out and "oracle" in out
    assert seen["market"] is None and "(market elasticity 1)" in out
    # --market-elasticity goes to the sweep and to the oracle, and the headings name it.
    main(["--seeds", "1", "3", "--react", "--market-elasticity", "0.5"])
    out = capsys.readouterr().out
    assert seen["market"] == 0.5 and "at an elasticity of 0.5" in out
    assert "(market elasticity 0.5)" in out
    main(["bench", "--seeds", "1", "3", "--template", "--market-elasticity", "0.5"])
    assert seen["market"] == 0.5 and seen["reviewers"][1] is not ORACLE
    with pytest.raises(SystemExit):
        main(["--seeds", "1", "3", "--market-elasticity", "-0.5"])
    # --scenario and --churn go to the sweep on both commands; a sweep always prints the
    # filings table, and the bench prints it when either is set.
    main(["--seeds", "1", "3", "--scenario", "upgauge", "--churn"])
    out = capsys.readouterr().out
    assert seen["scenario"] is UPGAUGE_SCENARIO and seen["churn"]
    assert "the upgauge schedule scenario, the airline filing weekly revisions" in out
    assert "The air schedule's filings through day 59" in out
    main(["bench", "--seeds", "1", "3", "--template", "--elasticity", "fixed:1.0", "--churn"])
    out = capsys.readouterr().out
    assert seen["churn"] and seen["scenario"] is DEFAULT_SCENARIO
    assert "The air schedule's filings through day 59" in out
    with pytest.raises(SystemExit):
        main(["--seeds", "1", "3", "--scenario", "bogus"])
    # --level sets the level flag on every learn arm, on the sweep and on the bench, and prints
    # the factor table for those arms.
    main(["--seeds", "1", "3", "--elasticity", "true", "--elasticity", "learn:1.0", "--level"])
    out = capsys.readouterr().out
    assert "learn:1 level" in out and "the factor each hotel scaled its forecast by" in out
    main(["bench", "--seeds", "1", "3", "--template", "--elasticity", "learn:1.0", "--level"])
    out = capsys.readouterr().out
    assert "Elasticity learn:1 level: each reviewer" in out
    assert "Elasticity learn:1 level, oracle: the factor each hotel scaled" in out
    with pytest.raises(SystemExit):
        main(["--seeds", "1", "3", "--level"])
    with pytest.raises(SystemExit):
        main(["bench", "--seeds", "1", "3", "--template", "--elasticity", "fixed:1.0", "--level"])
    # --policy adds the rule-based control's table to the sweep and to the bench.
    main(["--seeds", "1", "3", "--policy", "pace"])
    out = capsys.readouterr().out
    assert seen["policy"] == "pace" and "Against the pace policy" in out
    main(["bench", "--seeds", "1", "3", "--template", "--elasticity", "true", "--policy", "pace"])
    out = capsys.readouterr().out
    assert seen["policy"] == "pace" and "Against the pace policy" in out and "oracle" in out
    with pytest.raises(SystemExit):
        main(["--seeds", "1", "3", "--policy", "bogus"])
    for argv in (
        ["--seeds", "1", "3", "--demand-bias", "0"],
        ["bench", "--seeds", "1", "3", "--template", "--demand-bias", "-1"],
        ["bench", "--seeds", "1", "3", "--template", "--demand-bias", "x"],
        ["bench", "--seeds", "1", "3", "--template", "--cautious"],
    ):
        with pytest.raises(SystemExit):
            main(argv)


def test_an_arms_call_records_are_read_from_its_folder_and_counted_once(tmp_path):
    agent = Agent(SEED, tmp_path, elasticity=FIXED_1, model="scripted")
    assert _calls(agent) == []  # no file, no client: nothing
    agent.cache_dir.mkdir(parents=True)
    (agent.cache_dir / "day010_convention.json").write_text(json.dumps({"request_digest": "a"}))
    lines = [
        {"request_digest": "a", "input_tokens": 1000, "output_tokens": 100},
        {"request_digest": "a", "input_tokens": 1200, "output_tokens": 120},
        {"request_digest": "b", "input_tokens": 1000, "output_tokens": 100},
    ]
    (agent.cache_dir / "calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in lines))
    assert _calls(agent) == [{**lines[1], "bad_attempt": 0, "retries": 0}]


@pytest.mark.parametrize(
    "argv",
    [
        ["bench"],  # the seeds are required
        ["bench", "--seeds", "2", "1"],  # FIRST after LAST
        ["bench", "--seeds", "1", "2", "--template", "--model", "x"],  # the template runs no model
        ["bench", "--seeds", "1", "2", "--elasticity", "guess:1"],
    ],
)
def test_the_bench_command_rejects_bad_arguments(argv, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-a-key")
    with pytest.raises(SystemExit):
        main(argv)


def test_the_bench_needs_a_key_unless_it_runs_the_template_alone(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        main(["bench", "--seeds", "1", "1"])
    assert BENCH_MODES == ("fixed:1.0", "fixed:2.0", "true")


@pytest.mark.slow
def test_the_offline_bench_on_20_seeds_pins_the_benchmarks_headline(tmp_path):
    """The template and oracle arms need no key, so they pin the headline of the benchmark's tables.
    The template arms are the --seeds sweep's arms, and they end where the recorded sweep of the
    wrong elasticities ended. The oracle arms end where the recorded benchmark put them and accept
    the share of plans it recorded. The live arms are not pinned, because the cache is not
    committed."""
    modes = [FIXED_1, ElasticityMode.parse("fixed:2.0")]
    arms = sweep(1, 20, tmp_path / "cache", modes, reviewers=[TEMPLATE, ORACLE])
    by_arm = {(str(arm.mode), arm.reviewer.name): arm for arm in arms}
    assert statistics.mean(by_arm[("fixed:1", "template")].changes) == pytest.approx(8438, abs=1)
    assert statistics.mean(by_arm[("fixed:2", "template")].changes) == pytest.approx(9551, abs=1)
    assert statistics.mean(by_arm[("fixed:1", "oracle")].changes) == pytest.approx(30588, abs=1)
    assert statistics.mean(by_arm[("fixed:2", "oracle")].changes) == pytest.approx(23058, abs=1)
    assert round(by_arm[("fixed:1", "oracle")].counts.accept_rate, 2) == 0.15
    assert round(by_arm[("fixed:2", "oracle")].counts.accept_rate, 2) == 0.29
    for mode in ("fixed:1", "fixed:2"):
        oracle = by_arm[(mode, "oracle")]
        assert oracle.counts.precision == oracle.counts.recall == 1.0 and oracle.wins == 20
        assert by_arm[(mode, "template")].counts.declined == 0


@pytest.mark.slow
def test_the_demand_bias_runs_pin_their_headline(tmp_path):
    """The true and fixed:1.0 template arms at a bias of 0.9 and 1.1 end where the recorded runs
    ended, so the demand-bias tables stay pinned."""
    headline = {0.9: (1913, -25179), 1.1: (112082, 93008)}
    for bias, (true_mean, fixed_mean) in headline.items():
        arms = sweep(1, 20, tmp_path / "cache", [TRUE_MODE, FIXED_1], demand_bias=bias)
        by_mode = {str(arm.mode): arm for arm in arms}
        assert statistics.mean(by_mode["true"].changes) == pytest.approx(true_mean, abs=1)
        assert statistics.mean(by_mode["fixed:1"].changes) == pytest.approx(fixed_mean, abs=1)


@pytest.mark.slow
def test_the_reacting_runs_pin_their_headline(tmp_path):
    """The template arms with the reaction on end where the recorded runs ended, so the reaction
    tables stay pinned."""
    cautious = ElasticityMode("learn", 1.0, cautious=True)
    arms = sweep(1, 20, tmp_path / "cache", [TRUE_MODE, cautious], react=True)
    by_mode = {str(arm.mode): arm for arm in arms}
    assert statistics.mean(by_mode["true"].changes) == pytest.approx(111272, abs=1)
    assert statistics.mean(by_mode["learn:1 cautious"].changes) == pytest.approx(298869, abs=1)
    assert by_mode["true"].own_median_flags == 481 and by_mode["true"].repeat_changes == 97


@pytest.mark.slow
def test_the_market_elasticity_runs_pin_their_headline(tmp_path):
    """The true-mode template arm with the reaction on ends where the recorded runs ended at a
    market elasticity of 0.5 and 1.0, so the market-elasticity table stays pinned."""
    for market, mean, twice in ((0.5, 72229, 46), (1.0, 43584, 25)):
        [arm] = sweep(1, 20, tmp_path / "cache", react=True, market_elasticity=market)
        assert statistics.mean(arm.changes) == pytest.approx(mean, abs=1)
        assert arm.repeat_changes == twice


@pytest.mark.slow
def test_the_level_runs_pin_their_headline(tmp_path):
    """The level arms at a demand bias of 0.9 and 1.1 end where the recorded runs ended, so the
    level tables stay pinned."""
    level = ElasticityMode("learn", 1.0, level=True)
    cautious = ElasticityMode("learn", 1.0, cautious=True, level=True)
    for bias, (plain_mean, cautious_mean) in ((0.9, (-15244, -3348)), (1.1, (95731, 103121))):
        arms = sweep(1, 20, tmp_path / "cache", [level, cautious], demand_bias=bias)
        by_mode = {str(arm.mode): arm for arm in arms}
        assert statistics.mean(by_mode["learn:1 level"].changes) == pytest.approx(plain_mean, abs=1)
        assert statistics.mean(by_mode["learn:1 cautious level"].changes) == pytest.approx(
            cautious_mean, abs=1
        )


@pytest.mark.slow
def test_the_learn_arms_pin_their_headline(tmp_path):
    """The template and oracle arms of the learned modes end where the recorded live benchmark put
    them, with and without the cautious rule and in the reacting market, so the learn-mode tables
    stay pinned. The live arms are not pinned, because the cache is not committed."""
    from hotel_market.bench import on_recent_changes, oracle
    from hotel_market.shops import REACTION_SHARE

    pins = {
        (False, "learn:1"): (14141, 30828, 0.21),
        (False, "learn:2"): (16258, 24794, 0.50),
        (True, "learn:1 cautious"): (25076, 31042, 0.34),
        (True, "learn:2 cautious"): (17634, 18599, 0.52),
    }
    for cautious in (False, True):
        modes = [ElasticityMode("learn", value, cautious=cautious) for value in (1.0, 2.0)]
        arms = sweep(1, 20, tmp_path / "cache", modes, reviewers=[TEMPLATE, ORACLE])
        by_arm = {(str(arm.mode), arm.reviewer.name): arm for arm in arms}
        for (_, mode), (template_mean, oracle_mean, accept) in pins.items():
            if (mode.endswith("cautious")) != cautious:
                continue
            template, truth = by_arm[(mode, "template")], by_arm[(mode, "oracle")]
            assert statistics.mean(template.changes) == pytest.approx(template_mean, abs=1)
            assert statistics.mean(truth.changes) == pytest.approx(oracle_mean, abs=1)
            assert round(truth.counts.accept_rate, 2) == accept
    # The reacting arm's oracle is told the reaction and the market elasticity, as the bench
    # command tells it.
    cautious = ElasticityMode("learn", 1.0, cautious=True)
    truth = oracle(demand_bias=1.0, market_elasticity=0.5, reaction_share=REACTION_SHARE)
    arms = sweep(
        1,
        20,
        tmp_path / "cache",
        [cautious],
        reviewers=[TEMPLATE, truth],
        react=True,
        market_elasticity=0.5,
    )
    by_name = {arm.reviewer.name: arm for arm in arms}
    assert statistics.mean(by_name["template"].changes) == pytest.approx(198089, abs=1)
    assert statistics.mean(by_name["oracle"].changes) == pytest.approx(198488, abs=1)
    for name, held in (("template", 0), ("oracle", 1)):
        counts = [on_recent_changes(r.entries, REPEAT_WINDOW) for r in by_name[name].seeds]
        assert (sum(c[0] for c in counts), sum(c[1] for c in counts)) == (556, held)


@pytest.mark.slow
def test_the_rule_based_control_runs_pin_their_headline(tmp_path):
    """The pace, rules and never-cut policies beside the true-mode template arm end where the
    recorded runs ended at the default bias and at 0.9, so the control table stays pinned."""
    pins = {
        ("pace", 1.0): (11462, 21437),
        ("pace", 0.9): (2015, -101),
        ("rules", 1.0): (22856, 10043),
        ("rules", 0.9): (657, 1256),
        ("never-cut", 1.0): (24780, 8119),
        ("never-cut", 0.9): (-461, 2374),
    }
    for (policy, bias), (rule_mean, margin) in pins.items():
        [arm] = sweep(1, 20, tmp_path / "cache", policy=policy, demand_bias=bias)
        assert statistics.mean(arm.control_changes) == pytest.approx(rule_mean, abs=1)
        assert statistics.mean(arm.against_control) == pytest.approx(margin, abs=1)


def test_a_learn_run_keeps_its_own_cache_and_says_where_its_estimates_ended(tmp_path):
    mode = ElasticityMode.parse("learn:1.0")
    fixed, books, agent = run(SEED, tmp_path / "d.jsonl", tmp_path / "cache", FakeClient(), mode)
    assert agent.cache_dir == tmp_path / "cache" / "seed7-learn-1" and agent.cache_dir.exists()
    text = summary(SEED, fixed, books, agent)
    assert "The agent learned its elasticity from the bookings, starting from 1; on day 59" in text
    assert all(
        f"{h.key} {agent.estimates[(59, h.key)].elasticity:.2f}" in text for h in DEMO.hotels
    )


def test_a_cautious_run_says_so_and_shows_the_band_on_each_change(tmp_path):
    mode = ElasticityMode("learn", 1.0, cautious=True)
    fixed, books, agent = run(SEED, tmp_path / "d.jsonl", tmp_path / "cache", FakeClient(), mode)
    assert agent.cache_dir.name == "seed7-learn-1-cautious"
    text = summary(SEED, fixed, books, agent)
    assert "and acting only where a change beat holding one standard error either side" in text
    changed = [e for e in agent.entries if e.action != HOLD]
    assert changed
    printed = format_entry(changed[0], DEMO)
    assert "across the band" in printed and "cautious: a change must also win at" in printed


def test_a_sweep_counts_the_shock_plans_apart_from_the_other_plans(first, tmp_path):
    # The plans the convention and the new flights raised, against every other plan.
    _, fixed, books, agent = first
    [arm] = sweep(SEED, SEED, tmp_path / "cache")
    [result] = arm.seeds
    assert SHOCK_PLAN_CAUSES == {NEW_EVENT, SEATS_UP}
    accepted = [e for e in agent.entries if e.action != HOLD]
    shock = [e for e in accepted if {NEW_EVENT, SEATS_UP} & set(e.causes)]
    assert shock and len(shock) <= len(accepted)
    assert (result.shock_changes, result.other_changes) == (len(shock), len(accepted) - len(shock))
    shock_pairs = {(e.hotel, s) for e in shock for s in e.new_rates}
    other_pairs = {(e.hotel, s) for e in accepted if e not in shock for s in e.new_rates}
    other_pairs -= shock_pairs
    assert result.shock_gain == pytest.approx(_gain_on(fixed, books, shock_pairs, DEMO.hotels))
    assert result.other_gain == pytest.approx(_gain_on(fixed, books, other_pairs, DEMO.hotels))
    assert result.shock_gain + result.other_gain == pytest.approx(result.contribution_change)
