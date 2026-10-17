"""Module 5: the booking curve, the day-0 preload and the daily booking loop."""

import math
from pathlib import Path

import numpy as np
import pytest

from hotel_market.bookings import ELASTICITY, Books, poisson_draw, preload_mean, simulate
from hotel_market.customer import DEMO_FILE, demo, load
from hotel_market.demand import DEMAND_BIAS, MARKET_ELASTICITY, expected_demand, normal_demand
from hotel_market.schedule import HORIZON_DAYS
from hotel_market.shops import REACTION_LAG, REACTION_SHARE, comp_median
from hotel_market.world import SIM_DAYS, stay_window

ROOT = Path(__file__).resolve().parents[1]

DEMO = demo()

SEED = 7


@pytest.fixture(scope="module")
def fixed():
    """A fixed-rate run with seed 7."""
    return simulate(SEED)


def _starting_rates(hotel):
    """The hotel's start rate on every stay date: where every rate begins."""
    return np.full(HORIZON_DAYS, hotel.start_rate)


def test_curve_matches_the_points_and_is_linear_in_between():
    lifestyle, convention = DEMO.hotel("lifestyle"), DEMO.hotel("convention")
    points = [lifestyle.curve(d) for d in (90, 60, 30, 7, 0)]
    assert points == pytest.approx([0.0, 0.2, 0.4, 0.7, 1.0])
    assert lifestyle.curve(45) == pytest.approx(0.3)
    assert lifestyle.curve(18.5) == pytest.approx(0.55)  # halfway between 7 (0.7) and 30 (0.4)
    assert lifestyle.curve(120) == 0.0
    # Each hotel has its own curve, flat beyond its last point: the convention hotel holds a
    # quarter of its bookings 90 or more days out.
    points = [convention.curve(d) for d in (90, 60, 30, 7, 0)]
    assert points == pytest.approx([0.25, 0.45, 0.6, 0.85, 1.0])
    assert convention.curve(120) == 0.25


def test_poisson_draw_is_the_poisson_quantile():
    # Poisson with mean 2: P(X <= 0) = 0.135, P(X <= 1) = 0.406, P(X <= 2) = 0.677.
    u = np.array([0.0, 0.40, 0.50, 0.68])
    assert poisson_draw(u, np.full(4, 2.0)).tolist() == [0, 1, 2, 3]


def test_poisson_draws_have_the_right_mean_and_spread():
    u = np.random.default_rng(0).random(100_000)
    for mean in (0.3, 4.0, 60.0, 300.0):
        draws = poisson_draw(u, np.full(u.size, mean))
        assert draws.mean() == pytest.approx(mean, rel=0.02)
        assert draws.var() == pytest.approx(mean, rel=0.05)


def test_a_bigger_mean_never_draws_fewer_rooms_on_the_same_luck():
    u = np.random.default_rng(1).random(10_000)
    assert (poisson_draw(u, np.full(u.size, 3.3)) >= poisson_draw(u, np.full(u.size, 3.0))).all()


def test_preload_mean_is_normal_demand_x_curve_of_days_out_plus_1():
    convention, airport = DEMO.hotel("convention"), DEMO.hotel("airport")
    # Stay date 0 is tonight (a Monday): 285 rooms x curve(1) = 285 x (1 - 0.15 / 7).
    assert preload_mean(convention, 0) == pytest.approx(285 * (1 - 0.15 / 7))
    # Stay date 89 is 89 days out. The convention hotel's curve holds 0.25 from 90 days out, so
    # that date, and every later one, starts with a quarter of its normal demand; the airport
    # hotel's curve is 0 there, so nothing is booked yet.
    assert preload_mean(convention, 89) == pytest.approx(0.25 * normal_demand(convention, 89))
    assert preload_mean(convention, 149) == pytest.approx(0.25 * normal_demand(convention, 149))
    assert preload_mean(airport, 89) == 0


def test_day_0_starts_with_the_bookings_made_before_the_run():
    books = Books(SEED)  # the preload only, before day 0's bookings
    for hotel in DEMO.hotels:
        i = hotel.row
        expected = sum(preload_mean(hotel, s) for s in range(HORIZON_DAYS))
        assert abs(books.rooms[i].sum() - expected) < 4 * math.sqrt(expected)
        assert (books.rooms[i] <= hotel.rooms).all()
        assert (books.rooms[i] == books.preload[i]).all()  # nothing but the preload yet
        if hotel.curve(90) == 0:  # not in day 0's window yet, and nothing booked that far ahead
            assert (books.rooms[i, 90:] == 0).all()
        else:
            assert (books.rooms[i, 90:] > 0).all()
        assert books.revenue[i] == pytest.approx(books.rooms[i] * _starting_rates(hotel))


