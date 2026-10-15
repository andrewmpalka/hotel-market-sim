"""schedule.py

Generates a synthetic air schedule for one made-up city.

The column names follow Cirium's published schedule data dictionary. The rest of the simulator
therefore reads data shaped like a real feed. Every row is synthetic: the carriers, flight
numbers and the destination airports do not exist. This repository contains no Cirium data and
has no affiliation with Cirium.

The rows hold three traps that give a wrong seat count if the code ignores them: codeshare rows that
repeat another carrier's seats, a bus link sold under a flight number with service type U, and a
second airport, QMS, that shares the city code QMC. seats_by_day handles all three. The seats
become arriving passengers at a load factor (passengers_by_day): a flight that flew before the
run fills LOAD_FACTOR of its seats, and a flight the airline adds opens emptier and fills over
RAMP_DAYS. The demand rule and the agent read the passengers.

The table has one row per flight per operating date. A schedule also has an "as of" day. A hotel
knows about a flight only after the airline has filed it. build_schedule(as_of_day) returns the
schedule as it was known on that simulation day.

A filing is a Shock of one of five kinds. An "add" files new routes and a "suspend" stops one for
a date range. An "equipment" change swaps a route's equipment code for a date range, so the seats
move while the flight count does not. A "frequency" change sets a route's daily flights for a
date range. A "time" change shifts a route's departure times and moves no seat. A Scenario is a
named list of shocks. AIR_SHOCKS is the default scenario, and SCENARIOS holds the others.

With --churn the airline also files weekly revisions drawn from the seed, below the detect
threshold: a departure-time change for a fortnight and an equipment swap of two to three weeks
(churn). A detector that fires on any revision fires on them; the threshold detector does not.

A row's marketing carrier sells the flight and its operating carrier flies it. Where the two
differ on an operating row, a regional airline flies the route for the marketing carrier under
a capacity-purchase agreement. XR does that for XB and XA on the E75 routes. On a codeshare row
the marketing carrier is the partner that sells seats on the operating carrier's flight. A wet
lease is a third arrangement, in which an airline rents another's aircraft and crew. No route
here is one, so IS_WETLEASE is False on every row. The columns modelled here carry no field for
the arrangement, so the carrier pair expresses it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd

SIM_START = date(2027, 1, 4)  # simulation day 0, a Monday
HORIZON_DAYS = 150  # 60 simulated days plus a 90-day look-ahead

MARKET_STATION = "QMC"  # made-up airport
SECOND_STATION = "QMS"  # made-up second airport in the same city
MARKET_CITY = "QMC"  # made-up city code (a city code can cover several airports)
MARKET_COUNTRY = "US"
MARKET_STATE = "CO"

# A flight that flew before the run fills this share of its seats, a mature route's usual load.
LOAD_FACTOR = 0.80
# A flight the airline adds opens with unsold seats and fills as the market learns of it: from the
# first load factor on its first operating day to the second after RAMP_DAYS, linear between. The
# second sits above a mature route's, because an airline adds a route where it expects demand.
RAMP_LOAD_FACTORS = (0.60, 0.85)
RAMP_DAYS = 90

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
    time_shift: int = 0  # minutes added to every departure, by a "time" revision


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


KINDS = ("add", "suspend", "equipment", "frequency", "time")  # what a filing can do


@dataclass(frozen=True)
class Shock:
    known_day: int  # the simulation day the airline files the change
    kind: str  # one of KINDS
    start_day: int
    end_day: int
    routes: tuple[Route, ...] = field(default_factory=tuple)  # for "add"
    origin: str | None = None  # the route the change applies to, with marketing
    marketing: str | None = None
    equipment: str | None = None  # for "equipment": the new code
    operating: str | None = None  # for "equipment": a new operating carrier, if the code brings one
    flights: int | None = None  # for "frequency": the new daily flights
    minutes: int = 0  # for "time": the departure shift, minutes either way


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


@dataclass(frozen=True)
class Scenario:
    """A named list of filings. The default is AIR_SHOCKS. A run's scenario may also carry the
    seeded churn (with_churn)."""

    name: str
    shocks: tuple[Shock, ...]

    def filing_days(self, last_day: int = HORIZON_DAYS - 1) -> tuple[int, ...]:
        """The days the airline files something, through last_day."""
        return tuple(sorted({s.known_day for s in self.shocks if s.known_day <= last_day}))


DEFAULT_SCENARIO = Scenario("default", tuple(AIR_SHOCKS))
UPGAUGE_SCENARIO = Scenario(
    "upgauge",
    (
        # Filed on day 15: XB takes the MSP route mainline on 738s for days 45 to 120. The
        # flight count stays at three, and the seats rise by 270 a day.
        Shock(
            known_day=15,
            kind="equipment",
            start_day=45,
            end_day=120,
            origin="MSP",
            marketing="XB",
            equipment="738",
            operating="XB",
        ),
        # Filed on day 35: the ORD route drops from four daily flights to two for days 60 to
        # 110, 332 seats a day fewer.
        Shock(
            known_day=35,
            kind="frequency",
            start_day=60,
            end_day=110,
            origin="ORD",
            marketing="XA",
            flights=2,
        ),
    ),
)
SCENARIOS = {DEFAULT_SCENARIO.name: DEFAULT_SCENARIO, UPGAUGE_SCENARIO.name: UPGAUGE_SCENARIO}

# The churn: weekly filings on days 7, 14, ... for CHURN_WEEKS weeks, on their own stream.
CHURN_STREAM = 3
CHURN_WEEKS = 8
CHURN_SHIFTS = (-30, -15, 15, 30)  # the departure-time changes, in minutes
CHURN_BLOCK = (14, 21)  # a swap lasts this many days: two to three weeks
# One-day equipment swaps between codes of nearly the same size: at most 30 seats on a day.
SWAPS = {"738": "321", "321": "738", "320": "32N", "32N": "320"}


def churn(seed: int) -> tuple[Shock, ...]:
    """The weekly revisions a seed files, each below the detect threshold. On each filing day the
    airline swaps one route's equipment for two to three weeks, starting one to six weeks out,
    and shifts another route's departures for a fortnight. A swap moves at most 24 seats a
    flight and 96 on a day, against a threshold of 212 on a day of 4,244."""
    rng = np.random.default_rng([seed, CHURN_STREAM])
    swappable = [r for r in BASE_ROUTES if r.equipment in SWAPS]
    found = []
    for week in range(1, CHURN_WEEKS + 1):
        filed = 7 * week
        route = swappable[int(rng.integers(len(swappable)))]
        start = filed + int(rng.integers(7, 43))
        length = int(rng.integers(CHURN_BLOCK[0], CHURN_BLOCK[1] + 1))
        found.append(
            Shock(
                filed,
                "equipment",
                start,
                start + length - 1,
                origin=route.origin,
                marketing=route.marketing,
                equipment=SWAPS[route.equipment],
            )
        )
        route = swappable[int(rng.integers(len(swappable)))]
        day = filed + int(rng.integers(7, 43))
        found.append(
            Shock(
                filed,
                "time",
                day,
                day + 13,
                origin=route.origin,
                marketing=route.marketing,
                minutes=int(rng.choice(CHURN_SHIFTS)),
            )
        )
    return tuple(found)


def with_churn(scenario: Scenario, seed: int) -> Scenario:
    """The scenario with the seed's churn filed on top of it."""
    return Scenario(f"{scenario.name}+churn", scenario.shocks + churn(seed))


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


