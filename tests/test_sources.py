"""Module 10, sources.py: the agent reads data only through the four interfaces, as of a day."""

import ast
import statistics
from pathlib import Path

import pytest

import hotel_market
from hotel_market.bookings import simulate
from hotel_market.customer import demo
from hotel_market.simulated import deciding, simulated_sources

DEMO = demo()

# The agent's modules, and the modules that hold the truth they must never read.
AGENT_MODULES = (
    "detect",
    "forecast",
    "estimate",
    "plan",
    "model",
    "agent",
    "text",
    "stored",
    "bench",
    "policy",
)
TRUTH_MODULES = ("demand", "bookings", "shops", "schedule", "shocks", "simulated")
TRUTH_NAMES = {
    "ELASTICITY",
    "EVENTS",
    "RATE_CUTS",
    "AIR_SHOCKS",
    "BASE_ROUTES",
    "Books",
    "simulate",
}


def _imports(name: str) -> list[tuple[str, str | None]]:
    """(module, imported name) for every import in one of the package's modules."""
    tree = ast.parse((Path(hotel_market.__file__).parent / f"{name}.py").read_text())
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(alias.name, None) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            found += [(node.module, alias.name) for alias in node.names]
    return found


def test_the_agent_reads_only_through_the_interfaces():
    forbidden = {f"hotel_market.{module}" for module in TRUTH_MODULES}
    for name in AGENT_MODULES:
        for module, imported in _imports(name):
            assert module not in forbidden, f"{name}.py imports {module}"
            if module == "hotel_market":
                assert imported not in TRUTH_MODULES, f"{name}.py imports hotel_market.{imported}"
            assert imported not in TRUTH_NAMES, f"{name}.py imports {imported} from {module}"


def test_the_simulated_sources_answer_as_of_the_day():
    books = simulate(7, last_day=40)
    sources = simulated_sources(books)
    for day in (0, 20, 40):
        # Rooms on the books as of a day: the opening rooms plus every day's bookings through it.
        expected = books.preload + books.daily_rooms[: day + 1].sum(axis=0)
        assert (sources.bookings.on_books(day) == expected).all()
    assert (sources.bookings.on_books(40) == books.rooms).all()  # today's answer is the books
    history = sources.bookings.history(20)
    assert history.taken.shape[0] == 20 and (history.taken == books.daily_rooms[:20]).all()
    assert (history.rates == books.daily_rates[:20]).all() and (
        history.opening == books.preload
    ).all()
    assert sources.shops.median_history(20).shape[0] == 20
    # Day 55 gains the 720 new seats on a normal day's 4,244 once the day-20 filing is known.
    assert sources.schedules.seats(19)[55] == 4244 and sources.schedules.seats(20)[55] == 4964
    assert sources.schedules.seat_change(19)[55] == 0
    assert sources.schedules.seat_change(20)[55] == pytest.approx(720 / 4244)
    assert sources.schedules.seat_revision(19)[55] == 0
    assert sources.schedules.seat_revision(20)[55] == pytest.approx(720 / 4244)
    assert [e.name for e in sources.events.known(9)] == []
    assert [e.name for e in sources.events.known(10)] == ["Convention"]
    hotel = DEMO.hotels[0]
    shopped = sources.shops.competitor_rates(10, hotel, 46)
    assert len(shopped) == 4
    assert sources.shops.median(10, hotel, 46) == pytest.approx(statistics.median(shopped.values()))