def test_a_new_rate_is_kept_to_the_cent():
    # Start rates are whole numbers, so the rates array must still hold fractions.
    books = Books(SEED)
    books.set_rates({("airport", 40): 147.35})
    assert books.rates[DEMO.hotel("airport").row, 40] == 147.35


def test_expected_new_bookings_follow_the_formula():
    books = Books(SEED)
    airport = DEMO.hotel("airport")
    for day, stay_day in [(0, 0), (0, 89), (19, 55), (20, 55), (45, 80)]:
        days_out = stay_day - day
        median = comp_median(day, airport, stay_day, seed=SEED)
        price = airport.start_rate / median
        # The market term reads the day's shop over the comp set's starting level.
        ratio = median / airport.starting_median()
        formula = (
            expected_demand(airport, stay_day, day, 1.0, ratio, DEMO.market_elasticity)
            * (airport.curve(days_out) - airport.curve(days_out + 1))
            * price**-ELASTICITY
        )
        assert books.expected_new_bookings(airport, stay_day, day) == pytest.approx(formula)
    # A rate 10% higher cuts the expected bookings by 1.1 ** -1.5.
    before = books.expected_new_bookings(airport, 55, 20)
    books.set_rates({("airport", 55): 1.1 * airport.start_rate})
    assert books.expected_new_bookings(airport, 55, 20) == pytest.approx(before * 1.1**-1.5)


def test_the_demand_bias_scales_the_preload_and_every_days_draw():
    plain, biased = Books(SEED), Books(SEED, demand_bias=0.9)
    assert plain.demand_bias == DEMAND_BIAS == 1.0 and biased.demand_bias == 0.9
    airport = DEMO.hotel("airport")
    assert preload_mean(airport, 0, demand_bias=0.9) == pytest.approx(
        0.9 * preload_mean(airport, 0)
    )
    for day, stay_day in [(0, 0), (19, 55), (45, 80)]:
        assert biased.expected_new_bookings(airport, stay_day, day) == pytest.approx(
            0.9 * plain.expected_new_bookings(airport, stay_day, day)
        )
    # The same luck draws fewer rooms around the smaller means. The rates and the competitor
    # medians are not the simulator's demand, so the bias leaves them alone.
    assert biased.preload.sum() < plain.preload.sum()
    full, less = simulate(SEED), simulate(SEED, demand_bias=0.9)
    assert less.rooms.sum() < full.rooms.sum() and (less.rates == full.rates).all()
    assert (less.daily_medians == full.daily_medians).all()
    assert less.rooms.sum() / full.rooms.sum() == pytest.approx(0.9, abs=0.03)
    assert np.array_equal(simulate(SEED, demand_bias=1.0).rooms, full.rooms)


def test_a_fifth_hotel_leaves_the_other_hotels_fixed_rate_bookings_unchanged(tmp_path, fixed):
    # Each hotel's luck and each competitor's shop noise come from streams keyed by the hotel's
    # key, so a hotel added to a copy of the customer file changes nothing at the other four.
    text = (ROOT / DEMO_FILE).read_text()
    fifth = """
[[hotels]]
key = "suburban"
name = "Suburban hotel"
rooms = 100
start_rate = 120
air_share = 0.30
base_occupancy = 0.70
weekday_factors = [1.00, 1.05, 1.05, 1.00, 0.95, 0.95, 1.00]
booking_curve = { days_out = [0, 7, 30, 60, 90], share = [1.00, 0.60, 0.30, 0.10, 0.00] }
competitors = [
    { name = "suburban comp 1", offset = -0.08 },
    { name = "suburban comp 2", offset = -0.03 },
    { name = "suburban comp 3", offset = 0.03 },
    { name = "suburban comp 4", offset = 0.08 },
]
"""
    path = tmp_path / "five.toml"
    path.write_text(text + fifth)
    five = load(path)
    assert [h.key for h in five.hotels][:4] == [h.key for h in DEMO.hotels]
    books = simulate(SEED, customer=five)
    assert books.rooms.shape == (5, HORIZON_DAYS)
    assert np.array_equal(books.rooms[:4], fixed.rooms)
    assert np.array_equal(books.revenue[:4], fixed.revenue)
    assert books.rooms[4].sum() > 0
    for hotel in DEMO.hotels:
        for day, stay in [(0, 40), (10, 46), (30, 38)]:
            assert books.comp_median(day, hotel, stay) == fixed.comp_median(day, hotel, stay)


