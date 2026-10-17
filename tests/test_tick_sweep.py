"""scripts/tick_sweep.py: the template sweep on the daily clock and on a finer one."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("tick_sweep", ROOT / "scripts" / "tick_sweep.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_sweep_runs_a_seed_at_each_clock_and_reads_the_lag_from_the_filing(script, tmp_path):
    """Seed 7 at one tick a day is the README's run. At four ticks the agent decides after each
    tick, so some decisions fall off the day's last tick, and the lag from the day-20 filing to
    the first accepted raise on its stay dates is counted in ticks from the filing's tick."""
    one = script.seed_result(7, 1, tmp_path / "one")
    four = script.seed_result(7, 4, tmp_path / "four")
    assert one["change"] == pytest.approx(19796, abs=1)
    assert (
        one["off_last"] == one["off_last_accepted"] == 0
    )  # the daily loop's only tick is the last
    assert four["off_last"] > 0 and four["off_last_accepted"] >= 0
    assert one["lag"] == 0  # the filing and the raise are both on day 20, the one tick
    assert four["lag"] is not None and four["lag"] >= 0
    rows = [script.sweep(7, 7, ticks, tmp_path / f"ticks-{ticks}") for ticks in (1, 4)]
    assert rows[0]["changes"] == [one["change"]] and rows[1]["changes"] == [four["change"]]
    assert rows[0]["raised"] == 1 and rows[0]["lag"] == 0
    text = script.table(rows)
    assert text.startswith("| Ticks a day | Mean change a seed | SD | SE | Range | Ahead | p |")
    assert (
        "| 1 | +$19,796 | n/a | n/a | +$19,796 to +$19,796 | 1 of 1 | 1.0 | 0 | 0 | 1 of 1 | 0.00 |"
        in text
    )
    assert text.count("\n| 4 |") == 1
    assert "Paired difference, 4 ticks minus 1: mean " in text and "sign test p" in text
    assert script.FILING_DAY == 20


def test_the_sweep_takes_a_customer_and_an_event_and_reads_what_its_stay_dates_did(
    script, tmp_path
):
    """On the intraday market the lag runs from the concert's announcement, tick 2 of day 25 at
    four ticks, to the first accepted raise on its stay dates at its two hotels. The finer clock
    reaches the raise with fewer rooms already booked on those nights, because the daily loop
    cannot act before the day ends, and the table carries the two columns."""
    from hotel_market.customer import load

    market = load(ROOT / "customers" / "demo-intraday.toml")
    concert = script.find_event(market, "concert")
    assert concert.name == "Concert" and concert.known_day == 25
    with pytest.raises(SystemExit, match="no event named"):
        script.find_event(market, "parade")
    one = script.seed_result(7, 1, tmp_path / "one", market, concert)
    four = script.seed_result(7, 4, tmp_path / "four", market, concert)
    assert one["lag"] == 0 and four["lag"] is not None and four["lag"] >= 0
    assert 0 < four["rooms_before_raise"] < one["rooms_before_raise"]
    assert one["earned"] > 0 and four["earned"] > 0
    rows = [
        script.sweep(7, 7, ticks, tmp_path / f"ticks-{ticks}", market, concert) for ticks in (1, 4)
    ]
    assert rows[0]["rooms_before_raise"] == one["rooms_before_raise"]
    assert rows[1]["earned"] == four["earned"]
    text = script.table(rows, "the concert announcement")
    assert (
        "Seeds with a raise after the concert announcement | Mean lag in ticks | Rooms booked"
        in text
    )
    assert "| Contribution on its stay dates against the fixed-rate run |" in text
    assert text.count("\n| 4 |") == 1 and "Paired difference, 4 ticks minus 1" in text
    # The day-20 filing lands at tick 1 of day 20 in this market, so the lag counts from there.
    assert script.filing_moment(market, 4) == script.moment_index(20, 1, 4)
    assert script.filing_moment(script.demo(), 4) == script.moment_index(20, 3, 4)
