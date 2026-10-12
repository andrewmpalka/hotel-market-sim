"""agent.py

The agent's daily loop. After each day's bookings it reads the detect numbers and builds an entry
for every flag. It queues the plans worth the minimum and asks the model, or the template, about
each hotel's queue. It returns the accepted rate changes. The simulator applies them from the
next day and then holds the changed stay dates for 7 days.

It also gives the one piece of advice it does not simulate. That is a two-night minimum stay on
an event's peak night when that night is ahead of pace. It gives it once per hotel and event.

The elasticity the agent prices with comes from one of three modes. In the default mode, true, it
is ORACLE_ELASTICITY, the simulator's own value. The agent is then never wrong about price
response. With fixed:X it is X for the whole run. With learn:X it starts from the prior X. The
agent then re-estimates it every day for every hotel from the bookings made before that day
(estimate.py).

Every entry records the elasticity it was estimated with, and the request carries it. The reason
can therefore cite it, and a change of mode changes the cache key. With --cautious, a learning
agent also respects the estimate's standard error. A change must then beat holding one standard
error either side (plan.py). With --level, a learning agent also feeds the fit's intercept back.
It scales its forecast, the pace baseline included, by the fitted demand level once the fit has
enough observations (estimate.level_factor), and every plan record carries the factor.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from hotel_market.customer import Customer, demo
from hotel_market.detect import AHEAD, detect_numbers, flags
from hotel_market.estimate import Estimate, estimate_elasticity, level_factor
from hotel_market.forecast import ORACLE_MARKET_ELASTICITY, peak_night
from hotel_market.model import MODEL, Client, ask, request_for
from hotel_market.plan import (
    HOLD,
    MODES,
    ORACLE_ELASTICITY,
    TRUE_PRICING,
    Entry,
    Pricing,
    entry_for,
)
from hotel_market.sources import Event, Sources
from hotel_market.world import Hotel

MIN_STAY = "two-night minimum stay"


@dataclass(frozen=True)
class ElasticityMode:
    """Where the agent's elasticity comes from: true, fixed:X or learn:X."""

    kind: str  # one of MODES
    value: float  # ORACLE_ELASTICITY for true, the value for fixed, the prior for learn
    cautious: bool = False  # learn only: the cautious rule in plan.py
    level: bool = False  # learn only: the forecast is scaled by the fitted demand level

    @classmethod
    def parse(cls, text: str) -> ElasticityMode:
        """ "true", "fixed:1.0" or "learn:2.0"."""
        if text == "true":
            return cls("true", ORACLE_ELASTICITY)
        kind, _, number = text.partition(":")
        if kind not in MODES or kind == "true" or not number:
            raise ValueError(f"{text!r} is not true, fixed:X or learn:X")
        try:
            value = float(number)
        except ValueError:
            raise ValueError(f"{number!r} is not a number") from None
        if value <= 0:
            raise ValueError(f"{text}: the elasticity must be above zero")
        return cls(kind, value)

    def __str__(self) -> str:
        text = self.kind if self.kind == "true" else f"{self.kind}:{self.value:g}"
        if self.cautious:
            text += " cautious"
        if self.level:
            text += " level"
        return text


TRUE_MODE = ElasticityMode("true", ORACLE_ELASTICITY)


@dataclass
class Advice:
    """A two-night minimum stay on an event's peak night. Advice only: not simulated."""

    day: int
    hotel: str  # hotel key
    stay_day: int
    event: str
    reason: str

    def to_json(self) -> dict:
        """The decisions.jsonl line for this advice."""
        return {
            "day": self.day,
            "hotel": self.hotel,
            "stays": [self.stay_day, self.stay_day],
            "causes": [AHEAD],
            "event": self.event,
            "action": MIN_STAY,
            "value_at_stake": None,
            "reason": self.reason,
            "simulated": False,
        }


