"""Module 11, customer.py: the market from its file, and the target as a setting."""

from dataclasses import replace
from pathlib import Path

import pytest

from hotel_market import customer
from hotel_market.agent import Agent
from hotel_market.bookings import Books, simulate
from hotel_market.cli import main
from hotel_market.customer import CUSTOMER_VARIABLE, DEMO_FILE, demo, demo_path, load
from hotel_market.detect import detect_numbers, flags
from hotel_market.model import request_for
from hotel_market.plan import entry_for
from hotel_market.simulated import simulated_sources

ROOT = Path(__file__).resolve().parents[1]
DEMO = demo()


def test_the_demo_file_describes_the_market_in_claude_md():
    assert DEMO.name == "demo" and DEMO.target == "contribution"
    table = {h.name: (h.rooms, h.start_rate, h.air_share, h.base_occupancy) for h in DEMO.hotels}
    assert table == {
        "Downtown convention hotel": (400, 220, 0.60, 0.75),
        "Downtown full-service hotel": (250, 190, 0.45, 0.75),
        "Lifestyle hotel": (120, 240, 0.50, 0.75),
        "Airport hotel": (150, 140, 0.80, 0.85),
    }
    assert [h.row for h in DEMO.hotels] == [0, 1, 2, 3]
    assert DEMO.cost_share == 1 / 3 and (DEMO.floor_share, DEMO.ceiling_share) == (0.70, 1.40)
    assert (DEMO.pace_share, DEMO.pace_noise_sd) == (0.10, 3)
    assert (DEMO.seat_threshold, DEMO.median_threshold, DEMO.hold_days) == (0.05, 0.05, 7)
    assert DEMO.min_value_at_stake == 250
    assert (DEMO.curve_days_out, DEMO.curve_share) == (
        (0, 7, 30, 60, 90),
        (1.0, 0.7, 0.4, 0.2, 0.0),
    )
    assert DEMO.curve(45) == pytest.approx(0.3)
    assert load(ROOT / DEMO_FILE) == DEMO


def test_a_customer_file_with_a_bad_target_or_repeated_key_or_name_is_refused(tmp_path):
    text = (ROOT / DEMO_FILE).read_text()
    bad_target = tmp_path / "bad_target.toml"
    bad_target.write_text(text.replace('target = "contribution"', 'target = "profit"'))
    with pytest.raises(ValueError, match="target"):
        load(bad_target)
    repeated = tmp_path / "repeated.toml"
    repeated.write_text(text.replace('key = "airport"', 'key = "lifestyle"'))
    with pytest.raises(ValueError, match="keys must be unique"):
        load(repeated)
    # A request names its hotel, and the oracle and the scripted client match on the name.
    same_name = tmp_path / "same_name.toml"
    same_name.write_text(text.replace('name = "Airport hotel"', 'name = "Lifestyle hotel"'))
    with pytest.raises(ValueError, match="names must be unique"):
        load(same_name)


def _refused(tmp_path, old: str, new: str, match: str) -> None:
    """The demo file with one value changed is refused, with an error that names the field."""
    text = (ROOT / DEMO_FILE).read_text()
    assert old in text
    bad = tmp_path / "bad.toml"
    bad.write_text(text.replace(old, new, 1))
    with pytest.raises(ValueError, match=match):
        load(bad)


def test_a_hotel_needs_seven_weekday_factors(tmp_path):
    _refused(
        tmp_path,
        "weekday_factors = [0.95, 1.10, 1.10, 1.05, 0.90, 0.95, 0.80]",
        "weekday_factors = [0.95, 1.10, 1.10, 1.05, 0.90, 0.95]",
        "hotel 'convention': weekday_factors needs seven",
    )


def test_the_booking_curves_days_out_must_ascend(tmp_path):
    _refused(tmp_path, "days_out = [0, 7, 30, 60, 90]", "days_out = [0, 30, 7, 60, 90]", "days_out")


