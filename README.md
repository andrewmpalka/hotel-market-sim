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

## The model as a reviewer

In this repository the model is a reviewer, because code computes every
candidate rate action and its estimate before the model is asked. The model
accepts or declines each plan in a hotel's queue and writes the reason, and its
answer is checked against the options it was given, so it cannot choose a rate
the code did not compute. The fixed-rate run is the control, which means every
gain is measured against the same bookings with no rate change. The seed and the
cache make every run reproducible, because the same seed draws the same bookings
and a cached answer is read back before the model is asked. The oracle reviewer
is the ceiling, because it scores each plan with the simulator's own elasticity
and declines the plan when holding scores at least as well. The shape of the
comparison follows Coinbase's series on building and evaluating a fraud agent.

The benchmark ran seeds 1 to 20 in three elasticity modes with the template, the
oracle and the three current Claude models. In the true mode every plan is
scored at the simulator's own elasticity, so every reviewer accepts every plan
and earns the template's +$32,899 a seed, which means only the mismatched modes
can separate them. At a fixed elasticity of 1.0 accepting every plan earns
+$8,438 a seed and the oracle earns +$30,588 while accepting 15% of the plans,
so a reviewer had $22,150 a seed to recover. Opus recovered 28% of it and earned
+$14,584 a seed, ahead in 17 of 20 seeds, because it declined 47 plans with a
precision of 1.00 and a recall of 0.14, so every plan it declined was one the
oracle declined too but it caught one in seven of them. Its declines cluster on
the day-40 raise of 10% on every day of the week on stay dates 70 to 90 after
the seat cut, 36 of the 47 cases, and its reasons cite an elasticity "fixed for
the run rather than learned from our bookings" together with the dates trailing
pace and sitting above the median. At 2.0 it declined one plan and tied with
accept-all, +$9,557 against +$9,551, while the oracle earned +$23,058. Sonnet
and Haiku declined nothing, so they tie with the template everywhere. So one
model beats accept-all, by $6,146 a seed at a fixed elasticity of 1.0 and by
nothing at 2.0, for $0.41 an arm at list prices, but for the other two the value
of the run is in the code and the model is a reason-writer.

Post-training is not done here, because the world is one this repository wrote.
A model trained on these runs would learn the simulator's Poisson draws and its
elasticity of 1.5 and nothing about hotels, so its gains would say nothing about
a real market. The learning a pricing system can honestly do here is the one
estimate.py does, which fits one parameter to observed bookings.

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
- The live models were benchmarked on seeds 1 to 20 (docs/results.md); only
  Opus ever declines a plan, and learn mode has not been run live.
- The container image has not been built, and the suite has run on Python 3.11,
  3.12 and 3.13 only.

The next version puts each hotel's past rate changes and their outcomes into the
model request. It reprices when data arrives during the day. Its simulated
competitors react to rate changes.
