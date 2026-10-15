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
    stays, days = range(75, 76), range(16, 26)
    rows, agent, books, fixed = median_path.median_path(7, "lifestyle", stays, days, react=True)
    plain, _, plain_books, _ = median_path.median_path(7, "lifestyle", stays, days)
    assert books.react and fixed.react and not plain_books.react
    assert [day for day, _ in rows] == [day for day, _ in plain] == list(days)
    assert all((fixed.rates[h.row] == h.start_rate).all() for h in demo().hotels)
    rate = {day: cells[0][0] for day, cells in rows}  # stay 75, a Saturday
    median = {day: cells[0][1] for day, cells in rows}
    unmoved = {day: cells[0][1] for day, cells in plain}  # the same shop with no reaction
    # The lifestyle hotel's plan accepted on day 18 takes effect on day 19, and a second raise
    # on day 21. The median follows each REACTION_LAG days later. The shop noise moves both runs
    # alike, so the reaction is the gap between them.
    assert rate[18] == 240 and rate[19] > 240 and rate[21] > rate[19]
    for day in range(16, 19 + REACTION_LAG):
        assert median[day] == unmoved[day]
    for day in range(19 + REACTION_LAG, 21 + REACTION_LAG):
        assert median[day] - unmoved[day] == pytest.approx(REACTION_SHARE * (rate[19] - 240))
    for day in range(21 + REACTION_LAG, 26):
        assert median[day] - unmoved[day] == pytest.approx(REACTION_SHARE * (rate[21] - 240))
    # Without the reaction the median stays within the noise of its starting level.
    assert all(abs(unmoved[day] / 240 - 1) <= 0.03 for day in days)
    median_path.main(
        [
            "--seed",
            "7",
            "--react",
            "--hotel",
            "lifestyle",
            "--stays",
            "75",
            "75",
            "--days",
            "16",
            "25",
        ]
    )
    out = capsys.readouterr().out
    assert "Seed 7, Lifestyle hotel, template run, competitors moving 50%" in out
    assert "stay 75" in out and "Day 18: raise" in out and "Rooms sold by day 25" in out
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
    # cheaper market draws more demand at 0.5, so the hotel sells more rooms over the stay dates.
    medians = {day: cells[0][1] for day, cells in rows}
    assert medians[30] < 0.92 * medians[29]
    sold = [int(answered.rooms[row, s] - plain.rooms[row, s]) for s in stays]
    assert min(sold) >= 0 and sum(sold) > 0
    for s in stays:
        assert answered_fixed.rooms[row, s] == answered.rooms[row, s]  # nothing changed here
