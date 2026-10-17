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
        "10.6% to 13.7% below the median",
        "up 10.3% to 17.1%",
    } <= phrases
    assert {"992", "$220", "$242", "45 to 48", "1.5", "$140 less than holding"} <= phrases
    assert {"10", "5%", "10%", "45", "48"} <= tokens  # the day, and the figures inside names
    assert "8052.54" not in phrases | tokens  # raw values are not for quoting
    # A phrase must appear whole: a sign, a cut or one end of a range on its own is not a
    # quotation.
    assert audit.appears("13.7%", "we sit 10.6% to 13.7% below the median", phrases, tokens)
    assert not audit.appears("13.7%", "our rate sits 13.7% below the median", phrases, tokens)
    assert not audit.appears("-13.7%", "we sit 10.6% to -13.7% below the median", phrases, tokens)
    assert not audit.appears("$140", "the plan loses $140 in contribution", phrases, tokens)
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
    """One live run of seed 7 with claude-opus-5-5 is kept as a fixture. It holds the four requests
    and answers and the measurements of the calls. The audit on them finds no declined plan. It
    lists five figures it cannot match to a request phrase, three per-day gains the request holds
    as "more than holding" phrases and the day and the rooms of an earlier change the reason
    paraphrased, and four sentences without a request figure. This is the evidence that UNK-01,
    UNK-02 and UNK-09 in kg/ rest on."""
    audit.audit(FIXTURE)
    out = capsys.readouterr().out
    assert "4 model calls, 6 entries decided, 0 declined." in out
    assert "5 figures in reasons do not appear in their request." in out
    assert "day020_lifestyle.json entry 75-75: 18" in out
    assert "4 sentences hold no figure from the request." in out
    calls = [json.loads(line) for line in (FIXTURE / "calls.jsonl").read_text().splitlines()]
    assert len(calls) == 4
    assert {c["stop_reason"] for c in calls} == {"end_turn"}
    assert {c["model"] for c in calls} == {"claude-opus-5-5"}
    assert not any(c["fallback"] for c in calls)


def test_the_recorded_live_run_replays_without_a_key_and_gives_19796(tmp_path):
    """With the fixture as the cache, the run of seed 7 reads every answer from it. It never calls
    the model, and it ends where the live run ended. A change to the request makes the fixture
    stale. This test then says to record a live run again."""
    shutil.copytree(FIXTURE, tmp_path / "cache" / "seed7", ignore=shutil.ignore_patterns("*.jsonl"))
    fixed, books, agent = run(7, tmp_path / "decisions.jsonl", tmp_path / "cache", NoCalls())
    change = sum(books.contribution(h) - fixed.contribution(h) for h in demo().hotels)
    assert change == pytest.approx(19796, abs=1)
    # The default model in the default mode resolves to cache/seed7, and each record names it.
    assert agent.model == MODEL and agent.cache_dir == tmp_path / "cache" / "seed7"
    assert all(json.loads(p.read_text())["model"] == MODEL for p in FIXTURE.glob("day*_*.json"))
    decided = [e for e in agent.entries if e.queued]
    assert len(decided) == 6 and all(e.reason_source == "model" for e in decided)
    assert all(e.action != HOLD for e in decided)
    recorded = {
        (r["request"]["day"], r["request"]["hotel"]["name"], d["id"]): d["reason"]
        for p in sorted(FIXTURE.glob("day*_*.json"))
        for r in [json.loads(p.read_text())]
        for d in r["decisions"]
    }
    names = {hotel.key: hotel.name for hotel in demo().hotels}
    assert {(e.day, names[e.hotel], e.id): e.reason for e in decided} == recorded


FIXTURE_INTRADAY = ROOT / "tests" / "fixtures" / "live_seed7_intraday"


def test_the_recorded_intraday_run_of_seed_7_passes_the_audit(capsys):
    """One live run of seed 7 on the intraday market at four ticks a day, with claude-opus-5-5,
    is kept as a second fixture, its records named by their tick. The audit on them finds no
    declined plan. It lists eleven figures it cannot match to a request phrase, per-day gains the
    request holds as "more than holding" phrases and the days and rooms of earlier changes the
    reasons paraphrased, and five sentences without a request figure."""
    audit.audit(FIXTURE_INTRADAY)
    out = capsys.readouterr().out
    assert "Day 25, tick 2, Lifestyle hotel" in out
    assert "10 model calls, 13 entries decided, 0 declined." in out
    assert "11 figures in reasons do not appear in their request." in out
    assert "day020-t1_lifestyle.json entry 75-75: 18" in out
    assert "5 sentences hold no figure from the request." in out
    names = sorted(p.name for p in FIXTURE_INTRADAY.glob("day*_*.json"))
    assert len(names) == 10 and all("-t" in name for name in names)
    assert "day025-t2_lifestyle.json" in names and "day025-t2_full-service.json" in names
    assert all(json.loads(p.read_text())["model"] == MODEL for p in FIXTURE_INTRADAY.glob("*.json"))
    lines = (FIXTURE_INTRADAY / "calls.jsonl").read_text().splitlines()
    calls = [json.loads(line) for line in lines]
    assert len(calls) == 10
    assert {c["stop_reason"] for c in calls} == {"end_turn"}
    assert {c["model"] for c in calls} == {"claude-opus-5-5"}
    assert not any(c["fallback"] for c in calls)


