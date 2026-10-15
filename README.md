# Hotel market simulator

A simulator of one made-up hotel market and its pricing agent. Four hotels of
one brand share it; the agent reads the simulated feeds on days 0 to 59. Four
shocks arrive: a convention (day 10), new flights (day 20), a competitor rate
cut at the full-service hotel (day 30) and a route suspension (day 40). Code
computes every number; the model picks a plan or holding and writes the reason.
The schedule columns follow Cirium's published data dictionary, but every row
is synthetic. The repository has no Cirium data and no affiliation with Cirium.

The agent's demand forecast is the simulator's own formula and reads the
simulator's own event uplift from the events feed, so every headline figure is
a perfect-information result that measures the loop and not a forecast. In the
default run every reviewer, the template and the three models, accepts every
plan, so those figures measure the plans and not the model.

## Run it

    make setup          # .venv with the package, pytest and ruff
    make test           # the tests; make test-all adds the nine slow ones
    make demo SEED=7    # demo.duckdb from the recorded run, then the demo page

make demo needs the network once, to install streamlit, and needs no API key for
the shipped market at seed 7, which is what the recorded run covers. Every other
command is in docs/commands.md.

## Results

Seeds 1 to 20, the agent run against the fixed-rate run over stay dates 0 to
149. The reasons are the template's, and the agent uses the simulator's
elasticity.

| Measure | Value |
| --- | ---: |
| Seeds where the agent earned more contribution | 20 of 20 |
| Mean contribution change per seed | +$32,899 |
| Smallest and largest contribution change | +$13,479 and +$52,809 |
| Mean room revenue change per seed | -$22,861 |
| Rate changes over the 20 seeds | 179 |
| Accepted plans' estimated gain over holding, summed | +$681,054 |
| Realised gain on the same plans, summed | +$657,979 |

The same runs in a revenue manager's measures, each the mean over the seeds:

| Hotel | Occupancy, fixed / agent | Average rate, fixed / agent | RevPAR, fixed / agent |
| --- | ---: | ---: | ---: |
| Downtown convention hotel | 78.4% / 78.2% | $220.00 / $220.58 | $172.54 / $172.55 |
| Downtown full-service hotel | 77.6% / 77.3% | $190.00 / $190.56 | $147.36 / $147.35 |
| Lifestyle hotel | 77.2% / 76.3% | $240.00 / $242.61 | $185.29 / $185.05 |
| Airport hotel | 88.9% / 86.2% | $140.00 / $143.36 | $124.46 / $123.61 |

RevPAR is flat or lower at every hotel, so the gain is room cost not paid on the
rooms the agent gave up, and the airport hotel's gain is zero once that cost
falls to 22.7% of the rate (docs/results.md, In a revenue manager's measures).

## Three findings

**Where the money comes from.** Contribution rises in 20 of 20 seeds and room
revenue falls in every one, because the agent raises in nearly all accepted
plans and the lost revenue is smaller than the saved room cost. With the cost at
a third of the start rate and an elasticity of 1.5, the start rate is already
the best rate on a night that will not sell out, so the gain lies in the nights
the shocks make scarce. The convention and the new flights carry 96% of it
(docs/results.md, the table of where each arm's gain came from). The
convention's share comes mostly from the competitors' 15% raise, because a hotel
that holds its rate then sits 13% below its comp set, and the rate ratio sends
it 23% more of the remaining demand. With that raise at zero the mean is
+$19,480 a seed and the event plans earn +$538 (docs/results.md, The convention
without the competitors' raise). Half the headline rides on the new flights,
where the seat link is exact and immediate and the airport hotel's base
occupancy was set so that the flights fill it.

**Against a rule that prices on the same flags.** The never-cut control earns
+$24,780 a seed by itself. The agent's lead over it is +$8,119, with a standard
deviation of about $6,600 across the seeds, and the agent is ahead in 17 seeds
of 20, which a sign test puts at p 0.003. Against the same rule with 5% cuts the
lead is +$10,043, because every cut loses in this market. That follows from the
constant elasticity of 1.5 and the cost at a third of the rate, which together
make the start rate the contribution-best rate on a night that will not sell out
and the floor the revenue-best rate. In the reacting market that the next
version makes the default, the same never-cut control beats the agent in every
seed, which docs/results.md explains as the ratchet (docs/results.md, The
rule-based control).

**What the model adds, and what learns.** In the default run the model adds
nothing, because every reviewer accepts every plan. As a reviewer in a mode
where the agent's elasticity is wrong, Opus recovers 28% of what a perfect
reviewer could at a fixed elasticity of 1.0 and 4% in a learned mode, and
Sonnet and Haiku decline nothing. The one piece that learns from the
bookings is the elasticity estimator, a Poisson regression with a prior, and
the agent that uses it keeps 43% to 76% of the gain, set by the prior and the
cautious rule (docs/reviewers.md for the reviewers, docs/results.md for the
rest).

## The limit that matters

The forecast is right by construction. With the simulator's demand scaled by
0.9, which the agent never sees, the gain falls to +$1,913 a seed, ahead in 12
seeds of 20, which is not distinguishable from zero (p 0.50). The demand-bias
section of docs/results.md has the table, and the other limits are in
docs/limits.md.

## Read more

- docs/results.md: the tables of every experiment, with their commands.
- docs/reviewers.md: the model as a reviewer, the oracle and the benchmark.
- docs/limits.md: the known limits, and the next version.
- docs/commands.md: every command, make target and Docker line.
- docs/schedule-feed.md: the air schedule feed as this repository models it.
- kg/: a map of the repository for agents, with kg/README.md as the legend.

The next version puts each hotel's past rate changes and their outcomes into the
model request, reprices as data arrives during the day and makes the competitors
react by default. The stored route then refuses a later day, the tables keep
each decision's outcome, and each hotel gets its own booking curve.
