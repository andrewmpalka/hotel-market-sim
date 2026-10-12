"""schedule.py

Generates a synthetic air schedule for one made-up city.

The column names follow Cirium's published schedule data dictionary. The rest of the simulator
therefore reads data shaped like a real feed. Every row is synthetic: the carriers, flight
numbers and the destination airports do not exist. This repository contains no Cirium data and
has no affiliation with Cirium.

The rows hold three traps that give a wrong seat count if the code ignores them. The first is
codeshare rows that repeat another carrier's seats. The second is a bus link sold under a flight
number, service type U. The third is a second airport, QMS, that shares the city code QMC.
seats_by_day handles all three.

The table has one row per flight per operating date. A schedule also has an "as of" day. A hotel
knows about a flight only after the airline has filed it. build_schedule(as_of_day) returns the
schedule as it was known on that simulation day.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta

import pandas as pd

SIM_START = date(2027, 1, 4)  # simulation day 0, a Monday
HORIZON_DAYS = 150  # 60 simulated days plus a 90-day look-ahead

MARKET_STATION = "QMC"  # made-up airport
SECOND_STATION = "QMS"  # made-up second airport in the same city
MARKET_CITY = "QMC"  # made-up city code (a city code can cover several airports)
MARKET_COUNTRY = "US"
MARKET_STATE = "CO"

# equipment code -> (first, business, economy) seats
EQUIPMENT = {
    "738": (0, 16, 150),
    "321": (0, 20, 170),
    "320": (0, 12, 148),
    "E75": (0, 12, 64),
    "32N": (0, 0, 180),
    "BUS": (0, 0, 50),  # a coach sold under a flight number
}


@dataclass(frozen=True)
class Route:
    origin: str  # departure airport
    origin_city: str  # departure city code
    origin_state: str
    marketing: str  # carrier that sells the flight
    operating: str  # carrier that flies it
    flights: int  # arrivals per day
    equipment: str
    distance: int  # miles
    first_flight_number: int
    reduced_tue_sat: int = 0  # how many of the daily flights skip Tuesday and Saturday
    codeshare_partner: str | None = None
    destination: str = MARKET_STATION  # arrival airport
    service_type: str = "J"  # J is scheduled passenger service, U a bus or rail link
    # (first day, last day) ranges when the route operates, in simulation days
    periods: tuple[tuple[int, int], ...] = ((0, HORIZON_DAYS - 1),)


# One route per line reads as the table it is, so the formatter leaves this block alone.
# fmt: off
BASE_ROUTES = [
    Route("ORD", "CHI", "IL", "XA", "XA", 4, "738", 890, 100, reduced_tue_sat=1,
          codeshare_partner="XP"),
    Route("DEN", "DEN", "CO", "XA", "XA", 3, "738", 210, 200, reduced_tue_sat=1),
    Route("ATL", "ATL", "GA", "XB", "XB", 4, "321", 1200, 300, reduced_tue_sat=1,
          codeshare_partner="XP"),
    Route("DFW", "DFW", "TX", "XC", "XC", 3, "320", 640, 400, reduced_tue_sat=1),
    Route("LAX", "LAX", "CA", "XA", "XA", 2, "738", 860, 500),
    Route("SEA", "SEA", "WA", "XD", "XD", 2, "738", 1020, 600),
    Route("PHX", "PHX", "AZ", "XC", "XC", 2, "320", 600, 700),
    Route("MSP", "MSP", "MN", "XB", "XR", 3, "E75", 680, 3100, reduced_tue_sat=1),
    Route("SLC", "SLC", "UT", "XB", "XR", 2, "E75", 390, 3200, destination=SECOND_STATION),
    Route("SFO", "SFO", "CA", "XA", "XR", 2, "E75", 960, 3300),
    Route("LAS", "LAS", "NV", "XE", "XE", 1, "320", 610, 800, reduced_tue_sat=1),
    Route("EWR", "NYC", "NJ", "XA", "XA", 1, "738", 1600, 900),
    # Not a flight: a daily bus from Denver, sold under an XA flight number.
    Route("DEN", "DEN", "CO", "XA", "XA", 1, "BUS", 210, 290, service_type="U"),
]
# fmt: on


@dataclass(frozen=True)
class Shock:
    known_day: int  # the simulation day the airline files the change
    kind: str  # "add" or "suspend"
    start_day: int
    end_day: int
    routes: tuple[Route, ...] = field(default_factory=tuple)  # for "add"
    origin: str | None = None  # for "suspend"
    marketing: str | None = None


AIR_SHOCKS = [
    # Filed on day 20: four new daily flights, 720 seats in total, from day 50.
    Shock(
        known_day=20,
        kind="add",
        start_day=50,
        end_day=HORIZON_DAYS - 1,
        routes=(
            Route("MCO", "ORL", "FL", "XE", "XE", 2, "32N", 1550, 820),
            Route("BNA", "BNA", "TN", "XE", "XE", 2, "32N", 1010, 840),
        ),
    ),
    # Filed on day 40: the DFW route (480 seats a day) stops for days 70 to 90.
    Shock(known_day=40, kind="suspend", start_day=70, end_day=90, origin="DFW", marketing="XC"),
]


def _remove_window(periods, start, end):
    """Cut the days start..end out of a list of (first, last) periods."""
    out = []
    for first, last in periods:
        if end < first or start > last:
            out.append((first, last))
            continue
        if first < start:
            out.append((first, start - 1))
        if last > end:
            out.append((end + 1, last))
    return tuple(out)


def routes_as_of(as_of_day: int) -> list[Route]:
    """The route list as it was known on a simulation day."""
    routes = list(BASE_ROUTES)
    for shock in AIR_SHOCKS:
        if as_of_day < shock.known_day:
            continue
        if shock.kind == "add":
            for r in shock.routes:
                routes.append(replace(r, periods=((shock.start_day, shock.end_day),)))
        elif shock.kind == "suspend":
            routes = [
                replace(r, periods=_remove_window(r.periods, shock.start_day, shock.end_day))
                if (r.origin == shock.origin and r.marketing == shock.marketing)
                else r
                for r in routes
            ]
    return routes


def _operates(route: Route, flight_index: int, weekday: int) -> bool:
    """weekday: Monday is 0. The last `reduced_tue_sat` flights skip Tuesday and Saturday."""
    reduced = flight_index >= route.flights - route.reduced_tue_sat
    return not (reduced and weekday in (1, 5))


def build_schedule(as_of_day: int = HORIZON_DAYS) -> pd.DataFrame:
    """One row per flight per operating date, as known on `as_of_day`."""
    rows = []
    for route in routes_as_of(as_of_day):
        first, business, economy = EQUIPMENT[route.equipment]
        for i in range(route.flights):
            flight_number = route.first_flight_number + i
            # spread departures between 07:00 and 19:00
            dep_hour = 7 + (12 * i) // max(route.flights, 1)
            dow = [_operates(route, i, wd) for wd in range(7)]
            for first_day, last_day in route.periods:
                for day in range(first_day, last_day + 1):
                    d = SIM_START + timedelta(days=day)
                    if not dow[d.weekday()]:
                        continue
                    base = {
                        "OPERATING_DATE_LOCAL": d,
                        "FLIGHT_NUMBER": flight_number,
                        "MARKETING_CARRIER_IATA": route.marketing,
                        "OPERATING_CARRIER_IATA": route.operating,
                        "IS_CODESHARE": False,
                        "CODESHARE_INFO": (
                            f"{route.codeshare_partner} {7000 + flight_number}"
                            if route.codeshare_partner
                            else None
                        ),
                        "IS_WETLEASE": route.marketing != route.operating,
                        "SERVICE_TYPE_IATA": route.service_type,
                        "EFFECTIVE_DATE": SIM_START + timedelta(days=first_day),
                        "DISCONTINUE_DATE": SIM_START + timedelta(days=last_day),
                        "IS_OPERATING_MONDAY": dow[0],
                        "IS_OPERATING_TUESDAY": dow[1],
                        "IS_OPERATING_WEDNESDAY": dow[2],
                        "IS_OPERATING_THURSDAY": dow[3],
                        "IS_OPERATING_FRIDAY": dow[4],
                        "IS_OPERATING_SATURDAY": dow[5],
                        "IS_OPERATING_SUNDAY": dow[6],
                        "DEPARTURE_STATION_CODE_IATA": route.origin,
                        "DEPARTURE_COUNTRY_CODE_IATA": "US",
                        "DEPARTURE_STATE_PROVINCE_CODE_IATA": route.origin_state,
                        "DEPARTURE_CITY_CODE_IATA": route.origin_city,
                        "PASSENGER_DEPARTURE_TIME_LOCAL": datetime.combine(d, time(dep_hour, 15)),
                        "ARRIVAL_STATION_CODE_IATA": route.destination,
                        "ARRIVAL_COUNTRY_CODE_IATA": MARKET_COUNTRY,
                        "ARRIVAL_STATE_PROVINCE_CODE_IATA": MARKET_STATE,
                        "ARRIVAL_CITY_CODE_IATA": MARKET_CITY,
                        "EQUIPMENT_SUBTYPE_CODE_IATA": route.equipment,
                        "FIRST_CLASS_SEATS": first,
                        "BUSINESS_CLASS_SEATS": business,
                        "ECONOMY_CLASS_SEATS": economy,
                        "FLIGHT_DISTANCE": route.distance,
                    }
                    rows.append(base)
                    if route.codeshare_partner:
                        # The partner sells the same seats under its own flight number.
                        # These rows must be left out when seats are added up.
                        rows.append(
                            {
                                **base,
                                "FLIGHT_NUMBER": 7000 + flight_number,
                                "MARKETING_CARRIER_IATA": route.codeshare_partner,
                                "IS_CODESHARE": True,
                                "CODESHARE_INFO": f"{route.marketing} {flight_number}",
                                "IS_WETLEASE": False,
                            }
                        )
    df = pd.DataFrame(rows)
    df = df.sort_values(["OPERATING_DATE_LOCAL", "PASSENGER_DEPARTURE_TIME_LOCAL", "FLIGHT_NUMBER"])
    df.insert(0, "EXPANDED_ID", range(1, len(df) + 1))
    return df.reset_index(drop=True)


def seats_by_day(schedule: pd.DataFrame, city: str = MARKET_CITY) -> pd.Series:
    """Arriving seats per simulation day.

    Codeshare rows repeat seats that an operating row already counts, so they
    are dropped. Only scheduled passenger service is kept. Arrivals are
    grouped by city, so both of the city's airports count.
    """
    s = schedule[
        (schedule["ARRIVAL_CITY_CODE_IATA"] == city)
        & (~schedule["IS_CODESHARE"])
        & (schedule["SERVICE_TYPE_IATA"] == "J")
    ]
    seats = s["FIRST_CLASS_SEATS"] + s["BUSINESS_CLASS_SEATS"] + s["ECONOMY_CLASS_SEATS"]
    sim_day = s["OPERATING_DATE_LOCAL"].map(lambda d: (d - SIM_START).days)
    out = seats.groupby(sim_day).sum()
    return out.reindex(range(HORIZON_DAYS), fill_value=0).rename("seats")


def seat_change(as_of_day: int) -> pd.Series:
    """Fractional change in arriving seats against the schedule with no shocks.

    0.18 means seats are 18% above baseline for that day. This is the number
    the demand rule and the agent's flagging code both read.
    """
    baseline = seats_by_day(build_schedule(as_of_day=-1))
    known = seats_by_day(build_schedule(as_of_day=as_of_day))
    return ((known - baseline) / baseline).rename("seat_change")


def seat_revision(as_of_day: int) -> pd.Series:
    """Fractional change in arriving seats against the schedule known one day earlier.

    This catches a change on the day it is filed. The day-40 cut needs it. Seats on days 70 to 90
    stay above the original baseline even after the cut. The day-20 flights are still there.
    """
    before = seats_by_day(build_schedule(as_of_day=as_of_day - 1))
    after = seats_by_day(build_schedule(as_of_day=as_of_day))
    return ((after - before) / before).rename("seat_revision")


if __name__ == "__main__":
    full = build_schedule()
    full.to_csv("schedule.csv", index=False)
    base = seats_by_day(build_schedule(as_of_day=-1))
    print(f"rows written: {len(full)}")
    print("baseline seats, first week (Mon to Sun):", base.iloc[:7].tolist())
    for day in (19, 21, 41):
        change = seat_change(day)
        print(f"as of day {day}: day 55 {change.loc[55]:+.1%}, day 80 {change.loc[80]:+.1%}")
    print(f"revision filed on day 40, for day 80: {seat_revision(40).loc[80]:+.1%}")