def test_same_seed_gives_the_same_books_and_another_seed_does_not(fixed):
    again = simulate(SEED)
    assert np.array_equal(again.rooms, fixed.rooms)
    assert np.array_equal(again.revenue, fixed.revenue)
    assert not np.array_equal(simulate(SEED + 1).rooms, fixed.rooms)


def test_fixed_rate_occupancy_is_between_60_and_90_percent_for_stay_dates_0_to_59(fixed):
    for hotel in DEMO.hotels:
        assert 0.60 <= fixed.occupancy(hotel, range(SIM_DAYS)) <= 0.90


def test_every_stay_date_to_149_is_complete(fixed):
    # Had the loop stopped at day 59, stay dates 140 to 149 would be nearly empty.
    for hotel in DEMO.hotels:
        assert fixed.occupancy(hotel, range(140, 150)) > 0.60


def test_rooms_never_exceed_the_hotel(fixed):
    for hotel in DEMO.hotels:
        assert (fixed.rooms[hotel.row] <= hotel.rooms).all()


def test_fixed_rate_revenue_is_rooms_times_starting_rate(fixed):
    for hotel in DEMO.hotels:
        i = hotel.row
        assert fixed.revenue[i] == pytest.approx(fixed.rooms[i] * _starting_rates(hotel))


def test_contribution_is_revenue_minus_the_cost_of_every_room_sold(fixed):
    for hotel in DEMO.hotels:
        i = hotel.row
        stays = range(40, 50)
        expected = (
            fixed.revenue[i, 40:50].sum() - fixed.rooms[i, 40:50].sum() * hotel.start_rate / 3
        )
        assert fixed.contribution(hotel, stays) == pytest.approx(expected)


def test_occupancy_is_rooms_sold_over_rooms_available(fixed):
    for hotel in DEMO.hotels:
        i = hotel.row
        expected = fixed.rooms[i, 40:50].sum() / (hotel.rooms * 10)
        assert fixed.occupancy(hotel, range(40, 50)) == pytest.approx(expected)


def test_average_rate_is_room_revenue_over_rooms_sold(fixed):
    for hotel in DEMO.hotels:
        i = hotel.row
        expected = fixed.revenue[i, 40:50].sum() / fixed.rooms[i, 40:50].sum()
        assert fixed.average_rate(hotel, range(40, 50)) == pytest.approx(expected)
        assert fixed.average_rate(hotel, range(40, 50)) == pytest.approx(hotel.start_rate)
    # Before day 0 the airport hotel has nothing booked beyond the window, so there is no rate
    # to average; the convention hotel holds its group base there, at the start rate.
    airport, convention = DEMO.hotel("airport"), DEMO.hotel("convention")
    assert math.isnan(Books(SEED).average_rate(airport, range(140, 150)))
    assert Books(SEED).average_rate(convention, range(140, 150)) == convention.start_rate


def test_revpar_is_room_revenue_over_rooms_available(fixed):
    for hotel in DEMO.hotels:
        i = hotel.row
        stays = range(40, 50)
        expected = fixed.revenue[i, 40:50].sum() / (hotel.rooms * 10)
        assert fixed.revpar(hotel, stays) == pytest.approx(expected)
        occupancy_x_rate = fixed.occupancy(hotel, stays) * fixed.average_rate(hotel, stays)
        assert fixed.revpar(hotel, stays) == pytest.approx(occupancy_x_rate)


def test_rates_can_only_change_on_days_0_to_59():
    asked = []

    def decide(day, books):
        asked.append(day)
        return {}

    simulate(SEED, decide)
    assert asked == list(range(SIM_DAYS))


def test_decisions_see_the_books_after_that_days_bookings():
    seen = {}

    def decide(day, books):
        if day == 10:
            seen["rooms"] = books.rooms.copy()
        return {}

    simulate(SEED, decide)
    through_day_10 = Books(SEED)
    for day in range(11):
        through_day_10.book(day)
    assert np.array_equal(seen["rooms"], through_day_10.rooms)


