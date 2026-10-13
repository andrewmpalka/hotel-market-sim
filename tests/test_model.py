"""Module 7, model.py: the request, the cached answer, the template and the Claude client."""

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from hotel_market.customer import demo
from hotel_market.detect import flags
from hotel_market.model import (
    BACKOFF_SECONDS,
    MODEL,
    RETRIES,
    SYSTEM,
    CacheMiss,
    ClaudeClient,
    Measured,
    ModelRefused,
    StaleCache,
    as_decision_list,
    ask,
    request_digest,
    request_for,
    schema_for,
)
from hotel_market.plan import HOLD, Pricing, entry_for
from hotel_market.text import versus_holding

DEMO = demo()

SCHEMA = {"type": "object", "properties": {}}  # any schema will do for the client tests


class FakeClient:
    """Stands in for the model. It accepts each plan, or gives one choice. With several choices, it
    gives one per call in turn and repeats the last one."""

    model = "fake"

    def __init__(self, *choices):
        self.choices = list(choices)
        self.calls = []

    def complete(self, system, prompt, schema):
        request = json.loads(prompt)
        self.calls.append(request)
        choice = self.choices[min(len(self.calls), len(self.choices)) - 1] if self.choices else None
        return json.dumps(
            {
                "decisions": [
                    {
                        "id": e["id"],
                        "choice": choice or e["plan"],
                        "reason": f"Fake reason for {e['id']}.",
                    }
                    for e in request["entries"]
                ]
            }
        )


class Refusing:
    """Stands in for a Claude client whose every call ends in a refusal."""

    model = "refusing"

    def __init__(self):
        self.calls = 0

    def complete(self, system, prompt, schema):
        self.calls += 1
        raise ModelRefused("the model declined")


def _sdk_error(status):
    """One of the SDK's own status errors, as a rate limit (429) or an overload (529) arrives."""
    import anthropic

    try:
        import httpx2 as httpx  # the SDK's HTTP client; earlier SDKs use httpx
    except ImportError:
        import httpx
    response = httpx.Response(status, request=httpx.Request("POST", "https://api.anthropic.com"))
    error = anthropic.RateLimitError if status == 429 else anthropic.InternalServerError
    return error("the API said no", response=response, body=None)


def _sdk(replies):
    """A fake SDK whose create() takes the next reply from the list. An exception is raised. Any
    other reply is answered as text with 1,200 input tokens."""

    def create(**kwargs):
        reply = replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return SimpleNamespace(
            model="claude-opus-5-5-20260901",
            usage=SimpleNamespace(
                input_tokens=1200,
                output_tokens=300,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
            ),
            stop_reason="end_turn",
            stop_details=None,
            content=[SimpleNamespace(type="text", text=reply)],
            _request_id="req_1",
        )

    return SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))


class NoCalls:
    def complete(self, system, prompt, schema):
        raise AssertionError("the model was called")


@pytest.fixture
def convention_request(day10):
    """Day 10's request for the convention hotel: the one entry its convention flag made."""
    _, table = day10
    entries = [entry_for(10, f, table) for f in flags(10, table) if f.hotel == "convention"]
    return request_for(10, DEMO.hotel("convention"), entries), entries


def test_the_request_holds_each_entrys_plan_and_hold_as_its_only_options(convention_request):
    request, [entry] = convention_request
    [asked] = request["entries"]
    assert asked["options"] == [entry.plan, "hold"]
    assert asked["plan"] == entry.plan
    assert asked["value_at_stake"] == versus_holding(entry.value_at_stake)
    assert [d["day"] for d in asked["by_day_of_week"]] == ["Thu", "Fri", "Sat", "Sun"]
    assert request["hotel"]["name"] == "Downtown convention hotel"