def _inside_window(periods, start, end):
    """The parts of a list of (first, last) periods that fall on the days start..end."""
    return tuple(
        (max(first, start), min(last, end))
        for first, last in periods
        if not (end < first or start > last)
    )


def _revised(route: Route, shock: Shock) -> list[Route]:
    """The route after an equipment, frequency or time filing: the days inside the filing's range
    carry the revision, and the others stay as they were."""
    if route.origin != shock.origin or route.marketing != shock.marketing:
        return [route]
    inside = _inside_window(route.periods, shock.start_day, shock.end_day)
    outside = _remove_window(route.periods, shock.start_day, shock.end_day)
    if shock.kind == "equipment":
        revised = replace(
            route, equipment=shock.equipment, operating=shock.operating or route.operating
        )
    elif shock.kind == "frequency":
        revised = replace(
            route, flights=shock.flights, reduced_tue_sat=min(route.reduced_tue_sat, shock.flights)
        )
    elif shock.kind == "time":
        revised = replace(route, time_shift=route.time_shift + shock.minutes)
    else:
        raise ValueError(f"unknown filing kind {shock.kind!r}; the kinds are {KINDS}")
    found = [replace(route, periods=outside)] if outside else []
    if inside:
        found.append(replace(revised, periods=inside))
    return found


