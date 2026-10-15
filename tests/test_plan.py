"""Module 7, plan.py: a flag's candidates and estimates, and its plan by day of the week."""

import math
from dataclasses import replace

import numpy as np
import pytest

from hotel_market.bookings import poisson_draw
from hotel_market.customer import demo
from hotel_market.demand import expected_demand
from hotel_market.detect import AHEAD, Flag, detect_numbers, flags
from hotel_market.estimate import ELASTICITY_MIN
from hotel_market.forecast import ORACLE_MARKET_ELASTICITY
from hotel_market.model import request_digest, request_for
from hotel_market.plan import (
    HALFWAY,
    HOLD,
    Candidate,
    Entry,
    FlagNumbers,
    Pricing,
    Range,
    WeekdayGroup,
    entry_for,
    expected_bookings,
    rescored,
)
from hotel_market.simulated import simulated_sources
from hotel_market.world import weekday

DEMO = demo()


def _expected_bookings_by_hand(mean, unsold):
    """E[min(N, unsold)] for N Poisson, summed term by term far into the tail."""
    if mean == 0:
        return 0.0
    top = int(mean + 20 * math.sqrt(mean) + 50)
    return sum(
        min(k, unsold) * math.exp(k * math.log(mean) - mean - math.lgamma(k + 1))
        for k in range(top)
    )


def _entry(*gains):
    """A made-up entry: one day-of-week group per gain, each with hold at 1,000."""
    weekdays = [
        WeekdayGroup(
            wd,
            [Candidate(HOLD, {wd: 140.0}, 1000.0), Candidate("raise 5%", {wd: 147.0}, 1000.0 + g)],
        )
        for wd, g in enumerate(gains)
    ]
    numbers = FlagNumbers(
        days_out=Range(0, 6),
        rooms_on_books=0,
        unsold_rooms=0,
        remaining_demand=0.0,
        pace_gap=0.0,
        passenger_change=Range(0.0, 0.0),
        passenger_revision=Range(0.0, 0.0),
        rate=Range(140.0, 140.0),
        comp_median=Range(140.0, 140.0),
        rate_vs_median=Range(0.0, 0.0),
        median_change=Range(0.0, 0.0),
        new_event=None,
    )
    return Entry(
        5,
        "airport",
        0,
        len(gains) - 1,
        (AHEAD,),
        numbers,
        weekdays,
        minimum=DEMO.min_value_at_stake,
    )


def _airport_entry(day, books):
    """The airport hotel's entry for stay dates 50 to 109: the flag the new flights raise."""
    table = detect_numbers(day, simulated_sources(books))
    [entry] = [
        entry_for(day, f, table)
        for f in flags(day, table)
        if f.hotel == "airport" and f.first_stay == 50
    ]
    return entry, table


def test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits(day10):
    _, table = day10
    airport = DEMO.hotel("airport")
    entry = entry_for(10, Flag(10, "airport", 40, 53, (AHEAD,)), table)  # two full weeks
    rates = table.query("hotel == 'airport'").set_index("stay_day")["rate"]
    assert [g.weekday for g in entry.weekdays] == list(range(7))
    for g in entry.weekdays:
        assert g.stays == [s for s in range(40, 54) if weekday(s) == g.weekday]
        assert [c.name for c in g.candidates] == [HOLD, "raise 5%", "raise 10%", "lower 5%"]
        for c, factor in zip(g.candidates, (1.00, 1.05, 1.10, 0.95)):
            assert c.rates == pytest.approx({s: factor * rates[s] for s in g.stays})
    # A rate already near the ceiling is clamped to it.
    near = table.copy()
    near.loc[(near["hotel"] == "airport") & (near["stay_day"] == 40), "rate"] = (
        0.97 * airport.ceiling
    )
    [group] = entry_for(10, Flag(10, "airport", 40, 40, (AHEAD,)), near).weekdays
    assert group.candidates[2].rates[40] == pytest.approx(airport.ceiling)


def test_a_comp_median_drop_adds_lower_halfway_to_the_new_median(books_through):
    table = detect_numbers(30, simulated_sources(books_through(30)))
    [entry] = [
        entry_for(30, f, table)
        for f in flags(30, table)
        if f.hotel == "full-service" and f.first_stay == 37
    ]
    rows = table.query("hotel == 'full-service'").set_index("stay_day")
    for g in entry.weekdays:
        halfway = next(c for c in g.candidates if c.name == HALFWAY)
        for s in g.stays:
            assert halfway.rates[s] == pytest.approx(
                (rows.loc[s, "rate"] + rows.loc[s, "comp_median"]) / 2
            )


