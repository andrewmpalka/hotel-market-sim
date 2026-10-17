"""Module 10, sources.py: the agent reads data only through the four interfaces, as of a day."""

import ast
import statistics
from pathlib import Path

import pytest

import hotel_market
from hotel_market.bookings import simulate
from hotel_market.customer import demo
from hotel_market.schedule import LOAD_FACTOR, RAMP_DAYS, RAMP_LOAD_FACTORS
from hotel_market.simulated import deciding, simulated_sources

DEMO = demo()

# The agent's modules, and the modules that hold the truth they must never read.
AGENT_MODULES = (
    "detect",
    "forecast",
    "estimate",
    "plan",
    "model",
    "agent",
    "text",
    "stored",
    "bench",
    "policy",
)
TRUTH_MODULES = ("demand", "bookings", "shops", "schedule", "shocks", "simulated")
TRUTH_NAMES = {
    "ELASTICITY",
    "EVENTS",
    "RATE_CUTS",
    "AIR_SHOCKS",
    "BASE_ROUTES",
    "Books",
    "simulate",
}


def _imports(name: str) -> list[tuple[str, str | None]]:
    """(module, imported name) for every import in one of the package's modules."""
    tree = ast.parse((Path(hotel_market.__file__).parent / f"{name}.py").read_text())
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(alias.name, None) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            found += [(node.module, alias.name) for alias in node.names]
    return found


def test_the_agent_reads_only_through_the_interfaces():
    forbidden = {f"hotel_market.{module}" for module in TRUTH_MODULES}
    for name in AGENT_MODULES:
        for module, imported in _imports(name):
            assert module not in forbidden, f"{name}.py imports {module}"
            if module == "hotel_market":
                assert imported not in TRUTH_MODULES, f"{name}.py imports hotel_market.{imported}"
            assert imported not in TRUTH_NAMES, f"{name}.py imports {imported} from {module}"


def test_the_simulated_sources_answer_as_of_the_day():
    books = simulate(7, last_day=40)
    sources = simulated_sources(books)
    for day in (0, 20, 40):
        # Rooms on the books as of a day: the opening rooms plus every day's bookings through it.
        expected = books.preload + books.daily_rooms[: day + 1].sum(axis=0)
        assert (sources.bookings.on_books(day) == expected).all()
    assert (sources.bookings.on_books(40) == books.rooms).all()  # today's answer is the books
    history = sources.bookings.history(20)
    assert history.taken.shape[0] == 20 and (history.taken == books.daily_rooms[:20]).all()
    assert (history.rates == books.daily_rates[:20]).all() and (
        history.opening == books.preload
    ).all()
    assert sources.shops.median_history(20).shape[0] == 20
    # Day 55 gains the 720 new seats on a normal day's 4,244 once the day-20 filing is known. The
    # passengers they carry ramp from day 50, so on day 55 the new flights are five days in.
    assert sources.schedules.seats(19)[55] == 4244 and sources.schedules.seats(20)[55] == 4964
    assert sources.schedules.passengers(19)[55] == pytest.approx(4244 * LOAD_FACTOR)
    opening, full = RAMP_LOAD_FACTORS
    added = 720 * (opening + (full - opening) * 5 / RAMP_DAYS)
    assert sources.schedules.passengers(20)[55] == pytest.approx(4244 * LOAD_FACTOR + added)
    assert sources.schedules.passenger_change(19)[55] == 0
    assert sources.schedules.passenger_change(20)[55] == pytest.approx(added / (4244 * LOAD_FACTOR))
    assert sources.schedules.passenger_revision(19)[55] == 0
    assert sources.schedules.passenger_revision(20)[55] == pytest.approx(
        added / (4244 * LOAD_FACTOR)
    )
    assert [e.name for e in sources.events.known(9)] == []
    assert [e.name for e in sources.events.known(10)] == ["Convention"]
    hotel = DEMO.hotels[0]
    shopped = sources.shops.competitor_rates(10, hotel, 46)
    assert len(shopped) == 4
    assert sources.shops.median(10, hotel, 46) == pytest.approx(statistics.median(shopped.values()))


