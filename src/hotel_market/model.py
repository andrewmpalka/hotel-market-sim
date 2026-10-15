"""model.py

The model call. One call per hotel per day sees that hotel's queued entries. It picks the plan or
hold for each and writes two or three sentences of reason. The request holds every number the
model may use. The answer is checked against the options in the request, so the model chooses and
writes and nothing more.

The model's answers are cached under cache/seed<seed>/, one file per day and hotel, keyed by a
digest of the request. Each record also carries a digest of the system prompt, so an edited prompt
stops a rerun instead of returning the old answers. A rerun reads them first. With no client, a
template accepts each plan and
writes a reason from the entry's numbers. The template is a function of the request, so it is
never cached. Nothing here needs an API key. Each record names the model asked, and an agent
given another model keeps its answers in their own folder (agent.py).

A replay only reads the cache. A Measured client wraps any client, records every call to a
calls.jsonl and asks again after an SDK error or an invalid answer.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from hotel_market.detect import MEDIAN_DOWN, MEDIAN_UP, NEW_EVENT, SEATS_CUT, SEATS_UP
from hotel_market.plan import (
    DAY_NAMES,
    HOLD,
    Candidate,
    EarlierChange,
    Entry,
    FlagNumbers,
    Pricing,
    WeekdayGroup,
)
from hotel_market.text import (
    against_median_range,
    band_verdict,
    capitalize_first,
    dollars,
    money_range,
    number,
    pace_text,
    percent_change_range,
    rooms,
    span,
    tens_of_dollars,
    versus_holding,
    versus_holding_at_end,
)
from hotel_market.world import Hotel, weekday

MODEL = "claude-opus-5-5"
# The current model at each tier, the benchmark's default reviewers (bench.py); MODEL is first.
MODELS = ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5")

SYSTEM = """\
You advise the central revenue manager of a brand's hotels. Each entry below is a \
run of stay dates at one hotel where something changed. For each day of the \
week in the entry, code has compared candidate rate actions by their estimated \
contribution (room revenue minus the cost of servicing the rooms) on the rooms \
still unsold, and picked the best. Together those picks form the entry's plan.

For each entry, choose the plan to recommend it, or "hold" to decline it and \
keep the current rates. Then write two or three plain sentences the revenue \
manager can read: what changed, what we recommend, and why. Write as "we". \
State only what the entry shows: use only figures that appear in the entry, do \
not compute new ones, and make no claim about price sensitivity or risk that \
the entry does not contain. Every figure in the request is written the way a \
report writes it, with its unit and, where it has one, its direction in words, \
such as "14.6% below the median", "up 15.0%", "44 rooms ahead of pace" or \
"$120 less than holding", and a range is one phrase, such as "10.7% to 14.6% \
below the median" or "up 17.0% to 21.6%". Copy these phrases whole; do not \
add a sign, a direction word or a rounding of your own, and do not quote one \
end of a range on its own. Each entry also lists our earlier changes on its \
stay dates, each with the rooms booked since it against the rooms expected; \
you may cite these as written and must not compute from them. In a sentence \
that lists several gains, "more than \
holding" may be written once for all of them, as in "$280 on Tuesday and $60 \
on Wednesday, $340 more than holding in all". Write an event's name in lower \
case inside a sentence. The request's elasticity field says which price \
sensitivity \
every estimate assumes: "assumed" is a value the agent was given, "fixed" a \
value set for the run, and "learn" one estimated from the bookings, with its \
standard error. When that field says cautious, each candidate also shows its \
estimate at the low and the high end of the elasticity band, and the plan \
changes a rate only where the change beats holding at both ends. Each \
candidate's band_verdict states that rule's result for it; copy the verdict \
as written. When that \
field has a market_elasticity, the market's demand falls as the comp median \
rises by that power, and the estimates already count it. When it has a level, \
the agent scaled its demand forecast by that factor, learned from the \
bookings, and the estimates already count it."""

# The mode the model sees for the default pricing. The command-line option is "true",
# the simulator's own value; to the model it is a value the agent was given.
MODE_NAMES = {"true": "assumed"}