def test_expected_bookings_is_the_mean_of_a_poisson_count_that_stops_at_the_unsold_rooms():
    assert expected_bookings(3.0, 1) == pytest.approx(
        1 - math.exp(-3.0)
    )  # one room: sold unless N = 0
    assert expected_bookings(20.0, 400) == pytest.approx(20.0)  # far from full: the mean
    assert expected_bookings(500.0, 100) == pytest.approx(100.0)  # far past full: every room
    assert expected_bookings(0.0, 50) == 0 and expected_bookings(10.0, 0) == 0
    for mean, unsold in [(100.0, 100), (145.0, 150), (0.5, 3), (37.2, 41)]:
        assert expected_bookings(mean, unsold) == pytest.approx(
            _expected_bookings_by_hand(mean, unsold)
        )
    # Near full it is clearly below min(mean, unsold), the cap it replaced.
    assert expected_bookings(100.0, 100) == pytest.approx(96.01, abs=0.01)


def test_expected_bookings_matches_the_simulators_daily_draws():
    # Twenty days of Poisson draws, each stopped at the rooms still unsold, as
    # bookings.py books them.
    rng = np.random.default_rng(0)
    mean, unsold, days, runs = 145.0, 150, 20, 40_000
    left = np.full(runs, unsold)
    for _ in range(days):
        left -= np.minimum(poisson_draw(rng.random(runs), np.full(runs, mean / days)), left)
    sold = unsold - left
    assert sold.mean() == pytest.approx(
        expected_bookings(mean, unsold), abs=4 * sold.std() / math.sqrt(runs)
    )
    assert sold.mean() < min(mean, unsold) - 2


def test_estimate_is_expected_contribution_on_the_unsold_rooms(day10):
    _, table = day10
    # Stay date 40 at the airport is far from full; the convention hotel's peak
    # night 45 would overfill.
    for key, stay_day in (("airport", 40), ("convention", 45)):
        hotel = DEMO.hotel(key)
        [group] = entry_for(10, Flag(10, key, stay_day, stay_day, (AHEAD,)), table).weekdays
        row = table.query("hotel == @key and stay_day == @stay_day").iloc[0]
        ratio = row["comp_median"] / hotel.starting_median()
        demand = expected_demand(hotel, stay_day, 10, 1.0, ratio, DEMO.market_elasticity)
        remaining = demand * (1 - hotel.curve(stay_day - 10))
        unsold = hotel.rooms - row["rooms"]
        for c in group.candidates:
            rate = c.rates[stay_day]
            mean = remaining * (rate / row["comp_median"]) ** -1.5
            assert c.estimate == pytest.approx(
                _expected_bookings_by_hand(mean, unsold) * (rate - hotel.start_rate / 3)
            )


def test_on_nights_that_will_not_sell_out_the_start_rate_is_already_best(books_through):
    # With flat rates every night starts at 3 x cost, the best rate when demand
    # cannot fill the hotel: a Wednesday and a Saturday alike.
    table = detect_numbers(0, simulated_sources(books_through(0)))
    for stay_day in (2, 5):
        entry = entry_for(0, Flag(0, "airport", stay_day, stay_day, (AHEAD,)), table)
        assert not entry.changed_weekdays and entry.value_at_stake == 0 and not entry.queued


def _sell_out_chance(hotel, table, stay_day, day):
    """The chance that the night sells out at today's rate: P(Poisson(mean) >= unsold)."""
    row = table.query("hotel == @hotel.key and stay_day == @stay_day").iloc[0]
    ratio = row["comp_median"] / hotel.starting_median()
    demand = expected_demand(hotel, stay_day, day, 1.0, ratio, DEMO.market_elasticity)
    mean = demand * (1 - hotel.curve(stay_day - day)) * (row["rate"] / row["comp_median"]) ** -1.5
    unsold = int(hotel.rooms - row["rooms"])
    counts = np.arange(unsold)
    log_factorial = np.concatenate(([0.0], np.cumsum(np.log(counts[1:]))))
    return 1 - np.exp(counts * math.log(mean) - mean - log_factorial).sum()


