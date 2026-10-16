# Hotel market simulator

A simulator of one made-up hotel market and its pricing agent. Four hotels of
one brand share it; the agent reads the simulated feeds on days 0 to 59. Four
shocks arrive: a convention (day 10), new flights (day 20), a competitor rate
cut at the full-service hotel (day 30) and a route suspension (day 40). Code
computes every number; the model picks a plan or holding and writes the reason.
The schedule columns follow Cirium's published data dictionary, but every row
is synthetic. The repository has no Cirium data and no affiliation with Cirium.

The agent's demand forecast is the simulator's own formula and reads the
simulator's own event uplift from the events feed, so every headline figure is a
perfect-information result that measures the loop and not a forecast. In the
default run every reviewer, the template and the three models, says yes to every
plan, so those figures measure the plans and not the model. The template is a
stand-in that answers in the model's place when there is no key; it says yes to
every plan and writes a reason from the entry's own figures.

## Run it

    make setup          # .venv with the package, pytest and ruff
    make test           # the tests; make test-all adds the nine slow ones
    make demo SEED=7    # demo.duckdb from the recorded run, then the demo page

make demo needs the network once, to install streamlit, and needs no API key.
The recorded run covers the shipped market at seed 7 on world v2, and the
template answers wherever it does not. Every other command is in
docs/commands.md.

## Results

Seeds 1 to 20, the agent run against the fixed-rate run over stay dates 0 to
149, run on 2026-10-15 on world v2. The reasons are the template's, and the agent
uses the simulator's elasticity.

| Measure | Value |
| --- | ---: |
| Seeds where the agent earned more contribution | 20 of 20 |
| Mean contribution change per seed | +$16,164 |
| Smallest and largest contribution change | +$11,589 and +$23,394 |
| Mean room revenue change per seed | -$27,684 |
| Rate changes over the 20 seeds | 106 |
| Accepted plans' estimated gain over holding, summed | +$391,434 |
| Realised gain on the same plans, summed | +$323,281 |

The same runs in a revenue manager's measures, each the mean over the seeds:

| Hotel | Occupancy, fixed / agent | Average rate, fixed / agent | RevPAR, fixed / agent |
| --- | ---: | ---: | ---: |
| Downtown convention hotel | 76.9% / 76.8% | $220.00 / $220.03 | $169.07 / $169.07 |
| Downtown full-service hotel | 76.5% / 76.5% | $190.00 / $190.06 | $145.37 / $145.36 |
| Lifestyle hotel | 77.0% / 76.1% | $240.00 / $242.50 | $184.76 / $184.44 |
| Airport hotel | 88.9% / 86.1% | $140.00 / $143.44 | $124.50 / $123.53 |

