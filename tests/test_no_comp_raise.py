"""scripts/no_comp_raise.py: the convention's competitor raise at zero, next to the shipped run."""

import importlib.util
from pathlib import Path

import pytest

from hotel_market import shocks

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location(
        "no_comp_raise", ROOT / "scripts" / "no_comp_raise.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_raise_at_zero_keeps_the_uplift_and_puts_the_event_back(script, tmp_path):
    shipped = shocks.EVENTS[0]
    assert shipped.comp_rate_raise == 0.15 and shipped.uplift == 0.35
    rows = [script.sweep(7, 7, raise_, tmp_path / f"raise-{raise_:g}") for raise_ in (0.15, 0.0)]
    assert shocks.EVENTS[0] == shipped  # put back after each sweep
    # As shipped, seed 7 is the README's run. On world v2 the downtown hotels hold most of their
    # convention business before the announcement, so neither arm accepts a plan on the
    # convention nights at this seed, nothing sells out at fixed rates, and the two agree.
    assert rows[0]["mean"] == pytest.approx(19796, abs=1) and rows[0]["ahead"] == 1
    assert rows[0]["nights"] == rows[1]["nights"] == 8
    for row in rows:
        assert row["plans"] == row["gain"] == row["sellouts"] == 0
    assert rows[1]["mean"] == pytest.approx(rows[0]["mean"])
    text = script.table(rows)
    assert text.startswith("| Competitors' raise | Mean change a seed | Range | Ahead |")
    assert "| 15% | +$19,796 | +$19,796 to +$19,796 | 1 of 1 | 0 | +$0 | 0 of 8 |" in text
    assert "| 0% |" in text and text.count("\n") == 3