def test_a_rate_change_applies_from_the_next_day_and_touches_no_other_stay_date(fixed):
    # On day 10, put the airport hotel's rate for stay date 40 at its ceiling.
    airport = DEMO.hotel("airport")
    i = airport.row
    changed = simulate(
        SEED, lambda day, books: {("airport", 40): airport.ceiling} if day == 10 else {}
    )

    # The rooms booked through day 10 were sold at the starting rate, the rest at the ceiling.
    through_day_10 = Books(SEED)
    for day in range(11):
        through_day_10.book(day)
    early = through_day_10.rooms[i, 40]
    late = changed.rooms[i, 40] - early
    assert changed.revenue[i, 40] == pytest.approx(
        early * airport.start_rate + late * airport.ceiling
    )

    # The dearer rate never books more rooms, and every other draw is unchanged.
    assert changed.rooms[i, 40] < fixed.rooms[i, 40]
    others = np.ones(fixed.rooms.shape, dtype=bool)
    others[i, 40] = False
    assert np.array_equal(changed.rooms[others], fixed.rooms[others])


def test_the_reaction_reads_the_hotels_rate_three_days_back_from_the_log():
    airport = DEMO.hotel("airport")
    row, change = airport.row, 0.1 * airport.start_rate
    books, plain = Books(SEED, react=True), Books(SEED)
    assert books.react and not plain.react
    for day in range(6):
        books.book(day)
        plain.book(day)
    # Two rates change after day 5's bookings, so they are in force from day 6. Stay 96 is
    # outside day 6's window, so day 6's log holds no rate for it.
    books.set_rates({("airport", 40): 1.1 * airport.start_rate, ("airport", 96): 242.0})
    for day in range(6, 12):
        books.book(day)
        plain.book(day)
    # A shop on day 9 reads day 6, the first day of the new rate; day 8 still reads the old one.
    assert books.hotel_change(2, airport, 40) == 0 and books.hotel_change(8, airport, 40) == 0
    assert books.hotel_change(9, airport, 40) == pytest.approx(change)
    assert books.hotel_change(9, airport, 96) == 0  # not known on day 6: outside its window
    assert books.hotel_change(10, airport, 96) == pytest.approx(242.0 - airport.start_rate)
    assert plain.hotel_change(9, airport, 40) == 0  # the reaction is off
    # The median the loop shopped follows: the same as the plain run until day 8, then up by
    # REACTION_SHARE of the change, and the method answers what the log holds.
    assert books.daily_medians[8, row, 40] == plain.daily_medians[8, row, 40]
    assert books.daily_medians[9, row, 40] == pytest.approx(
        plain.daily_medians[9, row, 40] + REACTION_SHARE * change
    )
    assert books.comp_median(9, airport, 40) == books.daily_medians[9, row, 40]
    assert REACTION_LAG == 3
    # The fixed-rate run never changes a rate, so it is the same with the reaction on.
    assert np.array_equal(
        simulate(SEED, last_day=30, react=True).rooms, simulate(SEED, last_day=30).rooms
    )


def test_the_market_elasticity_scales_each_days_draw_by_the_medians_level():
    convention = DEMO.hotel("convention")
    plain, market = Books(SEED, market_elasticity=0.0), Books(SEED, market_elasticity=0.5)
    # The customer file's value is the default, and it is the module's default too.
    assert Books(SEED).market_elasticity == DEMO.market_elasticity == MARKET_ELASTICITY == 1.0
    assert plain.market_elasticity == 0.0 and market.market_elasticity == 0.5
    assert convention.starting_median() == convention.start_rate
    # Before the convention is known the median moves only with the shop noise, within 3% of
    # its start. On day 10 the competitors raise 15%, and the market's demand falls by the
    # shopped ratio ** -0.5.
    before = plain.comp_median(9, convention, 46) / convention.starting_median()
    assert 0.97 <= before <= 1.03
    assert market.expected_new_bookings(convention, 46, 9) == pytest.approx(
        plain.expected_new_bookings(convention, 46, 9) * before**-0.5
    )
    ratio = plain.comp_median(10, convention, 46) / convention.starting_median()
    assert ratio == pytest.approx(1.15, rel=0.03)
    assert market.expected_new_bookings(convention, 46, 10) == pytest.approx(
        plain.expected_new_bookings(convention, 46, 10) * ratio**-0.5
    )
    assert np.array_equal(
        simulate(SEED, last_day=30, market_elasticity=1.0).rooms, simulate(SEED, last_day=30).rooms
    )
    assert not np.array_equal(
        simulate(SEED, last_day=30, market_elasticity=0.0).rooms, simulate(SEED, last_day=30).rooms
    )


