"""Module 7, agent.py: the daily loop, the 7-day hold, and the minimum-stay advice."""

import json
from types import SimpleNamespace

import pytest

from hotel_market.agent import MIN_STAY, Agent, ElasticityMode
from hotel_market.bookings import Books, simulate
from hotel_market.customer import demo
from hotel_market.detect import AHEAD
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
    # The day-10 convention plan holds the stay dates it changed for 7 days.
    [plan] = [e for e in agent.entries if e.day == 10 and e.hotel == "convention"]
    assert plan.action == plan.plan and plan.new_rates
    for stay_day in plan.new_rates:
        assert agent.held[("convention", stay_day)] >= 10
        assert not [
            e
            for e in agent.entries
            if e.hotel == "convention"
            and 11 <= e.day <= 17
            and e.first_stay <= stay_day <= e.last_stay
        ]


def test_the_log_lists_every_entry_and_advice_in_order(run):
    agent, _ = run
    log = agent.log
    assert len(log) == len(agent.entries) + len(agent.advice)
    assert [line["day"] for line in log] == sorted(line["day"] for line in log)
    # Within a day, the entries come first and the advice last.
    day_34 = [line["simulated"] for line in log if line["day"] == 34]
    assert day_34 == sorted(day_34, reverse=True) and day_34[-1] is False


def test_a_model_that_declines_changes_no_rate(tmp_path):
    agent = Agent(SEED, cache_dir=tmp_path, client=DecliningClient())
    books = simulate(SEED, deciding(agent))
    assert all(e.action == HOLD for e in agent.entries)
    assert all(e.reason_source == "model" for e in agent.entries if e.queued)
    assert (books.rates == simulate(SEED).rates).all()


def test_minimum_stay_advice_is_not_repeated_on_later_days(tmp_path):
    agent = Agent(SEED, cache_dir=tmp_path)
    ahead = SimpleNamespace(hotel="convention", first_stay=44, last_stay=46, causes=(AHEAD,))
    sources = simulated_sources(Books(SEED))
    assert [a.stay_day for a in agent.advice_for(34, [ahead], sources)] == [45]
    assert agent.advice_for(35, [ahead], sources) == []


def test_minimum_stay_advice_is_given_once_per_hotel_and_event_and_not_simulated(run):
    agent, _ = run
    assert agent.advice
    assert len({a.hotel for a in agent.advice}) == len(agent.advice)
    for advice in agent.advice:
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
    assert change == pytest.approx(2930.63, abs=0.01)
    assert sum(1 for e in agent.entries if e.action != HOLD) == 17 and len(agent.entries) == 89


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
