"""plan.py

What the agent could do about a flag, and what each option is worth.

Every flag is a hotel and a run of stay dates. Each gets the same candidates: hold, raise 5%,
raise 10% and lower 5%. When the comp median dropped, "lower halfway to the new median" joins
them. Each candidate's rates are clamped to the hotel's floor and ceiling. Code estimates the
contribution each candidate would earn on the rooms still unsold:

    demand                 = remaining expected demand
                             x (rate / comp median) ** -AGENT_ELASTICITY
    estimated bookings     = E[min(N, unsold rooms)], N Poisson with that mean
    estimated contribution = estimated bookings x (rate - cost per occupied room)

The bookings still to come arrive at random, as the simulator draws them, and stop when the hotel
is full. A night expected to come close to full therefore still sells out fairly often. The
estimate counts that.

Within a flag, the best candidate is chosen for each day of the week on its own. A plan can
therefore raise Mondays and hold Tuesdays. Value at stake is what the plan earns over holding,
summed over the days of the week it changes. A plan worth less than the customer's minimum value
at stake is held and not queued. The demo market's minimum is $250. The customer also sets the
target: with "revenue" the estimate counts the rate alone, without the room cost.

The elasticity in the estimate is the agent's, not the simulator's. In the default mode it is
ORACLE_ELASTICITY, the simulator's own value handed to the agent as an oracle. The agent can also
be given a fixed value, or learn one from the bookings it has seen (estimate.py). Each entry
records the Pricing it was estimated with.

A learned elasticity comes with a standard error, and the cautious rule makes the agent respect
it. Every candidate is also scored at the estimate one standard error lower and one higher. That
is the band, clamped to the estimator's bounds. A candidate replaces hold only if it beats hold
at the estimate and at both ends of the band. The minimum value at stake applies to the whole
plan, as in every mode. Without the rule, the highest estimate wins as before.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from hotel_market.customer import Customer, demo
from hotel_market.detect import MEDIAN_DOWN, Flag
from hotel_market.estimate import ELASTICITY_MAX, ELASTICITY_MIN
from hotel_market.world import Hotel, weekday

# The elasticity the default mode prices with. It is the simulator's own value, handed to
# the agent as an oracle: a real hotel has no oracle, which is what the other modes test.
ORACLE_ELASTICITY = 1.5
MODES = ("true", "fixed", "learn")  # where the agent's elasticity comes from
BAND_STANDARD_ERRORS = (
    1  # the cautious rule scores each candidate this far either side of the estimate
)

HOLD = "hold"
HALFWAY = "lower halfway to the new median"
CANDIDATES = ((HOLD, 1.00), ("raise 5%", 1.05), ("raise 10%", 1.10), ("lower 5%", 0.95))
PLAN_ORDER = tuple(name for name, _ in CANDIDATES[1:]) + (HALFWAY,)  # how a plan names its actions
DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@dataclass(frozen=True)
class Pricing:
    """The elasticity the agent prices with on a day, and where it came from."""

    elasticity: float
    mode: str  # one of MODES
    standard_error: float | None = None  # learn only: from the fit, prior included
    prior: float | None = None  # learn only: where the estimate started
    observations: int | None = None  # learn only: the (stay date, booking day) pairs used
    cautious: bool = False  # learn only: a change must also beat hold across the band

    @property
    def band(self) -> tuple[float, float] | None:
        """The elasticities BAND_STANDARD_ERRORS either side of the estimate, clamped to
        the estimator's bounds. None unless the cautious rule is on."""
        if not self.cautious:
            return None
        spread = BAND_STANDARD_ERRORS * self.standard_error
        low = max(self.elasticity - spread, ELASTICITY_MIN)
        high = min(self.elasticity + spread, ELASTICITY_MAX)
        return (low, high)

    def to_json(self) -> dict:
        """The elasticity field of a request and a log line. The cautious fields appear
        only when the rule is on, so a record without it reads as before."""
        record = asdict(self)
        if self.cautious:
            record["band"] = Range(*self.band).to_json()
        else:
            del record["cautious"]
        return record


TRUE_PRICING = Pricing(ORACLE_ELASTICITY, "true")


@dataclass(frozen=True)
class StayDate:
    """What the estimate needs to know about one stay date of a flag."""

    stay_day: int
    rate: float  # the hotel's current rate
    comp_median: float
    unsold: int  # rooms still unsold
    remaining_demand: float  # expected demand still to come, before the rate's effect on it


@dataclass
class Candidate:
    """One rate action for the stay dates of a weekday group, and what it is worth."""

    name: str
    rates: dict[int, float]  # rate by stay day, clamped to the floor and ceiling
    estimate: float  # estimated contribution on the rooms still unsold
    band: tuple[float, float] | None = None  # cautious only: the estimate at the band's ends


