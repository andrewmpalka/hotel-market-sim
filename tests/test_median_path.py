"""scripts/median_path.py: the comp median's path next to the hotel's rate, from a template run."""

import importlib.util
from pathlib import Path

import pytest

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
    rows, agent, books = median_path.median_path(7, "convention", stays, days, react=True)
    assert books.react and [day for day, _ in rows] == list(days)
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
    plain, _, plain_books = median_path.median_path(7, "convention", stays, days)
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
    assert "stay 45" in out and "Day 10: raise" in out
