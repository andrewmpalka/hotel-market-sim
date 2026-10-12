# Hotel market simulator

This repository holds a simulator of one hotel market and an agent that sets
rates in it. Four hotels of one brand share the market. The market produces
daily bookings, competitor rate shops, one convention and two changes to the air
schedule. Each day the agent flags the stay dates where a signal changed. Code
scores the rate options for each flag. The model accepts or declines each plan
and writes the reason for the revenue manager.

The schedule columns follow Cirium's published data dictionary, but every row is
synthetic. The repository has no Cirium data and no affiliation with Cirium.

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
    hotel-market bench --seeds 1 20 --template --demand-bias 0.9 --elasticity true --elasticity learn:1.0
                                                        # the simulator's demand times 0.9, which the agent never sees
    hotel-market bench --seeds 1 20 --template --react  # competitors follow the hotels' rate changes, three days later
    hotel-market bench --seeds 1 20 --template --react --market-elasticity 0.5
                                                        # the market's demand answers the comp median's level; the agent is told the value
    python scripts/median_path.py --seed 7 --react --hotel convention --stays 45 48 --days 9 15
                                                        # a comp median's path next to the hotel's rate

With make, on a Mac or Linux machine:

    make setup                 # create .venv and install the package, pytest and ruff into it
    make test                  # the tests; make test-all includes the slow check; make lint runs ruff
    make run SEED=7            # the template run; make live SEED=7 uses the model
    make bench FIRST=1 LAST=3  # the reviewers benchmarked; make bench BENCH=--template runs it offline
    make day SEED=7 DAY=20     # a day through the stored tables; make day-replay DAY=20 replays it
    make help                  # every target

With Docker:

    docker build -t hotel-market:py3.12 .                        # --build-arg PYTHON=3.11 for another Python
    docker run --rm -v "$PWD:/work" hotel-market:py3.12 --seed 7 --template
    docker run --rm -v "$PWD:/work" -e ANTHROPIC_API_KEY hotel-market:py3.12 --seed 7
    docker run --rm --entrypoint python -w /app hotel-market:py3.12 -m pytest -p no:cacheprovider tests

## Results

Seeds 1 to 20, the agent run against the fixed-rate run over stay dates 0 to 149. The reasons are the template's and the elasticity is the simulator's.

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

Contribution increases in all 20 seeds and room revenue decreases. The agent
raises rates in nearly all accepted plans, so the hotels sell fewer rooms. The
lost revenue is smaller than the saved cost of the rooms. The two shocks, the
convention and the new flights, produce 96% of the gain.

An agent that learns the price response keeps 43% to 76% of the gain. The start
value and the cautious rule set the share. The agent uses the simulator's demand
formula, so the results test the machinery. A forecast for a real market would
need the demand model learned from real bookings.

## The model as a reviewer

The model does not set rates. Code computes every candidate action for a hotel
and estimates the contribution of each one before the model is asked. The model
then sees one hotel's queue of plans for the day. It accepts or declines each
plan and writes the reason in both cases. Code checks the answer against the
options in the request. The model cannot return a rate that code did not
compute.

Every gain is measured against a control run with no rate changes. The same seed
produces the same bookings in both runs, so the accepted plans are the only
difference between them. The cache returns a stored answer before the model is
asked again, so a run can be repeated exactly.

The oracle reviewer scores every plan with the simulator's own elasticity. It
declines the plan when holding scores at least as well. No reviewer can decline
better with these candidates, so the oracle is the ceiling. The comparison
follows the shape of Coinbase's series on a fraud agent. It has a control arm,
an oracle, and a reviewer scored on decline precision and recall.

The benchmark runs seeds 1 to 20 in three elasticity modes. Each mode has five
reviewers: the template, which accepts every plan, the oracle, and the three
current Claude models. In the true mode, every plan is scored with the
simulator's own elasticity, so accepting every plan is correct. The oracle and
the three models accept every plan, and each earns the template's +$32,899 a
seed. The two modes with a wrong elasticity separate the reviewers.

At a fixed elasticity of 1.0, accepting every plan earns +$8,438 a seed. The
oracle earns +$30,588 and accepts 15% of the plans. The difference, $22,150 a
seed, is the value a reviewer can recover. Opus recovers 28% of it. It earns
+$14,584 a seed and beats the fixed-rate run in 17 of 20 seeds.