@dataclass
class WeekdayGroup:
    """The stay dates of one day of the week within a flag, with their candidates."""

    weekday: int  # Monday is 0
    candidates: list[Candidate]  # hold first
    cautious: bool = False  # whether the cautious rule picks the best candidate
    stay_dates: list[StayDate] = field(default_factory=list)  # what the estimates were made from

    @property
    def stays(self) -> list[int]:
        return sorted(self.hold.rates)

    @property
    def hold(self) -> Candidate:
        return self.candidates[0]

    @property
    def best(self) -> Candidate:
        """The candidate with the highest estimate, hold winning a tie. Under the
        cautious rule, the highest of those that replace hold, else hold."""
        if self.cautious:
            eligible = [c for c in self.candidates[1:] if self.replaces_hold(c)]
            if not eligible:
                return self.hold
            return max(eligible, key=lambda candidate: candidate.estimate)
        # max() keeps the first of equal estimates, so hold wins a tie.
        return max(self.candidates, key=lambda candidate: candidate.estimate)

    @property
    def gain(self) -> float:
        """What the best candidate earns over holding."""
        return self.best.estimate - self.hold.estimate

    def gains(self, candidate: Candidate) -> tuple[float, float, float]:
        """What a candidate earns over holding at the band's low elasticity, at the
        estimate, and at the band's high elasticity."""
        return (
            candidate.band[0] - self.hold.band[0],
            candidate.estimate - self.hold.estimate,
            candidate.band[1] - self.hold.band[1],
        )

    def replaces_hold(self, candidate: Candidate) -> bool:
        """The cautious rule: ahead of hold at the estimate and at both ends of the band.
        The minimum value at stake applies to the whole plan, as in every mode."""
        low, mid, high = self.gains(candidate)
        return mid > 0 and low > 0 and high > 0

    @property
    def rejected_at_an_end(self) -> list[Candidate]:
        """Cautious only. The candidates ahead of hold at the estimate that the band rejected. They
        fell behind hold at one end of it.
        """
        if not self.cautious:
            return []
        return [
            c for c in self.candidates[1:] if self.gains(c)[1] > 0 and not self.replaces_hold(c)
        ]


@dataclass(frozen=True)
class Range:
    """The lowest and highest of a number over a flag's stay dates. Iterating one gives the two
    ends, so the wording helpers in text.py take it as they take a pair. In JSON it is a named
    pair, {"lowest": x, "highest": y}."""

    lowest: float
    highest: float

    def __iter__(self) -> Iterator[float]:
        yield self.lowest
        yield self.highest

    def to_json(self) -> dict:
        return {"lowest": self.lowest, "highest": self.highest}


@dataclass(frozen=True)
class FlagNumbers:
    """The detect numbers over a flag's stay dates: totals where they add up, a
    Range where they do not. Rounded, for the model and the log."""

    days_out: Range
    rooms_on_books: int
    unsold_rooms: int
    remaining_demand: float
    pace_gap: float
    seat_change: Range
    seat_revision: Range
    rate: Range
    comp_median: Range
    rate_vs_median: Range
    median_change: Range
    new_event: str | None

    def to_json(self) -> dict:
        return asdict(self)  # a Range becomes its named pair