def test_record_fixture_copies_the_cache_records_and_the_calls_into_the_fixture(tmp_path):
    cache = tmp_path / "cache" / "seed7"
    cache.mkdir(parents=True)
    for name in ("day010_convention.json", "day020_airport.json"):
        (cache / name).write_text('{"record": "%s"}' % name)
    (cache / "notes.txt").write_text("not a record")
    calls = cache / "calls.jsonl"
    calls.write_text('{"call": 1}\n')
    target = tmp_path / "fixture"
    target.mkdir()
    (target / "day034_convention.json").write_text("stale")  # an earlier run's record goes
    written = audit.record_fixture(cache, calls, target)
    assert sorted(p.name for p in written) == [
        "calls.jsonl",
        "day010_convention.json",
        "day020_airport.json",
    ]
    assert sorted(p.name for p in target.iterdir()) == [
        "calls.jsonl",
        "day010_convention.json",
        "day020_airport.json",
    ]
    assert (target / "day020_airport.json").read_text() == '{"record": "day020_airport.json"}'
    assert (target / "calls.jsonl").read_text() == '{"call": 1}\n'
    assert audit.FIXTURE.name == "live_seed7" and audit.FIXTURE.parent.name == "fixtures"
    assert audit.fixture() == audit.FIXTURE and audit.fixture(4).name == "live_seed7_intraday"
    with pytest.raises(SystemExit, match="no cache records"):
        audit.record_fixture(tmp_path / "empty", calls, target)


def test_record_fixture_replays_the_run_from_its_cache_and_keeps_its_calls(
    tmp_path, monkeypatch, capsys, day10
):
    # A second live run would delete the first run's calls.jsonl, so --record-fixture audits
    # the cache the way --audit-only does and copies what the live run left.
    _, table = day10
    hotel = demo().hotel("convention")
    entries = [entry_for(10, f, table) for f in flags(10, table) if f.hotel == "convention"]
    request = request_for(10, hotel, entries)
    cache = tmp_path / "cache" / "seed7"
    cache.mkdir(parents=True)
    record = {"request_digest": "x", "request": request, "source": "model"}
    record["decisions"] = template_decisions(request)
    (cache / "day010_convention.json").write_text(json.dumps(record))
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
    (tmp_path / "calls.jsonl").write_text(json.dumps(call) + "\n")
    monkeypatch.setattr(audit, "FIXTURE", tmp_path / "fixture")
    monkeypatch.setattr(audit, "live_run", lambda *a, **k: pytest.fail("the model ran again"))
    audit.main(["--seed", "7", "--record-fixture", "--out", str(tmp_path)])
    assert "1 model calls, 1 entries decided, 0 declined." in capsys.readouterr().out
    assert sorted(p.name for p in (tmp_path / "fixture").iterdir()) == [
        "calls.jsonl",
        "day010_convention.json",
    ]
    assert (tmp_path / "calls.jsonl").exists()


def test_record_fixture_at_four_ticks_reads_the_markets_cache_and_names_the_intraday_folder(
    tmp_path, monkeypatch, capsys, day10
):
    """With --customer and --ticks the audit reads the cache folder the agent names for that
    market and clock, whose records carry their tick, prints the tick with the day, and copies
    into the daily fixture's name with _intraday added."""
    _, table = day10
    hotel = demo().hotel("convention")
    entries = [entry_for(10, f, table) for f in flags(10, table) if f.hotel == "convention"]
    request = request_for(10, hotel, entries)
    cache = tmp_path / "cache" / "demo-intraday" / "seed7-ticks4"
    cache.mkdir(parents=True)
    record = {"request_digest": "x", "request": request, "source": "model"}
    record["decisions"] = template_decisions(request)
    (cache / "day010-t2_convention.json").write_text(json.dumps(record))
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
    (tmp_path / "calls.jsonl").write_text(json.dumps(call) + "\n")
    monkeypatch.setattr(audit, "FIXTURE", tmp_path / "fixture")
    monkeypatch.setattr(audit, "live_run", lambda *a, **k: pytest.fail("the model ran again"))
    market = ROOT / "customers" / "demo-intraday.toml"
    audit.main(
        ["--seed", "7", "--record-fixture", "--out", str(tmp_path)]
        + ["--customer", str(market), "--ticks", "4"]
    )
    out = capsys.readouterr().out
    assert "Day 10, tick 2, Downtown convention hotel" in out
    assert "1 model calls, 1 entries decided, 0 declined." in out
    assert sorted(p.name for p in (tmp_path / "fixture_intraday").iterdir()) == [
        "calls.jsonl",
        "day010-t2_convention.json",
    ]
    assert not (tmp_path / "fixture").exists()
