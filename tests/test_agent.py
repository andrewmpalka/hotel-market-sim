"""Module 7, agent.py: the daily loop, the 7-day hold, and the minimum-stay advice."""

import json
from types import SimpleNamespace

import pytest

from hotel_market.agent import MIN_STAY, Agent, ElasticityMode
from hotel_market.bookings import Books, simulate
from hotel_market.customer import demo
from hotel_market.detect import AHEAD
from hotel_market.estimate import level_factor
from hotel_market.model import MODEL
from hotel_market.plan import HOLD, TRUE_PRICING, Pricing
from hotel_market.schedule import HORIZON_DAYS
from hotel_market.simulated import deciding, simulated_sources

DEMO = demo()

SEED = 7


class DecliningClient:
    """Stands in for a model that declines every plan."""

    def complete(self, system, prompt, schema):
        request = json.loads(prompt)
        return json.dumps(
            {
                "decisions": [
                    {"id": e["id"], "choice": HOLD, "reason": f"Declined {e['id']}."}
                    for e in request["entries"]
                ]
            }
        )


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    """A seed-7 agent run with the template, and its books."""
    agent = Agent(SEED, cache_dir=tmp_path_factory.mktemp("cache"))
    return agent, simulate(SEED, deciding(agent))


def test_entries_below_the_minimum_are_held_and_stay_out_of_the_queue(run):
    agent, _ = run
    held = [e for e in agent.entries if not e.queued]
    assert held and all(e.action == HOLD for e in held)
    assert any(e.reason.startswith("No change beats holding") for e in held)
    small = [e for e in held if e.changed_weekdays]
    assert small and all(
        f"under the ${DEMO.min_value_at_stake:,} minimum" in e.reason for e in small
    )
    queued = [e for e in agent.entries if e.queued]
    assert queued and all(
        e.value_at_stake >= DEMO.min_value_at_stake and e.reason_source == "template"
        for e in queued
    )


def test_accepted_rates_apply_and_hold_those_stay_dates_for_7_days(run):
    agent, books = run
    # Every stay date ends the run at the rate of the last change accepted for it,
    # or at its start rate if nothing changed it.
    last = {}
    for e in agent.entries:
        if e.action != HOLD:
            last.update({(e.hotel, s): r for s, r in e.new_rates.items()})
    assert last
    for hotel in DEMO.hotels:
        for s in range(HORIZON_DAYS):
            assert books.rates[hotel.row, s] == pytest.approx(
                last.get((hotel.key, s), hotel.start_rate)
            )
    # The first accepted plan holds the stay dates it changed for 7 days.
    plan = next(e for e in agent.entries if e.action != HOLD)
    assert plan.action == plan.plan and plan.new_rates
    for stay_day in plan.new_rates:
        assert agent.held[(plan.hotel, stay_day)] >= plan.day
        assert not [
            e
            for e in agent.entries
            if e.hotel == plan.hotel
            and plan.day + 1 <= e.day <= plan.day + 7
            and e.first_stay <= stay_day <= e.last_stay
        ]


def test_the_log_lists_every_entry_and_advice_in_order(run):
    agent, _ = run
    log = agent.log
    assert len(log) == len(agent.entries) + len(agent.advice)
    assert [line["day"] for line in log] == sorted(line["day"] for line in log)
    # Within a day, the entries come first and the advice last.
    for day in {a.day for a in agent.advice}:
        flags = [line["simulated"] for line in log if line["day"] == day]
        assert flags == sorted(flags, reverse=True) and flags[-1] is False


def test_a_model_that_declines_changes_no_rate(tmp_path):
    agent = Agent(SEED, cache_dir=tmp_path, client=DecliningClient())
    books = simulate(SEED, deciding(agent))
    assert all(e.action == HOLD for e in agent.entries)
    assert all(e.reason_source == "model" for e in agent.entries if e.queued)
    assert (books.rates == simulate(SEED).rates).all()