def test_the_simulated_rate_shops_carry_the_reaction_the_simulator_used():
    from hotel_market.bookings import Books
    from hotel_market.shops import REACTION_SHARE, comp_median

    hotel = DEMO.hotel("convention")
    books = Books(7, react=True)
    for day in range(6):
        books.book(day)
    books.set_rates({("convention", 50): hotel.start_rate + 20.0})  # in force from day 6
    for day in range(6, 13):
        books.book(day)
    sources = simulated_sources(books)
    # Before the lag the shop is the seed's own; from day 9 it carries the reaction, and the
    # source answers exactly what the loop shopped and logged.
    assert sources.shops.median(8, hotel, 50) == comp_median(8, hotel, 50, seed=7)
    assert sources.shops.median(9, hotel, 50) == pytest.approx(
        comp_median(9, hotel, 50, seed=7) + REACTION_SHARE * 20.0
    )
    assert sources.shops.median(9, hotel, 50) == books.daily_medians[9, hotel.row, 50]
    shopped = sources.shops.competitor_rates(9, hotel, 50)
    assert statistics.median(shopped.values()) == pytest.approx(sources.shops.median(9, hotel, 50))
    assert sources.shops.median_history(10)[9, hotel.row, 50] == sources.shops.median(9, hotel, 50)


def test_the_simulated_first_median_is_the_shop_before_any_shock():
    from hotel_market.shops import comp_median

    sources = simulated_sources(simulate(7, last_day=12))
    convention = DEMO.hotel("convention")
    assert sources.shops.first_median(convention, 46) == comp_median(-1, convention, 46, seed=7)
    assert sources.shops.first_median(convention, 46) == sources.shops.median(0, convention, 46)
    assert sources.shops.median(10, convention, 46) == pytest.approx(
        1.15 * sources.shops.first_median(convention, 46)
    )


def test_the_simulated_schedules_follow_the_runs_scenario():
    from hotel_market.schedule import UPGAUGE_SCENARIO
    from hotel_market.simulated import SimulatedSchedules

    sources = simulated_sources(simulate(7, last_day=16, scenario=UPGAUGE_SCENARIO))
    assert sources.schedules.seats(14)[52] == 4244 and sources.schedules.seats(15)[52] == 4514
    assert SimulatedSchedules().seats(20)[55] == 4964  # the default, as before


def test_the_simulated_sources_refuse_a_later_day_and_hand_out_copies():
    books = simulate(7, last_day=20)
    sources = simulated_sources(books, 20)
    hotel = DEMO.hotels[0]
    assert sources.bookings.on_books(20).shape == books.rooms.shape
    assert sources.bookings.history(21).taken.shape[0] == 21  # today's bookings are in
    assert sources.shops.median_history(21).shape[0] == 21
    for ask in (
        lambda: sources.bookings.on_books(21),
        lambda: sources.bookings.rates(21),
        lambda: sources.bookings.history(22),
        lambda: sources.shops.competitor_rates(21, hotel, 50),
        lambda: sources.shops.median(21, hotel, 50),
        lambda: sources.shops.median_history(22),
        lambda: sources.schedules.seats(21),
        lambda: sources.events.known(21),
    ):
        with pytest.raises(ValueError, match="day 2[12] on day 20"):
            ask()
    assert simulated_sources(books).events.known(59)  # made with no day, as a test may
    # The arrays are copies, so writing to them leaves the simulator's log alone.
    history = sources.bookings.history(20)
    history.taken[0, hotel.row, 0] = 999
    history.opening[hotel.row, 0] = 999
    assert books.daily_rooms[0, hotel.row, 0] != 999 and books.preload[hotel.row, 0] != 999
    rates = sources.bookings.rates(20)
    rates[hotel.row, 25] = 1.0
    assert books.daily_rates[20, hotel.row, 25] != 1.0
    medians = sources.shops.median_history(20)
    medians[0, hotel.row, 0] = 1.0
    assert books.daily_medians[0, hotel.row, 0] != 1.0
    # The simulator makes the day's sources for the day it is deciding.
    seen = []

    class Spy:
        def decide(self, day, sources):
            seen.append((day, sources.bookings.as_of_day, sources.events.as_of_day))
            return {}

    simulate(7, deciding(Spy()), last_day=2)
    assert seen == [(0, 0, 0), (1, 1, 1), (2, 2, 2)]