def test_a_raise_wins_where_the_night_would_often_sell_out_at_todays_rate(day10):
    # Day 10: the convention is announced and its competitors raise 15%. The full-service
    # hotel's Thursday peak night (45) would then sell out at today's rate about as often as
    # not, so a raise wins and the plan is queued. The convention hotel already holds most of
    # its group business, so its Thursday hardly ever sells out and nothing worth the minimum
    # beats holding.
    _, table = day10
    full_service, convention = DEMO.hotel("full-service"), DEMO.hotel("convention")
    assert 0.3 < _sell_out_chance(full_service, table, 45, 10) < 0.6
    assert _sell_out_chance(convention, table, 45, 10) < 0.05
    entries = {(f.hotel, f.first_stay): entry_for(10, f, table) for f in flags(10, table)}
    full_service_entry, convention_entry = entries["full-service", 45], entries["convention", 45]
    [thursday] = [g for g in full_service_entry.weekdays if g.stays == [45]]
    assert thursday.best.name == "raise 10%" and full_service_entry.queued
    assert convention_entry.value_at_stake < 10 and not convention_entry.queued


def test_after_the_new_flights_the_airport_raises_every_night_close_to_full(books_through):
    # As of day 20 the new flights have just opened at their lowest load factor. The airport's
    # busiest nights, Mondays, Wednesdays, Thursdays and Sundays, raise 10%; Tuesdays and Fridays
    # sit a little further from full and raise 5%; Saturday, the quietest night, holds.
    entry, _ = _airport_entry(20, books_through(20))
    best = {g.weekday: g.best.name for g in entry.weekdays}
    assert [best[d] for d in (0, 2, 3, 6)] == ["raise 10%"] * 4
    assert [best[d] for d in (1, 4)] == ["raise 5%"] * 2
    assert best[5] == HOLD
    assert all(g.best.name.startswith("raise") for g in entry.changed_weekdays)
    assert entry.value_at_stake == pytest.approx(sum(g.gain for g in entry.changed_weekdays))
    assert set(entry.new_rates) == {s for g in entry.changed_weekdays for s in g.stays}


def test_a_night_close_to_full_raises_where_a_cap_on_demand_would_hold(books_through):
    # The lifestyle hotel's Fridays as of day 20, with the new flights just filed, are expected
    # about 96% full.
    lifestyle = DEMO.hotel("lifestyle")
    table = detect_numbers(20, simulated_sources(books_through(20)))
    [flag] = [f for f in flags(20, table) if f.hotel == "lifestyle" and f.first_stay == 50]
    entry = entry_for(20, flag, table)
    [friday] = [g for g in entry.weekdays if g.weekday == 4]
    rows = table.query("hotel == 'lifestyle'").set_index("stay_day")
    full = sum(expected_demand(lifestyle, s, 20) for s in friday.stays) / (
        lifestyle.rooms * len(friday.stays)
    )
    assert 0.95 < full < 1.00

    def capped(candidate):
        """The estimate the exact one replaced: expected demand capped at the unsold rooms."""
        return sum(
            min(
                expected_demand(lifestyle, s, 20)
                * (1 - lifestyle.curve(s - 20))
                * (r / rows.loc[s, "comp_median"]) ** -1.5,
                lifestyle.rooms - rows.loc[s, "rooms"],
            )
            * (r - lifestyle.room_cost)
            for s, r in candidate.rates.items()
        )

    assert max(friday.candidates, key=capped).name == HOLD
    assert friday.best.name == "raise 10%" and friday.gain > 0


def test_a_plan_lists_its_changes_by_day_of_week():
    entry = _entry(300, 0, 0, 50)
    assert entry.plan == "raise 5% on Mon, Thu"
    assert entry.value_at_stake == 350
    assert set(entry.new_rates) == {0, 3}
    # A second action on Sunday follows the first, after a semicolon, and adds its gain.
    sunday = WeekdayGroup(
        6, [Candidate(HOLD, {6: 140.0}, 1000.0), Candidate("raise 10%", {6: 154.0}, 1080.0)]
    )
    entry.weekdays.append(sunday)
    assert entry.plan == "raise 5% on Mon, Thu; raise 10% on Sun"
    assert entry.value_at_stake == 430
    assert entry.new_rates == {0: 147.0, 3: 147.0, 6: 154.0}


def test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue():
    assert DEMO.min_value_at_stake == 250
    assert _entry(250).queued
    assert not _entry(249.99).queued
    assert not _entry(0).queued


def _cautious_group(*candidates):
    """A weekday group under the cautious rule: hold at 1,000 at every elasticity, then
    one candidate per (estimate, band) given."""
    hold = Candidate(HOLD, {0: 140.0}, 1000.0, (1000.0, 1000.0))
    others = [
        Candidate(f"raise {i}%", {0: 140.0 + i}, estimate, band)
        for i, (estimate, band) in enumerate(candidates, start=5)
    ]
    return WeekdayGroup(0, [hold] + others, cautious=True)


