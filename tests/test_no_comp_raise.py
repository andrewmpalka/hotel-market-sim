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
    # As shipped, seed 7 is the README's run. Without the raise the comp median never rises on
    # the convention nights, so no plan is made there and nothing sells out at fixed rates.
    assert rows[0]["mean"] == pytest.approx(14734, abs=1) and rows[0]["ahead"] == 1
    assert rows[0]["plans"] >= 1 and rows[0]["sellouts"] >= 1 and rows[0]["nights"] == 8
    assert rows[1]["plans"] == rows[1]["gain"] == rows[1]["sellouts"] == 0
    assert rows[1]["nights"] == 8 and rows[1]["mean"] != rows[0]["mean"]
    text = script.table(rows)
    assert text.startswith("| Competitors' raise | Mean change a seed | Range | Ahead |")
    assert "| 15% | +$14,734 | +$14,734 to +$14,734 | 1 of 1 | 1 | -$728 | 1 of 8 |" in text
    assert "| 0% |" in text and text.count("\n") == 3