def test_another_model_gets_its_own_cache_folder_and_record(tmp_path):
    # The default model in the default mode keeps cache/seed7, so the recorded run replays.
    assert Agent(SEED, tmp_path).model == MODEL and Agent(SEED, tmp_path).cache_dir.name == "seed7"
    assert Agent(SEED, tmp_path, client=DecliningClient()).cache_dir.name == "seed7"
    # Another model joins the folder name after the mode, and every record names it.
    agent = Agent(
        SEED,
        tmp_path,
        client=DecliningClient(),
        elasticity=ElasticityMode.parse("fixed:1.0"),
        model="claude-sonnet-5-5",
    )
    assert agent.cache_dir.name == "seed7-fixed-1-claude-sonnet-5-5"
    simulate(SEED, deciding(agent))
    records = [json.loads(p.read_text()) for p in sorted(agent.cache_dir.glob("day*_*.json"))]
    assert records and {r["model"] for r in records} == {"claude-sonnet-5-5"}
    assert {r["source"] for r in records} == {"model"}
    # Unnamed, the model is the client's own when the client has one.
    named = SimpleNamespace(model="claude-haiku-5-5", complete=DecliningClient().complete)
    assert Agent(SEED, tmp_path, client=named).cache_dir.name == "seed7-claude-haiku-5-5"


def test_minimum_stay_advice_is_not_repeated_on_later_days(tmp_path):
    agent = Agent(SEED, cache_dir=tmp_path)
    ahead = SimpleNamespace(hotel="convention", first_stay=44, last_stay=46, causes=(AHEAD,))
    sources = simulated_sources(Books(SEED))
    assert [a.stay_day for a in agent.advice_for(34, [ahead], sources)] == [45]
    assert agent.advice_for(35, [ahead], sources) == []


def test_minimum_stay_advice_is_given_once_per_hotel_and_event_and_not_simulated(tmp_path):
    # Each downtown hotel's convention peak night, flagged ahead of pace, draws one piece of
    # advice; the same flag the next day draws none.
    agent = Agent(SEED, cache_dir=tmp_path)
    sources = simulated_sources(Books(SEED))
    ahead = [
        SimpleNamespace(hotel=key, first_stay=44, last_stay=46, causes=(AHEAD,))
        for key in ("convention", "full-service")
    ]
    found = agent.advice_for(34, ahead, sources)
    assert [a.hotel for a in found] == ["convention", "full-service"]
    assert agent.advice_for(35, ahead, sources) == []
    for advice in found:
        line = advice.to_json()
        assert (
            line["action"] == MIN_STAY
            and line["simulated"] is False
            and line["value_at_stake"] is None
        )
        assert line["stays"] == [45, 45]  # the peak night, computed in code


@pytest.mark.parametrize(
    "text, kind, value",
    [("true", "true", 1.5), ("fixed:1.0", "fixed", 1.0), ("learn:2", "learn", 2.0)],
)
def test_elasticity_modes_parse_and_print(text, kind, value):
    mode = ElasticityMode.parse(text)
    assert (mode.kind, mode.value) == (kind, value)
    assert ElasticityMode.parse(str(mode)) == mode


@pytest.mark.parametrize("text", ["guess:1", "learn", "fixed:x", "fixed:-1", "true:1.5", "learn:0"])
def test_a_mode_that_is_not_true_fixed_or_learn_is_rejected(text):
    with pytest.raises(ValueError):
        ElasticityMode.parse(text)


