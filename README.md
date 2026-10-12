# Hotel market simulator

This is a simulator of one hotel market and an agent that prices in it. Four
hotels of one brand share the market, which produces daily bookings, competitor
rate shops, one convention and two changes to the air schedule. Each day the
agent flags the stay dates where something changed, and code scores the rate
options for each flag. That leaves the model one job, which is to accept or
decline a plan and write the reason for the revenue manager. The schedule
columns follow Cirium's published data dictionary, because that is the shape
real schedule data arrives in. Every row here is synthetic, and the repository
has no Cirium data and no affiliation with Cirium.

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

Contribution rises in all 20 seeds while room revenue falls, because the agent
almost always raises rates, which sells fewer rooms. That loses some revenue,
but it saves more in the cost of servicing those rooms. Almost all of the gain,
96% of it, comes from the two shocks, the convention and the new flights. An
agent that has to learn price response for itself keeps between 43% and 76% of
that gain, and where it lands in that range depends on the value it starts from
and on whether the cautious rule is on. The agent shares the simulator's own
demand formula, so these numbers only show that the machinery works. A forecast
for a real market would need the demand model learned from real bookings.

## The model as a reviewer

The model never sets a rate. Code works out every candidate action for a hotel
and estimates what each one would earn, and only then does the model see
anything. What it sees is one hotel's queue of plans for the day. For each plan
it accepts or declines, and it writes the reason either way. Its answer is
checked against the options it was given, so it cannot invent a rate the code
did not compute, and that is why this repository calls it a reviewer. Every gain
is measured against a control run that changes no rate at all. The same seed
draws the same bookings in both runs, so the only difference between them is the
plans the agent put through, and because a cached answer is read back before the
model is asked again, a run can be repeated exactly. The oracle reviewer is the
ceiling for this job, because it scores every plan with the simulator's own
elasticity and declines whenever holding scores at least as well, which is the
best decline decision anyone could make with these candidates. The comparison, a
control arm and an oracle with decline precision and recall, takes its shape
from Coinbase's series on building and evaluating a fraud agent.

The benchmark ran seeds 1 to 20 in three elasticity modes, with five reviewers
in each mode: the template that accepts everything, the oracle, and the three
current Claude models. The tables are in docs/results.md. In the true mode there
was nothing to find out, because every plan is already scored with the
simulator's own elasticity, so accepting all of them is right. The oracle and
all three models did exactly that, and every one of them earned the template's
+$32,899 a seed. The two modes where the code's elasticity is wrong are the ones
that tell the reviewers apart. At a fixed elasticity of 1.0, accepting every
plan earns +$8,438 a seed, and the oracle earns +$30,588 while accepting only
15% of the plans. That gap of $22,150 a seed is what a good reviewer could
recover.

Opus recovered 28% of it. It earned +$14,584 a seed and came out ahead of the
fixed-rate run in 17 seeds of 20. It got there by declining 47 plans, and every
one of them was a plan the oracle also declined, so its precision is 1.00. But
it caught only one in seven of the plans the oracle declined, so its recall is
0.14, and its dollar-weighted recall of 0.25 says the ones it did catch were the
costlier ones. Almost all of its declines are one plan. On day 40, after the
seat cut, the code wants to raise rates 10% on every day of the week for stay
dates 70 to 90, and Opus held instead in 36 of the 47 cases. Its reasons say the
estimate rests on an elasticity "fixed for the run rather than learned from our
bookings" while the dates are behind pace and already priced above the median.
At a fixed elasticity of 2.0 it declined one plan in twenty seeds and finished
level with accept-all, +$9,557 against +$9,551, with the oracle at +$23,058.

Sonnet and Haiku declined nothing in any mode, so their runs are the template's
runs. The one model that beat accept-all did it by $6,146 a seed at a fixed
elasticity of 1.0 and by nothing at 2.0, and it cost $0.41 per seed to ask. For
the other two the value of the run is entirely in the code, and the model is
there to write the reasons.

There is no post-training in this repository, because the world here is one the
repository wrote. A model trained on these runs would learn the simulator's
Poisson draws and its elasticity of 1.5, and it would learn nothing about
hotels, so anything it gained would say nothing about a real market. The
learning a pricing system can honestly do in a world like this is what
estimate.py does, which is to fit one parameter to the bookings it has seen.

## Known limits

- All data is synthetic, so there is no real market, airline, hotel or booking
  in it.
- The agent's demand forecast and booking curve are the simulator's own, held
  equal by a test; the demand level and the curve are never learned.
- By default the agent is handed the simulator's elasticity of 1.5;
  `--elasticity fixed:X` and `learn:X` take it away.
- Demand moves by the hotel's share of guests arriving by air times the change
  in arriving seats; that link is a modelling choice.
- The minimum-stay recommendation is advice only, because the simulator has no
  length of stay, and it is left out of every estimate and result.
- The estimates assume the simulator's Poisson booking noise; real bookings
  arrive less evenly, with groups, cancellations and no-shows.
- The cost of an occupied room is one third of the start rate, which makes the
  start rate contribution-best on a night that will not sell out.
- The $250 minimum applies to a whole plan, so a small change on one day of the
  week can ride inside a plan that clears the minimum on its other days.
- Competitors never react to the hotels' rates; theirs move only with the
  scripted shocks.
- There is one rate per hotel and stay date, with no room types, group blocks,
  cancellations or no-shows.
- Without an API key every plan is accepted, so a template run measures the
  plans and leaves the model's judgement out.
- The live models were benchmarked on seeds 1 to 20 (docs/results.md); only
  Opus ever declines a plan, and learn mode has not been run live.
- The container image has not been built, and the suite has run on Python 3.11,
  3.12 and 3.13 only.

The next version puts each hotel's past rate changes and what they earned into
the model request, so the model can weigh a plan against the last ones. It also
reprices when data arrives during the day, and its simulated competitors react
to the hotels' rate changes.
