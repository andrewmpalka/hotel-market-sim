"""Fixtures shared by the test files, and the slow marker.

A test marked slow runs a 20-seed sweep or several, and the nine together take about
20 minutes on a laptop. Plain `pytest` skips them; `pytest --slow` (which `make test-all`
runs) includes them.
"""

import os
from pathlib import Path

import pytest

# The demo customer file, wherever the tests run from (the container runs them from /work).
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HOTEL_MARKET_CUSTOMER", str(ROOT / "customers" / "demo.toml"))

from hotel_market.bookings import Books  # noqa: E402
from hotel_market.detect import detect_numbers  # noqa: E402
from hotel_market.simulated import simulated_sources  # noqa: E402

SEED = 7


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", help="also run the slow 20-seed checks")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: a 20-seed check; skipped unless --slow is given")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--slow"):
        return
    skip = pytest.mark.skip(reason="slow: run with --slow or make test-all")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def books_through():
    """A function giving the books after each of days 0 to `day` at fixed rates, seed 7."""

    def build(day: int) -> Books:
        books = Books(SEED)
        for d in range(day + 1):
            books.book(d)
        return books

    return build


@pytest.fixture(scope="session")
def demo_file(tmp_path_factory):
    """The demo page's file for the recorded seed, built once for the session."""
    from hotel_market.demo_data import build

    path = tmp_path_factory.mktemp("demo") / "demo.duckdb"
    assert build(7, path), "the recorded run of seed 7 was not found"
    return path


@pytest.fixture(scope="session")
def day10(books_through):
    """The books after day 10's bookings at fixed rates, and that day's detect numbers."""
    books = books_through(10)
    return books, detect_numbers(10, simulated_sources(books))