def schema_for(request: dict) -> dict:
    """The shape of an answer to this request: one required decision per entry, keyed by the
    entry's id, each choosing between that entry's plan and hold. An answer therefore cannot leave
    an entry out or borrow another entry's plan. The API allows a required property per key and
    not an array bound above one, which is why the decisions are an object. ClaudeClient turns
    the object back into the list the cache and the check read."""
    entries = request["entries"]
    decisions = {
        entry["id"]: {
            "type": "object",
            "properties": {
                "choice": {"type": "string", "enum": sorted(entry["options"])},
                "reason": {"type": "string"},
            },
            "required": ["choice", "reason"],
            "additionalProperties": False,
        }
        for entry in entries
    }
    return {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "object",
                "properties": decisions,
                "required": [entry["id"] for entry in entries],
                "additionalProperties": False,
            },
        },
        "required": ["decisions"],
        "additionalProperties": False,
    }


def as_decision_list(text: str) -> str:
    """The model's answer with its decisions as the list the cache and the check read. The schema
    asks for an object keyed by entry id; a list, as a fake or an older answer gives it, passes
    through. Text that is not JSON passes through too, for the check to reject."""
    try:
        answer = json.loads(text)
    except ValueError:
        return text
    decisions = answer.get("decisions") if isinstance(answer, dict) else None
    if not isinstance(decisions, dict):
        return text
    answer["decisions"] = [{"id": key, **value} for key, value in decisions.items()]
    return json.dumps(answer)


class Client(Protocol):
    """Whatever answers a request. Two optional attributes shape how ask() treats the answers. The
    attribute name is the source a decision records, "model" when absent. The attribute cached
    says whether the answers are kept in the cache, True when absent. An uncached client, such as
    the oracle grader in bench.py, answers like the template. Nothing is written, and nothing of
    the model's is read. Its name is read after each answer, so it may name the answer's source."""

    def complete(self, system: str, prompt: str, schema: dict) -> str:
        """Send one request and return the model's JSON text."""


class StaleCache(Exception):
    """A cached answer was written for a different request."""


class CacheMiss(Exception):
    """A replay needed a cached answer that is not there."""


class ModelRefused(Exception):
    """The model declined the request, and so did the fallback."""


class ClaudeClient:
    """Asks Claude through the Anthropic SDK. Live calls need an API key; nothing
    else in the project does."""

    def __init__(self, model: str = MODEL, sdk: Any = None):
        if sdk is None:
            import anthropic  # imported here so that offline runs never load it

            # A key that is not scoped to a workspace needs the workspace named on every request.
            workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
            headers = {"anthropic-workspace-id": workspace} if workspace else None
            sdk = anthropic.Anthropic(default_headers=headers)
        self.sdk = sdk
        self.model = model
        self.last: dict | None = None  # what the last call returned, for a Measured wrapper

    def complete(self, system: str, prompt: str, schema: dict) -> str:
        self.last = None  # a failed attempt leaves nothing for the wrapper to count
        response = self.sdk.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            # If a safety classifier declines, the API re-runs the request on the
            # fallback model Anthropic recommends for that kind of refusal.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = getattr(response, "usage", None)
        self.last = {
            "model": getattr(response, "model", None) or self.model,
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            "stop_reason": response.stop_reason,
            "fallback": any(block.type == "fallback" for block in response.content),
            "request_id": getattr(response, "_request_id", None),
        }
        if response.stop_reason == "refusal":
            raise ModelRefused(f"the model declined: {response.stop_details}")
        if response.stop_reason == "max_tokens":
            raise ValueError("the model's answer was cut off at max_tokens")
        return as_decision_list(_answer_text(list(response.content)))


RETRIES = 2  # how many times a Measured client asks again after an SDK error or an invalid answer
BACKOFF_SECONDS = 2.0  # the wait before it asks again after an SDK error; it doubles on each retry
# The anthropic errors a Measured client asks again, by class name so that this module imports
# without the SDK: a status error (a rate limit, an overload) or a connection error. The SDK has
# retried each of them itself before it raises.
SDK_ERRORS = ("APIStatusError", "APIConnectionError")
_INVALID = (
    ValueError,
    KeyError,
    TypeError,
)  # not JSON, no decisions, or a choice outside the options