def test_the_sources_hand_the_agent_another_markets_calendar():
    """The events and the rate cuts a run's sources carry are the customer's own, so the agent
    learns of another market's regatta through the same interface, with no module of its own
    changed."""
    from hotel_market.customer import load

    harbour = load(Path(hotel_market.__file__).resolve().parents[2] / "customers" / "harbour.toml")
    books = simulate(7, last_day=26, customer=harbour)
    sources = simulated_sources(books, 26)
    assert [e.name for e in sources.events.known(11)] == []
    assert [e.name for e in sources.events.known(12)] == ["Regatta"]
    resort, _, station = harbour.hotels
    assert sources.shops.median(12, resort, 41) > 1.05 * sources.shops.median(11, resort, 41)
    assert sources.shops.median(25, station, 34) < 0.94 * sources.shops.median(24, station, 34)
    assert sources.bookings.on_books(26).shape == (3, 150)
    demo_sources = simulated_sources(simulate(7, last_day=12), 12)
    assert [e.name for e in demo_sources.events.known(9)] == []  # the convention is day 10's
    assert [e.name for e in demo_sources.events.known(12)] == ["Convention"]


def test_the_simulated_rate_shops_carry_the_reaction_the_simulator_used():
    from hotel_market.bookings import Books
    from hotel_market.shops import REACTION_SHARE, comp_median

    hotel = DEMO.hotel("convention")
    books = Books(7, react=True)
    for day in range(6):
        books.book(day)
    books.set_rates({("convention", 50): hotel.start_rate + 20.0})  # in force from day 6
    for day in range(6, 13):
        books.book(day)
    sources = simulated_sources(books)
    # Before the lag the shop is the seed's own; from day 9 it carries the reaction, and the
    # source answers exactly what the loop shopped and logged.
    assert sources.shops.median(8, hotel, 50) == comp_median(8, hotel, 50, seed=7)
    assert sources.shops.median(9, hotel, 50) == pytest.approx(
        comp_median(9, hotel, 50, seed=7) + REACTION_SHARE * 20.0
    )
    assert sources.shops.median(9, hotel, 50) == books.daily_medians[9, hotel.row, 50]
    shopped = sources.shops.competitor_rates(9, hotel, 50)
    assert statistics.median(shopped.values()) == pytest.approx(sources.shops.median(9, hotel, 50))
    assert sources.shops.median_history(10)[9, hotel.row, 50] == sources.shops.median(9, hotel, 50)


def test_the_first_median_is_the_comp_sets_base_rate_median_before_any_shock_or_noise():
    sources = simulated_sources(simulate(7, last_day=12))
    convention = DEMO.hotel("convention")
    first = sources.shops.first_median(convention)
    assert first == convention.starting_median() == convention.start_rate
    assert abs(sources.shops.median(0, convention, 46) / first - 1) <= 0.03  # the noise alone
    assert sources.shops.median(10, convention, 46) == pytest.approx(1.15 * first, rel=0.03)


def test_the_simulated_schedules_follow_the_runs_scenario():
    from hotel_market.schedule import UPGAUGE_SCENARIO
    from hotel_market.simulated import SimulatedSchedules

    sources = simulated_sources(simulate(7, last_day=16, scenario=UPGAUGE_SCENARIO))
    assert sources.schedules.seats(14)[52] == 4244 and sources.schedules.seats(15)[52] == 4514
    assert SimulatedSchedules().seats(20)[55] == 4964  # the default, as before


def test_the_simulated_sources_refuse_a_later_day_and_hand_out_copies():
    books = simulate(7, last_day=20)
    sources = simulated_sources(books, 20)
    hotel = DEMO.hotels[0]
    assert sources.bookings.on_books(20).shape == books.rooms.shape
    assert sources.bookings.history(21).taken.shape[0] == 21  # today's bookings are in
    assert sources.shops.median_history(21).shape[0] == 21
    for ask in (
        lambda: sources.bookings.on_books(21),
        lambda: sources.bookings.rates(21),
        lambda: sources.bookings.history(22),
        lambda: sources.shops.competitor_rates(21, hotel, 50),
        lambda: sources.shops.median(21, hotel, 50),
        lambda: sources.shops.median_history(22),
        lambda: sources.schedules.seats(21),
        lambda: sources.events.known(21),
    ):
        with pytest.raises(ValueError, match="day 2[12] on day 20"):
            ask()
    assert simulated_sources(books).events.known(59)  # made with no day, as a test may
    # The arrays are copies, so writing to them leaves the simulator's log alone.
    history = sources.bookings.history(20)
    history.taken[0, hotel.row, 0] = 999
    history.opening[hotel.row, 0] = 999
    assert books.daily_rooms[0, hotel.row, 0] != 999 and books.preload[hotel.row, 0] != 999
    rates = sources.bookings.rates(20)
    rates[hotel.row, 25] = 1.0
    assert books.daily_rates[20, hotel.row, 25] != 1.0
    medians = sources.shops.median_history(20)
    medians[0, hotel.row, 0] = 1.0
    assert books.daily_medians[0, hotel.row, 0] != 1.0
    # The simulator makes the day's sources for the day it is deciding.
    seen = []

    class Spy:
        def decide(self, day, sources):
            seen.append((day, sources.bookings.as_of_day, sources.events.as_of_day))
            return {}

    simulate(7, deciding(Spy()), last_day=2)
    assert seen == [(0, 0, 0), (1, 1, 1), (2, 2, 2)]