@dataclass
class Entry:
    """One flag's entry in the day's queue. It holds the best candidate for each day of the week,
    and those together make the plan. It also holds what became of it.
    """

    day: int
    hotel: str  # hotel key
    first_stay: int
    last_stay: int
    causes: tuple[str, ...]
    numbers: FlagNumbers
    weekdays: list[WeekdayGroup]
    action: str = HOLD  # HOLD, or the plan once it is accepted
    reason: str = ""
    reason_source: str = "code"  # "code" when held by rule, else "template" or "model"
    pricing: Pricing = TRUE_PRICING  # the elasticity the estimates assume
    minimum: float = 0.0  # the customer's minimum value at stake for the queue
    target: str = "contribution"  # what the estimates count: contribution or revenue

    @property
    def id(self) -> str:
        return f"{self.first_stay}-{self.last_stay}"

    @property
    def changed_weekdays(self) -> list[WeekdayGroup]:
        """The days of the week whose best candidate is not hold."""
        return [group for group in self.weekdays if group.best.name != HOLD]

    @property
    def plan(self) -> str:
        """The changes in words, such as "raise 5% on Mon, Thu; raise 10% on Sun".
        Empty when nothing beats holding."""
        parts = []
        for action in PLAN_ORDER:
            days = [DAY_NAMES[g.weekday] for g in self.changed_weekdays if g.best.name == action]
            if days:
                parts.append(f"{action} on {', '.join(days)}")
        return "; ".join(parts)

    @property
    def value_at_stake(self) -> float:
        """What the plan earns over holding, summed over the days of the week it changes."""
        return sum(group.gain for group in self.changed_weekdays)

    @property
    def queued(self) -> bool:
        return self.value_at_stake >= self.minimum

    @property
    def new_rates(self) -> dict[int, float]:
        """The plan's rates, for the stay dates it changes."""
        return {s: rate for g in self.changed_weekdays for s, rate in g.best.rates.items()}

    @property
    def current_rates(self) -> dict[int, float]:
        return {s: rate for g in self.weekdays for s, rate in g.hold.rates.items()}

    @property
    def rejected_at_an_end(self) -> int:
        """Cautious only: how many candidates the band rejected, over the days of the week."""
        return sum(len(group.rejected_at_an_end) for group in self.weekdays)

    def to_json(self) -> dict:
        """The decisions.jsonl line for this entry."""
        line = {
            "day": self.day,
            "hotel": self.hotel,
            "stays": [self.first_stay, self.last_stay],
            "causes": list(self.causes),
            "numbers": self.numbers.to_json(),
            "elasticity": self.pricing.to_json(),
            "by_weekday": [_weekday_json(group) for group in self.weekdays],
            "plan": self.plan or None,
            "value_at_stake": round(self.value_at_stake, 2),
            "queued": self.queued,
            "action": self.action,
            "new_rates": None if self.action == HOLD else _rates_json(self.new_rates),
            "reason": self.reason,
            "reason_source": self.reason_source,
            "simulated": True,
        }
        if self.pricing.cautious:
            line["rejected_at_an_end"] = self.rejected_at_an_end
        if self.target != "contribution":
            line["target"] = self.target
        return line


def _weekday_json(group: WeekdayGroup) -> dict:
    return {
        "weekday": DAY_NAMES[group.weekday],
        "stays": group.stays,
        "candidates": [_candidate_json(candidate) for candidate in group.candidates],
        "best": group.best.name,
        "gain": round(group.gain, 2),
    }


def _candidate_json(candidate: Candidate) -> dict:
    record = {
        "name": candidate.name,
        "rates": lowest_highest(candidate.rates.values()).to_json(),
        "estimate": round(candidate.estimate, 2),
    }
    if candidate.band is not None:
        record["band"] = band_json(candidate.band)
    return record


def band_json(band: tuple[float, float]) -> dict:
    """A candidate's estimates at the two ends of the elasticity band, as a named pair.
    Not a lowest-highest range: the low elasticity can give the higher estimate."""
    low, high = band
    return {"at_low_elasticity": round(low, 2), "at_high_elasticity": round(high, 2)}


def _rates_json(rates: dict[int, float]) -> dict[str, float]:
    return {str(stay_day): round(rate, 2) for stay_day, rate in rates.items()}


def lowest_highest(values: Iterable[float], digits: int = 2) -> Range:
    """The lowest and highest of some numbers, rounded."""
    values = [float(value) for value in values]
    return Range(round(min(values), digits), round(max(values), digits))


def expected_bookings(mean: float, unsold: int) -> float:
    """E[min(N, unsold)] for N Poisson with the given mean. It is the rooms a stay date can expect
    to sell. Its bookings arrive at random and stop at a full hotel.
    """
    if mean <= 0 or unsold <= 0:
        return 0.0
    counts = np.arange(unsold)  # 0, 1, ..., unsold - 1: every count that leaves rooms unsold
    log_factorial = np.concatenate(([0.0], np.cumsum(np.log(counts[1:]))))
    probability = np.exp(counts * math.log(mean) - mean - log_factorial)  # P(N = count)
    sold_below_full = counts @ probability
    chance_of_full = 1 - probability.sum()
    return float(sold_below_full + unsold * chance_of_full)


def entry_for(
    day: int,
    flag: Flag,
    table: pd.DataFrame,
    pricing: Pricing = TRUE_PRICING,
    customer: Customer | None = None,
) -> Entry:
    """A flag's entry: its candidates for each day of the week, each with its estimate."""
    customer = customer or demo()
    hotel = customer.hotel(flag.hotel)
    cost = hotel.room_cost if customer.scores_contribution() else 0.0
    rows = _flag_rows(flag, table)
    stay_dates = _stay_dates(day, hotel, rows, customer)
    weekdays = []
    for wd in sorted({weekday(s.stay_day) for s in stay_dates}):
        in_group = [s for s in stay_dates if weekday(s.stay_day) == wd]
        candidates = _candidates(hotel, in_group, flag.causes, pricing, cost)
        group = WeekdayGroup(wd, candidates, cautious=pricing.cautious, stay_dates=in_group)
        weekdays.append(group)
    numbers = _flag_numbers(rows, stay_dates)
    return Entry(
        day,
        flag.hotel,
        flag.first_stay,
        flag.last_stay,
        flag.causes,
        numbers,
        weekdays,
        pricing=pricing,
        minimum=customer.min_value_at_stake,
        target=customer.target,
    )