def test_every_figure_in_the_request_is_a_display_string(convention_request):
    request, [entry] = convention_request
    [asked] = request["entries"]
    numbers = asked["numbers"]
    # Every figure is the string the model copies, a signed quantity as a phrase with
    # its direction in words and no sign, and a range as one phrase, the single value
    # when both ends read the same.
    assert asked["stay_dates"] == "45 to 48" and numbers["days_out"] == "35 to 38"
    assert numbers["rate"] == "$220" and numbers["comp_median"] == "$246 to $258"
    assert numbers["rate_vs_median"] == "10.7% to 14.6% below the median"
    assert numbers["median_change"] == "up 15.0%" and numbers["seat_revision"] == "unchanged"
    assert numbers["unsold_rooms"] == "1,188" and numbers["pace_gap"] == "15 rooms ahead of pace"
    assert asked["value_at_stake"] == "$8,050 more than holding"  # an estimate, to the $10
    assert request["hotel"]["floor"] == "$154" and request["hotel"]["rooms"] == "400"
    assert request["hotel"]["cost_per_occupied_room"] == "$73"
    for weekday in asked["by_day_of_week"]:
        for candidate in weekday["candidates"]:
            assert candidate["rates"].startswith("$")
            assert candidate["estimated_contribution"].startswith("$")
            assert candidate["estimated_contribution"].endswith("0")
            assert candidate["versus_hold"].endswith("holding")
    thursday = asked["by_day_of_week"][0]["candidates"]
    assert [c["rates"] for c in thursday] == ["$220", "$231", "$242", "$209"]
    assert thursday[0]["versus_hold"] == "the same as holding"
    assert thursday[2]["versus_hold"] == "$5,770 more than holding"
    # The only raw numbers left are the day and each day of the week's own stay dates,
    # which are a list of dates and not a range; every other figure is a string.
    assert _number_paths(request) == {"day", "entries.by_day_of_week.stay_dates"}


def _number_paths(value, path="") -> set[str]:
    """The dotted paths of every int or float in a nested dict, list indexes left out."""
    if isinstance(value, bool):
        return set()
    if isinstance(value, (int, float)):
        return {path}
    if isinstance(value, dict):
        return {p for k, v in value.items() for p in _number_paths(v, f"{path}.{k}" if path else k)}
    if isinstance(value, list):
        return {p for v in value for p in _number_paths(v, path)}
    return set()


def test_the_schema_limits_ids_and_choices_to_the_requests_options(convention_request):
    request, [entry] = convention_request
    decisions = schema_for(request)["properties"]["decisions"]
    # One required decision per entry id, each limited to that entry's plan and hold: an answer
    # cannot leave an entry out or borrow another's plan. The API allows required properties
    # and not an array bound above one, which is why the decisions are an object.
    assert decisions["type"] == "object" and decisions["required"] == [entry.id]
    assert decisions["additionalProperties"] is False
    decision = decisions["properties"][entry.id]
    assert decision["properties"]["choice"]["enum"] == sorted([entry.plan, HOLD])
    assert decision["required"] == ["choice", "reason"]
    two = json.loads(json.dumps(request))
    two["entries"].append({**two["entries"][0], "id": "50-52", "plan": "raise 5% on Mon"})
    two["entries"][1]["options"] = ["raise 5% on Mon", HOLD]
    decisions = schema_for(two)["properties"]["decisions"]
    assert decisions["required"] == [entry.id, "50-52"]
    assert decisions["properties"]["50-52"]["properties"]["choice"]["enum"] == sorted(
        ["raise 5% on Mon", HOLD]
    )


def test_the_client_turns_the_answer_object_back_into_the_decision_list():
    answer = {"decisions": {"45-48": {"choice": HOLD, "reason": "We hold."}}}
    listed = json.loads(as_decision_list(json.dumps(answer)))
    assert listed == {"decisions": [{"id": "45-48", "choice": HOLD, "reason": "We hold."}]}
    already = json.dumps({"decisions": [{"id": "45-48", "choice": HOLD, "reason": "x"}]})
    assert as_decision_list(already) == already  # a list passes through
    assert as_decision_list("not json") == "not json"  # the check rejects it later


def test_ask_calls_the_model_once_and_then_reads_the_cache(convention_request, tmp_path):
    request, _ = convention_request
    client = FakeClient()
    first = ask(request, tmp_path / "day010_convention.json", client)
    assert len(client.calls) == 1 and first["source"] == "model"
    again = ask(request, tmp_path / "day010_convention.json", client)
    assert len(client.calls) == 1 and again == first
    assert ask(request, tmp_path / "day010_convention.json", NoCalls(), replay=True) == first


def test_a_replay_never_calls_the_model(tmp_path):
    request = {"day": 1, "hotel": {}, "entries": []}
    with pytest.raises(CacheMiss):
        ask(request, tmp_path / "missing.json", NoCalls(), replay=True)


def test_a_cache_written_for_another_request_is_refused(convention_request, tmp_path):
    request, _ = convention_request
    ask(request, tmp_path / "c.json", FakeClient())
    changed = json.loads(json.dumps(request))
    changed["entries"][0]["value_at_stake"] += " or so"
    with pytest.raises(StaleCache):
        ask(changed, tmp_path / "c.json", FakeClient())