def test_a_share_must_lie_between_0_and_1(tmp_path):
    _refused(tmp_path, "cost_share = 0.3333333333333333", "cost_share = 1.5", "cost_share")
    _refused(tmp_path, "air_share = 0.60", "air_share = 1.6", "hotel 'convention': air_share")


def test_the_floor_must_be_below_the_ceiling(tmp_path):
    _refused(tmp_path, "ceiling_share = 1.40", "ceiling_share = 0.60", "floor_share.*ceiling_share")


def test_rooms_and_the_start_rate_must_be_positive(tmp_path):
    _refused(tmp_path, "rooms = 400", "rooms = 0", "hotel 'convention': rooms")
    _refused(tmp_path, "start_rate = 220", "start_rate = -220", "hotel 'convention': start_rate")


def test_the_revenue_target_scores_candidates_on_the_rate_alone(day10, tmp_path):
    _, table = day10
    revenue = replace(DEMO, target="revenue")
    [flag] = [f for f in flags(10, table) if f.hotel == "convention"]
    on_contribution = entry_for(10, flag, table, customer=DEMO)
    on_revenue = entry_for(10, flag, table, customer=revenue)
    hotel = DEMO.hotel("convention")
    for group, plain in zip(on_revenue.weekdays, on_contribution.weekdays):
        for candidate, plain_candidate in zip(group.candidates, plain.candidates):
            # The same expected bookings, each worth the rate instead of the rate minus the cost.
            assert candidate.estimate > plain_candidate.estimate
            rates = list(candidate.rates.values())
            bookings = plain_candidate.estimate / (rates[0] - hotel.room_cost)
            assert candidate.estimate == pytest.approx(bookings * rates[0])
    assert on_revenue.target == "revenue" and on_revenue.to_json()["target"] == "revenue"
    assert "target" not in on_contribution.to_json()
    request = request_for(10, hotel, [on_revenue])
    assert request["target"] == "revenue"
    assert "target" not in request_for(10, hotel, [on_contribution])
    agent = Agent(7, tmp_path, customer=revenue)
    assert agent.cache_dir.name == "seed7-revenue"


def test_the_command_takes_a_customer_file_and_a_target(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["--seed", "7", "--replay", "0", "--template", "--customer", str(ROOT / DEMO_FILE)])
    assert "Day 0 queue, replayed from the cache (seed 7)" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["--seed", "7", "--target", "profit"])
    with pytest.raises(FileNotFoundError):
        main(["--seed", "7", "--replay", "0", "--template", "--customer", "missing.toml"])


def test_without_a_customer_the_demo_market_is_the_default(tmp_path):
    agent = Agent(7, tmp_path)
    assert agent.customer == DEMO
    assert Books(7).customer == DEMO and simulate(7, last_day=0).customer == DEMO
    table = detect_numbers(10, simulated_sources(Books(7)))
    assert set(table["hotel"]) == {h.key for h in DEMO.hotels}


def test_the_customer_variable_names_the_default_file(tmp_path, monkeypatch):
    copy = tmp_path / "market.toml"
    copy.write_text((ROOT / DEMO_FILE).read_text().replace('name = "demo"', 'name = "copy"'))
    monkeypatch.setenv(CUSTOMER_VARIABLE, str(copy))
    assert demo_path() == copy and load(demo_path()).name == "copy"
    monkeypatch.delenv(CUSTOMER_VARIABLE)
    # A customers/demo.toml under the working directory never counts, so two checkouts cannot
    # read each other's file.
    (tmp_path / "customers").mkdir()
    (tmp_path / "customers" / "demo.toml").write_text(copy.read_text())
    monkeypatch.chdir(tmp_path)
    checkout = Path(customer.__file__).resolve().parents[2] / DEMO_FILE
    if checkout.exists():  # the package is a source checkout: its repository root's file is found
        assert demo_path() == ROOT / DEMO_FILE and load(demo_path()).name == "demo"
    else:  # the package is installed, as in the image: the error names the two ways out
        with pytest.raises(FileNotFoundError, match=CUSTOMER_VARIABLE):
            demo_path()