def test_each_mode_records_the_elasticity_its_plans_assume(run, tmp_path):
    agent, _ = run
    assert agent.cache_dir.name == "seed7"
    assert {e.pricing for e in agent.entries} == {TRUE_PRICING}
    fixed_mode = Agent(SEED, tmp_path, elasticity=ElasticityMode.parse("fixed:1.0"))
    simulate(SEED, deciding(fixed_mode))
    assert fixed_mode.cache_dir.name == "seed7-fixed-1"
    assert {e.pricing for e in fixed_mode.entries} == {Pricing(1.0, "fixed")}
    learner = Agent(SEED, tmp_path, elasticity=ElasticityMode.parse("learn:2.0"))
    simulate(SEED, deciding(learner))
    assert learner.cache_dir.name == "seed7-learn-2"
    assert set(learner.estimates) == {(day, h.key) for day in range(60) for h in DEMO.hotels}
    for entry in learner.entries:
        found = learner.estimates[(entry.day, entry.hotel)]
        assert entry.pricing == Pricing(
            found.elasticity, "learn", found.standard_error, 2.0, found.observations
        )
        assert entry.to_json()["elasticity"] == entry.pricing.to_json()
    # Day 0 starts from the prior; by day 59 the bookings have moved every hotel off it.
    assert all(learner.estimates[(0, h.key)].elasticity == 2.0 for h in DEMO.hotels)
    assert all(learner.estimates[(59, h.key)].elasticity != 2.0 for h in DEMO.hotels)


def test_plain_learn_mode_gives_the_same_results_as_before(tmp_path):
    fixed = simulate(SEED)
    agent = Agent(SEED, tmp_path, elasticity=ElasticityMode.parse("learn:1.0"))
    books = simulate(SEED, deciding(agent))
    change = sum(books.contribution(h) - fixed.contribution(h) for h in DEMO.hotels)
    assert change == pytest.approx(2469.25, abs=0.01)
    assert sum(1 for e in agent.entries if e.action != HOLD) == 14 and len(agent.entries) == 67


def test_a_cautious_agent_records_the_band_and_what_it_rejected(tmp_path):
    mode = ElasticityMode("learn", 1.0, cautious=True)
    assert str(mode) == "learn:1 cautious"
    agent = Agent(SEED, tmp_path, elasticity=mode)
    simulate(SEED, deciding(agent))
    assert agent.cache_dir.name == "seed7-learn-1-cautious"
    assert agent.entries
    for entry in agent.entries:
        assert entry.pricing.cautious and entry.pricing.band is not None
        for group in entry.weekdays:
            assert group.cautious and all(c.band is not None for c in group.candidates)
            if group.best.name != HOLD:
                assert group.replaces_hold(group.best)
        line = entry.to_json()
        assert line["rejected_at_an_end"] == entry.rejected_at_an_end
        assert line["elasticity"]["cautious"] is True
        assert set(line["elasticity"]["band"]) == {"lowest", "highest"}
    assert sum(e.rejected_at_an_end for e in agent.entries) > 0


def test_a_level_agent_scales_its_forecast_by_the_fitted_demand_level(tmp_path):
    mode = ElasticityMode("learn", 1.0, level=True)
    assert str(mode) == "learn:1 level"
    assert str(ElasticityMode("learn", 1.0, cautious=True, level=True)) == "learn:1 cautious level"
    agent = Agent(SEED, tmp_path / "cache", elasticity=mode)
    assert agent.cache_dir.name == "seed7-learn-1-level"
    simulate(SEED, deciding(agent), demand_bias=0.9)
    # Until the fit has enough observations the factor is 1. By day 59 it sits near the bias of
    # 0.9 at every hotel, and every plan record carries the day's factor.
    early = [e for e in agent.entries if e.day <= 5]
    assert early and all(e.pricing.level == 1.0 for e in early)
    for hotel in DEMO.hotels:
        assert 0.85 <= level_factor(agent.estimates[(59, hotel.key)]) <= 0.95
    late = [e for e in agent.entries if e.day >= 30]
    assert late and all(0.8 <= e.pricing.level < 1.0 for e in late)
    assert all("level" in line["elasticity"] for line in agent.log if "elasticity" in line)
    plain = Agent(SEED, tmp_path / "plain", elasticity=ElasticityMode("learn", 1.0))
    simulate(SEED, deciding(plain), last_day=20, demand_bias=0.9)
    assert plain.entries and all(e.pricing.level == 1.0 for e in plain.entries)
