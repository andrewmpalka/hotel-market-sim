"""Module 7, model.py: the request, the cached answer, the template and the Claude client."""

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from hotel_market.customer import demo
from hotel_market.detect import flags
from hotel_market.model import (
    CacheMiss,
    ClaudeClient,
    ModelRefused,
    StaleCache,
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
    """Stands in for the model: accepts each plan, or always gives one choice."""

    def __init__(self, choice=None):
        self.choice = choice
        self.calls = []

    def complete(self, system, prompt, schema):
        request = json.loads(prompt)
        self.calls.append(request)
        return json.dumps(
            {
                "decisions": [
                    {
                        "id": e["id"],
                        "choice": self.choice or e["plan"],
                        "reason": f"Fake reason for {e['id']}.",
                    }
                    for e in request["entries"]
                ]
            }
        )


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
    decision = schema_for(request)["properties"]["decisions"]["items"]["properties"]
    assert decision["id"]["enum"] == [entry.id]
    assert decision["choice"]["enum"] == sorted([entry.plan, HOLD])


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
    assert "cautious" not in other["elasticity"]
    assert request_digest(request) != request_digest(other)
    [decision] = ask(request, tmp_path / "t.json")["decisions"]
    assert decision["reason"].endswith(
        "Each change also beats holding with the elasticity at both ends of the band 1.2 to 1.8."
    )