def routes_as_of(as_of_day: int, scenario: Scenario = DEFAULT_SCENARIO) -> list[Route]:
    """The route list as it was known on a simulation day, under a scenario."""
    routes = list(BASE_ROUTES)
    for shock in scenario.shocks:
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
        else:
            routes = [revised for r in routes for revised in _revised(r, shock)]
    return routes


def _operates(route: Route, flight_index: int, weekday: int) -> bool:
    """weekday: Monday is 0. The last `reduced_tue_sat` flights skip Tuesday and Saturday."""
    reduced = flight_index >= route.flights - route.reduced_tue_sat
    return not (reduced and weekday in (1, 5))


def build_schedule(
    as_of_day: int = HORIZON_DAYS, scenario: Scenario = DEFAULT_SCENARIO
) -> pd.DataFrame:
    """One row per flight per operating date, as known on `as_of_day` under a scenario."""
    rows = []
    for route in routes_as_of(as_of_day, scenario):
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
                        # A differing operating carrier is capacity purchase, never a wet lease.
                        "IS_WETLEASE": False,
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
                        "PASSENGER_DEPARTURE_TIME_LOCAL": datetime.combine(d, time(dep_hour, 15))
                        + timedelta(minutes=route.time_shift),
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


def _arrivals(schedule: pd.DataFrame, city: str) -> pd.DataFrame:
    """The rows that carry seats into the city: codeshare rows repeat seats that an operating row
    already counts, so they are dropped. Only scheduled passenger service is kept. Arrivals are
    grouped by city, so both of the city's airports count."""
    return schedule[
        (schedule["ARRIVAL_CITY_CODE_IATA"] == city)
        & (~schedule["IS_CODESHARE"])
        & (schedule["SERVICE_TYPE_IATA"] == "J")
    ]


def _seats(rows: pd.DataFrame) -> pd.Series:
    return rows["FIRST_CLASS_SEATS"] + rows["BUSINESS_CLASS_SEATS"] + rows["ECONOMY_CLASS_SEATS"]


def _by_day(rows: pd.DataFrame, values: pd.Series, name: str, fill) -> pd.Series:
    sim_day = rows["OPERATING_DATE_LOCAL"].map(lambda d: (d - SIM_START).days)
    out = values.groupby(sim_day).sum()
    return out.reindex(range(HORIZON_DAYS), fill_value=fill).rename(name)


def seats_by_day(schedule: pd.DataFrame, city: str = MARKET_CITY) -> pd.Series:
    """Arriving seats per simulation day, from the rows _arrivals keeps."""
    rows = _arrivals(schedule, city)
    return _by_day(rows, _seats(rows), "seats", 0)