def _sdk_error(error: BaseException) -> bool:
    return any(cls.__name__ in SDK_ERRORS for cls in type(error).__mro__)


class Measured:
    """Wraps any client, records each call and asks again after a bad attempt.

    One record per call holds the request's day, hotel and digest, the model asked and the model
    that answered. It also holds the input and output tokens, the wall time, the stop reason and
    the retries made. It flags whether any attempt was bad and whether the request failed in the
    end. A bad attempt is an SDK error, an invalid answer or a refusal. An SDK error is asked
    again after a backoff, and an invalid answer at once. A refusal is not asked again, because
    the API has already re-run it on the fallback model.

    When the retries run out, the record is written and then the error is raised. The records are
    kept in `calls`. They are also appended to a calls.jsonl when a path is given, so an arm's
    calls sit beside its cache. The client's model, name and cached flag pass through.
    """

    def __init__(
        self,
        client: Client,
        path: Path | None = None,
        retries: int = RETRIES,
        backoff: float = BACKOFF_SECONDS,
    ):
        self.client = client
        self.path = Path(path) if path is not None else None
        self.retries = retries
        self.backoff = backoff
        self.calls: list[dict] = []
        self.model = getattr(client, "model", getattr(client, "name", None))
        if hasattr(client, "name"):
            self.name = client.name
        if hasattr(client, "cached"):
            self.cached = client.cached

    def complete(self, system: str, prompt: str, schema: dict) -> str:
        request = json.loads(prompt)
        record = {
            "day": request["day"],
            "hotel": request["hotel"]["name"],
            "request_digest": request_digest(request),
            "asked": self.model,
            "model": self.model,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "seconds": 0.0,
            "stop_reason": None,
            "fallback": False,
            "request_id": None,
            "retries": 0,
            "bad_attempt": False,
            "failed": False,
            "error": None,
        }
        attempts = 0
        while True:
            attempts += 1
            start = time.perf_counter()
            try:
                text = self.client.complete(system, prompt, schema)
                _check(json.loads(text)["decisions"], request)
                error = None
            except Exception as failure:
                if not (isinstance(failure, (ModelRefused, *_INVALID)) or _sdk_error(failure)):
                    raise
                error = failure
            record["seconds"] += time.perf_counter() - start
            self._add_usage(record)
            if error is None:
                break
            record["bad_attempt"] = True
            record["error"] = type(error).__name__
            if isinstance(error, ModelRefused) or attempts > self.retries:
                break
            if _sdk_error(error):
                time.sleep(self.backoff * 2 ** (attempts - 1))
        record["retries"] = attempts - 1
        record["failed"] = error is not None
        record["seconds"] = round(record["seconds"], 2)
        self.calls.append(record)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as file:
                file.write(json.dumps(record) + "\n")
        if error is not None:
            raise error
        return text

    def _add_usage(self, record: dict) -> None:
        """What the wrapped client knows about its last call, when it is a ClaudeClient."""
        last = getattr(self.client, "last", None)
        if not last:
            return
        record["model"] = last.get("model") or record["model"]
        for field in (
            "input_tokens",
            "output_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
        ):
            record[field] += last.get(field, 0) or 0
        record["stop_reason"] = last.get("stop_reason")
        record["fallback"] = record["fallback"] or bool(last.get("fallback"))
        record["request_id"] = last.get("request_id")


def _answer_text(blocks: list) -> str:
    """The text of the model that answered. After a fallback, the content holds
    what the declining model wrote, then a "fallback" block, then the answer."""
    handovers = [i for i, block in enumerate(blocks) if block.type == "fallback"]
    start = handovers[-1] + 1 if handovers else 0
    return "".join(block.text for block in blocks[start:] if block.type == "text")


