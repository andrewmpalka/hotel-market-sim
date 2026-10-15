"""scripts/median_path.py: the comp median's path next to the hotel's rate, from a template run."""

import importlib.util
from pathlib import Path

import pytest

from hotel_market.customer import demo
from hotel_market.shops import REACTION_LAG, REACTION_SHARE

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def median_path():
    spec = importlib.util.spec_from_file_location(
        "median_path", ROOT / "scripts" / "median_path.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_median_follows_the_hotels_change_after_the_lag(median_path, capsys):
    stays, days = range(45, 49), range(8, 18)
    rows, agent, books, fixed = median_path.median_path(7, "convention", stays, days, react=True)
    assert books.react and fixed.react and [day for day, _ in rows] == list(days)
    assert all((fixed.rates[h.row] == h.start_rate).all() for h in demo().hotels)
    rate = {day: cells[0][0] for day, cells in rows}  # stay 45
    median = {day: cells[0][1] for day, cells in rows}
    # The convention is announced on day 10, the competitors raise that day, and the plan the
    # agent accepts takes effect on day 11. The median then follows REACTION_LAG days later.
    assert rate[10] == 220 and rate[11] > 220 and rate[17] == rate[11]
    assert median[10] > median[9]
    for day in range(11, 11 + REACTION_LAG):
        assert median[day] == median[10]
    moved = 11 + REACTION_LAG
    assert median[moved] - median[moved - 1] == pytest.approx(REACTION_SHARE * (rate[11] - 220))
    assert median[17] == median[moved]
    # Without the reaction the median stays where the shock left it.
    plain, _, plain_books, _ = median_path.median_path(7, "convention", stays, days)
    assert not plain_books.react
    assert all(cells[0][1] == median[10] for day, cells in plain if day >= 10)
    median_path.main(
        [
            "--seed",
            "7",
            "--react",
            "--hotel",
            "convention",
            "--stays",
            "45",
            "48",
            "--days",
            "8",
            "17",
        ]
    )
    out = capsys.readouterr().out
    assert "Seed 7, Downtown convention hotel, template run, competitors moving 50%" in out
    assert "stay 45" in out and "Day 10: raise" in out and "Rooms sold by day 17" in out
    assert "market elasticity 1" in out  # the customer file's value


def test_a_market_elasticity_softens_a_competitor_cut_for_the_hotel(median_path):
    stays, days = range(37, 40), range(29, 40)
    rows, _, plain, _ = median_path.median_path(
        7, "full-service", stays, days, market_elasticity=0.0
    )
    _, _, answered, answered_fixed = median_path.median_path(
        7, "full-service", stays, days, market_elasticity=0.5
    )
    row = plain.customer.hotel("full-service").row
    # The cut on day 30 drops the median by about a tenth and the hotel holds its rate. A
    # cheaper market draws more demand at 0.5, so the hotel sells more rooms on each stay date.
    medians = {day: cells[0][1] for day, cells in rows}
    assert medians[30] < 0.92 * medians[29]
    for s in stays:
        assert answered.rooms[row, s] > plain.rooms[row, s]
        assert answered_fixed.rooms[row, s] == answered.rooms[row, s]  # nothing changed here