def test_without_a_client_the_template_accepts_the_plan_and_quotes_the_numbers(
    convention_request, tmp_path
):
    request, [entry] = convention_request
    record = ask(request, tmp_path / "t.json")
    [decision] = record["decisions"]
    assert record["source"] == "template" and decision["choice"] == entry.plan
    # The template copies the request's display strings whole, as the model is told to.
    assert (
        "$8,050 more than holding in contribution on the 1,188 rooms still unsold"
        in (decision["reason"])
    )
    assert decision["reason"].startswith(
        "The comp median is up 15.0% since yesterday and a convention was announced on stay "
        "dates 45 to 48. We recommend the plan, "
    )
    assert decision["reason"].endswith(
        "Bookings are 15 rooms ahead of pace, and our rate sits 10.7% to 14.6% below the median."
    )
    # The template is never cached, so a client is asked afresh.
    assert not (tmp_path / "t.json").exists()
    client = FakeClient()
    assert ask(request, tmp_path / "t.json", client)["source"] == "model"
    assert len(client.calls) == 1


def test_the_template_never_reads_the_models_cache(convention_request, tmp_path):
    request, [entry] = convention_request
    ask(request, tmp_path / "m.json", FakeClient(HOLD))  # the model declined the plan
    [decision] = ask(request, tmp_path / "m.json")["decisions"]
    assert decision["choice"] == entry.plan  # the template still accepts it


def test_a_template_answer_cached_by_an_older_version_is_ignored_and_replaced(
    convention_request, tmp_path
):
    request, _ = convention_request
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"request_digest": "old", "source": "template", "decisions": []}))
    client = FakeClient()
    assert ask(request, path, client)["source"] == "model"
    assert len(client.calls) == 1
    assert json.loads(path.read_text())["source"] == "model"


def test_a_choice_that_is_not_the_plan_or_hold_is_rejected(convention_request, tmp_path):
    request, _ = convention_request
    with pytest.raises(ValueError):
        ask(request, tmp_path / "x.json", FakeClient("raise 50%"))


def test_the_cache_record_names_the_model_asked(convention_request, tmp_path):
    request, _ = convention_request
    # The default model unless the caller names another; the agent passes its own.
    assert ask(request, tmp_path / "a.json", FakeClient())["model"] == MODEL
    record = ask(request, tmp_path / "b.json", FakeClient(), model="claude-sonnet-5-5")
    assert record["model"] == "claude-sonnet-5-5"
    assert json.loads((tmp_path / "b.json").read_text())["model"] == "claude-sonnet-5-5"
    # A record from before the field was added names no model and still reads back.
    older = {"request_digest": request_digest(request), "request": request, "source": "model"}
    older["decisions"] = record["decisions"]
    (tmp_path / "c.json").write_text(json.dumps(older))
    assert ask(request, tmp_path / "c.json", NoCalls(), replay=True) == older


def test_a_measured_client_records_one_call(convention_request, tmp_path):
    request, _ = convention_request
    client = Measured(FakeClient(), tmp_path / "calls.jsonl")
    text = client.complete(SYSTEM, json.dumps(request), schema_for(request))
    assert json.loads(text)["decisions"][0]["choice"] == request["entries"][0]["plan"]
    [record] = client.calls
    assert record["asked"] == "fake" and record["model"] == "fake"  # the wrapped client's own
    assert record["retries"] == 0 and record["bad_attempt"] is False and record["failed"] is False
    assert record["error"] is None
    assert record["input_tokens"] == record["output_tokens"] == 0  # a fake client has no usage
    assert record["stop_reason"] is None and record["fallback"] is False
    assert 0 <= record["seconds"] < 1
    assert [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()] == [
        record
    ]
    # The wrapped client's model, name and cached flag pass through, so ask() still treats
    # a measured oracle as uncached and an agent still names the model for its folder.
    assert client.model == "fake" and not hasattr(client, "cached")

    class Uncached(FakeClient):
        name, cached = "oracle", False

    measured = Measured(Uncached())
    assert (measured.name, measured.cached, measured.model) == ("oracle", False, "fake")
    assert ask(request, tmp_path / "u.json", measured)["source"] == "oracle"
    assert not (tmp_path / "u.json").exists() and len(measured.calls) == 1