def request_for(day: int, hotel: Hotel, entries: list[Entry]) -> dict:
    """What the model sees for one hotel's queue. Every number in it comes from code.

    The entries of one hotel on one day share their pricing, so the request carries it once. A
    change to the elasticity changes the request's digest.
    """
    pricing = {entry.pricing for entry in entries}
    targets = {entry.target for entry in entries}
    if len(pricing) != 1 or len(targets) != 1:
        raise ValueError(f"one request needs one pricing and one target, got {pricing}, {targets}")
    request = {
        "day": day,
        "hotel": {
            "name": hotel.name,
            "rooms": rooms(hotel.rooms),
            "floor": dollars(hotel.floor),
            "ceiling": dollars(hotel.ceiling),
            "cost_per_occupied_room": dollars(hotel.room_cost),
        },
        "elasticity": _pricing_request(pricing.pop()),
        "entries": [_entry_request(entry) for entry in entries],
    }
    target = targets.pop()
    if target != "contribution":
        request["target"] = target  # the estimates count room revenue, not contribution
    return request


def _days(value: float) -> str:
    return str(int(value))


def _pricing_request(pricing: Pricing) -> dict:
    """The pricing as the model sees it. Every number is a display string. The default mode is named
    "assumed" and not the command line's "true" (MODE_NAMES)."""
    request = {
        "elasticity": number(pricing.elasticity),
        "mode": MODE_NAMES.get(pricing.mode, pricing.mode),
        "standard_error": _optional(pricing.standard_error, number),
        "prior": _optional(pricing.prior, number),
        "observations": _optional(pricing.observations, rooms),
    }
    if pricing.cautious:
        request["cautious"] = True
        request["band"] = span(pricing.band, number)
    if pricing.market_elasticity:
        # Left out at 0.0, where the market's level moves nothing.
        request["market_elasticity"] = number(pricing.market_elasticity)
    if pricing.level != 1.0:
        request["level"] = number(pricing.level)  # the factor the forecast was scaled by
    return request


def _optional(value: float | None, display: Callable[[float], str]) -> str | None:
    return None if value is None else display(value)


def _entry_request(entry: Entry) -> dict:
    return {
        "id": entry.id,
        "stay_dates": span((entry.first_stay, entry.last_stay), _days),
        "what_changed": list(entry.causes),
        "numbers": _numbers_request(entry.numbers),
        "by_day_of_week": [_weekday_request(group) for group in entry.weekdays],
        "plan": entry.plan,
        "value_at_stake": versus_holding(entry.value_at_stake),
        "options": [entry.plan, HOLD],
        # The hotel's own earlier changes on these dates, each with what has come of it so far.
        "earlier_changes_on_these_dates": [
            earlier_change_text(change) for change in entry.earlier_changes
        ],
    }


def earlier_change_text(change: EarlierChange) -> str:
    """One earlier change as the model and the manager read it, such as "day 10: raised 10% to
    $242 on Thu 45; since then 31 rooms booked against 24 expected". Code computed every figure
    (agent.py), so the model may cite it and must not compute from it."""
    moved = change.new_rate / change.old_rate - 1
    return (
        f"day {change.day}: {'raised' if moved > 0 else 'lowered'} {abs(moved):.0%} to "
        f"{dollars(change.new_rate)} on {DAY_NAMES[weekday(change.stay_day)]} {change.stay_day}; "
        f"since then {rooms(change.booked_since)} rooms booked against "
        f"{rooms(change.expected_since)} expected"
    )


def _numbers_request(numbers: FlagNumbers) -> dict:
    """The flag's numbers as display strings. A signed quantity reads as a phrase with its direction
    in words, and a range as one phrase (text.py). The model then copies a phrase that already
    reads correctly."""
    return {
        "days_out": span(numbers.days_out, _days),
        "rooms_on_books": rooms(numbers.rooms_on_books),
        "unsold_rooms": rooms(numbers.unsold_rooms),
        "remaining_demand": rooms(numbers.remaining_demand),
        "pace_gap": pace_text(numbers.pace_gap),
        # The keys keep their names from world v1; the figures are arriving passengers.
        "seat_change": percent_change_range(numbers.passenger_change),
        "seat_revision": percent_change_range(numbers.passenger_revision),
        "rate": money_range(numbers.rate),
        "comp_median": money_range(numbers.comp_median),
        "rate_vs_median": against_median_range(numbers.rate_vs_median),
        "median_change": percent_change_range(numbers.median_change),
        "new_event": numbers.new_event,
    }


