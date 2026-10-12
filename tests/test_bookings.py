"""Module 5: the booking curve, the day-0 preload and the daily booking loop."""

import math

import numpy as np
import pytest

from hotel_market.bookings import ELASTICITY, Books, poisson_draw, preload_mean, simulate
from hotel_market.customer import demo
from hotel_market.demand import DEMAND_BIAS, expected_demand
from hotel_market.schedule import HORIZON_DAYS
from hotel_market.shops import REACTION_LAG, REACTION_SHARE, comp_median
from hotel_market.world import SIM_DAYS

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
    assert [DEMO.curve(d) for d in (90, 60, 30, 7, 0)] == pytest.approx([0.0, 0.2, 0.4, 0.7, 1.0])
    assert DEMO.curve(45) == pytest.approx(0.3)
    assert DEMO.curve(18.5) == pytest.approx(0.55)  # halfway between 7 (0.7) and 30 (0.4)
    assert DEMO.curve(120) == 0.0


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
    convention = DEMO.hotel("convention")
    # Stay date 0 is tonight (a Monday): 285 rooms x DEMO.curve(1) = 285 x (1 - 0.3 / 7).
    assert preload_mean(convention, 0) == pytest.approx(285 * (1 - 0.3 / 7))
    # Stay date 89 is 89 days out: DEMO.curve(90) is 0, so nothing is booked yet.
    assert preload_mean(convention, 89) == 0


def test_day_0_starts_with_the_bookings_made_before_the_run():
    books = Books(SEED)  # the preload only, before day 0's bookings
    for hotel in DEMO.hotels:
        i = hotel.row
        expected = sum(preload_mean(hotel, s) for s in range(90))
        assert abs(books.rooms[i, :90].sum() - expected) < 4 * math.sqrt(expected)
        assert (books.rooms[i] <= hotel.rooms).all()
        assert (books.rooms[i, 90:] == 0).all()  # not in day 0's window yet
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
        price = airport.start_rate / comp_median(day, airport, stay_day, seed=SEED)
        formula = (
            expected_demand(airport, stay_day, day)
            * (DEMO.curve(days_out) - DEMO.curve(days_out + 1))
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
    # Before day 0 nothing is booked beyond the window, so there is no rate to average.
    assert math.isnan(Books(SEED).average_rate(DEMO.hotels[0], range(140, 150)))


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