def test_a_measured_client_retries_a_bad_answer_and_counts_it(convention_request, tmp_path):
    request, _ = convention_request
    # The first answer picks an option the request does not hold; the second is valid.
    wrapped = FakeClient("raise 50%", None)
    client = Measured(wrapped, tmp_path / "calls.jsonl")
    text = client.complete(SYSTEM, json.dumps(request), schema_for(request))
    assert json.loads(text)["decisions"][0]["choice"] == request["entries"][0]["plan"]
    assert len(wrapped.calls) == 2
    [record] = client.calls
    assert record["retries"] == 1 and record["bad_attempt"] is True and record["failed"] is False
    assert record["error"] == "ValueError"
    # A refusal has already been re-run on the fallback model by the API, so it is not asked
    # again: the request fails at once, and the record says so.
    refusing = Refusing()
    client = Measured(refusing, tmp_path / "calls.jsonl")
    with pytest.raises(ModelRefused):
        client.complete(SYSTEM, json.dumps(request), schema_for(request))
    assert refusing.calls == 1
    [record] = client.calls
    assert record["retries"] == 0 and record["bad_attempt"] is True and record["failed"] is True
    assert record["error"] == "ModelRefused"
    assert len((tmp_path / "calls.jsonl").read_text().splitlines()) == 2
    # Through ask(), nothing is cached for a call that never got a valid answer.
    with pytest.raises(ModelRefused):
        ask(request, tmp_path / "r.json", Measured(Refusing()))
    assert not (tmp_path / "r.json").exists()
    # An answer that never becomes valid is given up after RETRIES more tries.
    stubborn = FakeClient("raise 50%")
    with pytest.raises(ValueError):
        Measured(stubborn).complete(SYSTEM, json.dumps(request), schema_for(request))
    assert len(stubborn.calls) == RETRIES + 1 == 3


def test_a_call_record_names_its_day_hotel_and_request_digest(convention_request, tmp_path):
    request, _ = convention_request
    client = Measured(FakeClient())
    client.complete(SYSTEM, json.dumps(request), schema_for(request))
    [record] = client.calls
    assert (record["day"], record["hotel"]) == (10, "Downtown convention hotel")
    assert record["request_digest"] == request_digest(request)
    # The same digest keys the cache record, so a call is joined to the answer it produced.
    cached = ask(request, tmp_path / "day010_convention.json", FakeClient())
    assert cached["request_digest"] == record["request_digest"]


def test_a_measured_client_retries_an_sdk_error_after_a_backoff(
    convention_request, tmp_path, monkeypatch
):
    request, _ = convention_request
    waits = []
    monkeypatch.setattr("time.sleep", waits.append)
    answer = FakeClient().complete(SYSTEM, json.dumps(request), {})
    sdk = _sdk([answer, _sdk_error(429), answer])
    client = Measured(ClaudeClient(sdk=sdk), tmp_path / "calls.jsonl")
    client.complete(SYSTEM, json.dumps(request), schema_for(request))  # a clean first call
    client.complete(SYSTEM, json.dumps(request), schema_for(request))  # rate limited, then not
    first, second = client.calls
    assert first["retries"] == 0 and first["bad_attempt"] is False
    assert second["retries"] == 1 and second["bad_attempt"] is True and second["failed"] is False
    assert second["error"] == "RateLimitError" and second["stop_reason"] == "end_turn"
    # The failed attempt left nothing to count: the tokens are one answer's, not two.
    assert second["input_tokens"] == 1200 and second["model"] == "claude-opus-5-5-20260901"
    assert waits == [BACKOFF_SECONDS]
    # The SDK's errors are matched by class name, so model.py never imports the SDK.

    class APIConnectionError(Exception):
        pass

    class Flaky(FakeClient):
        def complete(self, system, prompt, schema):
            if not self.calls:
                self.calls.append(None)
                raise APIConnectionError("no route to the API")
            return super().complete(system, prompt, schema)

    client = Measured(Flaky(), backoff=0)
    client.complete(SYSTEM, json.dumps(request), schema_for(request))
    [record] = client.calls
    assert record["retries"] == 1 and record["error"] == "APIConnectionError"
    assert record["failed"] is False and waits == [BACKOFF_SECONDS, 0]


