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


def test_the_five_lines_follow_the_concert_on_the_intraday_market(script, tmp_path):
    """On the intraday market the concert's announcement lands at the day's one tick at one tick
    a day and at tick 2 of 4 at four; at the lifestyle hotel the first event flag and the first
    raise on its two stay dates come at the same moment on both clocks, so the lines differ in
    the tick named and in what the nights earned."""
    from hotel_market.customer import load

    market = load(ROOT / "customers" / "demo-intraday.toml")
    concert = script.find_event(market, "Concert")
    with pytest.raises(SystemExit, match="no event named"):
        script.find_event(market, "parade")
    one = script.facts(7, "lifestyle", 1, tmp_path / "one", market, concert)
    four = script.facts(7, "lifestyle", 4, tmp_path / "four", market, concert)
    assert one[0] == "tick 1 of 1 on day 25" and four[0] == "tick 2 of 4 on day 25"
    assert one[1] == "tick 1 of 1 on day 25" and four[1] == "tick 2 of 4 on day 25"
    assert one[2] == "tick 1 of 1 on day 25" and four[2] == "tick 2 of 4 on day 25"
    assert one[3] == "31 to 32" and four[3] == "31 to 32"
    assert one[4].startswith(("+$", "-$")) and four[4].startswith(("+$", "-$"))
    text = script.table(one, four, 4, "The concert announcement")
    assert text.startswith("| The concert announcement | --ticks 1 | --ticks 4 |")
    assert "| The announcement landed at | tick 1 of 1 on day 25 | tick 2 of 4 on day 25 |" in text
    assert text.count("\n") == 6 and script.EVENT_LINE == "The announcement landed at"
