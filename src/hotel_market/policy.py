"""policy.py

Rule-based controls: pricers with no estimates and no model, for the comparison the fixed-rate
run cannot give. A fixed-rate run never moves a rate, so any gain against it includes what a
hotel's own rules would have earned anyway. A rule that acts on the same flags is the fairer
yardstick.

Each policy maps the flag causes it acts on to a direction. PacePolicy raises every stay date
that runs ahead of pace by the detect threshold and lowers every one that runs behind. RulesPolicy
keeps those steps and adds the rules the agent's first design retired: raise on an event flag's
dates and on a seat-up flag's dates, and lower on a seat-cut flag's dates. NeverCutPolicy keeps
the rules policy's raises and never lowers, because in this market the start rate is already the
best rate on a night that will not sell out, so every cut the rules policy makes loses money.
Every step is POLICY_STEP, clamped to the hotel's floor and ceiling. A flag whose causes point
both ways is left alone. Each policy respects the same hold the agent does, so a changed stay
date rests for hold_days unless a shock cause lifts the hold. It reads the day through the four
sources, as the agent does, and the simulator wraps it with simulated.deciding(). It acts only
on a flag, so a market that is simply larger or smaller than the start rates assume raises
nothing until a flag says so.
"""

from __future__ import annotations

from collections.abc import Mapping

from hotel_market.customer import Customer, demo
from hotel_market.detect import AHEAD, BEHIND, NEW_EVENT, SEATS_CUT, SEATS_UP, detect_numbers, flags
from hotel_market.sources import Sources

POLICY_STEP = 0.05  # the raise on a raising cause and the cut on a lowering cause
RAISE, LOWER = 1, -1


class PacePolicy:
    """The pace rule as a decider. decide(day, sources) returns the rate changes to apply from the
    next day, keyed by (hotel key, stay day), and keeps the hold it leaves."""

    name = "pace"
    rules: Mapping[str, int] = {AHEAD: RAISE, BEHIND: LOWER}  # flag cause -> direction

    def __init__(self, customer: Customer | None = None):
        self.customer = customer or demo()
        self.held: dict[tuple[str, int], int] = {}  # (hotel key, stay day) -> day last changed
        self.acted: int = 0  # the flags the rule changed a rate on
        self.changed: int = 0  # the (hotel, stay date) pairs it changed, over the run

    def direction(self, causes: tuple[str, ...]) -> int:
        """RAISE or LOWER when the flag's causes the policy knows point one way, else 0."""
        directions = {self.rules[cause] for cause in causes if cause in self.rules}
        return directions.pop() if len(directions) == 1 else 0

    def decide(self, day: int, sources: Sources) -> dict[tuple[str, int], float]:
        table = detect_numbers(day, sources, self.customer)
        changes: dict[tuple[str, int], float] = {}
        for flag in flags(day, table, self.held, self.customer):
            direction = self.direction(flag.causes)
            if not direction:
                continue
            factor = 1 + direction * POLICY_STEP
            hotel = self.customer.hotel(flag.hotel)
            rows = table[
                (table["hotel"] == flag.hotel)
                & table["stay_day"].between(flag.first_stay, flag.last_stay)
            ]
            moved = False
            for stay_day, rate in zip(rows["stay_day"].tolist(), rows["rate"].tolist()):
                new = hotel.clamp(factor * float(rate))
                if new != float(rate):
                    changes[(flag.hotel, int(stay_day))] = new
                    self.held[(flag.hotel, int(stay_day))] = day
                    moved = True
            if moved:
                self.acted += 1
        self.changed += len(changes)
        return changes


class RulesPolicy(PacePolicy):
    """The pace steps plus the retired rules: raise on an event or seat-up flag, lower on a
    seat-cut flag."""

    name = "rules"
    rules: Mapping[str, int] = {
        AHEAD: RAISE,
        BEHIND: LOWER,
        NEW_EVENT: RAISE,
        SEATS_UP: RAISE,
        SEATS_CUT: LOWER,
    }


class NeverCutPolicy(PacePolicy):
    """The rules policy's raises with no cut: a behind-pace or seat-cut flag is left alone."""

    name = "never-cut"
    rules: Mapping[str, int] = {AHEAD: RAISE, NEW_EVENT: RAISE, SEATS_UP: RAISE}


POLICIES = {
    PacePolicy.name: PacePolicy,
    RulesPolicy.name: RulesPolicy,
    NeverCutPolicy.name: NeverCutPolicy,
}
