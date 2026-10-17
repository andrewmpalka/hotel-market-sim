"""Module 11, customer.py: the market from its file, and the target as a setting."""

from dataclasses import replace
from pathlib import Path

import pytest

from hotel_market import customer
from hotel_market.agent import Agent, ElasticityMode
from hotel_market.bookings import Books, simulate
from hotel_market.cli import main, run
from hotel_market.customer import CUSTOMER_VARIABLE, DEMO_FILE, demo, demo_path, load
from hotel_market.demand import MARKET_ELASTICITY
from hotel_market.detect import detect_numbers, flags
from hotel_market.forecast import ORACLE_MARKET_ELASTICITY
from hotel_market.model import request_for
from hotel_market.plan import entry_for
from hotel_market.simulated import simulated_sources
from hotel_market.sources import Event
from hotel_market.world import RateCut

ROOT = Path(__file__).resolve().parents[1]
HARBOUR_FILE = ROOT / "customers" / "harbour.toml"
INTRADAY_FILE = ROOT / "customers" / "demo-intraday.toml"
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
    # Each hotel carries its own booking curve, pinned at the same days out.
    assert all(h.curve_days_out == (0, 7, 30, 60, 90) for h in DEMO.hotels)
    assert {h.key: h.curve_share for h in DEMO.hotels} == {
        "convention": (1.0, 0.85, 0.6, 0.45, 0.25),
        "full-service": (1.0, 0.75, 0.5, 0.3, 0.1),
        "lifestyle": (1.0, 0.7, 0.4, 0.2, 0.0),
        "airport": (1.0, 0.5, 0.2, 0.05, 0.0),
    }
    assert DEMO.hotel("lifestyle").curve(45) == pytest.approx(0.3)
    assert DEMO.market_elasticity == 1.0 == MARKET_ELASTICITY == ORACLE_MARKET_ELASTICITY
    # The market's calendar is the file's too: the convention and the competitor rate cut.
    assert DEMO.events == (
        Event("Convention", 10, 45, 48, ("convention", "full-service"), 0.35, 0.15),
    )
    assert DEMO.rate_cuts == (
        RateCut(30, 37, 39, "full-service", ("full-service comp 1", "full-service comp 2"), 0.2),
    )
    assert load(ROOT / DEMO_FILE) == DEMO


def test_the_second_market_has_three_hotels_of_other_shapes_and_its_own_calendar():
    harbour = load(HARBOUR_FILE)
    assert harbour.name == "harbour" and [h.key for h in harbour.hotels] == [
        "resort",
        "city-centre",
        "station",
    ]
    assert [h.row for h in harbour.hotels] == [0, 1, 2]
    resort, city, station = harbour.hotels
    # A resort that books far out and takes few guests by air; a station hotel that books late.
    assert resort.curve(90) == 0.35 and station.curve(30) == 0.15 and station.curve(90) == 0
    assert max(resort.air_share, station.air_share) < city.air_share
    assert {h.curve_share for h in harbour.hotels} != {h.curve_share for h in DEMO.hotels}
    # Its own limits, thresholds, comp offsets and price response.
    assert (harbour.floor_share, harbour.ceiling_share, harbour.cost_share) == (0.75, 1.35, 0.30)
    assert (harbour.pace_share, harbour.median_threshold, harbour.hold_days) == (0.12, 0.06, 5)
    assert harbour.min_value_at_stake == 200 and harbour.market_elasticity == 0.8
    assert resort.starting_median() != resort.start_rate  # the offsets are not symmetric
    assert len(resort.competitors) == 4
    # The regatta lifts the resort and the city-centre hotel; the cut hits the station hotel.
    [regatta] = harbour.events
    assert (regatta.name, regatta.known_day, regatta.hotels) == (
        "Regatta",
        12,
        ("resort", "city-centre"),
    )
    [cut] = harbour.rate_cuts
    assert (cut.known_day, cut.hotel, cut.competitors) == (
        25,
        "station",
        ("station comp 1", "station comp 2"),
    )


def test_an_event_or_a_cut_that_names_an_unknown_hotel_or_competitor_is_refused(tmp_path):
    _refused(
        tmp_path,
        'hotels = ["convention", "full-service"]',
        'hotels = ["convention", "casino"]',
        "event 'Convention' names no hotel",
    )
    _refused(tmp_path, 'hotel = "full-service"', 'hotel = "casino"', "rate cut names no hotel")
    _refused(
        tmp_path,
        'competitors = ["full-service comp 1", "full-service comp 2"]',
        'competitors = ["full-service comp 1", "full-service comp 9"]',
        "rate cut at hotel 'full-service' names no competitor",
    )
    # A market may have no calendar at all.
    text = (ROOT / DEMO_FILE).read_text()
    bare = tmp_path / "bare.toml"
    bare.write_text(text[: text.index("[[events]]")])
    assert load(bare).events == () and load(bare).rate_cuts == ()


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


