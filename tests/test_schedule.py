"""The schedule numbers under "Done when" in CLAUDE.md, and the traps in the rows."""

from datetime import timedelta

import numpy as np
import pytest

from hotel_market.customer import demo
from hotel_market.schedule import (
    AIR_SHOCKS,
    CHURN_BLOCK,
    DEFAULT_SCENARIO,
    HORIZON_DAYS,
    KINDS,
    LOAD_FACTOR,
    MARKET_CITY,
    MARKET_COUNTRY,
    MARKET_STATE,
    MARKET_STATION,
    RAMP_DAYS,
    RAMP_LOAD_FACTORS,
    SCENARIOS,
    SIM_START,
    UPGAUGE_SCENARIO,
    Scenario,
    Shock,
    build_schedule,
    churn,
    passenger_change,
    passenger_revision,
    passengers_by_day,
    seat_change,
    seat_revision,
    seats_by_day,
    with_churn,
)

TUESDAY, SATURDAY = 1, 5


@pytest.fixture(scope="module")
def rows():
    """Every row of the schedule with no shocks."""
    return build_schedule(as_of_day=-1)


@pytest.fixture(scope="module")
def baseline(rows):
    """Arriving seats per day in the schedule with no shocks."""
    return seats_by_day(rows)


def _sum_seats(rows):
    """Seats per simulation day for whichever rows are passed in, with no filtering."""
    seats = rows["FIRST_CLASS_SEATS"] + rows["BUSINESS_CLASS_SEATS"] + rows["ECONOMY_CLASS_SEATS"]
    day = rows["OPERATING_DATE_LOCAL"].map(lambda d: (d - SIM_START).days)
    return seats.groupby(day).sum().reindex(range(HORIZON_DAYS), fill_value=0)


def _days(reduced: bool) -> list[int]:
    """Every day in the horizon that is (or is not) a Tuesday or Saturday."""
    return [
        day
        for day in range(HORIZON_DAYS)
        if ((SIM_START + timedelta(days=day)).weekday() in (TUESDAY, SATURDAY)) == reduced
    ]


def test_normal_day_has_4244_seats(baseline):
    assert baseline[_days(reduced=False)].unique().tolist() == [4244]


def test_tuesdays_and_saturdays_have_3326_seats(baseline):
    assert baseline[_days(reduced=True)].unique().tolist() == [3326]


def test_seat_change_as_of_day_21_is_plus_17_percent_for_day_55():
    assert round(seat_change(21).loc[55], 2) == 0.17


def test_passengers_are_seats_at_the_load_factor_and_a_new_route_ramps():
    # A flight that flew before the run fills 80% of its seats, so a normal day's 4,244 seats
    # carry 3,395.2 passengers. The day-20 filing's 720 seats open at 60% on day 50, their first
    # operating day, and fill to 85% by day 140, linear between, so day 55 gains five days of
    # the ramp and day 140 the full 85%.
    assert (LOAD_FACTOR, RAMP_LOAD_FACTORS, RAMP_DAYS) == (0.80, (0.60, 0.85), 90)
    before, after = build_schedule(19), build_schedule(21)
    base = passengers_by_day(before)
    assert base[_days(reduced=False)].unique().tolist() == pytest.approx([4244 * 0.80])
    assert base[_days(reduced=True)].unique().tolist() == pytest.approx([3326 * 0.80])
    known = passengers_by_day(after)
    opening, full = RAMP_LOAD_FACTORS
    for day, since in [(50, 0), (55, 5), (140, 90), (149, 99)]:
        load = opening + (full - opening) * min(since, RAMP_DAYS) / RAMP_DAYS
        assert known[day] - base[day] == pytest.approx(720 * load)
    assert known[49] == base[49]
    assert passenger_change(21)[55] == pytest.approx((known[55] - base[55]) / base[55])
    assert (
        round(passenger_change(21).loc[55], 2) == 0.13 and round(seat_change(21).loc[55], 2) == 0.17
    )
    # A suspended route keeps its load factor when it resumes: the DFW flights carry 80% of
    # their 480 seats on day 69 and again on day 91, and nothing on days 70 to 90.
    dfw = build_schedule(41)
    dfw = dfw[dfw["DEPARTURE_STATION_CODE_IATA"] == "DFW"]
    carried = passengers_by_day(dfw)
    assert carried[69] == carried[91] == pytest.approx(480 * 0.80) and carried[80] == 0
    assert passenger_revision(40)[80] == pytest.approx(
        -480 * 0.80 / passengers_by_day(build_schedule(39))[80]
    )