class Agent:
    """The daily decision. decide(day, sources) runs after each of days 0 to 59. It returns the rate
    changes to apply from the next day. It reads the day through the four sources and never the
    simulator. simulated.deciding() wraps it for a run.

    `model` names the model the client asks. It is the client's own name when the client has one,
    else model.MODEL. It goes into the cache folder when it is not the default, and into every cache
    record. `market_elasticity` is the run's market price response, handed to the agent as the
    share elasticity is in the default mode. Every plan record carries it.
    """

    def __init__(
        self,
        seed: int,
        cache_dir: Path = Path("cache"),
        client: Client | None = None,
        replay: bool = False,
        elasticity: ElasticityMode = TRUE_MODE,
        customer: Customer | None = None,
        model: str | None = None,
        market_elasticity: float = ORACLE_MARKET_ELASTICITY,
    ):
        self.customer = customer or demo()
        self.model = model or getattr(client, "model", None) or MODEL
        self.market_elasticity = market_elasticity
        # Another mode, target or model gives other answers, so they live in their own folder.
        folder = f"seed{seed}" if elasticity == TRUE_MODE else f"seed{seed}-{elasticity}"
        if not self.customer.scores_contribution():
            folder += f"-{self.customer.target}"
        if self.model != MODEL:
            folder += f"-{self.model}"
        self.cache_dir = Path(cache_dir) / folder.replace(":", "-").replace(" ", "-")
        self.client = client
        self.replay = replay
        self.elasticity = elasticity
        self.estimates: dict[tuple[int, str], Estimate] = {}  # (day, hotel key) -> learn's estimate
        self.held: dict[
            tuple[str, int], int
        ] = {}  # (hotel key, stay day) -> day of its last rate change
        self.advised: set[tuple[str, str]] = set()  # (hotel key, event name) already given advice
        self.entries: list[Entry] = []  # every flag's entry, in order
        self.today: list[
            Entry
        ] = []  # the day's entries while they are decided; a client may read them
        self.advice: list[Advice] = []

    def decide(self, day: int, sources: Sources) -> dict[tuple[str, int], float]:
        """Decide the day's flags and return the rate changes to apply from tomorrow."""
        today = self.plans_for(day, sources)
        self.today = today
        for hotel in self.customer.hotels:
            self._decide(day, hotel, [entry for entry in today if entry.hotel == hotel.key])
        self.entries.extend(today)
        self.advice.extend(self.advice_for(day, today, sources))
        return self._rate_changes(day, today)

    def plans_for(self, day: int, sources: Sources) -> list[Entry]:
        """Every flag's entry for the day, with its plan, before anything is asked."""
        customer = self.customer
        pricing = {hotel.key: self._pricing(day, hotel, sources) for hotel in customer.hotels}
        levels = {key: p.level for key, p in pricing.items()}
        table = detect_numbers(day, sources, customer, self.market_elasticity, levels)
        return [
            entry_for(day, flag, table, pricing[flag.hotel], customer)
            for flag in flags(day, table, self.held, customer)
        ]

    def resume(
        self, held: Mapping[tuple[str, int], int], advised: Iterable[tuple[str, str]]
    ) -> None:
        """Pick up the state that earlier days left. That state is the stay dates under the hold, by
        the day of their last accepted change. It also holds the (hotel key, event) pairs already
        advised. A table-backed run gives each day's agent its state this way."""
        self.held = dict(held)
        self.advised = set(advised)

    @property
    def log(self) -> list[dict]:
        """Every entry and advice as a decisions.jsonl line, in order: by day, entries first."""
        return [record.to_json() for record in sorted(self.entries + self.advice, key=_log_order)]

    def _pricing(self, day: int, hotel: Hotel, sources: Sources) -> Pricing:
        """The elasticity the hotel's estimates assume today, by the agent's mode."""
        mode, market = self.elasticity, self.market_elasticity
        if mode.kind == "learn":
            estimate = estimate_elasticity(sources, hotel, day, mode.value, self.customer, market)
            self.estimates[(day, hotel.key)] = estimate
            return Pricing(
                estimate.elasticity,
                "learn",
                standard_error=estimate.standard_error,
                prior=estimate.prior,
                observations=estimate.observations,
                cautious=mode.cautious,
                market_elasticity=market,
                level=level_factor(estimate) if mode.level else 1.0,
            )
        if mode.kind == "fixed":
            return Pricing(mode.value, "fixed", market_elasticity=market)
        return replace(TRUE_PRICING, market_elasticity=market)

    def _decide(self, day: int, hotel: Hotel, entries: list[Entry]) -> None:
        """Ask about the hotel's queued entries, and give every entry its action and reason."""
        queued = [entry for entry in entries if entry.queued]
        if queued:
            path = self.cache_dir / f"day{day:03d}_{hotel.key}.json"
            request = request_for(day, hotel, queued)
            answer = ask(request, path, self.client, self.replay, model=self.model)
            decisions = {decision["id"]: decision for decision in answer["decisions"]}
            for entry in queued:
                entry.action = decisions[entry.id]["choice"]
                entry.reason = decisions[entry.id]["reason"]
                entry.reason_source = answer["source"]
        for entry in entries:
            if not entry.queued:
                entry.reason = _held_reason(entry)

    def _rate_changes(self, day: int, entries: list[Entry]) -> dict[tuple[str, int], float]:
        """The accepted plans' rates by (hotel key, stay day); those dates go under the hold."""
        changes = {}
        for entry in entries:
            if entry.action == HOLD:
                continue
            for stay_day, rate in entry.new_rates.items():
                changes[(entry.hotel, stay_day)] = rate
                self.held[(entry.hotel, stay_day)] = day
        return changes

    def advice_for(self, day: int, entries: list[Entry], sources: Sources) -> list[Advice]:
        """Advice for each event whose peak night is ahead of pace, once per hotel and event."""
        found = []
        for entry in entries:
            if AHEAD not in entry.causes:
                continue
            hotel = self.customer.hotel(entry.hotel)
            for event in sources.events.known(day):
                if hotel.key not in event.hotels or (hotel.key, event.name) in self.advised:
                    continue
                peak = peak_night(hotel, event, sources, self.market_elasticity)
                if entry.first_stay <= peak <= entry.last_stay:
                    self.advised.add((hotel.key, event.name))
                    found.append(
                        Advice(day, hotel.key, peak, event.name, _advice_reason(peak, event))
                    )
        return found


def _log_order(record: Entry | Advice) -> tuple[int, bool]:
    return record.day, isinstance(record, Advice)


def _held_reason(entry: Entry) -> str:
    if not entry.changed_weekdays:
        return "No change beats holding on any day of the week."
    return (
        f"The best plan, {entry.plan}, is worth ${entry.value_at_stake:,.0f}, under the "
        f"${entry.minimum:,} minimum, so the rates hold."
    )


def _advice_reason(peak: int, event: Event) -> str:
    return (
        f"Stay date {peak} is the {event.name.lower()}'s peak night and is ahead of pace. "
        f"A two-night minimum keeps one-night guests from filling it ahead of longer stays. "
        f"This is advice only: the simulator has no length of stay."
    )