RevPAR is flat or lower at every hotel, so the gain is room cost not paid on the
rooms the agent gave up, and the airport hotel's gain is zero once that cost
falls to 24.7% of the rate (docs/results.md, In a revenue manager's measures).

## Three findings

**Where the money comes from.** Contribution rises in 20 of 20 seeds and room
revenue falls in every one, because the agent raises in nearly all accepted
plans and the lost revenue is smaller than the saved room cost. With the cost at
a third of the start rate and an elasticity of 1.5, the start rate is already
the best rate on a night that will not sell out, so the gain lies in the nights
the shocks make scarce. The convention and the new flights carry 94% of it
(docs/results.md, the table of where each arm's gain came from), and nearly all
of that is the new flights: the convention plans earn +$614 a seed on their
stay dates, and +$100 with the competitors' 15% raise at zero, which moves the
mean from +$16,164 to +$15,611 (docs/results.md, The convention without the
competitors' raise). On world v2 the downtown hotels hold most of their
convention business as group blocks before the announcement, and the market's
own price response takes back part of what the raise gives, so the convention
adds little either way. The new flights' passengers ramp from a 60% load factor
over 90 days rather than arriving at once, and the airport hotel's base
occupancy was set so that the flights fill it.

**Against a rule that prices on the same flags.** The never-cut control earns
+$10,468 a seed by itself, run on 2026-10-15 on world v2. The agent's lead over it
is +$5,696, with a standard deviation of about $5,900 across the
seeds, and the agent is ahead in 18 seeds of 20, which a sign test puts
at p <0.001. Against the same rule with 5% cuts the lead is +$7,156, because
every cut loses in this market. That follows from the constant elasticity of
1.5 and the cost at a third of the rate, which together make the start rate the
contribution-best rate on a night that will not sell out and the floor the
revenue-best rate. In the reacting market at a market elasticity of 0.5, the
never-cut control earns +$112,877 and the agent is -$54,602 against it,
ahead in 0 seeds of 20, which docs/results.md explains as the ratchet
(docs/results.md, The rule-based control). Run on a finer clock, four ticks a
day with `--ticks 4`, the agent earns +$16,204 a seed against +$16,164 on the
daily clock, a paired difference of +$40 with a standard error of $108, p 1.0:
a finer clock earns nothing in this world, because the world's demand moves
once a day except at the shocks, and that is the expected result
(docs/results.md, The clock).

**What the model adds, and what learns.** Measured on 2026-10-15 on world v2: in
the default run the model added nothing, because every reviewer said yes to
every plan, and as a reviewer in a mode where the agent's elasticity was wrong,
Opus recovered 34% of what a perfect reviewer could at a fixed elasticity of 1.0
and 10% in a learned mode, by declining 230 and 41 plans that the oracle also
declined, while Sonnet declined 8 and 3 and Haiku none and 3, so those two tie
with saying yes to every plan. In those modes saying yes to every plan earns
-$6,265 and +$804 a seed against the oracle's +$13,107 and +$13,199, so the
reviewer matters more on world v2 than it did on world v1. The benchmark's 7,744
calls cost $85.87 at list prices. The one piece that learns from the bookings is
the elasticity estimator, a Poisson regression with a prior, and on world v2 the
agent that uses it keeps little of the gain unless the cautious rule is on
(docs/reviewers.md for the reviewers, docs/results.md for the rest).

## Data as it comes in

Data as it comes in means that the agent runs at the tick the data lands, a
rate applies from the next tick, and the next day's request carries what
happened on the dates it changed. The third of those is the read-back: each
entry in a request lists the hotel's earlier changes on its stay dates, with
the rooms booked since each against the rooms expected, so the model sees what
its last decision did before it makes the next one.

On a clock, not in real time, the loop runs, and a tick is a slice of a
simulated day: with `--ticks N` each day is cut into N ticks, the bookings
land at every tick, the rate shop at tick 2, the airlines' filings at tick 3
and the events at tick 4, each at tick 1 when N is smaller than its slot, and
the agent runs after each tick reading the feeds as of that tick. Until a feed
lands, a tick sees the previous value. N of 1 is the daily loop unchanged:
every feed lands at the one tick and the agent runs once a day, as every figure
above was measured. Real time is this loop with a wall clock behind the
sources: a feed arrives when it arrives, and the agent runs when one does.

## What this is when a customer stands behind it

Each piece here stands for something a hotel company already has. The customer
file is the market: its hotels, their curves and comp sets, its thresholds and
its calendar of events and competitor moves. The four interfaces are the
reservation system, the rate shop, the schedule feed and the events calendar,
which is why the agent reads nothing else. The stored tables are the day's
snapshot that the customer's systems write, and run-day is the daily job that
runs the agent over them, so a deployment is that job on that snapshot. The
clock is the cadence of their feeds: a feed that lands once a day gives the
daily loop, and one that lands through the day gives the ticks. The cache and
the replay are the audit trail, because every decision keeps the request the
model saw, the answer it gave and the digest that ties the two together, and a
day can be rebuilt from the tables alone. A second market is run with one flag
and no change to the agent: `hotel-market --customer customers/harbour.toml
--seed 7 --template`.

## What the world taught me

**The ratchet.** When I let the competitors follow the hotel's changes, the
rule that raises on every flag and never cuts beat the agent, and not by a
little: in the reacting market at a market elasticity of 0.5 it earns +$112,877
a seed over frozen rates, and the agent finishes $54,602 behind it, ahead in no
seed of 20. The mechanism is plain once you follow one stay date through. The
hotel raises, the competitors move half of the way three days later, the comp
median jumps, the detector reads the jump as news and lifts the hold, so the
agent raises again. The never-cut rule rides that loop on every flag without
stopping to estimate anything, which is why it climbs further than an agent
that scores each step. A revenue manager would recognise the pattern at once,
because it is what a comp set does when everyone shops everyone else and
nobody wants to be the one who cut. The gain looks real inside the simulator
because the market's demand only falls by the power of 0.5 there, and nothing
here says how much of it a real market would give back. The figures are in
[the rule-based control table](docs/results.md#the-rule-based-control).

**The convention.** The convention is announced on day 10 for stay dates 45 to
48, which is 35 days out, and at a convention hotel an announcement that late
changes very little, because the group block and most of the transient rooms
are already on the books. On world v2 the two downtown hotels hold a quarter
and a tenth of their rooms 90 days out, so the convention plans earn +$614 a
seed on their stay dates with the competitors' 15% raise and +$100 without it,
and taking the raise away moves the 20-seed mean only from +$16,164 to
+$15,611. What that told me is that the money in a convention sits in the
group block and in the minimum stay, and the agent only advises on the second
and never touches the first. The next version puts an event that is known
before the run into the day-0 preload, so the books on day 0 carry it the way
a real hotel's would. The figures are in
[the convention table](docs/results.md#the-convention-without-the-competitors-raise).

**The clock.** I built a finer clock expecting it to earn something, and on
this world it earned nothing: at four ticks a day the agent makes +$16,204 a
seed against +$16,164 on the daily clock, a paired difference of +$40 with a
standard error of $108, ahead in 10 seeds of 20. The reason is in the feeds and
not in the agent. The rate shop, the filings and the events each land once a
day, and the bookings are one draw a day split over the ticks, so a tick that
runs before the data lands sees yesterday's numbers and has nothing new to
decide. A finer clock would earn where a shop, a filing or a booking stream
moves within the day, which is what a live feed does and this one does not
([the clock table](docs/results.md#the-clock-one-tick-a-day-against-four)).
So the loop keeps three cadences: the day, on which the feeds land and the
figures are measured, the tick, at which the agent reads the feeds and a rate
takes effect, and the read-back of outcomes into the next request, which
carries what happened on a changed date back to the model as the rooms booked
since against the rooms expected.

## The limit that matters

The forecast is right by construction. With the simulator's demand scaled by
0.9, which the agent never sees, the gain falls to +$1,069 a seed, ahead in 12 seeds of 20, which a sign test puts at p 0.50, on 2026-10-15 on world v2. The demand-bias
section of docs/results.md has the table, and the other limits are in
docs/limits.md.

## Read more

- docs/results.md: the tables of every experiment, with their commands.
- docs/reviewers.md: the model as a reviewer, the oracle and the benchmark.
- docs/limits.md: the known limits, and the next version.
- docs/commands.md: every command, make target and Docker line.
- docs/schedule-feed.md: the air schedule feed as this repository models it.
- kg/: a map of the repository for agents, with kg/README.md as the legend.

The next version adds per-weekday terms to the estimator, adds cancellations
and segments, and puts an event known before the run into the preload. The
clock is an option: `--ticks N` on the main command, the bench, run-day and
demo-data, and a run on the daily clock is unchanged.
