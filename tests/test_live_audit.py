"""scripts/live_audit.py: the audit of the model's reasons against their requests."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

from hotel_market.cli import run
from hotel_market.customer import demo
from hotel_market.detect import flags
from hotel_market.model import MODEL, request_for, template_decisions
from hotel_market.plan import HOLD, entry_for

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("live_audit", ROOT / "scripts" / "live_audit.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit = _load()


def test_a_range_in_a_reason_is_read_as_its_two_ends():
    assert audit.figures_in("about 12–14% below the median") == ["12%", "14%"]
    assert audit.figures_in("$217 to 220, stays 45-48") == ["$217", "$220", "45", "48"]
    assert audit.figures_in("our rate sits 14.6% below the median") == ["14.6%"]
    assert audit.figures_in("a sign of the model's own: -14.6% below") == ["-14.6%"]
    # Two figures with different units are not a range: each stays as written.
    assert audit.figures_in("raising 10% to $242 on Thu") == ["10%", "$242"]
    assert audit.figures_in("rose +15.0% to $217–$220") == ["+15.0%", "$217", "$220"]
    # Punctuation after a figure is not part of it; thousands commas are.
    assert audit.figures_in("1,188 rooms, $8,050, and 12674 rooms.") == ["1,188", "$8,050", "12674"]


def test_the_requests_display_strings_and_whole_numbers_are_what_a_reason_may_quote(day10):
    _, table = day10
    hotel = demo().hotel("convention")
    entries = [entry_for(10, f, table) for f in flags(10, table) if f.hotel == "convention"]
    request = request_for(10, hotel, entries)
    phrases, tokens = audit.quotable(request)
    assert {
        "the same as holding",
        "13.4% to 14.6% below the median",
        "up 13.7% to 18.8%",
    } <= phrases
    assert {"955", "$220", "$242", "45 to 48", "1.5", "$180 less than holding"} <= phrases
    assert {"10", "5%", "10%", "45", "48"} <= tokens  # the day, and the figures inside names
    assert "8052.54" not in phrases | tokens  # raw values are not for quoting
    # A phrase must appear whole: a sign, a cut or one end of a range on its own is not a
    # quotation.
    assert audit.appears("14.6%", "we sit 13.4% to 14.6% below the median", phrases, tokens)
    assert not audit.appears("14.6%", "our rate sits 14.6% below the median", phrases, tokens)
    assert not audit.appears("-14.6%", "we sit 13.4% to -14.6% below the median", phrases, tokens)
    assert not audit.appears("$180", "the plan loses $180 in contribution", phrases, tokens)
    assert audit.appears("10%", "we recommend raising 10% to $242", phrases, tokens)
    # The template copies the display strings whole, so every figure it quotes is known.
    [decision] = template_decisions(request)
    reason = decision["reason"]
    assert all(audit.appears(f, reason, phrases, tokens) for f in audit.figures_in(reason))
    assert audit.sentences_without_figures(reason, phrases, tokens) == []


def test_a_sentence_that_lists_several_gains_may_write_more_than_holding_once():
    phrases = {"$280 more than holding", "$60 more than holding", "$340 more than holding"}
    phrases |= {"$120 less than holding"}
    listed = "Tuesday adds $280 and Wednesday $60, $340 more than holding in all."
    assert audit.stray_figures(listed, phrases, set()) == []
    assert audit.sentences_without_figures(listed, phrases, set()) == []
    # Without the phrase in the sentence, the bare gains are the model's own figures.
    assert audit.stray_figures("Tuesday adds $280 and Wednesday $60.", phrases, set()) == [
        "$280",
        "$60",
    ]
    # The phrase vouches only for a gain the request holds as "more than holding".
    assert audit.stray_figures("Monday is $120, more than holding.", phrases, set()) == ["$120"]
    # It vouches within its own sentence, not the whole reason.
    assert audit.stray_figures(
        "The plan is $340 more than holding. We like the $340.", phrases, set()
    ) == ["$340"]


def test_sentences_without_a_request_figure_are_listed():
    phrases, tokens = {"$8,050 more than holding", "1,188"}, set()
    reason = (
        "We recommend the plan. It adds $8,050 more than holding on 1,188 rooms. "
        "Demand looks strong to us. It adds $8,050 in contribution."
    )
    assert audit.sentences_without_figures(reason, phrases, tokens) == [
        "We recommend the plan.",
        "Demand looks strong to us.",
        "It adds $8,050 in contribution.",
    ]


def test_the_audit_reads_a_cache_and_reports_what_is_not_in_the_request(tmp_path, capsys, day10):
    _, table = day10
    hotel = demo().hotel("convention")
    entries = [entry_for(10, f, table) for f in flags(10, table) if f.hotel == "convention"]
    request = request_for(10, hotel, entries)
    [decision] = template_decisions(request)
    decision["reason"] += " Risk looks low, and 7 days of hold follow."
    cache = tmp_path / "cache" / "seed7"
    cache.mkdir(parents=True)
    (cache / "day010_convention.json").write_text(
        json.dumps(
            {"request_digest": "x", "request": request, "source": "model", "decisions": [decision]}
        )
    )
    audit.audit(cache)
    out = capsys.readouterr().out
    assert "1 model calls, 1 entries decided, 0 declined." in out
    assert "1 figures in reasons do not appear in their request." in out
    assert "Not in the request: 7" in out
    assert "No request figure: Risk looks low, and 7 days of hold follow." in out
    with pytest.raises(SystemExit):
        audit.audit(tmp_path / "nothing")


def test_the_audit_finds_a_bench_arms_cache_and_its_calls(tmp_path, capsys, day10):
    # A bench arm in a mismatched mode keeps its cache in the mode's folder and its calls
    # inside it; --elasticity names the folder the way the agent does.
    _, table = day10
    hotel = demo().hotel("convention")
    entries = [entry_for(10, f, table) for f in flags(10, table) if f.hotel == "convention"]
    request = request_for(10, hotel, entries)
    [decision] = template_decisions(request)
    decision["choice"] = HOLD
    arm = tmp_path / "cache" / "seed7-fixed-1"
    arm.mkdir(parents=True)
    record = {"request_digest": "x", "request": request, "source": "model", "decisions": [decision]}
    (arm / "day010_convention.json").write_text(json.dumps(record))
    call = {
        "input_tokens": 1000,
        "output_tokens": 500,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "seconds": 4.0,
        "stop_reason": "end_turn",
        "model": "claude-opus-5-5",
        "fallback": False,
    }
    (arm / "calls.jsonl").write_text(json.dumps(call) + "\n")
    audit.main(["--audit-only", "--seed", "7", "--elasticity", "fixed:1.0", "--out", str(tmp_path)])
    out = capsys.readouterr().out
    assert "1 model calls, 1 entries decided, 1 declined." in out
    assert "declined: day 10, Downtown convention hotel, entry 45-48" in out
    # The cost comes from the bench's price table for the default model: $4 in, $20 out.
    assert "Cost at list prices ($4.00 in, $20.00 out per million tokens): $0.01." in out
    with pytest.raises(SystemExit):  # the default mode's folder is not there
        audit.main(["--audit-only", "--seed", "7", "--out", str(tmp_path)])


def test_the_audit_finds_a_cautious_reacting_arms_cache(tmp_path, capsys, day10):
    # A reacting arm at a market elasticity keeps its cache under cache/react/market-E/, and the
    # cautious rule joins the folder name; the three options name the folder the way the bench does.
    _, table = day10
    hotel = demo().hotel("convention")
    entries = [entry_for(10, f, table) for f in flags(10, table) if f.hotel == "convention"]
    request = request_for(10, hotel, entries)
    [decision] = template_decisions(request)
    decision["choice"] = HOLD
    arm = tmp_path / "cache" / "react" / "market-0.5" / "seed7-learn-1-cautious"
    arm.mkdir(parents=True)
    record = {"request_digest": "x", "request": request, "source": "model", "decisions": [decision]}
    (arm / "day010_convention.json").write_text(json.dumps(record))
    options = ["--elasticity", "learn:1.0", "--cautious", "--react", "--market-elasticity", "0.5"]
    audit.main(["--audit-only", "--seed", "7", *options, "--out", str(tmp_path)])
    out = capsys.readouterr().out
    assert "1 model calls, 1 entries decided, 1 declined." in out
    with pytest.raises(SystemExit):  # the same arm with no reaction has no folder
        audit.main(["--audit-only", "--seed", "7", *options[:3], "--out", str(tmp_path)])


# ---- the recorded live run ------------------------------------------------------

FIXTURE = ROOT / "tests" / "fixtures" / "live_seed7"


class NoCalls:
    def complete(self, system, prompt, schema):
        raise AssertionError("the model was called: the recorded run does not cover this request")


def test_the_recorded_live_run_of_seed_7_passes_the_audit(capsys):
    """One live run of seed 7 with claude-opus-5-5 is kept as a fixture. It holds the seven requests
    and answers and the measurements of the calls. The audit on them finds no declined plan, no
    figure outside its request and no sentence without a request figure. This is the evidence
    that UNK-01, UNK-02 and UNK-09 in kg/ rest on."""
    audit.audit(FIXTURE)
    out = capsys.readouterr().out
    assert "7 model calls, 7 entries decided, 0 declined." in out
    assert "0 figures in reasons do not appear in their request." in out
    assert "0 sentences hold no figure from the request." in out
    calls = [json.loads(line) for line in (FIXTURE / "calls.jsonl").read_text().splitlines()]
    assert len(calls) == 7
    assert {c["stop_reason"] for c in calls} == {"end_turn"}
    assert {c["model"] for c in calls} == {"claude-opus-5-5"}
    assert not any(c["fallback"] for c in calls)


@pytest.mark.xfail(reason="world v2; re-record with make live-audit SEED=7", strict=True)
def test_the_recorded_live_run_replays_without_a_key_and_gives_28818(tmp_path):
    """With the fixture as the cache, the run of seed 7 reads every answer from it. It never calls
    the model, and it ends where the live run ended. A change to the request makes the fixture
    stale. This test then says to record a live run again."""
    shutil.copytree(FIXTURE, tmp_path / "cache" / "seed7", ignore=shutil.ignore_patterns("*.jsonl"))
    fixed, books, agent = run(7, tmp_path / "decisions.jsonl", tmp_path / "cache", NoCalls())
    change = sum(books.contribution(h) - fixed.contribution(h) for h in demo().hotels)
    assert change == pytest.approx(28818, abs=1)
    # The default model in the default mode resolves to cache/seed7, and the fixture's
    # records, written before the record named its model, read back as they are.
    assert agent.model == MODEL and agent.cache_dir == tmp_path / "cache" / "seed7"
    assert all("model" not in json.loads(p.read_text()) for p in FIXTURE.glob("day*_*.json"))
    decided = [e for e in agent.entries if e.queued]
    assert len(decided) == 7 and all(e.reason_source == "model" for e in decided)
    assert all(e.action != HOLD for e in decided)
    recorded = {
        (r["request"]["day"], r["request"]["hotel"]["name"], d["id"]): d["reason"]
        for p in sorted(FIXTURE.glob("day*_*.json"))
        for r in [json.loads(p.read_text())]
        for d in r["decisions"]
    }
    names = {hotel.key: hotel.name for hotel in demo().hotels}
    assert {(e.day, names[e.hotel], e.id): e.reason for e in decided} == recorded
