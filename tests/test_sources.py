"""Module 10, sources.py: the agent reads data only through the four interfaces, as of a day."""

import ast
import statistics
from pathlib import Path

import pytest

import hotel_market
from hotel_market.bookings import simulate
from hotel_market.customer import demo
from hotel_market.simulated import simulated_sources

DEMO = demo()

# The agent's modules, and the modules that hold the truth they must never read.
AGENT_MODULES = ("detect", "forecast", "estimate", "plan", "model", "agent", "text", "stored")
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