# ---- the clock: one draw a day, split over the ticks --------------------------------------

# The fixed-rate seed-7 run's daily log, hashed, as it stood before the day's draw was split over
# the ticks (the run of 2026-10-15 on world v2). The default clock must book these bytes.
DAILY_ROOMS_DIGEST = "20db41d45c0dfc2f07648e873f59394aa3c2507ddb0c261eb6fb69c1a87c405a"


def test_the_fixed_rate_run_books_the_same_rooms_at_one_tick_a_day_and_at_four():
    """The day's count is drawn once and each booking goes to a tick, so the rooms per hotel and
    stay date are the same at every number of ticks, not only in expectation. The tick log sums
    to the daily log, and the revenue is the same because no rate changed."""
    import hashlib

    one, four = simulate(7), simulate(7, ticks=4)
    assert (one.daily_rooms == four.daily_rooms).all() and (one.rooms == four.rooms).all()
    assert (one.revenue == four.revenue).all() and (one.daily_rates == four.daily_rates).all()
    assert four.tick_rooms.shape == (150, 4, 4, 150)
    assert (four.tick_rooms.sum(axis=1) == four.daily_rooms).all()
    assert (one.tick_rooms[:, 0] == one.daily_rooms).all()
    assert (four.tick_rooms[20, :, 0, 45] > 0).sum() >= 2  # a day's bookings spread over its ticks
    assert hashlib.sha256(one.daily_rooms.tobytes()).hexdigest() == DAILY_ROOMS_DIGEST
    assert hashlib.sha256(four.daily_rooms.tobytes()).hexdigest() == DAILY_ROOMS_DIGEST


def test_the_default_clock_books_byte_for_byte_what_it_booked_before_the_split():
    """With one tick a day, the loop, the draw and the log are what they were before the split was
    built: the digest of the daily log is the one recorded then."""
    import hashlib

    books = simulate(7)
    assert books.ticks == 1 and books.tick_rooms.shape == (150, 1, 4, 150)
    assert hashlib.sha256(books.daily_rooms.tobytes()).hexdigest() == DAILY_ROOMS_DIGEST


def test_a_rate_changed_at_a_tick_thins_or_tops_up_the_ticks_after_it():
    """At four ticks a day, a rate changed after tick 2 applies from tick 3. A raise thins the
    bookings still to come that day, and a cut tops them up, each in proportion to the demand
    response at the new rate; the ticks before the change and every other hotel book exactly what
    the fixed-rate run books."""
    hotel = DEMO.hotel("convention")
    fixed = simulate(7, last_day=6, ticks=4)

    def at_tick_2_of_day_5(rate):
        def decide(day, books, tick):
            if (day, tick) == (5, 2):
                return {(hotel.key, s): rate for s in stay_window(5)}
            return {}

        return decide

    raised = simulate(7, at_tick_2_of_day_5(hotel.ceiling), last_day=6, ticks=4)
    cut = simulate(7, at_tick_2_of_day_5(hotel.floor), last_day=6, ticks=4)
    i = hotel.row
    for books in (raised, cut):
        assert (books.tick_rooms[:5] == fixed.tick_rooms[:5]).all()  # the days before
        assert (books.tick_rooms[5, :2] == fixed.tick_rooms[5, :2]).all()  # the ticks before
        others = [h.row for h in DEMO.hotels if h.row != i]
        assert (books.tick_rooms[5:, :, others] == fixed.tick_rooms[5:, :, others]).all()
    later = slice(2, None)  # ticks 3 and 4
    assert (raised.tick_rooms[5, later, i] <= fixed.tick_rooms[5, later, i]).all()
    assert raised.tick_rooms[5, later, i].sum() < fixed.tick_rooms[5, later, i].sum()
    assert (cut.tick_rooms[5, later, i] >= fixed.tick_rooms[5, later, i]).all()
    assert cut.tick_rooms[5, later, i].sum() > fixed.tick_rooms[5, later, i].sum()
    stays = list(stay_window(5))
    assert (raised.tick_rates[5, later, i][:, stays] == hotel.ceiling).all()
    assert (raised.tick_rates[5, :2, i][:, stays] == hotel.start_rate).all()
    assert (raised.rates[i, stays] == hotel.ceiling).all()  # in force from tick 3 and tomorrow
    # The revenue booked after the change is at the new rate.
    assert raised.revenue[i, stays].sum() == pytest.approx(
        (
            raised.tick_rooms[5, :2, i][:, stays].sum()
            + fixed.tick_rooms[:5, :, i][:, :, stays].sum()
            + raised.preload[i, stays].sum()
        )
        * hotel.start_rate
        + (
            raised.tick_rooms[5, later, i][:, stays].sum()
            + raised.tick_rooms[6, :, i][:, stays].sum()
        )
        * hotel.ceiling
    )