def test_a_booking_curves_days_out_must_ascend_from_0(tmp_path):
    # The first match is the convention hotel's, and the error names the hotel.
    before = "days_out = [0, 7, 30, 60, 90]"
    for after in ("days_out = [0, 30, 7, 60, 90]", "days_out = [1, 7, 30, 60, 90]"):
        _refused(tmp_path, before, after, "hotel 'convention': booking_curve.days_out")


def test_a_booking_curves_shares_start_at_1_on_the_night_and_never_rise(tmp_path):
    before = "share = [1.00, 0.85, 0.60, 0.45, 0.25]"
    for after in (
        "share = [0.95, 0.85, 0.60, 0.45, 0.25]",  # not every booking is in by the night
        "share = [1.00, 0.85, 0.60, 0.65, 0.25]",  # a rise with the days out
        "share = [1.00, 0.85, 0.60, 0.45, -0.25]",  # below 0
    ):
        _refused(tmp_path, before, after, "hotel 'convention': booking_curve.share")


def test_a_share_must_lie_between_0_and_1(tmp_path):
    _refused(tmp_path, "cost_share = 0.3333333333333333", "cost_share = 1.5", "cost_share")
    _refused(tmp_path, "elasticity = 1.0", "elasticity = -1.0", "market.elasticity")
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


def test_another_market_keeps_its_cache_under_its_own_name(tmp_path):
    # The demo's paths do not change, so the recorded run replays. A second market's folders go
    # under its name, so a keyed run of it never reads the demo's answers and stops with StaleCache.
    assert DEMO.name == DEMO_FILE.stem
    assert Agent(7, tmp_path).cache_dir == tmp_path / "seed7"
    assert Agent(7, tmp_path, customer=DEMO).cache_dir == tmp_path / "seed7"
    harbour = load(HARBOUR_FILE)
    assert Agent(7, tmp_path, customer=harbour).cache_dir == tmp_path / "harbour" / "seed7"
    fixed = Agent(7, tmp_path, customer=harbour, elasticity=ElasticityMode.parse("fixed:1.0"))
    assert fixed.cache_dir == tmp_path / "harbour" / "seed7-fixed-1"


def test_the_command_takes_a_customer_file_and_a_target(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["--seed", "7", "--replay", "0", "--template", "--customer", str(ROOT / DEMO_FILE)])
    assert "Day 0 queue, replayed from the cache (seed 7)" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["--seed", "7", "--target", "profit"])
    with pytest.raises(FileNotFoundError):
        main(["--seed", "7", "--replay", "0", "--template", "--customer", "missing.toml"])


def test_the_second_market_runs_from_its_file_with_no_change_to_the_agent(
    tmp_path, monkeypatch, capsys
):
    """One flag runs the other market: the summary names its three hotels and nothing of the
    demo market's, and the agent's modules are the ones tests/test_sources.py keeps out of the
    simulator."""
    monkeypatch.chdir(tmp_path)
    main(["--seed", "7", "--template", "--customer", str(HARBOUR_FILE)])
    out = capsys.readouterr().out
    assert "All three hotels" in out and "Harbour resort" in out and "Station hotel" in out
    assert "Downtown" not in out and "Airport hotel" not in out
    assert "Days 0 to 59:" in out and (tmp_path / "decisions.jsonl").exists()
    assert "at an elasticity of 0.8 in both runs" in out


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


def _with_ticks(tmp_path, shop_ticks, event_tick, cut_tick, filing_tick):
    """A copy of the demo file that names the ticks its news lands at."""
    text = (ROOT / DEMO_FILE).read_text()
    assert text.count("elasticity = 1.0\n") == 1
    text = (
        text.replace("elasticity = 1.0\n", f"elasticity = 1.0\nshop_ticks = {list(shop_ticks)}\n")
        .replace("known_day = 10\n", f"known_day = 10\nknown_tick = {event_tick}\n")
        .replace("known_day = 30\n", f"known_day = 30\nknown_tick = {cut_tick}\n")
        + f"\n[[filings]]\nknown_day = 20\ntick = {filing_tick}\n"
    )
    path = tmp_path / "ticks.toml"
    path.write_text(text)
    return path


