"""Module 25, policy.py: the pace rule as a control with no estimates and no model."""

import pytest

from hotel_market.bookings import simulate
from hotel_market.customer import demo
from hotel_market.detect import AHEAD, BEHIND, NEW_EVENT, SEATS_CUT, SEATS_UP, detect_numbers, flags
from hotel_market.policy import (
    LOWER,
    POLICIES,
    POLICY_STEP,
    RAISE,
    NeverCutPolicy,
    PacePolicy,
    RulesPolicy,
)
from hotel_market.simulated import deciding, simulated_sources

DEMO = demo()
SEED = 7


@pytest.fixture(scope="module")
def ruled():
    """A seed-7 run priced by the pace rule, and the rule that priced it."""
    rule = PacePolicy()
    return rule, simulate(SEED, deciding(rule))


def test_the_rule_raises_ahead_of_pace_and_lowers_behind_by_the_step(ruled):
    assert POLICY_STEP == 0.05
    assert POLICIES == {"pace": PacePolicy, "rules": RulesPolicy, "never-cut": NeverCutPolicy}
    rule, books = ruled
    assert rule.changed >= rule.acted > 0  # one or more stay dates per flag acted on
    # Replay day 0 on a fresh rule: every flag with a pace cause moves its stay dates by the
    # step from the rate in force, clamped, and nothing else moves.
    fresh = PacePolicy()
    day0 = simulate(SEED, last_day=0)
    sources = simulated_sources(day0)
    table = detect_numbers(0, sources, DEMO)
    changes = fresh.decide(0, sources)
    expected = {}
    for flag in flags(0, table, customer=DEMO):
        factor = 1 + POLICY_STEP if AHEAD in flag.causes else 1 - POLICY_STEP
        if not {AHEAD, BEHIND} & set(flag.causes):
            continue
        hotel = DEMO.hotel(flag.hotel)
        for stay_day in range(flag.first_stay, flag.last_stay + 1):
            new = hotel.clamp(factor * hotel.start_rate)
            if new != hotel.start_rate:
                expected[(flag.hotel, stay_day)] = new
    assert changes == expected and changes
    assert all(fresh.held[key] == 0 for key in changes)


def test_the_rule_keeps_the_hold_and_reads_only_the_sources(ruled):
    rule, books = ruled
    # A changed stay date rests for hold_days: no pair is changed again within the hold unless a
    # shock cause lifted it, which the detector decides, as it does for the agent.
    assert all(day <= 59 for day in rule.held.values())
    # The rule's run differs from the fixed-rate run only where it changed a rate.
    fixed = simulate(SEED)
    changed = {key for key in rule.held}
    for hotel in DEMO.hotels:
        for stay_day in range(150):
            if (hotel.key, stay_day) not in changed:
                assert books.rates[hotel.row, stay_day] == fixed.rates[hotel.row, stay_day]
    assert sum(books.contribution(h) - fixed.contribution(h) for h in DEMO.hotels) != 0


def test_the_rules_policy_adds_the_event_and_seat_rules_and_skips_a_conflict():
    pace, rules = PacePolicy(), RulesPolicy()
    assert pace.direction((NEW_EVENT,)) == 0 and rules.direction((NEW_EVENT,)) == RAISE
    assert rules.direction((SEATS_UP,)) == RAISE and rules.direction((SEATS_CUT,)) == LOWER
    assert (
        rules.direction((AHEAD, SEATS_UP)) == RAISE
        and rules.direction((BEHIND, SEATS_CUT)) == LOWER
    )
    assert rules.direction((AHEAD, SEATS_CUT)) == 0  # the causes point both ways
    assert rules.direction(("comp median up",)) == 0 and rules.direction(()) == 0
    # On day 10 the convention is announced: the rules policy raises the downtown hotels'
    # convention nights, which the pace policy leaves alone unless they run ahead of pace.
    sources = simulated_sources(simulate(SEED, last_day=10))
    by_rules, by_pace = RulesPolicy().decide(10, sources), PacePolicy().decide(10, sources)
    convention = {(key, s) for key in ("convention", "full-service") for s in range(45, 49)}
    assert convention <= set(by_rules)
    assert all(
        by_rules[key] == pytest.approx(1.05 * DEMO.hotel(key[0]).start_rate) for key in convention
    )
    assert not convention <= set(by_pace)
    assert all(by_rules[key] == by_pace[key] for key in set(by_pace) & set(by_rules) - convention)


def test_the_never_cut_policy_keeps_the_raises_and_never_lowers():
    never = NeverCutPolicy()
    assert never.name == "never-cut" and POLICIES["never-cut"] is NeverCutPolicy
    assert never.direction((AHEAD,)) == RAISE and never.direction((NEW_EVENT,)) == RAISE
    assert never.direction((SEATS_UP,)) == RAISE
    assert never.direction((BEHIND,)) == 0 and never.direction((SEATS_CUT,)) == 0
    assert (
        never.direction((AHEAD, SEATS_CUT)) == RAISE
    )  # a cut cause is no rule here, so no conflict
    # On day 40 the seat cut is filed. The rules policy lowers the cut dates; this one leaves
    # them alone and only ever raises.
    sources = simulated_sources(simulate(SEED, last_day=40))
    by_rules, by_never = RulesPolicy().decide(40, sources), NeverCutPolicy().decide(40, sources)
    lowered = {key for key, rate in by_rules.items() if rate < DEMO.hotel(key[0]).start_rate}
    assert lowered and not lowered & set(by_never)
    assert by_never and all(rate > DEMO.hotel(key[0]).start_rate for key, rate in by_never.items())
