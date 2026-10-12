# Hotel market simulator

A Python simulator of one made-up hotel market, and an agent that reads the
simulated data each day and recommends rate changes for four hotels of one
brand. Every number is synthetic. README.md has the commands and the results;
docs/results.md has the tables of every experiment.

## Rules

1. Code computes every number. The model only chooses among candidate
   actions and writes the reason, and its answer is checked against the
   options it was given.
2. Every run takes a seed. Two runs with the same seed and settings produce
   the same bookings and the same decisions.jsonl.
3. Nothing may use information before the day it becomes known. Every lookup
   takes as_of_day: a flight counts from the day the airline files it, an
   event from the day it is announced, a competitor's rate from the day it
   is shopped.
4. Model responses are saved under cache/, keyed by seed, day and hotel (and
   by the elasticity mode and the model when they are not the defaults), and
   a rerun reads the cache first. Without an API key, model.py writes a
   template reason, so the tests run offline. The template's answers are
   never cached.
5. Python 3.11+, numpy, pandas, duckdb, pytest, ruff and the anthropic SDK,
   declared in pyproject.toml. No web UI, no database server (DuckDB is a
   file the daily commands write), no real data.
6. The agent's modules (detect, forecast, estimate, plan, model, agent, text
   and stored) read data only through the four interfaces in sources.py and
   never import demand, bookings, shops, schedule, shocks or simulated;
   tests/test_sources.py fails if one does.
7. Constants that describe the simulator stay in code. Everything specific
   to a market lives in its customer file under customers/.
8. Nothing from a .env file, cache/, a DuckDB file or an API key is ever
   committed. .gitignore lists them; keep it that way.

## Layout

The code is the package src/hotel_market/, installed from the repository
root with pip install -e ".[dev]" and imported as hotel_market.<module>.

| Module | Holds |
| --- | --- |
| schedule.py | the air schedule as known on a day, its seat counts, both air shocks |
| world.py | the Hotel and Competitor dataclasses and the calendar |
| customer.py | reads a market's customer file; demo() is customers/demo.toml |
| sources.py | the four interfaces: Bookings, RateShops, Schedules, Events |
| shocks.py | the convention (known day 10) and the competitor rate cut (day 30) |
| demand.py | the simulator's expected and normal demand per hotel and stay date |
| shops.py | competitor rates and comp medians from a seeded rate shop |
| bookings.py | the booking curve, the day-0 preload and the daily booking loop |
| forecast.py | the agent's own demand model, from the hotel's settings and the feeds |
| detect.py | the detect numbers, the flags and the hold |
| estimate.py | the learned elasticity: a Poisson regression with a prior |
| plan.py | each flag's candidates, estimates and plan, per day of the week |
| model.py | the model call, its cache, the answer schema, the template and the measured client |
| agent.py | the daily loop, the elasticity modes and the minimum-stay advice |
| simulated.py | the simulator as the four sources, and the decide hook |
| stored.py | the four sources over the DuckDB tables, and the writers |
| text.py | wording shared by the template reasons and the reports |
| cli.py | the hotel-market command, which python -m hotel_market also runs |
| bench.py | the benchmark of the model as a reviewer: the oracle grader, its measures, the reviewers and the price table |

Around the package: tests/ holds one test file per module, conftest.py and
tests/fixtures/live_seed7/, one recorded live run; customers/demo.toml is the
demo market; sql/schema.sql defines the seven stored tables; scripts/
live_audit.py runs and audits a live seed; kg/ and kg_check.py are the
knowledge graph and its checker; Makefile and Dockerfile wrap the setup;
docs/results.md holds the experiment tables.

## Commands

    make setup                 # .venv with the package, pytest and ruff
    make test                  # the tests; the slow 20-seed check is skipped
    make test-all              # every test, the slow check included
    make lint                  # ruff check, and ruff format as a check
    make run SEED=7            # both runs with the template reasons
    make live SEED=7           # the model writes the reasons (ANTHROPIC_API_KEY, here or in .env)
    make live-audit SEED=7     # the live run, measured, then its audit
    make bench FIRST=1 LAST=3  # the reviewers benchmarked (ANTHROPIC_API_KEY); BENCH=--template runs it offline
    make day SEED=7 DAY=20     # one day through the stored tables; make day-replay DAY=20 replays it
    make image                 # the Docker image; make docker-test and docker-run SEED=7 use it
    python kg_check.py         # the graph against the code; --write-index rewrites kg/index.md

`make help` lists every target. The raw commands are in README.md.

## Commits

One module or feature per commit, with its tests, so the tests present pass
at every commit; modules that cannot be separated share one commit. The
subject line is under 72 characters and in the imperative. The body is at
most three lines, written only when the reason is not obvious. No measured
numbers in a message. The author is Andrew Palka
<16229834+andrewmpalka@users.noreply.github.com>; keep the Claude co-author
line.

## Knowledge graph

kg/ is a map of this repository for agents. Read kg/index.md before opening
source files and follow the [[ID]] links to the nodes you need; kg/README.md
is the legend. Update the graph in the same commit as the code: a change to
code and the change to its nodes go together, a [C] claim cites a test that
fails when the claim is false, and a Commit line names a commit of this
history. Every node is Simplified Technical English: one fact a line, no
sentence over 20 words, active voice, present tense, a field line of at most
240 characters and a node of at most 8 fields. Measured figures live in RES
nodes in kg/results.md, one per experiment with its command and its table in
docs/results.md; a decision keeps one headline figure and links to its RES
node. A claim no test can confirm is a policy node, with Kind: policy and
Evidence: review. python kg_check.py --write-index rewrites kg/index.md from
the nodes, and python kg_check.py and tests/test_kg.py fail when the graph
and the code disagree.