def test_a_decider_cannot_reach_a_future_draw_the_live_rooms_or_the_scenarios_shocks():
    """The sources a decider is handed hold copies of what the day knows and nothing else: no
    Books, no Scenario, no array that shares memory with the simulator's, no log past the day,
    and no filing or event still to come. Rule 3 therefore holds through an attribute as well as
    through a method."""
    import numpy as np

    from hotel_market.bookings import Books
    from hotel_market.schedule import Scenario

    seen = {}

    class Probe:
        def decide(self, day, sources):
            if day == 5:
                for name in ("bookings", "shops", "schedules", "events"):
                    seen[name] = dict(vars(getattr(sources, name)))
            return {}

    books = simulate(7, deciding(Probe()), last_day=5)
    values = [value for held in seen.values() for value in held.values()]
    assert values and not any(isinstance(value, (Books, Scenario)) for value in values)
    arrays = [value for value in values if isinstance(value, np.ndarray)]
    own = [
        books._daily_luck,
        books._preload_luck,
        books.rooms,
        books.revenue,
        books.rates,
        books.daily_rooms,
        books.daily_rates,
        books.daily_medians,
        books.preload,
    ]
    assert arrays and not any(np.shares_memory(held, live) for held in arrays for live in own)
    assert all(held.shape[0] == 6 for held in arrays if held.ndim == 3)  # the log through day 5
    assert seen["events"]["_events"] == []  # the convention is announced on day 10
    assert set(seen["schedules"]["_filed"]) == {-1}  # the first filing is on day 20


def test_a_source_made_for_a_tick_refuses_a_later_tick_of_its_day_on_both_routes(tmp_path):
    """A source made for (day, tick) answers that tick, the ticks before it and every earlier day,
    and refuses a later tick of its day as it refuses a later day. With no tick named, a
    question means the day's last tick, which the source made for an earlier tick also refuses.
    The same guard runs over the stored tables."""
    from hotel_market import stored

    books = simulate(7, last_day=20, ticks=4)
    hotel = DEMO.hotels[0]
    connection = stored.connect(tmp_path / "ticks.duckdb")
    try:
        for sources in (
            simulated_sources(books, 20, 2),
            stored.stored_sources(connection, DEMO, 20, 2, ticks=4),
        ):
            assert (sources.bookings.ticks, sources.events.ticks) == (4, 4)
            assert sources.bookings.on_books(20, 2).shape == (len(DEMO.hotels), 150)
            assert sources.bookings.on_books(20, 1).shape == (len(DEMO.hotels), 150)
            assert sources.bookings.on_books(19).shape == (len(DEMO.hotels), 150)
            assert sources.events.known(19) == sources.events.known(19, 4)
            for ask in (
                lambda: sources.bookings.on_books(20, 3),
                lambda: sources.bookings.on_books(20),  # no tick: the last, tick 4
                lambda: sources.bookings.rates(20, 4),
                lambda: sources.shops.competitor_rates(20, hotel, 50, 3),
                lambda: sources.shops.median(20, hotel, 50),
                lambda: sources.schedules.seats(20, 3),
                lambda: sources.schedules.passengers(20),
                lambda: sources.schedules.passenger_change(20, 3),
                lambda: sources.schedules.passenger_revision(20),
                lambda: sources.events.known(20, 3),
            ):
                with pytest.raises(ValueError, match="tick [34] of day 20 on tick 2"):
                    ask()
            with pytest.raises(ValueError, match="day 21 on day 20"):
                sources.events.known(21, 1)
            # The bookings before tomorrow are the whole of today, which tick 2 does not know.
            with pytest.raises(ValueError, match="tick 4 of day 20 on tick 2"):
                sources.bookings.history(21)
            with pytest.raises(ValueError, match="tick 4 of day 20 on tick 2"):
                sources.shops.median_history(21)
            sources.bookings.history(20)  # the days before today are known
            with pytest.raises(ValueError, match="tick 5 is not 1 to 4"):
                sources.events.known(19, 5)
    finally:
        connection.close()
    # With one tick a day, the default, every question means the whole day, as before.
    daily = simulated_sources(simulate(7, last_day=20), 20)
    assert daily.bookings.ticks == 1 and daily.bookings.as_of_tick is None
    assert (daily.bookings.on_books(20) == daily.bookings.on_books(20, 1)).all()
    with pytest.raises(ValueError, match="tick 2 is not 1 to 1"):
        daily.bookings.on_books(20, 2)