def _weekday_request(group: WeekdayGroup) -> dict:
    return {
        "day": DAY_NAMES[group.weekday],
        "stay_dates": group.stays,
        "candidates": [
            {
                "name": candidate.name,
                "rates": money_range(candidate.rates.values()),
                "estimated_contribution": tens_of_dollars(candidate.estimate),
                "versus_hold": versus_holding(candidate.estimate - group.hold.estimate),
                **_band_request(candidate, group),
            }
            for candidate in group.candidates
        ],
        "best": group.best.name,
    }


def _band_request(candidate: Candidate, group: WeekdayGroup) -> dict:
    """Cautious only. The estimate, and its value over hold, at each end of the band. All three
    values the rule used then reach the model. Each is named by the end of the band, because the
    low elasticity can give the higher estimate. The value over hold at an end reads to the dollar
    under $10, and every candidate but hold carries the rule's verdict as a phrase (text.py). The
    model copies the verdict in place of reading it off the rounded gains."""
    if candidate.band is None:
        return {}
    low, high = candidate.band
    gain_low, gain_mid, gain_high = group.gains(candidate)
    request = {
        "estimated_contribution_band": {
            "at_low_elasticity": tens_of_dollars(low),
            "at_high_elasticity": tens_of_dollars(high),
        },
        "versus_hold_band": {
            "at_low_elasticity": versus_holding_at_end(gain_low),
            "at_high_elasticity": versus_holding_at_end(gain_high),
        },
    }
    if candidate is not group.hold:
        request["band_verdict"] = band_verdict(gain_low, gain_mid, gain_high)
    return request