def test_a_file_may_name_the_ticks_its_news_lands_at(tmp_path):
    """The market's shop_ticks, a filing's tick and an event's or a cut's known_tick are optional.
    The demo file names none, so it reads as it did, and a tick that is not a whole number from 1,
    or a market with no shop, is refused."""
    assert DEMO.shop_ticks == (2,) and DEMO.filing_ticks == ()
    assert DEMO.events[0].known_tick is None and DEMO.rate_cuts[0].known_tick is None
    market = load(_with_ticks(tmp_path, [1, 2, 3, 4], 2, 3, 1))
    assert market.shop_ticks == (1, 2, 3, 4) and market.filing_ticks == ((20, 1),)
    assert market.events[0].known_tick == 2 and market.rate_cuts[0].known_tick == 3
    assert market.events == (replace(DEMO.events[0], known_tick=2),)
    for bad in ((0, 2, 3, 1), (1, 0, 1, 1), (1, 2, 0, 1), (1, 2, 3, 0), (1.5, 2, 3, 1)):
        with pytest.raises(ValueError, match="a tick is a whole number from 1"):
            load(_with_ticks(tmp_path, bad[:1], *bad[1:]))
    with pytest.raises(ValueError, match="names no tick"):
        load(_with_ticks(tmp_path, [], 2, 3, 1))
    # An event's rush is a share, 0 by default.
    _refused(tmp_path, "comp_rate_raise = 0.15\n", "comp_rate_raise = 0.15\nrush = 1.5\n", "rush")
    text = (ROOT / DEMO_FILE).read_text()
    (tmp_path / "rush.toml").write_text(
        text.replace("comp_rate_raise = 0.15\n", "comp_rate_raise = 0.15\nrush = 0.5\n")
    )
    assert load(tmp_path / "rush.toml").events[0].rush == 0.5 and DEMO.events[0].rush == 0.0


def test_the_default_file_runs_as_before_with_its_ticks_spelled_out(tmp_path):
    """A copy of the demo file that names the ticks the file defaults to, the shop at slot 2, the
    filing at tick 3, the convention at the day's last tick and the cut in the day's first shop,
    books the same rooms and writes the same decisions file byte for byte, at one tick a day and
    at four. The clock lands a named tick 4 at tick 1 of a one-tick day, as it lands a slot."""
    spelled = load(_with_ticks(tmp_path, [2], 4, 1, 3))
    for ticks in (1, 4):
        fixed, books, _ = run(7, tmp_path / f"demo{ticks}.jsonl", tmp_path / "a", ticks=ticks)
        named, named_books, _ = run(
            7, tmp_path / f"named{ticks}.jsonl", tmp_path / "b", customer=spelled, ticks=ticks
        )
        assert (fixed.rooms == named.rooms).all() and (books.rooms == named_books.rooms).all()
        assert (books.revenue == named_books.revenue).all()
        assert (books.tick_rooms == named_books.tick_rooms).all()
        assert (tmp_path / f"demo{ticks}.jsonl").read_bytes() == (
            tmp_path / f"named{ticks}.jsonl"
        ).read_bytes()


def test_the_intraday_market_is_the_demo_market_with_news_inside_the_day():
    """customers/demo-intraday.toml keeps the demo's hotels, limits, thresholds, curves and four
    shocks and adds a shop at every tick, the cut from the day's second shop, the day-20 filing
    at tick 1, a concert a week out with a rush that sells its two hotels out, and a comp set
    that reprices a weekend on Thursday afternoon. At four ticks the concert's rooms land from
    the tick it is announced at."""
    market = load(INTRADAY_FILE)
    assert market.name == "demo-intraday" and market.hotels == DEMO.hotels
    settings = (
        "target", "floor_share", "ceiling_share", "cost_share", "pace_share", "pace_noise_sd",
        "seat_threshold", "median_threshold", "hold_days", "min_value_at_stake",
        "market_elasticity",
    )  # fmt: skip
    assert all(getattr(market, name) == getattr(DEMO, name) for name in settings)
    assert market.shop_ticks == (1, 2, 3, 4) and market.filing_ticks == ((20, 1),)
    assert market.rate_cuts == (replace(DEMO.rate_cuts[0], known_tick=2),)
    convention, concert, repricing = market.events
    assert convention == DEMO.events[0]
    assert concert == Event("Concert", 25, 31, 32, ("lifestyle", "full-service"), 2.0, 0.0, 2, 0.5)
    assert repricing == Event("Weekend repricing", 45, 47, 48, ("lifestyle",), 0.0, 0.10, 3)
    intraday = simulate(7, last_day=32, customer=market, ticks=4)
    daily = simulate(7, last_day=32, ticks=4)
    for key in ("lifestyle", "full-service"):
        hotel = market.hotel(key)
        assert (intraday.rooms[hotel.row, 31:33] == hotel.rooms).all()
        assert (daily.rooms[hotel.row, 31:33] < 0.8 * hotel.rooms).all()
        landed = intraday.tick_rooms[25, :, hotel.row, 31]
        assert landed[1:].sum() > 3 * landed[0]  # the rush books from tick 2 of day 25
