"""scripts/measures.py: both runs in a revenue manager's measures, and the break-even cost share."""

import importlib.util
from pathlib import Path

import pytest

from hotel_market.bookings import simulate
from hotel_market.customer import demo
from hotel_market.world import HORIZON_DAYS

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("measures", ROOT / "scripts" / "measures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_measures_are_the_books_measures_over_the_seeds(script, tmp_path):
    found = script.sweep(7, 7, tmp_path)
    fixed = simulate(7)
    hotel = demo().hotel("airport")
    own = found["airport"]
    stays = range(HORIZON_DAYS)
    assert own["fixed"]["occupancy"] == [pytest.approx(fixed.occupancy(hotel, stays))]
    assert own["fixed"]["rate"] == [pytest.approx(hotel.start_rate)]  # one rate, never changed
    assert own["fixed"]["revpar"] == [pytest.approx(fixed.revpar(hotel))]
    assert (
        0 < own["fixed"]["sold_out"][0] < 1
        and own["agent"]["sold_out"][0] < own["fixed"]["sold_out"][0]
    )
    # Seed 7: the airport hotel gives up rooms and revenue and still gains contribution.
    assert own["rooms"] < 0 and own["revenue"] < 0 < own["contribution"]
    assert own["contribution"] == pytest.approx(own["revenue"] - own["rooms"] * hotel.room_cost)
    measures = script.measures_table(found)
    assert measures.startswith("| Hotel | Occupancy, fixed | Occupancy, agent |")
    assert f"| Airport hotel | {fixed.occupancy(hotel, stays):.1%} |" in measures
    cost = script.cost_table(found, 1)
    share = (own["revenue"] / own["rooms"]) / hotel.start_rate
    assert f"| Airport hotel | {-own['rooms']:,.0f} |" in cost and f"| {share:.1%} |" in cost
