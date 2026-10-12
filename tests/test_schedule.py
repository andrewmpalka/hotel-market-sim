"""The schedule numbers under "Done when" in CLAUDE.md, and the traps in the rows."""

from datetime import timedelta

import pytest

from hotel_market.schedule import (
    HORIZON_DAYS,
    MARKET_CITY,
    MARKET_COUNTRY,
    MARKET_STATE,
    MARKET_STATION,
    SIM_START,
    build_schedule,
    seat_change,
    seats_by_day,
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