def test_a_request_that_fails_past_retries_still_leaves_a_record(
    convention_request, tmp_path, monkeypatch
):
    import anthropic

    request, _ = convention_request
    waits = []
    monkeypatch.setattr("time.sleep", waits.append)
    overloaded = _sdk([_sdk_error(529) for _ in range(RETRIES + 1)])
    client = Measured(ClaudeClient(sdk=overloaded), tmp_path / "calls.jsonl")
    with pytest.raises(anthropic.InternalServerError):
        client.complete(SYSTEM, json.dumps(request), schema_for(request))
    [record] = client.calls
    assert record["failed"] is True and record["bad_attempt"] is True
    assert record["retries"] == RETRIES and record["error"] == "InternalServerError"
    assert record["input_tokens"] == 0 and record["request_id"] is None
    assert [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()] == [
        record
    ]
    assert waits == [BACKOFF_SECONDS, 2 * BACKOFF_SECONDS]
    # An error that is neither the SDK's nor a bad answer is a bug: raised at once, no record.

    class Broken:
        def complete(self, system, prompt, schema):
            raise RuntimeError("a bug in the client")

    client = Measured(Broken())
    with pytest.raises(RuntimeError):
        client.complete(SYSTEM, json.dumps(request), schema_for(request))
    assert client.calls == []


def test_a_measured_claude_client_records_its_usage(convention_request):
    request, _ = convention_request
    answer = FakeClient().complete(SYSTEM, json.dumps(request), {})
    content = [SimpleNamespace(type="text", text=answer)]

    def create(**kwargs):
        return SimpleNamespace(
            model="claude-opus-5-5-20260901",
            usage=SimpleNamespace(
                input_tokens=1200,
                output_tokens=300,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
            ),
            stop_reason="end_turn",
            stop_details=None,
            content=content,
            _request_id="req_1",
        )

    sdk = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    client = Measured(ClaudeClient(sdk=sdk))
    client.complete(SYSTEM, json.dumps(request), schema_for(request))
    [record] = client.calls
    assert record["asked"] == MODEL and record["model"] == "claude-opus-5-5-20260901"
    assert (record["input_tokens"], record["output_tokens"]) == (1200, 300)
    assert record["stop_reason"] == "end_turn" and record["request_id"] == "req_1"
    assert record["fallback"] is False and record["retries"] == 0
    assert client.client.last["input_tokens"] == 1200
    # After a hand-over to the fallback model, the record says so.
    content.insert(0, SimpleNamespace(type="fallback"))
    client.complete(SYSTEM, json.dumps(request), schema_for(request))
    assert client.calls[1]["fallback"] is True


def test_claude_client_sends_the_request_and_handles_a_refusal():
    sent = {}

    def create(**kwargs):
        sent.update(kwargs)
        return SimpleNamespace(
            stop_reason=reply.stop_reason,
            stop_details=None,
            content=[SimpleNamespace(type="text", text='{"decisions": []}')],
        )

    reply = SimpleNamespace(stop_reason="end_turn")
    client = ClaudeClient(
        sdk=SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    )
    assert client.complete("the system prompt", "the request", SCHEMA) == '{"decisions": []}'
    assert sent["model"] == "claude-opus-5-5"
    assert sent["fallbacks"] == "default" and sent["betas"] == ["server-side-fallback-2026-07-01"]
    assert sent["output_config"] == {
        "effort": "medium",
        "format": {"type": "json_schema", "schema": SCHEMA},
    }
    assert sent["system"] == "the system prompt"
    assert sent["messages"] == [{"role": "user", "content": "the request"}]
    reply.stop_reason = "refusal"
    with pytest.raises(ModelRefused):
        client.complete("the system prompt", "the request", SCHEMA)


def test_claude_client_keeps_only_the_fallback_models_answer():
    # The first model began, declined and handed over; only the text after the
    # hand-over is the answer.
    content = [
        SimpleNamespace(type="text", text='{"decis'),
        SimpleNamespace(type="fallback"),
        SimpleNamespace(type="text", text='{"decisions": []}'),
    ]
    sdk = SimpleNamespace(
        beta=SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(
                    stop_reason="end_turn", stop_details=None, content=content
                )
            )
        )
    )
    assert (
        ClaudeClient(sdk=sdk).complete("the system prompt", "the request", SCHEMA)
        == '{"decisions": []}'
    )


def _priced(entries, pricing):
    return [replace(entry, pricing=pricing) for entry in entries]


def test_the_request_carries_the_elasticity_and_its_digest_changes_with_it(convention_request):
    request, entries = convention_request
    # The model sees the default mode as "assumed"; the command line keeps "true".
    assert request["elasticity"] == {
        "elasticity": "1.5",
        "mode": "assumed",
        "standard_error": None,
        "prior": None,
        "observations": None,
    }
    assert entries[0].pricing.mode == "true"
    hotel = DEMO.hotel("convention")
    learned = request_for(10, hotel, _priced(entries, Pricing(1.6, "learn", 0.2, 1.0, 1234)))
    assert learned["elasticity"]["elasticity"] == "1.6" and learned["elasticity"]["mode"] == "learn"
    assert learned["elasticity"]["observations"] == "1,234"
    assert request_digest(learned) != request_digest(request)
    assert request_digest(json.loads(json.dumps(request))) == request_digest(request)
    with pytest.raises(ValueError):  # one request, one pricing
        request_for(10, hotel, entries + _priced(entries, Pricing(1.0, "fixed")))


