# Hotel market simulator

Four hotels of one brand share a simulated market. It has daily bookings,
competitor rate shops, one event and two air schedule changes. An agent flags
changes, and code scores rate options. A model picks plan or hold and explains
it. Schedule columns follow Cirium's published data dictionary. Every row is
synthetic. The repository has no Cirium data or affiliation.

## Install and run

Python 3.11 or later, from the repository root:

    pip install -e ".[dev]"                  # the package, its dependencies, pytest and ruff
    python -m pytest                         # the tests, offline; the slow 20-seed check is skipped
    python -m pytest --slow                  # every test, the 20-seed check included
    ruff check . && ruff format --check .    # the linter and the formatter, as a check
    python kg_check.py                       # the knowledge graph against the code

    hotel-market --seed 7 --template         # both runs, decisions.jsonl, the daily queues, the summary
    hotel-market --seed 7                    # the same, the model writing the reasons (needs ANTHROPIC_API_KEY)
    hotel-market --seed 7 --replay 20        # day 20's queue again, without a model call
    hotel-market --seeds 1 20                # seeds 1 to 20: mean and range of the contribution change
    hotel-market --seeds 1 20 --elasticity true --elasticity learn:1.0 --cautious   # one arm per mode
    hotel-market --seed 7 --customer customers/demo.toml --target revenue           # another market or target
    hotel-market run-day --seed 7 --as-of 20 --from 0   # days 0 to 20, one day at a time, through stored tables
    hotel-market replay --as-of 20                      # day 20's plans again, from the stored tables alone
    python scripts/live_audit.py --seed 7               # a live run, every model call measured, then audited
    hotel-market bench --seeds 1 20 --template          # the template and the oracle reviewer, in three modes, offline
    hotel-market bench --seeds 1 3                      # the same with each Claude model reviewing (needs ANTHROPIC_API_KEY)

With make, on a Mac or Linux machine:

    make setup                 # create .venv and install the package, pytest and ruff into it
    make test                  # the tests; make test-all includes the slow check; make lint runs ruff
    make run SEED=7            # the template run; make live SEED=7 uses the model
    make bench FIRST=1 LAST=3  # the reviewers benchmarked; make bench BENCH=--template runs it offline
    make day SEED=7 DAY=20     # a day through the stored tables; make day-replay DAY=20 replays it
    make help                  # every target

With Docker:

    docker build -t hotel-market .
    docker run --rm -v "$PWD:/work" hotel-market --seed 7 --template
    docker run --rm -v "$PWD:/work" -e ANTHROPIC_API_KEY hotel-market --seed 7
    docker run --rm --entrypoint python hotel-market -m pytest -p no:cacheprovider /app/tests

## Results

Seeds 1 to 20: the agent run against the fixed-rate run over stay dates 0 to 149, template reasons, the simulator's elasticity.

| Measure | Value |
| --- | ---: |
| Seeds where the agent earned more contribution | 20 of 20 |
| Mean contribution change per seed | +$32,899 |
| Smallest and largest contribution change | +$13,479 and +$52,809 |
| Mean room revenue change per seed | -$22,861 |
| Rate changes over the 20 seeds | 179 |
| Accepted plans' estimated gain over holding, summed | +$681,054 |
| Realised gain on the same plans, summed | +$657,979 |

Seed 7: room revenue and contribution per hotel, the fixed-rate run against the agent run, stay dates 0 to 149.

| Hotel | Revenue, fixed | Revenue, agent | Change | Contribution, fixed | Contribution, agent | Change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel | 10,370,360 | 10,367,821 | -2,539 | 6,913,573 | 6,917,488 | +3,915 (+0.1%) |
| Downtown full-service hotel | 5,532,800 | 5,522,502 | -10,298 | 3,688,533 | 3,695,019 | +6,485 (+0.2%) |
| Lifestyle hotel | 3,371,280 | 3,373,752 | +2,472 | 2,247,520 | 2,260,632 | +13,112 (+0.6%) |
| Airport hotel | 2,774,800 | 2,750,146 | -24,654 | 1,849,867 | 1,855,173 | +5,306 (+0.3%) |
| All four hotels | 22,049,240 | 22,014,221 | -35,019 | 14,699,493 | 14,728,311 | +28,818 (+0.2%) |

The tables of every experiment: [docs/results.md](docs/results.md).

In all 20 seeds, contribution rises and room revenue falls. The convention and
new flights produce 96% of the gain. An agent learning price response keeps 43%
to 76% of the gain. Its starting value and the cautious rule set the share. The
agent uses the simulator's demand formula, so the numbers test the machinery and
are not a forecast.

## Known limits

- All data is synthetic: no real market, airline, hotel or booking.
- The agent's demand forecast and booking curve are the simulator's own, held
  equal by a test; the demand level and the curve are never learned.
- By default the agent is handed the simulator's elasticity of 1.5;
  `--elasticity fixed:X` and `learn:X` take it away.
- Demand moves by the hotel's share of guests arriving by air times the change
  in arriving seats; that link is a modelling choice.
- The minimum-stay recommendation is advice only: the simulator has no length
  of stay, and the advice is left out of every estimate and result.
- The estimates assume the simulator's Poisson booking noise; real bookings
  arrive less evenly, with groups, cancellations and no-shows.
- The cost of an occupied room is one third of the start rate, which makes the
  start rate contribution-best on a night that will not sell out.
- The $250 minimum applies to a whole plan, so a small change on one day of the
  week can ride inside a plan that clears the minimum on its other days.
- Competitors never react to the hotels' rates; theirs move only with the
  scripted shocks.
- One rate per hotel and stay date: no room types, group blocks, cancellations
  or no-shows.
- Without an API key every plan is accepted, so a template run measures the
  plans, not the model's judgement.
- The live model has been measured on one seed in the default mode, where it
  accepted every plan; whether it ever declines one is not known.
- The container image has not been built, and the suite has run on Python 3.11,
  3.12 and 3.13 only.

The next version puts each hotel's past rate changes and their outcomes into the
model request. It reprices when data arrives during the day. Its simulated
competitors react to rate changes.