def test_summing_by_arrival_station_misses_the_second_airport(rows, baseline):
    flights = rows[~rows["IS_CODESHARE"] & (rows["SERVICE_TYPE_IATA"] == "J")]
    by_station = _sum_seats(flights[flights["ARRIVAL_STATION_CODE_IATA"] == MARKET_STATION])
    assert (by_station < baseline).all()
    # 4,244 and 3,326 less the 152 daily SLC seats that land at QMS
    assert sorted(by_station.unique().tolist()) == [3174, 4092]


def test_summing_with_type_u_rows_counts_the_bus(rows, baseline):
    city = rows[~rows["IS_CODESHARE"] & (rows["ARRIVAL_CITY_CODE_IATA"] == MARKET_CITY)]
    with_bus = _sum_seats(city)
    assert (with_bus > baseline).all()
    # 4,244 and 3,326 plus the 50-seat daily bus
    assert sorted(with_bus.unique().tolist()) == [3376, 4294]


def test_every_row_arrives_in_the_market_country_and_state(rows):
    assert (rows["ARRIVAL_COUNTRY_CODE_IATA"] == MARKET_COUNTRY).all()
    assert (rows["ARRIVAL_STATE_PROVINCE_CODE_IATA"] == MARKET_STATE).all()


def test_a_regional_operating_carrier_is_not_a_wet_lease(rows):
    # XR flies the E75 routes for XB and XA under capacity purchase. The carrier pair shows
    # that, and the wet-lease flag stays off, because a wet lease is a separate arrangement.
    operating = rows[~rows["IS_CODESHARE"]]
    regional = operating[operating["MARKETING_CARRIER_IATA"] != operating["OPERATING_CARRIER_IATA"]]
    assert set(regional["OPERATING_CARRIER_IATA"]) == {"XR"}
    assert set(regional["MARKETING_CARRIER_IATA"]) == {"XA", "XB"}
    assert set(regional["EQUIPMENT_SUBTYPE_CODE_IATA"]) == {"E75"}
    assert not rows["IS_WETLEASE"].any()
    # On a codeshare row the pair differs too: the partner sells seats on the operator's flight.
    codeshare = rows[rows["IS_CODESHARE"]]
    assert set(codeshare["MARKETING_CARRIER_IATA"]) == {"XP"}
    assert set(codeshare["OPERATING_CARRIER_IATA"]) == {"XA", "XB"}


def _on(rows, station, day):
    """A station's rows on one simulation day."""
    days = rows["OPERATING_DATE_LOCAL"].map(lambda d: (d - SIM_START).days)
    operating = ~rows["IS_CODESHARE"]  # the codeshare rows repeat the operating rows
    return rows[operating & (days == day) & (rows["DEPARTURE_STATION_CODE_IATA"] == station)]


def test_an_equipment_change_moves_the_seats_and_not_the_flight_count():
    # The upgauge scenario: filed on day 15, XB flies MSP on 738s from day 45. Day 52 is a
    # Thursday with three MSP flights, and each gains 90 seats.
    before, after = build_schedule(14, UPGAUGE_SCENARIO), build_schedule(15, UPGAUGE_SCENARIO)
    assert len(_on(before, "MSP", 52)) == len(_on(after, "MSP", 52)) == 3
    assert set(_on(before, "MSP", 52)["EQUIPMENT_SUBTYPE_CODE_IATA"]) == {"E75"}
    assert set(_on(after, "MSP", 52)["EQUIPMENT_SUBTYPE_CODE_IATA"]) == {"738"}
    assert set(_on(after, "MSP", 52)["OPERATING_CARRIER_IATA"]) == {"XB"}
    assert set(_on(after, "MSP", 44)["EQUIPMENT_SUBTYPE_CODE_IATA"]) == {"E75"}  # before day 45
    assert seats_by_day(after)[52] == seats_by_day(before)[52] + 270
    assert seat_revision(15, UPGAUGE_SCENARIO)[52] == pytest.approx(270 / 4244)
    assert seat_revision(15, UPGAUGE_SCENARIO)[44] == 0


