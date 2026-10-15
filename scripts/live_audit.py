"""live_audit.py

One seed with the live model, measured and audited.

    python scripts/live_audit.py --seed 7              # run live, then audit (needs an API key)
    python scripts/live_audit.py --seed 7 --audit-only # audit the cache a live run left
    python scripts/live_audit.py --seed 7 --audit-only --elasticity fixed:1.0
                                                       # audit a bench arm's cache (bench.py)
    python scripts/live_audit.py --seed 7 --record-fixture
                                                       # audit the cache a live run left, then
                                                       # copy its records and calls.jsonl into
                                                       # tests/fixtures/live_seed7

The run is the hotel-market command's run for the seed in the given mode. The default mode
applies unless --elasticity says otherwise. It makes both simulations, decisions.jsonl and the
cache. A Measured client (model.py) records each call's tokens, time, stop reason and answering
model to calls.jsonl.

The audit then reads the cache and prints every reason the model wrote, every plan it declined and
every figure in a reason that is not in the request.

Every figure in the request is a display string written by code. Examples are "$8,050 more than
holding", "10.7% to 14.6% below the median" and "1,188". The model is told to copy each one
whole, so the audit matches phrases sentence by sentence.

A figure in a reason counts as quoted in three cases: a display string that holds the figure and
appears whole in the same sentence, a whole number that the request holds as it is, such as a day,
and a bare dollar figure in a sentence with "more than holding". A figure inside a name, such as
"raise 5%", also counts.

The bare dollar figure counts if the request holds "<figure> more than holding". The prompt lets
that phrase be written once for several gains.

A range written as "12–14%" or "$217 to $220" counts as its two ends, each with the shared unit.
The audit lists every other figure with its reason for a person to judge. These include a sign or
a rounding of the model's own and one end of a range on its own. A sum, a difference or a figure
from the model's own knowledge also shows up there. For each reason the audit also prints every
sentence that holds no figure from the request. A person can then read what the model said on its
own account.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import time
from dataclasses import replace
from pathlib import Path

from hotel_market.agent import TRUE_MODE, Agent, ElasticityMode
from hotel_market.bench import PRICES
from hotel_market.cli import cache_root, run, summary
from hotel_market.demand import DEMAND_BIAS, MARKET_ELASTICITY
from hotel_market.model import HOLD, MODEL, ClaudeClient, Measured

# The default model's list prices, dollars per million tokens, from the bench's price table;
# the cost line is an estimate from them, and the token counts are printed for any other price.
INPUT_PRICE, OUTPUT_PRICE = PRICES[MODEL]

# A figure as written: an optional sign and dollar sign, digits with thousands commas,
# an optional decimal part, an optional percent sign. A comma after the last digit is
# punctuation, not part of the figure.
_FIGURE = r"[-+]?\$?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?"
FIGURE = re.compile(_FIGURE)
# "12–14%", "$217 to $220", "45-48": two figures that share a sign and a unit.
SPAN = re.compile(rf"(?P<a>{_FIGURE})\s*(?:–|—|-|to)\s*(?P<b>{_FIGURE})")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def live_run(seed: int, out_dir: Path, mode: ElasticityMode = TRUE_MODE) -> list[dict]:
    """Seed `seed` with the live model in `mode`, writing decisions.jsonl, cache/ and
    calls.jsonl under out_dir. A Measured client (model.py) records each call; the file holds
    this run's calls only. Returns the calls' measurements."""
    calls_path = out_dir / "calls.jsonl"
    if calls_path.exists():
        calls_path.unlink()
    client = Measured(ClaudeClient(), calls_path)
    start = time.perf_counter()
    fixed, books, agent = run(seed, out_dir / "decisions.jsonl", out_dir / "cache", client, mode)
    total = time.perf_counter() - start
    print(summary(seed, fixed, books, agent))
    print()
    print(f"{len(client.calls)} model calls in a run of {total:.0f} s, both simulations included.")
    return client.calls


def audit(cache_dir: Path) -> None:
    """Every reason, every declined plan, and every number not in its request."""
    files = sorted(cache_dir.glob("day*_*.json"))
    if not files:
        raise SystemExit(f"no cache files under {cache_dir}; run without --audit-only first")
    declined, stray, unfigured = [], [], []
    for path in files:
        record = json.loads(path.read_text())
        request, decisions = record["request"], record["decisions"]
        if record.get("source") != "model":
            print(f"{path.name}: written by {record.get('source')}, not the model; skipped")
            continue
        entries = {entry["id"]: entry for entry in request["entries"]}
        phrases, tokens = quotable(request)
        print(f"\nDay {request['day']}, {request['hotel']['name']}")
        for decision in decisions:
            entry = entries[decision["id"]]
            action = "declined" if decision["choice"] == HOLD else "accepted"
            print(
                f"  Entry {decision['id']} (stays {entry['stay_dates']}, "
                f"{', '.join(entry['what_changed'])}): plan {entry['plan']!r}, "
                f"worth {entry['value_at_stake']}; {action}"
            )
            print(f"    Reason: {decision['reason']}")
            if decision["choice"] == HOLD:
                declined.append(
                    (request["day"], request["hotel"]["name"], decision["id"], entry["plan"])
                )
            for text in stray_figures(decision["reason"], phrases, tokens):
                stray.append((path.name, decision["id"], text, decision["reason"]))
                print(f"    Not in the request: {text}")
            for sentence in sentences_without_figures(decision["reason"], phrases, tokens):
                unfigured.append((path.name, decision["id"], sentence))
                print(f"    No request figure: {sentence}")
    decided = sum(len(json.loads(p.read_text())["decisions"]) for p in files)
    print(f"\n{len(files)} model calls, {decided} entries decided, {len(declined)} declined.")
    for day, hotel, entry_id, plan in declined:
        print(f"  declined: day {day}, {hotel}, entry {entry_id}, plan {plan!r}")
    print(f"{len(stray)} figures in reasons do not appear in their request.")
    for file, entry_id, text, reason in stray:
        print(f"  {file} entry {entry_id}: {text}")
    print(f"{len(unfigured)} sentences hold no figure from the request.")


def report_calls(calls: list[dict]) -> None:
    if not calls:
        return
    inputs = [c["input_tokens"] for c in calls]
    outputs = [c["output_tokens"] for c in calls]
    seconds = [c["seconds"] for c in calls]
    cost = (sum(inputs) * INPUT_PRICE + sum(outputs) * OUTPUT_PRICE) / 1_000_000
    print(
        f"Tokens: {sum(inputs):,} in ({min(inputs):,} to {max(inputs):,} per call), "
        f"{sum(outputs):,} out ({min(outputs):,} to {max(outputs):,}); cache reads "
        f"{sum(c['cache_read_input_tokens'] for c in calls):,}, cache writes "
        f"{sum(c['cache_creation_input_tokens'] for c in calls):,}."
    )
    print(
        f"Time in the model: {sum(seconds):.0f} s ({min(seconds):.1f} to {max(seconds):.1f} s "
        f"per call, median {statistics.median(seconds):.1f} s)."
    )
    print(
        f"Cost at list prices (${INPUT_PRICE:.2f} in, ${OUTPUT_PRICE:.2f} out per million "
        f"tokens): ${cost:.2f}."
    )
    stops = sorted({str(c.get("stop_reason")) for c in calls})  # None on a failed call
    models = sorted({c["model"] for c in calls})
    print(
        f"Stop reasons: {', '.join(stops)}. Models that answered: {', '.join(models)}. "
        f"Fallbacks: {sum(c['fallback'] for c in calls)}."
    )


# ---- figures ----------------------------------------------------------------


# The request's strings under these keys are names, not figures: a figure inside one,
# such as the "5%" of "raise 5%", may be quoted on its own.
NAME_KEYS = {"name", "plan", "options", "id", "what_changed", "new_event", "mode", "day", "best"}


def quotable(request: dict) -> tuple[set[str], set[str]]:
    """What a reason may quote from its request. The phrases are the display strings of its figures,
    which must appear whole. The tokens may stand alone. They are the whole numbers the request
    holds as they are, such as a day. The figures inside names also count.
    """
    phrases: set[str] = set()
    tokens: set[str] = set()

    def walk(value, key=None) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, int):
            tokens.add(str(value))
        elif isinstance(value, str):
            if key in NAME_KEYS:
                tokens.update(figures_in(value))
            else:
                phrases.add(value)
        elif isinstance(value, dict):
            for inner_key, item in value.items():
                walk(item, inner_key)
        elif isinstance(value, list):
            for item in value:
                walk(item, key)

    walk(request)
    return phrases, tokens


# The prompt lets a sentence that lists several gains write this once for all of them.
GAINS = "more than holding"


def appears(figure: str, sentence: str, phrases: set[str], tokens: set[str]) -> bool:
    """Whether a figure written in a sentence is quoted from the request. A token may stand alone. A
    figure of a display string counts when the string appears whole in the sentence. The "7" of "7
    days" is not the "7" inside "10.7% below the median". A bare dollar figure counts in a sentence
    with "more than holding", if the request holds "<figure> more than holding"."""
    if figure in tokens:
        return True
    if any(figure in figures_in(phrase) and phrase in sentence for phrase in phrases):
        return True
    return figure.startswith("$") and GAINS in sentence and f"{figure} {GAINS}" in phrases


def stray_figures(reason: str, phrases: set[str], tokens: set[str]) -> list[str]:
    """The figures of a reason that are not quoted from the request, sentence by sentence."""
    return [
        figure
        for sentence in sentences(reason)
        for figure in figures_in(sentence)
        if not appears(figure, sentence, phrases, tokens)
    ]


def sentences(reason: str) -> list[str]:
    return [sentence for sentence in SENTENCE_END.split(reason.strip()) if sentence]


def figures_in(text: str) -> list[str]:
    """The figures written in a reason, a range such as "12–14%" read as its two ends."""
    return [m for m in FIGURE.findall(SPAN.sub(_expand_span, text)) if any(c.isdigit() for c in m)]


def _expand_span(match: re.Match) -> str:
    """ "12–14%" becomes "12% 14%", and "$217 to 220" becomes "$217 $220". Two figures
    with different units, as in "raising 10% to $242", are not a range and stay as
    written."""
    a, b = match.group("a"), match.group("b")
    dollars = ("$" in a, "$" in b)
    percents = (a.endswith("%"), b.endswith("%"))
    if any(dollars) and any(percents):
        return match.group(0)
    dollar = "$" if any(dollars) else ""
    unit = "%" if any(percents) else ""
    return f"{dollar}{a.strip('$%')}{unit} {dollar}{b.strip('$%')}{unit}"


def sentences_without_figures(reason: str, phrases: set[str], tokens: set[str]) -> list[str]:
    """The sentences of a reason that quote nothing from the request."""
    return [
        sentence
        for sentence in sentences(reason)
        if not any(appears(figure, sentence, phrases, tokens) for figure in figures_in(sentence))
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("."),
        help="where decisions.jsonl, cache/ and calls.jsonl go",
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        help="audit an existing cache without calling the model",
    )
    parser.add_argument(
        "--elasticity",
        type=ElasticityMode.parse,
        default=TRUE_MODE,
        metavar="MODE",
        help="the arm's mode, true (the default), fixed:X or learn:X; it names the cache folder",
    )
    parser.add_argument(
        "--cautious", action="store_true", help="the arm ran the cautious rule (learn only)"
    )
    parser.add_argument("--react", action="store_true", help="the arm ran with --react")
    parser.add_argument(
        "--record-fixture",
        action="store_true",
        help="audit the cache a live run left, as --audit-only does, then copy its records and "
        "calls.jsonl into tests/fixtures/live_seed7, replacing the recorded run the tests replay",
    )
    parser.add_argument(
        "--market-elasticity",
        dest="market_elasticity",
        type=float,
        default=MARKET_ELASTICITY,
        metavar="E",
        help="the arm's market elasticity, which names its cache folder",
    )
    args = parser.parse_args(argv)
    if args.record_fixture:  # a second live run would delete the first run's calls.jsonl
        args.audit_only = True
    if args.cautious:
        args.elasticity = replace(args.elasticity, cautious=True)
    # The arm's folder, as the command and the agent name it; a bench arm keeps its calls.jsonl
    # inside it.
    root = cache_root(args.out / "cache", DEMAND_BIAS, args.react, args.market_elasticity)
    cache_dir = Agent(args.seed, root, elasticity=args.elasticity).cache_dir
    calls_file = next(
        (p for p in (cache_dir / "calls.jsonl", args.out / "calls.jsonl") if p.exists()), None
    )
    calls: list[dict] = []
    if not args.audit_only:
        calls = live_run(args.seed, args.out, args.elasticity)
    elif calls_file is not None:
        calls = [json.loads(line) for line in calls_file.read_text().splitlines() if line]
    audit(cache_dir)
    print()
    report_calls(calls)
    if args.record_fixture:
        record_fixture(cache_dir, calls_file or args.out / "calls.jsonl", FIXTURE)


FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "live_seed7"


def record_fixture(cache_dir: Path, calls_file: Path, target: Path = FIXTURE) -> list[Path]:
    """Copy the arm's cache records and its calls.jsonl into the fixture folder, replacing what was
    there, so the tests replay this run. Returns the files written."""
    records = sorted(cache_dir.glob("day*_*.json"))
    if not records:
        raise SystemExit(f"no cache records under {cache_dir}; nothing to record")
    if not calls_file.exists():
        raise SystemExit(f"{calls_file} is missing; the run did not record its calls")
    target.mkdir(parents=True, exist_ok=True)
    for stale in list(target.glob("day*_*.json")) + [target / "calls.jsonl"]:
        if stale.exists():
            stale.unlink()
    written = []
    for source in [*records, calls_file]:
        destination = target / ("calls.jsonl" if source == calls_file else source.name)
        destination.write_bytes(source.read_bytes())
        written.append(destination)
    print(f"Recorded {len(records)} cache records and calls.jsonl into {target}")
    return written


if __name__ == "__main__":
    main()
