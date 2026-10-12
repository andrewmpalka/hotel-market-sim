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
from hotel_market.cli import (
    BENCH_MODES,
    REPORT_DAYS,
    SHOCK_PLAN_CAUSES,
    ArmResult,
    SeedResult,
    _calls,
    _gain_on,
    changed_stays,
    format_entry,
    main,
    queue,
    replay,
    run,
    summary,
    sweep,
)
from hotel_market.customer import demo
from hotel_market.detect import NEW_EVENT, SEATS_UP
from hotel_market.estimate import Estimate
from hotel_market.model import Measured
from hotel_market.plan import HOLD

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
    assert advice and all(
        line["action"] == MIN_STAY and line["value_at_stake"] is None for line in advice
    )


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
        lambda first, last, modes, customer: [ArmResult(TRUE_MODE, ROWS)],
    )
    main(["--seeds", "1", "3"])
    out = capsys.readouterr().out
    printed = [line.split() for line in out.splitlines() if line[:4].strip().isdigit()]
    assert printed == [["1", "+100", "-20", "3"], ["2", "-51", "+15", "1"], ["3", "+10", "+0", "2"]]
    # The mean of the unrounded changes: (100.4 - 50.6 + 10.0) / 3 = 19.93.
    assert (
        "Contribution change: mean +20, range -51 to +100; "
        "higher than the fixed-rate run in 2 of 3 seeds. "
        "The accepted plans were estimated to earn +170 and earned +60."
    ) in out
    assert "Revenue change: mean -2, range -20 to +15." in out
    assert "Where the gain came from" in out
    [source] = [line.split() for line in out.splitlines() if line.startswith("true ")]
    assert source == ["true", "3", "+94", "3", "-45"]


def test_a_revenue_target_arm_counts_wins_and_earnings_in_revenue(monkeypatch, capsys):
    arm = ArmResult(TRUE_MODE, ROWS, "revenue")
    assert arm.wins == 1 and arm.realised == pytest.approx(-5.0)
    monkeypatch.setattr("hotel_market.cli.sweep", lambda first, last, modes, customer: [arm])
    main(["--seeds", "1", "3", "--target", "revenue"])
    out = capsys.readouterr().out
    assert "candidates scored on revenue" in out
    assert "Contribution change: mean +20, range -51 to +100." in out
    assert (
        "Revenue change: mean -2, range -20 to +15; higher than the fixed-rate run in 1 of 3 "
        "seeds. The accepted plans were estimated to earn +170 and earned -5."
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
    monkeypatch.setattr("hotel_market.cli.sweep", lambda first, last, modes, customer: arms)
    main(["--seeds", "1", "3", "--elasticity", "true", "--elasticity", "learn:1.0", "--cautious"])
    out = capsys.readouterr().out
    rows = [line.split() for line in out.splitlines() if line.startswith(("true", "learn:1"))]
    # The mean revenue change of the rows is (-20 + 15 + 0) / 3 = -1.67.
    assert rows[0] == [
        "true",
        "+20",
        "-2",
        "-51",
        "to",
        "+100",
        "2/3",
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


def test_the_default_mode_still_gives_28818_on_seed_7(first):
    _, fixed, books, _ = first
    change = sum(books.contribution(h) - fixed.contribution(h) for h in DEMO.hotels)
    assert change == pytest.approx(28818, abs=1)


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
        "hotel_market.cli.sweep", lambda first, last, modes, customer, reviewers: arms
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
        return [
            arm.reviewer.name,
            f"{mean:+,.0f}",
            f"{min(arm.changes):+,.0f}",
            "to",
            f"{max(arm.changes):+,.0f}",
            f"{arm.wins}/2",
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
    assert rows["oracle"][6:8] == ["+0", "1.00"]
    assert rows["oracle"][9:13] == ["1.00", "1.00", "1.00", "1.00"]
    assert rows["template"][7] == "0.00" and rows["template"][9] == "-"
    assert rows["template"][10] == "0.00"
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
    assert _calls(agent) == [lines[1]]


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
def test_the_offline_bench_on_20_seeds_reproduces_the_fixed_arms(tmp_path):
    """The template arms of the bench are the --seeds sweep's arms, so they end where the
    recorded sweep of the wrong elasticities ended, and the oracle agrees with itself."""
    modes = [FIXED_1, ElasticityMode.parse("fixed:2.0")]
    arms = sweep(1, 20, tmp_path / "cache", modes, reviewers=[TEMPLATE, ORACLE])
    by_arm = {(str(arm.mode), arm.reviewer.name): arm for arm in arms}
    assert statistics.mean(by_arm[("fixed:1", "template")].changes) == pytest.approx(8438, abs=1)
    assert statistics.mean(by_arm[("fixed:2", "template")].changes) == pytest.approx(9551, abs=1)
    for mode in ("fixed:1", "fixed:2"):
        oracle = by_arm[(mode, "oracle")]
        assert oracle.counts.precision == oracle.counts.recall == 1.0
        assert by_arm[(mode, "template")].counts.declined == 0


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
    assert shock and len(shock) < len(accepted)
    assert (result.shock_changes, result.other_changes) == (len(shock), len(accepted) - len(shock))
    shock_pairs = {(e.hotel, s) for e in shock for s in e.new_rates}
    other_pairs = {(e.hotel, s) for e in accepted if e not in shock for s in e.new_rates}
    other_pairs -= shock_pairs
    assert result.shock_gain == pytest.approx(_gain_on(fixed, books, shock_pairs, DEMO.hotels))
    assert result.other_gain == pytest.approx(_gain_on(fixed, books, other_pairs, DEMO.hotels))
    assert result.shock_gain + result.other_gain == pytest.approx(result.contribution_change)
