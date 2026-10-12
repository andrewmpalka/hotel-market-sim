"""live_audit.py

One seed with the live model, measured and audited.

    python scripts/live_audit.py --seed 7              # run live, then audit (needs an API key)
    python scripts/live_audit.py --seed 7 --audit-only # audit the cache a live run left

The run is the hotel-market command's run for the seed in the default mode:
both simulations, decisions.jsonl and the cache. Around each model call it
records the tokens, the time, the stop reason and the model that answered,
and writes them to calls.jsonl. The audit then reads the cache and prints
every reason the model wrote, every plan it declined, and every number in a
reason that does not appear in the request the model was answering.

Every figure in the request is a display string written by code ("$8,050 more
than holding", "10.7% to 14.6% below the median", "1,188") that the model is
told to copy whole, so the audit matches phrases, sentence by sentence: a
figure in a reason is quoted from its request when a display string holding it
appears whole in the same sentence, when it is a whole number the request holds
as it is, such as a day, or a figure inside a name such as "raise 5%", or when
it is a bare dollar figure in a sentence that carries "more than holding" and
the request holds "<figure> more than holding", since the prompt lets that
phrase be written once for several gains. A range written as "12–14%" or "$217
to $220" counts as its two ends, each with the shared unit. Anything else is
listed, with its reason, for a person to judge: a sign or a rounding of the
model's own, one end of a range on its own, a sum, a difference or a figure
from its own knowledge all show up here. For each reason the audit also prints
every sentence that holds no figure from the request, so that a person can
read what the model said on its own account.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import time
from pathlib import Path

from hotel_market.cli import run, summary
from hotel_market.model import HOLD, ClaudeClient

# List prices for claude-opus-5-5 on 2026-10-06, dollars per million tokens; the
# cost line is an estimate from them, and the token counts are printed for any
# other price.
INPUT_PRICE = 4.00
OUTPUT_PRICE = 20.00

# A figure as written: an optional sign and dollar sign, digits with thousands commas,
# an optional decimal part, an optional percent sign. A comma after the last digit is
# punctuation, not part of the figure.
_FIGURE = r"[-+]?\$?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?"
FIGURE = re.compile(_FIGURE)
# "12–14%", "$217 to $220", "45-48": two figures that share a sign and a unit.
SPAN = re.compile(rf"(?P<a>{_FIGURE})\s*(?:–|—|-|to)\s*(?P<b>{_FIGURE})")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


class Recorder:
    """Stands in for the SDK: passes each call through and records its usage and time."""

    def __init__(self, sdk):
        self.sdk = sdk
        self.calls: list[dict] = []
        self.beta = self  # ClaudeClient calls sdk.beta.messages.create(...)
        self.messages = self

    def create(self, **request):
        start = time.perf_counter()
        response = self.sdk.beta.messages.create(**request)
        usage = response.usage
        self.calls.append(
            {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0)
                or 0,
                "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
                "seconds": round(time.perf_counter() - start, 2),
                "stop_reason": response.stop_reason,
                "model": response.model,
                "fallback": any(block.type == "fallback" for block in response.content),
                "request_id": getattr(response, "_request_id", None),
            }
        )
        return response


def live_run(seed: int, out_dir: Path) -> list[dict]:
    """Seed `seed` with the live model, writing decisions.jsonl, cache/ and calls.jsonl
    under out_dir. Returns the calls' measurements."""
    import anthropic

    # A key that is not scoped to a workspace needs the workspace named on every request.
    workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    headers = {"anthropic-workspace-id": workspace} if workspace else None
    recorder = Recorder(anthropic.Anthropic(default_headers=headers))
    client = ClaudeClient(sdk=recorder)
    start = time.perf_counter()
    fixed, books, agent = run(seed, out_dir / "decisions.jsonl", out_dir / "cache", client)
    total = time.perf_counter() - start
    (out_dir / "calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in recorder.calls))
    print(summary(seed, fixed, books, agent))
    print()
    print(
        f"{len(recorder.calls)} model calls in a run of {total:.0f} s, both simulations included."
    )
    return recorder.calls


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
    stops = sorted({c["stop_reason"] for c in calls})
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
    """What a reason may quote from its request: the display strings of its figures,
    which must appear whole, and the tokens that may stand alone, the whole numbers
    the request holds as they are (a day, a stay date) and the figures inside names."""
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
    """Whether a figure written in a sentence is quoted from the request: a token that
    may stand alone; one of the figures of a display string that appears whole in the
    sentence (the "7" of "7 days" is not the "7" inside "10.7% below the median"); or a
    bare dollar figure in a sentence that carries "more than holding", when the request
    holds "<figure> more than holding"."""
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
    args = parser.parse_args(argv)
    cache_dir = args.out / "cache" / f"seed{args.seed}"
    calls: list[dict] = []
    if not args.audit_only:
        calls = live_run(args.seed, args.out)
    elif (args.out / "calls.jsonl").exists():
        calls = [
            json.loads(line) for line in (args.out / "calls.jsonl").read_text().splitlines() if line
        ]
    audit(cache_dir)
    print()
    report_calls(calls)


if __name__ == "__main__":
    main()