def test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held():
    # Worth $400 at the estimate but behind hold at the high elasticity: held, and counted.
    group = _cautious_group((1400.0, (1500.0, 900.0)))
    assert group.best.name == HOLD and [c.name for c in group.rejected_at_an_end] == ["raise 5%"]
    # Ahead at all three: it replaces hold.
    group = _cautious_group((1300.0, (1310.0, 1290.0)))
    assert group.best.name == "raise 5%" and group.rejected_at_an_end == []
    # Ahead at all three by a little: it replaces hold too. The minimum value at stake
    # applies to the whole plan, through Entry.queued, as in every mode.
    group = _cautious_group((1010.0, (1005.0, 1001.0)))
    assert group.best.name == "raise 5%" and group.rejected_at_an_end == []
    # Behind hold at the estimate: held, and not counted as a band rejection.
    group = _cautious_group((990.0, (1200.0, 1050.0)))
    assert group.best.name == HOLD and group.rejected_at_an_end == []
    # The best at the estimate loses at an end; the next best passes and wins.
    group = _cautious_group((1600.0, (1700.0, 990.0)), (1300.0, (1310.0, 1290.0)))
    assert group.best.name == "raise 6%" and [c.name for c in group.rejected_at_an_end] == [
        "raise 5%"
    ]
    # Without the rule the highest estimate wins as before, and nothing is rejected.
    plain = WeekdayGroup(0, group.candidates)
    assert plain.best.name == "raise 5%" and plain.rejected_at_an_end == []


def test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side(day10):
    _, table = day10
    [flag] = [f for f in flags(10, table) if f.hotel == "convention"]
    pricing = Pricing(1.5, "learn", standard_error=0.3, prior=1.0, observations=2000, cautious=True)
    assert pricing.band == (1.2, 1.8)
    entry = entry_for(10, flag, table, pricing)
    plain = entry_for(10, flag, table, Pricing(1.5, "learn", 0.3, 1.0, 2000))
    at_low = entry_for(10, flag, table, Pricing(1.2, "fixed"))
    at_high = entry_for(10, flag, table, Pricing(1.8, "fixed"))
    for group, plain_group, low_group, high_group in zip(
        entry.weekdays, plain.weekdays, at_low.weekdays, at_high.weekdays
    ):
        assert group.cautious and not plain_group.cautious
        for c, plain_c, low_c, high_c in zip(
            group.candidates, plain_group.candidates, low_group.candidates, high_group.candidates
        ):
            assert c.estimate == plain_c.estimate and plain_c.band is None
            assert c.band == pytest.approx((low_c.estimate, high_c.estimate))
        if group.best.name != HOLD:
            assert group.replaces_hold(group.best)
    # The three values reach the log line; a plain entry's line reads as before.
    line, plain_line = entry.to_json(), plain.to_json()
    assert all(
        set(c["band"]) == {"at_low_elasticity", "at_high_elasticity"}
        for w in line["by_weekday"]
        for c in w["candidates"]
    )
    assert line["rejected_at_an_end"] == entry.rejected_at_an_end
    assert line["elasticity"]["cautious"] is True
    assert line["elasticity"]["band"] == {"lowest": 1.2, "highest": 1.8}
    assert "rejected_at_an_end" not in plain_line and "cautious" not in plain_line["elasticity"]
    assert not any("band" in c for w in plain_line["by_weekday"] for c in w["candidates"])
    # The band is clamped to the estimator's bounds, and only a cautious pricing has one.
    wide = Pricing(1.5, "learn", standard_error=1.2, prior=1.0, observations=10, cautious=True)
    assert wide.band == (ELASTICITY_MIN, 2.7)
    assert Pricing(1.5, "true").band is None


def test_rescoring_at_the_pricings_elasticity_gives_the_candidates_own_estimate(day10):
    # A group keeps the stay dates it was scored from, so a grader can score a candidate
    # again at another elasticity; at the pricing's own value it gets the estimate back.
    _, table = day10
    airport = DEMO.hotel("airport")
    entry = entry_for(10, Flag(10, "airport", 40, 46, (AHEAD,)), table, Pricing(1.0, "fixed"))
    for group in entry.weekdays:
        assert [s.stay_day for s in group.stay_dates] == group.stays
        for candidate in group.candidates:
            assert rescored(group, candidate, 1.0, airport.room_cost) == pytest.approx(
                candidate.estimate
            )
            # At the simulator's value a raise is worth less than it looked at 1.0.
            at_true = rescored(group, candidate, 1.5, airport.room_cost)
            if candidate.name.startswith("raise"):
                assert at_true < candidate.estimate