def test_each_feed_lands_at_its_tick_and_answers_the_previous_value_before_it():
    """With four ticks a day the rate shop lands at tick 2, the airlines' filing at tick 3 and the
    events at tick 4, the day's last, and the bookings at every tick. Before a feed lands, a
    question on a tick gets the previous value, the day before's. With one tick a day every feed
    lands at tick 1."""
    from hotel_market.world import FILING_TICK, SHOP_TICK, arrival_tick, news_tick

    assert (arrival_tick(SHOP_TICK, 4), arrival_tick(FILING_TICK, 4)) == (2, 3)
    assert (arrival_tick(SHOP_TICK, 2), arrival_tick(FILING_TICK, 2)) == (2, 1)
    assert {arrival_tick(slot, 1) for slot in (SHOP_TICK, FILING_TICK)} == {1}
    # An event lands at the day's last tick, and a cut shows in the day's first shop, unless the
    # file names a tick; a named tick beyond the day's last lands at tick 1, as a slot does.
    assert news_tick(None, 4, 4) == 4 and news_tick(None, 2, 2) == 2 and news_tick(None, 1, 1) == 1
    assert news_tick(None, 4, 1) == 1 and news_tick(2, 4, 4) == 2 and news_tick(4, 2, 2) == 1
    books = simulate(7, last_day=21, ticks=4)
    sources = simulated_sources(books)  # made with no day: any day, any tick
    hotel = DEMO.hotel("convention")
    # The shop: on day 10, tick 1 still shows day 9's shop, before the convention's raise.
    assert sources.shops.median(10, hotel, 46, 1) == sources.shops.median(9, hotel, 46)
    assert sources.shops.competitor_rates(10, hotel, 46, 1) == sources.shops.competitor_rates(
        9, hotel, 46, 4
    )
    assert sources.shops.median(10, hotel, 46, 2) == sources.shops.median(10, hotel, 46)
    assert sources.shops.median(10, hotel, 46, 2) > 1.1 * sources.shops.median(10, hotel, 46, 1)
    # The filing: on day 20, ticks 1 and 2 show the schedule as filed by day 19.
    assert sources.schedules.seats(20, 2)[55] == 4244 and sources.schedules.seats(20, 3)[55] == 4964
    assert sources.schedules.passengers(20, 2)[55] == sources.schedules.passengers(19)[55]
    assert sources.schedules.passenger_revision(20, 2)[55] == 0
    assert sources.schedules.passenger_revision(20, 3)[55] > 0  # against the previous tick
    assert sources.schedules.passenger_revision(20, 4)[55] == 0  # tick 3 already had it
    assert sources.schedules.passenger_revision(21, 1)[55] == 0
    # The events: the convention lands at tick 4 of day 10.
    assert sources.events.known(10, 3) == [] and sources.events.known(10) != []
    assert [e.name for e in sources.events.known(10, 4)] == ["Convention"]
    assert [e.name for e in sources.events.known(11, 1)] == ["Convention"]
    # The bookings: on the books grows tick by tick to the day's total, and the rates are the
    # tick's own.
    before = books.preload + books.daily_rooms[:20].sum(axis=0)
    for tick in range(1, 5):
        expected = before + books.tick_rooms[20, :tick].sum(axis=0)
        assert (sources.bookings.on_books(20, tick) == expected).all()
        assert (sources.bookings.rates(20, tick) == books.tick_rates[20, tick - 1]).all()
    assert (sources.bookings.on_books(20) == sources.bookings.on_books(20, 4)).all()
    assert (
        sources.bookings.on_books(20, 4) == books.preload + books.daily_rooms[:21].sum(axis=0)
    ).all()


