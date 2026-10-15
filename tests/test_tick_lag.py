"""scripts/tick_lag.py: the day-20 filing on the daily clock and on four ticks a day."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("tick_lag", ROOT / "scripts" / "tick_lag.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_five_lines_follow_the_filing_at_each_clock(script, tmp_path):
    """At one tick a day the filing lands at the day's one tick and the airport hotel's raise is
    accepted at the same moment; at four ticks the filing lands at tick 3 and the raise comes at
    tick 3 too, so the lag is the same tick, three quarters of the way through the day."""
    one = script.facts(7, "airport", 1, tmp_path / "one")
    four = script.facts(7, "airport", 4, tmp_path / "four")
    assert one[0] == "tick 1 of 1 on day 20" and four[0] == "tick 3 of 4 on day 20"
    assert one[1] == "tick 1 of 1 on day 20" and four[1] == "tick 3 of 4 on day 20"
    assert one[2] == "tick 1 of 1 on day 20" and four[2] == "tick 3 of 4 on day 20"
    assert one[3] == "50 to 109" and four[3] == "50 to 109"
    assert one[4].startswith(("+$", "-$")) and four[4].startswith(("+$", "-$"))
    text = script.table(one, four, 4)
    assert text.startswith("| The day-20 filing | --ticks 1 | --ticks 4 |")
    assert "| The filing landed at | tick 1 of 1 on day 20 | tick 3 of 4 on day 20 |" in text
    assert text.count("\n") == 6
    assert script.FILING_DAY == 20 and len(script.LINES) == 5