def ask(
    request: dict,
    path: Path,
    client: Client | None = None,
    replay: bool = False,
    model: str = MODEL,
) -> dict:
    """The decisions for one hotel's queue on one day.

    Without a client the template answers, and nothing is cached, because the template is a
    function of the request. An uncached client, one whose cached flag is false, is treated the
    same way. Its decisions record its name as their source. With any other client, the model's
    cached answer is read first.

    A cached answer written for a different request, or under a different system prompt, raises
    instead of answering the wrong question. A replay never calls the model: it reads the cache or
    raises. A new record names `model`, the model the client asks, so a cache with several
    models' answers tells them apart, and carries the prompt's digest.
    """
    if client is None:
        return {"source": "template", "decisions": template_decisions(request)}
    if not getattr(client, "cached", True):
        decisions = _answer(client, request)  # its name is read after, so it may name each answer
        answer = {"source": getattr(client, "name", "model"), "decisions": decisions}
        _check(answer["decisions"], request)
        return answer
    source = getattr(client, "name", "model")
    digest = request_digest(request)
    cached = _read_cache(path, digest)
    if cached is not None:
        _check(cached["decisions"], request)
        return cached
    if replay:
        raise CacheMiss(f"{path} is missing; run without --replay first")
    answer = {"source": source, "decisions": _answer(client, request)}
    _check(answer["decisions"], request)
    record = {
        "request_digest": digest,
        "prompt_digest": prompt_digest(),
        "request": request,
        **answer,
        "model": model,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")
    return record


def _answer(client: Client, request: dict) -> list[dict]:
    """The client's decisions for a request, as the schema shapes them."""
    text = client.complete(SYSTEM, json.dumps(request, indent=2), schema_for(request))
    return json.loads(text)["decisions"]


def request_digest(request: dict) -> str:
    """The cache key of a request: the sha256 of its sorted-keys JSON."""
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def prompt_digest(system: str = SYSTEM) -> str:
    """The sha256 of the system prompt, kept in each cache record so that a prompt edit is caught
    on the next read instead of returning answers made under the old prompt."""
    return hashlib.sha256(system.encode()).hexdigest()


def _read_cache(path: Path, digest: str) -> dict | None:
    """The model's cached answer to this request, or None when there is none.

    A file from before template answers stopped being cached is not the model's answer. It is
    ignored and overwritten by one. A record answered under another system prompt raises, and a
    record from before the prompt digest was kept reads as current.
    """
    if not path.exists():
        return None
    cached = json.loads(path.read_text())
    if cached.get("source") != "model":
        return None
    if cached["request_digest"] != digest:
        raise StaleCache(f"{path} was written for a different request; delete cache/ and rerun")
    if cached.get("prompt_digest", prompt_digest()) != prompt_digest():
        raise StaleCache(
            f"{path} was answered under another system prompt; delete cache/ and rerun, or put "
            f"the prompt back"
        )
    return cached


def _check(decisions: list[dict], request: dict) -> None:
    """One decision per entry, each choosing that entry's plan or hold."""
    options = {entry["id"]: entry["options"] for entry in request["entries"]}
    if sorted(decision["id"] for decision in decisions) != sorted(options):
        raise ValueError(f"expected one decision for each of {sorted(options)}, got {decisions}")
    for decision in decisions:
        if decision["choice"] not in options[decision["id"]]:
            raise ValueError(
                f"entry {decision['id']}: {decision['choice']!r} is not one of "
                f"{options[decision['id']]}"
            )


def template_decisions(request: dict) -> list[dict]:
    """The template's answer: accept each plan, with a reason built from the entry's numbers."""
    return [
        {
            "id": entry["id"],
            "choice": entry["plan"],
            "reason": _template_reason(
                entry, request["elasticity"], request.get("target", "contribution")
            ),
        }
        for entry in request["entries"]
    ]


def _template_reason(entry: dict, elasticity: dict, target: str) -> str:
    """Written from the request's display strings, each copied whole, as the model is
    told to write."""
    numbers = entry["numbers"]
    held_days = [weekday["day"] for weekday in entry["by_day_of_week"] if weekday["best"] == HOLD]
    held = f"; {', '.join(held_days)} hold" if held_days else ""
    counted = "contribution" if target == "contribution" else "room revenue"
    stays = entry["stay_dates"]
    earlier = entry.get("earlier_changes_on_these_dates") or []
    history = f" Our last change on these dates was on {earlier[-1]}." if earlier else ""
    return (
        f"{capitalize_first(_what_changed(entry['what_changed'], numbers))} on "
        f"stay date{'s' if ' to ' in stays else ''} {stays}. "
        f"We recommend the plan, {entry['plan']}{held}, which is estimated to earn "
        f"{entry['value_at_stake']} in {counted} on the {numbers['unsold_rooms']} rooms "
        f"still unsold. Bookings are {numbers['pace_gap']}, and our rate sits "
        f"{numbers['rate_vs_median']}.{history}{_elasticity_text(elasticity)}"
    )


def _elasticity_text(elasticity: dict) -> str:
    """How the estimates were priced, when that is not the assumed value."""
    if elasticity["mode"] == "fixed":
        return f" The estimates assume a fixed elasticity of {elasticity['elasticity']}."
    if elasticity["mode"] == "learn":
        text = (
            f" The estimates assume an elasticity of {elasticity['elasticity']}, learned "
            f"from {elasticity['observations']} observations with a standard error of "
            f"{elasticity['standard_error']} (prior {elasticity['prior']})."
        )
        if elasticity.get("cautious"):
            text += (
                f" Each change also beats holding with the elasticity at both ends of "
                f"the band {elasticity['band']}."
            )
        if elasticity.get("level"):
            text += f" The demand forecast is scaled by {elasticity['level']}, learned too."
        return text
    return ""


def _what_changed(causes: list[str], numbers: dict) -> str:
    """The causes as clauses with their phrases. An example is "arriving passengers are up 12.8% to
    23.0% against yesterday's schedule and a convention was announced"."""
    clauses = []
    for cause in causes:
        if cause in (SEATS_UP, SEATS_CUT):
            clauses.append(
                f"arriving passengers are {numbers['seat_revision']} against yesterday's schedule"
            )
        elif cause in (MEDIAN_UP, MEDIAN_DOWN):
            clauses.append(f"the comp median is {numbers['median_change']} since yesterday")
        elif cause == NEW_EVENT:
            clauses.append(f"a {numbers['new_event'].lower()} was announced")
        else:
            clauses.append(f"bookings are {cause}")
    return " and ".join(clauses)