def test_a_rush_books_part_of_an_events_uplift_within_two_days_and_the_same_total_by_the_night(
    tmp_path,
):
    """At four ticks a day, with the convention's rush at 0.5, the two downtown hotels book more
    rooms for the convention nights on the announcement day than with no rush, from the tick the
    announcement lands, and the stay dates expect the same rooms by the night: the rush moves
    half of the uplift's rooms into the announcement day and the next, evenly over those ticks,
    and takes them off the curve. The market elasticity is 0 here so the only demand factor that
    moves between the two runs is the rush. The agent's forecast reads the uplift and never the
    rush."""
    from hotel_market.customer import DEMO_FILE, load
    from hotel_market.demand import rush_profile

    text = (ROOT / DEMO_FILE).read_text()
    path = tmp_path / "rush.toml"
    raise_ = "comp_rate_raise = 0.15\n"
    path.write_text(text.replace(raise_, raise_ + "rush = 0.5\n"))
    rushed = load(path)
    assert rushed.events[0].rush == 0.5 and DEMO.events[0].rush == 0.0
    plain = simulate(7, last_day=48, ticks=4, market_elasticity=0.0)
    quick = simulate(7, last_day=48, ticks=4, market_elasticity=0.0, customer=rushed)
    rows = [DEMO.hotel(key).row for key in ("convention", "full-service")]
    nights = slice(45, 49)
    # Nothing moves before the announcement day, and the announcement day books more at its
    # last tick, the convention's, with the rush than without, and more over the day.
    assert (quick.tick_rooms[:10] == plain.tick_rooms[:10]).all()
    at_tick_4 = (3, rows, nights)
    assert quick.tick_rooms[10][at_tick_4].sum() > plain.tick_rooms[10][at_tick_4].sum() + 10
    assert quick.daily_rooms[10][rows, nights].sum() > plain.daily_rooms[10][rows, nights].sum()
    assert quick.daily_rooms[11][rows, nights].sum() > plain.daily_rooms[11][rows, nights].sum()
    # The other hotels and the other nights book exactly what they booked.
    others = [DEMO.hotel(key).row for key in ("lifestyle", "airport")]
    assert (quick.tick_rooms[:, :, others] == plain.tick_rooms[:, :, others]).all()
    assert (quick.daily_rooms[:, rows, :45] == plain.daily_rooms[:, rows, :45]).all()
    # The profile sums to nothing over the days: what the rush adds, the curve gives up.
    hotel = DEMO.hotel("convention")
    for night in range(45, 49):
        moved = 0.0
        for day in range(10, night + 1):
            removed, added = rush_profile(hotel, night, day, 4, rushed)
            moved += sum(added.values()) - removed
        assert moved == pytest.approx(0.0, abs=1e-9)
        assert rush_profile(hotel, night, 9, 4, rushed) == (0.0, {})
        assert rush_profile(hotel, night, 10, 4, DEMO) == (0.0, {})
    # The announcement day adds one tick's worth at tick 4 and the next day four ticks' worth.
    removed, added = rush_profile(hotel, 46, 10, 4, rushed)
    assert set(added) == {4} and removed > 0
    _, next_day = rush_profile(hotel, 46, 11, 4, rushed)
    assert set(next_day) == {1} and next_day[1] == pytest.approx(4 * added[4])
    # By the night the stay dates hold the same rooms within the draws' noise.
    before, after = plain.rooms[rows, nights].sum(), quick.rooms[rows, nights].sum()
    assert abs(after - before) < 0.05 * before
