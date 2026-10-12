"""Module 25, policy.py: the pace rule as a control with no estimates and no model."""

import pytest

from hotel_market.bookings import simulate
from hotel_market.customer import demo
from hotel_market.detect import AHEAD, BEHIND, detect_numbers, flags
from hotel_market.policy import POLICIES, POLICY_STEP, PacePolicy
from hotel_market.simulated import deciding, simulated_sources

DEMO = demo()
SEED = 7


@pytest.fixture(scope="module")
def ruled():
    """A seed-7 run priced by the pace rule, and the rule that priced it."""
    rule = PacePolicy()
    return rule, simulate(SEED, deciding(rule))


def test_the_rule_raises_ahead_of_pace_and_lowers_behind_by_the_step(ruled):
    assert POLICY_STEP == 0.05 and POLICIES == {"pace": PacePolicy}
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