def passengers_by_day(schedule: pd.DataFrame, city: str = MARKET_CITY) -> pd.Series:
    """Arriving passengers per simulation day: each flight's seats at its load factor. A flight
    whose first effective date is day 0 flew before the run and fills LOAD_FACTOR of its seats. A
    flight the airline added opens at the first ramp load factor on its first operating day and
    reaches the second RAMP_DAYS later, linear between, so a filing's passengers arrive more
    slowly than its seats. A suspended flight keeps its load factor when it resumes, because its
    first effective date is the one that counts."""
    rows = _arrivals(schedule, city)
    flight = (
        rows["MARKETING_CARRIER_IATA"]
        + " "
        + rows["FLIGHT_NUMBER"].astype(str)
        + " "
        + rows["DEPARTURE_STATION_CODE_IATA"]
    )
    opened = pd.to_datetime(rows.groupby(flight)["EFFECTIVE_DATE"].transform("min"))
    since = (pd.to_datetime(rows["OPERATING_DATE_LOCAL"]) - opened).dt.days.to_numpy()
    first, full = RAMP_LOAD_FACTORS
    ramp = first + (full - first) * np.minimum(since, RAMP_DAYS) / RAMP_DAYS
    load = np.where(opened > pd.Timestamp(SIM_START), ramp, LOAD_FACTOR)
    return _by_day(rows, _seats(rows) * load, "passengers", 0.0)


def seat_change(as_of_day: int, scenario: Scenario = DEFAULT_SCENARIO) -> pd.Series:
    """Fractional change in arriving seats against the schedule with no shocks. 0.18 means seats
    are 18% above baseline for that day."""
    baseline = seats_by_day(build_schedule(as_of_day=-1, scenario=scenario))
    known = seats_by_day(build_schedule(as_of_day=as_of_day, scenario=scenario))
    return ((known - baseline) / baseline).rename("seat_change")


def seat_revision(as_of_day: int, scenario: Scenario = DEFAULT_SCENARIO) -> pd.Series:
    """Fractional change in arriving seats against the schedule known one day earlier."""
    before = seats_by_day(build_schedule(as_of_day=as_of_day - 1, scenario=scenario))
    after = seats_by_day(build_schedule(as_of_day=as_of_day, scenario=scenario))
    return ((after - before) / before).rename("seat_revision")


def passenger_change(as_of_day: int, scenario: Scenario = DEFAULT_SCENARIO) -> pd.Series:
    """Fractional change in arriving passengers against the schedule with no shocks. This is the
    number the demand rule and the agent's forecast both read."""
    baseline = passengers_by_day(build_schedule(as_of_day=-1, scenario=scenario))
    known = passengers_by_day(build_schedule(as_of_day=as_of_day, scenario=scenario))
    return ((known - baseline) / baseline).rename("passenger_change")


def passenger_revision(as_of_day: int, scenario: Scenario = DEFAULT_SCENARIO) -> pd.Series:
    """Fractional change in arriving passengers against the schedule known one day earlier.

    This catches a change on the day it is filed. The day-40 cut needs it: passengers on days 70
    to 90 stay above the original baseline even after the cut, because the day-20 flights are
    still there.
    """
    before = passengers_by_day(build_schedule(as_of_day=as_of_day - 1, scenario=scenario))
    after = passengers_by_day(build_schedule(as_of_day=as_of_day, scenario=scenario))
    return ((after - before) / before).rename("passenger_revision")


if __name__ == "__main__":
    full = build_schedule()
    full.to_csv("schedule.csv", index=False)
    base = seats_by_day(build_schedule(as_of_day=-1))
    print(f"rows written: {len(full)}")
    print("baseline seats, first week (Mon to Sun):", base.iloc[:7].tolist())
    for day in (19, 21, 41):
        change = passenger_change(day)
        print(f"as of day {day}: day 55 {change.loc[55]:+.1%}, day 80 {change.loc[80]:+.1%}")
    print(f"revision filed on day 40, for day 80: {seat_revision(40).loc[80]:+.1%}")
