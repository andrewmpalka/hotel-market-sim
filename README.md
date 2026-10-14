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

make demo needs the network once, to install streamlit, and never needs an API
key. Every other command is in docs/commands.md.

## Results

Seeds 1 to 20, the agent run against the fixed-rate run over stay dates 0 to
149. The reasons are the template's and the elasticity is the simulator's.

| Measure | Value |
| --- | ---: |
| Seeds where the agent earned more contribution | 20 of 20 |
| Mean contribution change per seed | +$32,899 |
| Smallest and largest contribution change | +$13,479 and +$52,809 |
| Mean room revenue change per seed | -$22,861 |
| Rate changes over the 20 seeds | 179 |
| Accepted plans' estimated gain over holding, summed | +$681,054 |
| Realised gain on the same plans, summed | +$657,979 |

## Three findings

**Where the money comes from.** Contribution rises in 20 of 20 seeds and room
revenue falls in every one, because the agent raises in nearly all accepted
plans and the lost revenue is smaller than the saved room cost. With the cost
at a third of the start rate and an elasticity of 1.5, the start rate is
already the best rate on a night that will not sell out, so the gain lies in
the nights the shocks make scarce. The convention and the new flights carry
96% of it (docs/results.md, the table of where each arm's gain came from).

**Against a rule that prices on the same flags.** The never-cut control earns
+$24,780 a seed by itself. The agent's lead over it is +$8,119, and the agent
is ahead in 17 seeds of 20, so the control wins 3. Against the same rule with
5% cuts the lead is +$10,043, because every cut loses in this market
(docs/results.md, The rule-based control).

**What the model adds, and what learns.** In the default run the model adds
nothing, because every reviewer accepts every plan. As a reviewer in a mode
where the agent's elasticity is wrong, Opus recovers a share of 0.28 of what a
perfect reviewer could at a fixed elasticity of 1.0 and 4% in a learned mode,
and Sonnet and Haiku decline nothing. The one piece that learns from the
bookings is the elasticity estimator, a Poisson regression with a prior, and
the agent that uses it keeps 43% to 76% of the gain, set by the prior and the
cautious rule (docs/reviewers.md for the reviewers, docs/results.md for the
rest).

## The limit that matters

The forecast is right by construction. With the simulator's demand scaled by
0.9, which the agent never sees, the gain falls to +$1,913 a seed, ahead in 12
seeds of 20 (docs/results.md, The demand bias). The other limits are in
docs/limits.md.

## Read more

- docs/results.md: the tables of every experiment, with their commands.
- docs/reviewers.md: the model as a reviewer, the oracle and the benchmark.
- docs/limits.md: the known limits, and the next version.
- docs/commands.md: every command, make target and Docker line.
- docs/schedule-feed.md: the air schedule feed as this repository models it.
- kg/: a map of the repository for agents, with kg/README.md as the legend.

The next version puts each hotel's past rate changes and their outcomes into
the model request, reprices as data arrives during the day, and makes the
simulated competitors react by default.