def test_the_template_cites_a_fixed_or_learned_elasticity(convention_request, tmp_path):
    request, entries = convention_request
    hotel = DEMO.hotel("convention")
    [decision] = ask(request, tmp_path / "t.json")["decisions"]
    assert "elasticity" not in decision["reason"]
    learned = request_for(10, hotel, _priced(entries, Pricing(1.62, "learn", 0.21, 1.0, 1234)))
    [decision] = ask(learned, tmp_path / "t.json")["decisions"]
    assert decision["reason"].endswith(
        "The estimates assume an elasticity of 1.62, learned from 1,234 observations with a "
        "standard error of 0.21 (prior 1)."
    )
    fixed = request_for(10, hotel, _priced(entries, Pricing(1.0, "fixed")))
    [decision] = ask(fixed, tmp_path / "t.json")["decisions"]
    assert decision["reason"].endswith("The estimates assume a fixed elasticity of 1.")


def test_the_three_values_reach_the_model_request(day10, tmp_path):
    _, table = day10
    hotel = DEMO.hotel("convention")
    cautious = Pricing(1.5, "learn", 0.3, 1.0, 2000, cautious=True)
    plain = Pricing(1.5, "learn", 0.3, 1.0, 2000)
    convention = [f for f in flags(10, table) if f.hotel == "convention"]
    request = request_for(10, hotel, [entry_for(10, f, table, cautious) for f in convention])
    other = request_for(10, hotel, [entry_for(10, f, table, plain) for f in convention])
    assert request["elasticity"]["cautious"] is True
    assert request["elasticity"]["band"] == "1.2 to 1.8"
    [entry], [plain_entry] = request["entries"], other["entries"]
    for weekday, plain_weekday in zip(entry["by_day_of_week"], plain_entry["by_day_of_week"]):
        for candidate, plain_candidate in zip(weekday["candidates"], plain_weekday["candidates"]):
            band = candidate["estimated_contribution_band"]
            assert set(band) == {"at_low_elasticity", "at_high_elasticity"}
            assert band["at_low_elasticity"].startswith("$")
            versus = candidate["versus_hold_band"]
            assert set(versus) == {"at_low_elasticity", "at_high_elasticity"}
            assert all(value.endswith("holding") for value in versus.values())
            assert candidate["estimated_contribution"] == plain_candidate["estimated_contribution"]
            assert "estimated_contribution_band" not in plain_candidate
            assert "band_verdict" not in plain_candidate
    # The rule's verdict is stated for every candidate but hold, and it says "beats" exactly where
    # the rule passed the candidate, so the model copies the result instead of inferring it.
    [queued] = [entry_for(10, f, table, cautious) for f in convention]
    for group, weekday in zip(queued.weekdays, entry["by_day_of_week"]):
        for candidate, shown in zip(group.candidates, weekday["candidates"]):
            if candidate is group.hold:
                assert "band_verdict" not in shown
                continue
            passes = shown["band_verdict"] == "beats holding at both ends of the band"
            assert passes == group.replaces_hold(candidate)
            assert shown["band_verdict"].startswith(("beats holding", "does not beat holding"))
    assert "cautious" not in other["elasticity"]
    assert request_digest(request) != request_digest(other)
    [decision] = ask(request, tmp_path / "t.json")["decisions"]
    assert decision["reason"].endswith(
        "Each change also beats holding with the elasticity at both ends of the band 1.2 to 1.8."
    )


def test_the_system_prompt_tells_the_model_how_to_choose_and_write():
    for phrase in (
        'choose the plan to recommend it, or "hold" to decline it',
        'Write as "we"',
        "State only what the entry shows",
        "make no claim about price sensitivity or risk",
        "Copy these phrases whole",
        "do not quote one end of a range on its own",
        '"more than holding" may be written once',
        "Write an event's name in lower case",
        '"assumed" is a value the agent was given',
        "beats holding at both ends",
        "band_verdict states that rule's result",
    ):
        assert phrase in SYSTEM, phrase