def test_news_lands_at_the_ticks_the_customer_file_names(tmp_path):
    """A market that shops at every tick, announces its convention at tick 2, shows its day-30
    cut from tick 3 and lands the day-20 filing at tick 1: each feed answers the previous value
    before its tick and the new one from it. Each shop draws its own noise, the shop at the
    default slot is the demo market's own, and the simulator's day shops at the day's first. At
    one tick a day every piece of news lands at the day's one tick."""
    from hotel_market.customer import DEMO_FILE, load

    text = (Path(hotel_market.__file__).resolve().parents[2] / DEMO_FILE).read_text()
    path = tmp_path / "intraday.toml"
    path.write_text(
        text.replace("elasticity = 1.0\n", "elasticity = 1.0\nshop_ticks = [1, 2, 3, 4]\n")
        .replace("known_day = 10\n", "known_day = 10\nknown_tick = 2\n")
        .replace("known_day = 30\n", "known_day = 30\nknown_tick = 3\n")
        + "\n[[filings]]\nknown_day = 20\ntick = 1\n"
    )
    market = load(path)
    books = simulate(7, last_day=31, customer=market, ticks=4)
    sources = simulated_sources(books)
    convention, full = market.hotel("convention"), market.hotel("full-service")
    # The events: the convention lands at tick 2 of day 10.
    assert sources.events.known(10, 1) == [] and sources.events.known(9) == []
    assert [e.name for e in sources.events.known(10, 2)] == ["Convention"]
    assert [e.name for e in sources.events.known(10, 4)] == ["Convention"]
    # The cut: the shops at ticks 1 and 2 of day 30 do not show it, the shop at tick 3 does.
    cheapest = full.competitors[0]
    for tick in (1, 2):
        assert sources.shops.competitor_rates(30, full, 38, tick)[cheapest.name] > (
            0.9 * cheapest.base_rate
        )
    cut = 0.85 * cheapest.base_rate
    assert sources.shops.competitor_rates(30, full, 38, 3)[cheapest.name] < cut
    assert sources.shops.competitor_rates(31, full, 38, 1)[cheapest.name] < cut
    # The shops: a shop at every tick, each with its own noise, so four medians on day 10; the
    # shop at slot 2 is the demo market's day-10 shop, noise for noise.
    assert len({sources.shops.median(10, convention, 46, tick) for tick in (1, 2, 3, 4)}) == 4
    demo_sources = simulated_sources(simulate(7, last_day=10, ticks=4))
    assert sources.shops.competitor_rates(10, convention, 46, 2) == (
        demo_sources.shops.competitor_rates(10, convention, 46, 2)
    )
    assert sources.shops.competitor_rates(10, convention, 46, 1) != (
        demo_sources.shops.competitor_rates(10, convention, 46, 2)
    )
    # The simulator's day-30 draw shopped the day's first shop, before the cut showed.
    assert books.daily_medians[30, full.row, 38] == sources.shops.median(30, full, 38, 1)
    assert books.daily_medians[30, full.row, 38] > sources.shops.median(30, full, 38, 3)
    # The filing: tick 1 of day 20 already shows the new flights, and tick 2 adds nothing.
    assert sources.schedules.seats(20, 1)[55] == 4964 and sources.schedules.seats(19, 4)[55] == 4244
    assert sources.schedules.passenger_revision(20, 1)[55] > 0
    assert sources.schedules.passenger_revision(20, 2)[55] == 0
    # One tick a day: the day's one shop is the first slot's, and the day's news is all in.
    daily = simulated_sources(simulate(7, last_day=31, customer=market))
    assert [e.name for e in daily.events.known(10)] == ["Convention"]
    assert daily.shops.competitor_rates(30, full, 38)[cheapest.name] < cut
    assert daily.shops.competitor_rates(10, convention, 46) == (
        sources.shops.competitor_rates(10, convention, 46, 1)
    )
    assert daily.schedules.seats(20)[55] == 4964
