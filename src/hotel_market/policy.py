"""policy.py

A rule-based control: a pricer with no estimates and no model, for the comparison the fixed-rate
run cannot give. A fixed-rate run never moves a rate, so any gain against it includes what a
hotel's own rules would have earned anyway. A rule that acts on the same flags is the fairer
yardstick.

PacePolicy raises every stay date that runs ahead of pace by the detect threshold and lowers
every one that runs behind, both by POLICY_STEP, clamped to the hotel's floor and ceiling. It
respects the same hold the agent does, so a changed stay date rests for hold_days unless a shock
cause lifts the hold. It reads the day through the four sources, as the agent does, and the
simulator wraps it with simulated.deciding(). It acts only on a flag, so a market that is simply
larger or smaller than the start rates assume raises nothing until a flag says so.
"""

from __future__ import annotations

from hotel_market.customer import Customer, demo
from hotel_market.detect import AHEAD, BEHIND, detect_numbers, flags
from hotel_market.sources import Sources

POLICY_STEP = 0.05  # the raise on an ahead-of-pace flag and the cut on a behind-pace flag


class PacePolicy:
    """The pace rule as a decider. decide(day, sources) returns the rate changes to apply from the
    next day, keyed by (hotel key, stay day), and keeps the hold it leaves."""

    name = "pace"

    def __init__(self, customer: Customer | None = None):
        self.customer = customer or demo()
        self.held: dict[tuple[str, int], int] = {}  # (hotel key, stay day) -> day last changed
        self.acted: int = 0  # the flags the rule changed a rate on
        self.changed: int = 0  # the (hotel, stay date) pairs it changed, over the run

    def decide(self, day: int, sources: Sources) -> dict[tuple[str, int], float]:
        table = detect_numbers(day, sources, self.customer)
        changes: dict[tuple[str, int], float] = {}
        for flag in flags(day, table, self.held, self.customer):
            if AHEAD in flag.causes:
                factor = 1 + POLICY_STEP
            elif BEHIND in flag.causes:
                factor = 1 - POLICY_STEP
            else:
                continue
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


POLICIES = {PacePolicy.name: PacePolicy}