def _flag_rows(flag: Flag, table: pd.DataFrame) -> pd.DataFrame:
    """The detect numbers for the flag's hotel and stay dates, in stay-date order."""
    hotel_rows = table[table["hotel"] == flag.hotel]
    return hotel_rows[hotel_rows["stay_day"].between(flag.first_stay, flag.last_stay)]


def _stay_dates(day: int, hotel: Hotel, rows: pd.DataFrame, customer: Customer) -> list[StayDate]:
    stay_dates = []
    for row in rows.itertuples():
        stay_day = int(row.stay_day)
        still_to_come = 1 - float(customer.curve(stay_day - day))
        stay_dates.append(
            StayDate(
                stay_day=stay_day,
                rate=float(row.rate),
                comp_median=float(row.comp_median),
                unsold=hotel.rooms - int(row.rooms),
                remaining_demand=float(row.expected_demand) * still_to_come,
            )
        )
    return stay_dates


def _candidates(
    hotel: Hotel, stay_dates: list[StayDate], causes: tuple[str, ...], pricing: Pricing, cost: float
) -> list[Candidate]:
    """Hold, the three fixed moves, and lower halfway when the comp median dropped. Each is
    estimated at the pricing's elasticity and, under the cautious rule, at both ends of its band.
    The cost is the room cost when the target is contribution, 0 for revenue."""
    options = [
        (name, {s.stay_day: hotel.clamp(factor * s.rate) for s in stay_dates})
        for name, factor in CANDIDATES
    ]
    if MEDIAN_DOWN in causes:
        halfway = {
            s.stay_day: hotel.clamp(min(s.rate, (s.rate + s.comp_median) / 2)) for s in stay_dates
        }
        options.append((HALFWAY, halfway))
    band = pricing.band
    return [
        Candidate(
            name,
            rates,
            _estimate(stay_dates, rates, pricing.elasticity, cost),
            None if band is None else tuple(_estimate(stay_dates, rates, e, cost) for e in band),
        )
        for name, rates in options
    ]


def rescored(group: WeekdayGroup, candidate: Candidate, elasticity: float, cost: float) -> float:
    """A candidate's estimate made again at another elasticity, from the stay dates the group was
    built from. The cost is the room cost for contribution, 0 for revenue. A grader outside the
    agent's path uses this to score a plan at the simulator's elasticity."""
    return _estimate(group.stay_dates, candidate.rates, elasticity, cost)


def _estimate(
    stay_dates: list[StayDate], rates: dict[int, float], elasticity: float, cost: float
) -> float:
    """Estimated contribution (or revenue, when cost is 0) on the rooms still unsold,
    summed over the stay dates."""
    total = 0.0
    for s in stay_dates:
        rate = rates[s.stay_day]
        demand = s.remaining_demand * (rate / s.comp_median) ** -elasticity
        total += expected_bookings(demand, s.unsold) * (rate - cost)
    return total


def _flag_numbers(rows: pd.DataFrame, stay_dates: list[StayDate]) -> FlagNumbers:
    announced = [name for name in rows["new_event"].tolist() if name]
    return FlagNumbers(
        days_out=Range(int(rows["days_out"].min()), int(rows["days_out"].max())),
        rooms_on_books=int(rows["rooms"].sum()),
        unsold_rooms=sum(s.unsold for s in stay_dates),
        remaining_demand=round(sum(s.remaining_demand for s in stay_dates), 1),
        pace_gap=round(float(sum(rows["pace_gap"].tolist())), 1),
        seat_change=lowest_highest(rows["seat_change"].tolist(), digits=4),
        seat_revision=lowest_highest(rows["seat_revision"].tolist(), digits=4),
        rate=lowest_highest(rows["rate"].tolist()),
        comp_median=lowest_highest(rows["comp_median"].tolist()),
        rate_vs_median=lowest_highest(rows["rate_vs_median"].tolist(), digits=4),
        median_change=lowest_highest(rows["median_change"].tolist(), digits=4),
        new_event=announced[0] if announced else None,
    )