Opus declines 47 plans, and the oracle declines every one of them, so its
precision is 1.00. It catches one in seven of the oracle's declines, so its
recall is 0.14. Its dollar-weighted recall is 0.25, so its declines are the
costlier ones. The declines cluster on one plan. After the day-40 seat cut, code
plans a 10% raise on all seven days for stay dates 70 to 90. Opus holds instead
in 36 of the 47 cases.

Its reasons state that the estimate rests on an elasticity "fixed for the run
rather than learned from our bookings". They also state that the dates are
behind pace and priced above the median. At a fixed elasticity of 2.0, Opus
declines one plan in 20 seeds. It ties with accept-all, +$9,557 against +$9,551,
and the oracle earns +$23,058.

Sonnet and Haiku decline no plan in any mode, so their runs equal the template's
runs. One model beats accept-all, by $6,146 a seed at a fixed elasticity of 1.0
and by nothing at 2.0. Its calls cost $0.41 per seed. For the other two models,
the value of the run is in the code, and the model writes the reasons.

This repository does no post-training. Every booking in this world comes from
code in this repository. A model trained on these runs learns the simulator's
Poisson draws and its elasticity of 1.5 and nothing about hotels. Its gains say
nothing about a real market. The only learning that carries over to a real
market is the kind in estimate.py. It fits one parameter to the observed
bookings.

## Known limits

- All data is synthetic, so no real market, airline, hotel or booking appears in
  it.
- The agent's demand forecast and booking curve are the simulator's own. A test
  holds the forecast equal to the simulator's demand at the default demand bias
  of 1.0, and the curve is never learned. The option `--demand-bias F`
  multiplies the simulator's demand by F, which the agent never sees, so its
  forecast is wrong by that factor. At 0.9 the default run keeps +$1,913 a seed
  of its +$32,899, because every raise sells fewer rooms than the agent's
  estimate says. At 1.1 it earns +$112,082 a seed, because the start rates were
  set for a smaller market. The learning agent's day-59 elasticity stays at
  1.26 to 1.49 at both biases, so the level error lands in the estimator's
  intercept as designed (docs/results.md).
- By default the agent is handed the simulator's elasticity of 1.5;
  `--elasticity fixed:X` and `learn:X` take it away.
- Demand moves by the hotel's share of guests arriving by air times the change
  in arriving seats; that link is a modelling choice.
- The minimum-stay recommendation is advice only. The simulator has no length
  of stay, and the advice is not in any estimate or result.
- The estimates assume the simulator's Poisson booking noise; real bookings
  arrive less evenly, with groups, cancellations and no-shows.
- The cost of an occupied room is one third of the start rate, which makes the
  start rate contribution-best on a night that will not sell out.
- The $250 minimum applies to a whole plan, so a small change on one day of the
  week can ride inside a plan that clears the minimum on its other days.
- By default competitors never react to the hotels' rates, and the market has
  no price response of its own. Bookings follow a hotel's rate against the comp
  median alone, so a raise that every hotel matches costs no rooms. That is
  what the default makes free. The option `--react` makes each competitor move
  half of a hotel's change three days after it takes effect, read from the
  Books' own log, and `--market-elasticity E` makes the market's demand fall by
  the comp median over its starting level to the power of E, with the agent
  told E. With the reaction on, the default run earns +$111,272 a seed at an E
  of 0.0, +$72,229 at 0.5 and +$43,584 at 1.0, against +$32,899 with neither.
  Part of that gain is correct. Competitors that follow half of a raise lower
  the hotel's effective own-price elasticity below 1.5, so a raise pays more
  in that world and the agent is right to take it. The fault is the loop in
  which the competitors' answer to our own change is read as news and the
  hold lifts, and its measure is the stay dates changed twice within 14 days,
  which the term cut from 97 to 25. FRK-09 holds the open question for the
  rest. The oracle is told both settings, so it is the ceiling again
  (docs/results.md).
- There is one rate per hotel and stay date, with no room types, group blocks,
  cancellations or no-shows.
- Without an API key, every plan is accepted. A template run therefore measures
  the plans alone.
- The benchmark ran the live models on seeds 1 to 20 (docs/results.md), and only
  Opus declined any plan. Learn mode has not run live.
- The container image was built on Python 3.11, 3.12 and 3.14 and passed the
  suite on each. A seed-7 run inside it matches the native run (docs/results.md).

The next version puts each hotel's past rate changes and their outcomes into the
model request. The model can then compare a plan with the previous ones. It also
reprices when data arrives during the day, and its simulated competitors react
to the hotels' rate changes.