def test_a_frequency_change_sets_the_daily_flights():
    # Filed on day 35, ORD drops from four flights to two for days 60 to 110: 332 seats fewer
    # on a Monday. On a Tuesday the reduced flight is one of the two that remain.
    before, after = build_schedule(34, UPGAUGE_SCENARIO), build_schedule(35, UPGAUGE_SCENARIO)
    assert len(_on(before, "ORD", 70)) == 4 and len(_on(after, "ORD", 70)) == 2
    assert len(_on(after, "ORD", 59)) == 4  # before day 60
    assert len(_on(before, "ORD", 71)) == 3 and len(_on(after, "ORD", 71)) == 1
    assert seats_by_day(after)[70] == seats_by_day(before)[70] - 332
    assert seat_revision(35, UPGAUGE_SCENARIO)[70] == pytest.approx(-332 / seats_by_day(before)[70])


def test_a_time_change_moves_departures_and_no_seat():
    scenario = Scenario(
        "shifted", (Shock(5, "time", 10, 20, origin="LAX", marketing="XA", minutes=15),)
    )
    before, after = build_schedule(4, scenario), build_schedule(5, scenario)
    assert seats_by_day(before).equals(seats_by_day(after))
    for day in (9, 10, 20, 21):
        was = _on(before, "LAX", day)["PASSENGER_DEPARTURE_TIME_LOCAL"].to_numpy()
        now = _on(after, "LAX", day)["PASSENGER_DEPARTURE_TIME_LOCAL"].to_numpy()
        shift = np.timedelta64(15 if 10 <= day <= 20 else 0, "m")
        assert (now == was + shift).all()


def test_the_churn_files_weekly_revisions_below_the_threshold():
    filed = churn(7)
    assert len(filed) == 16 and churn(7) == filed and churn(8) != filed
    assert sorted({s.known_day for s in filed}) == [7, 14, 21, 28, 35, 42, 49, 56]
    assert {s.kind for s in filed} == {"equipment", "time"}
    # A swap lasts two to three weeks and starts one to six weeks out.
    assert CHURN_BLOCK == (14, 21)
    for swap in (s for s in filed if s.kind == "equipment"):
        assert 14 <= swap.end_day - swap.start_day + 1 <= 21
        assert 7 <= swap.start_day - swap.known_day <= 42
    churned = with_churn(DEFAULT_SCENARIO, 7)
    assert churned.name == "default+churn" and churned.shocks[:2] == tuple(AIR_SHOCKS)
    moved = 0
    for day in churned.filing_days(59):
        if day in (20, 40):
            continue
        revision = seat_revision(day, churned)
        assert revision.abs().max() < demo().seat_threshold
        # At most 24 seats a flight on four flights: 96 seats, 77 passengers, against about 170.
        seats = seats_by_day(build_schedule(day, churned)) - seats_by_day(
            build_schedule(day - 1, churned)
        )
        assert seats.abs().max() <= 96
        moved += int((revision != 0).any())
    assert moved > 0  # a detector that fires on any revision fires on the churn


def test_the_default_scenario_is_the_air_shocks_and_the_kinds_are_named():
    assert DEFAULT_SCENARIO.shocks == tuple(AIR_SHOCKS)
    assert SCENARIOS["default"] is DEFAULT_SCENARIO and SCENARIOS["upgauge"] is UPGAUGE_SCENARIO
    assert {s.kind for scenario in SCENARIOS.values() for s in scenario.shocks} <= set(KINDS)
    assert DEFAULT_SCENARIO.filing_days() == (20, 40)
    assert UPGAUGE_SCENARIO.filing_days() == (15, 35)
    bad = Scenario("bad", (Shock(0, "merge", 1, 2, origin="LAX", marketing="XA"),))
    with pytest.raises(ValueError, match="merge"):
        build_schedule(1, bad)