def test_rescoring_with_a_demand_bias_scales_the_remaining_demand(day10):
    # The grader's demand bias multiplies each stay date's remaining demand before the rate's
    # effect on it. At 1.0 it changes nothing, and the agent's own estimate never carries one.
    _, table = day10
    airport = DEMO.hotel("airport")
    entry = entry_for(10, Flag(10, "airport", 40, 46, (AHEAD,)), table, Pricing(1.5, "true"))
    lower = 0
    for group in entry.weekdays:
        scaled = replace(
            group,
            stay_dates=[
                replace(s, remaining_demand=0.9 * s.remaining_demand) for s in group.stay_dates
            ],
        )
        for candidate in group.candidates:
            cost = airport.room_cost
            assert rescored(group, candidate, 1.5, cost, demand_bias=1.0) == pytest.approx(
                candidate.estimate
            )
            at_bias = rescored(group, candidate, 1.5, cost, demand_bias=0.9)
            assert at_bias == pytest.approx(rescored(scaled, candidate, 1.5, cost))
            assert at_bias <= candidate.estimate
            lower += at_bias < candidate.estimate
    assert lower


def test_the_plan_record_carries_the_market_elasticity_and_a_zero_one_stays_out_of_the_request(
    day10,
):
    _, table = day10
    airport = DEMO.hotel("airport")
    flag = Flag(10, "airport", 40, 46, (AHEAD,))
    plain = entry_for(10, flag, table, Pricing(1.5, "true"))
    told = entry_for(10, flag, table, Pricing(1.5, "true", market_elasticity=0.5))
    zero = entry_for(10, flag, table, Pricing(1.5, "true", market_elasticity=0.0))
    assert ORACLE_MARKET_ELASTICITY == 1.0
    assert plain.to_json()["elasticity"]["market_elasticity"] == 1.0
    assert told.to_json()["elasticity"]["market_elasticity"] == 0.5
    # The agent scores every candidate against the median as shopped, so the candidates are the
    # same; the level's effect is already in the remaining demand the detect numbers carry.
    for a, b in zip(plain.weekdays, told.weekdays):
        assert [c.estimate for c in a.candidates] == [c.estimate for c in b.candidates]
    # The request names the value, the default included; at 0.0, where the level moves
    # nothing, it stays out.
    before, after = request_for(10, airport, [plain]), request_for(10, airport, [told])
    assert before["elasticity"]["market_elasticity"] == "1"
    assert after["elasticity"]["market_elasticity"] == "0.5"
    assert "market_elasticity" not in request_for(10, airport, [zero])["elasticity"]
    assert request_digest(before) != request_digest(after)


def test_the_grader_scores_a_raise_against_the_median_the_reaction_moves(day10):
    _, table = day10
    airport = DEMO.hotel("airport")
    entry = entry_for(10, Flag(10, "airport", 40, 46, (AHEAD,)), table, Pricing(1.5, "true"))
    cost = airport.room_cost
    base = followed = answered = cut_back = 0.0
    for group in entry.weekdays:
        for candidate in group.candidates:
            if not candidate.name.startswith("raise"):
                assert rescored(group, candidate, 1.5, cost, reaction_share=0.5) <= rescored(
                    group, candidate, 1.5, cost
                )
                continue
            base += rescored(group, candidate, 1.5, cost)
            followed += rescored(group, candidate, 1.5, cost, reaction_share=0.5)
            answered += rescored(
                group, candidate, 1.5, cost, market_elasticity=1.0, reaction_share=0.5
            )
            cut_back += rescored(
                group, candidate, 1.5, cost, market_elasticity=2.0, reaction_share=0.5
            )
    # Competitors following half of a raise make it worth more. A market that answers the
    # median's level takes some of that back at 1.0, and at 2.0 more than all of it.
    assert followed > answered > base > cut_back


def test_the_plan_record_carries_the_level_and_the_request_only_a_set_one(day10):
    _, table = day10
    airport = DEMO.hotel("airport")
    flag = Flag(10, "airport", 40, 46, (AHEAD,))
    learned = Pricing(1.2, "learn", standard_error=0.3, prior=1.0, observations=600)
    plain = entry_for(10, flag, table, learned)
    scaled = entry_for(10, flag, table, replace(learned, level=0.9))
    assert plain.to_json()["elasticity"]["level"] == 1.0
    assert scaled.to_json()["elasticity"]["level"] == 0.9
    assert "level" not in request_for(10, airport, [plain])["elasticity"]
    assert request_for(10, airport, [scaled])["elasticity"]["level"] == "0.9"
