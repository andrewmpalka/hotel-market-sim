# Hotel market simulator

[![tests](https://github.com/andrewmpalka/hotel-market-sim/actions/workflows/test.yml/badge.svg)](https://github.com/andrewmpalka/hotel-market-sim/actions/workflows/test.yml)

A pricing agent working for one customer: a brand that runs revenue centrally
for four hotels in a made-up city. Every number is synthetic. For 60 days the
agent reads the market's feeds and recommends what to charge. Bookings continue
for 150, so no night is still on sale at the end.

Usually nothing happens. Guests book along the expected curve with random
variation, competitors' rates wobble a little, and for an ordinary date the
current price is already the best one. The exceptions fall on days 10, 20, 30
and 40. In that order, a convention is announced, new flights are filed, a
rival discounts its rooms, and an airline suspends a route. The repository
calls these shocks. They are the only events that change demand or move a comp
set, which means there is nothing to earn at any other time. Because they are
fixed before the run starts, each dollar in the results can be traced to the
shock that produced it. The schedule rows follow Cirium's published column
names, but no data here comes from that company and the project has no
affiliation with it.

![The lifestyle hotel on day 20](docs/images/day20.png)

*Day 20 at the lifestyle hotel: the filing in the news, three recommendations
with the model's reasons closed under Why, and what happened since the last
change on those dates.*

## One customer, one file

A customer is the hotel company the agent works for. Everything specific to
it sits in [customers/demo.toml](customers/demo.toml), which the simulator and
the agent both read. A new customer gets its own file and needs no code
changes.

| Option | What it sets | This customer |
| --- | --- | --- |
| Hotels | Each one's rooms and starting rate | Convention 400 rooms at $220, full-service 250 at $190, lifestyle 120 at $240, airport 150 at $140 |
| Air share | What fraction of a hotel's guests fly in, and so how much airline news moves it | Convention 60%, full-service 45%, lifestyle 50%, airport 80% |
| Normal demand | How full a typical night is, and how that varies from Monday to Sunday | 75% (the airport 85%), with each hotel's own weekday pattern |
| Booking curve | How much of a night is usually booked at each number of days out | Convention a quarter at 90 days, airport half at a week |
| Competitors | Four per hotel, priced at fixed offsets from its rate | 8% and 3% below, 3% and 8% above |
| Rate limits | The lowest and highest the agent may charge | 70% and 140% of the starting rate |
| Room cost | What the hotel spends servicing each sale | A third of the starting rate |
| Flag thresholds | What sends a night to the agent to price | Bookings off pace by 10% of the rooms or 3 standard deviations, whichever is larger; arriving passengers revised by 5%; the comp median moved 5% since yesterday |
| Hold | How long a changed night ignores pace alone | 7 days |
| Minimum value | The smallest gain over leaving the price alone that is worth sending to the model | $250 |
| Target | What each option is scored on | Contribution, which is revenue minus room cost |
| Market price response | How much demand across the city falls when the comp median rises | 1.0, which is proportional |
| Calendar | The news this file schedules | A convention announced on day 10 that raises demand 35% at the two downtown hotels on nights 45 to 48; two of the full-service hotel's competitors cutting 20% from day 30 on nights 37 to 39 |

The other two shocks, new flights on day 20 and a suspended route on day 40,
are not in this file. They belong to the simulator's airline schedule,
[src/hotel_market/schedule.py](src/hotel_market/schedule.py), which all
markets share.

Two more files share this format.
[customers/demo-intraday.toml](customers/demo-intraday.toml) moves the demo's
news to set hours and adds a close-in concert, for runs at four ticks a day.
[customers/harbour.toml](customers/harbour.toml) is another customer, three
hotels in a harbor city, and it runs with one command-line option.

## Run it

    make setup          # .venv with the package, pytest and ruff
    make test           # the fast suite; make test-all adds the ten slow ones
    make demo SEED=7    # the read-only page

**Without an API key** everything works except a new model call, including
the simulator, every experiment in docs/results.md and the demo page. Seed 7's
answers are stored in the repository, so the page shows them offline. Where
nothing is stored, a stand-in takes the model's place. It approves whatever it
is given and drafts a reason from the entry's own figures, and the output says
so. The tests and the 20-seed sweeps rely on it, because they measure what the
code chooses.

**With an API key** the model reviews each plan and explains its verdict. Put
`ANTHROPIC_API_KEY` in `.env`, then run `make live SEED=7`, or `make bench` to
compare reviewers. Responses are cached by the request's digest, so a rerun or
a replay is free. A live seed costs between $0.08 and $0.20, and the full
benchmark came to $85.87.

The other commands are in [docs/commands.md](docs/commands.md).

## Same luck twice

All of the luck in this city comes from one number, the seed. The seed fixes
a stream of numbers that look random, and the same seed gives the same stream
on any machine. That stream decides which night each guest books, how far each
rate shop wobbles and how many people come to the concert, so the seed settles
all five months of luck before the run starts. The agent run and the
frozen-rate run use the same seed, which means they see the same guests on the
same days and any difference between them is the agent's doing. Anyone who
clones the repository and runs seed 7 gets the same decisions file, byte for
byte, and can check the results here for themselves. Seeds 1 to 20 give twenty
different five-month histories, and the results average over them and show
the spread, so you can tell a real gain from a lucky seed. Seed 7 is the demo
seed because it was the number typed into the first run, and it is row 7 of
every table.

## What the agent does each day

1. **Look.** For every hotel and stay date: are bookings ahead of or behind
   pace (where they usually are this far from arrival), did the comp median
   move (the middle rate among the hotel's four competitors), did arriving
   passengers change, was an event announced?
2. **Price.** On the dates where something changed, estimate what holding,
   raising 5%, raising 10% or lowering 5% would earn, on the rooms still
   unsold, with the chance of a sell-out counted.
3. **Ask.** Hand the best plan to the model: here are the numbers, agree or
   hold, and write a reason a revenue manager can read.
4. **Apply.** An accepted rate starts at the next tick, and those dates are
   left alone for seven days.

Code computes every number. The model only chooses between the plan and
holding, and its answer is checked against the options it was given. Without
a key, a stand-in answers in its place: it says yes to every plan and writes
a reason from the entry's own figures.

## The result

Twenty seeds, the agent against frozen rates, same booking luck in both runs.

| | |
| --- | ---: |
| Seeds where the agent earned more contribution (room revenue minus the cost of servicing each room sold) | 20 of 20 |
| Mean contribution change per seed | +$16,164 |
| Smallest and largest | +$11,589 and +$23,394 |
| Mean room revenue change per seed | −$27,684 |
| Rate changes over the 20 seeds | 106 |

Room revenue falls and contribution rises: the agent raises on the nights
that will fill, sells slightly fewer rooms at a better rate, and saves the
cost of servicing the rooms it did not sell. RevPAR is flat or lower at every
hotel. Say that before a hotel person asks.

| Hotel | Occupancy, fixed / agent | Average rate | RevPAR |
| --- | ---: | ---: | ---: |
| Downtown convention hotel | 76.9% / 76.8% | $220.00 / $220.03 | $169.07 / $169.07 |
| Downtown full-service hotel | 76.5% / 76.5% | $190.00 / $190.06 | $145.37 / $145.36 |
| Lifestyle hotel | 77.0% / 76.1% | $240.00 / $242.50 | $184.76 / $184.44 |
| Airport hotel | 88.9% / 86.1% | $140.00 / $143.44 | $124.50 / $123.53 |

The forecast is the simulator's own formula, so this is a measurement of the
loop, not of a forecast. Scale the simulator's demand by 0.9 without telling
the agent and the gain falls to +$1,069 a seed, ahead in 12 seeds of 20.

Details: [the sweep](docs/results.md), [the revenue manager's
measures](docs/results.md#in-a-revenue-managers-measures), [the demand
bias](docs/results.md#the-demand-bias).

## Against a rule, not just against frozen rates

Frozen rates are an easy opponent. The fair one is a rule that raises 5% on
the same flags and never lowers, with no estimate and no model.

| | Per seed |
| --- | ---: |
| The never-cut rule against frozen rates | +$10,468 |
| The agent's lead over the rule | +$5,696, ahead in 18 of 20 |
| The lead over the same rule with 5% cuts | +$7,156 |

Every cut loses in this market, because with the cost at a third of the
rate and an elasticity of 1.5 the start rate is already the best rate on a
night that will not sell out. The gain lives in the nights the shocks make
scarce, and the new flights carry nearly all of it.

Details: [the rule-based control](docs/results.md#the-rule-based-control).

## What the model adds

In the default run, nothing to the number: every reviewer, the stand-in and
the three models, said yes to every plan, because the plans were right. The
model's judgment shows only when the plans are wrong, so the benchmark makes
them wrong on purpose by giving the agent the wrong elasticity, and scores
each model on which plans it declines against a perfect reviewer.

| Reviewer | Share of the perfect reviewer's margin recovered | Plans declined |
| --- | ---: | ---: |
| Opus, fixed wrong elasticity | 34% | 230 |
| Opus, learned elasticity | 10% | 41 |
| Sonnet | ties with saying yes | 8 and 3 |
| Haiku | ties with saying yes | 0 and 3 |

In those modes saying yes to everything earns −$6,265 and +$804 a seed; the
perfect reviewer earns +$13,107 and +$13,199. The benchmark's 7,744 calls
cost $85.87.

Details: [docs/reviewers.md](docs/reviewers.md).

## Data as it comes in

The loop runs on a clock, not in real time. With `--ticks 4` each day has
four moments: bookings land at every one, the rate shop at the second,
airline filings at the third, events at the fourth. The agent runs after
each, a rate applies from the next, and the next day's request carries what
happened on the dates it changed: "since then 2 rooms booked against 1
expected." The default is one tick a day, and that run is byte-identical to
before the clock existed.

On the demo market a finer clock earns nothing, because the news lands once
a day. On the same market with news inside the day it earns real money,
because a concert announced at ten in the morning sells rooms by noon.

| Market | Daily clock | Four ticks | Difference |
| --- | ---: | ---: | ---: |
| Demo | +$16,164 | +$16,204 | +$40, ahead in 10 of 20 |
| Demo with intraday news | +$19,640 | +$21,741 | +$2,101, ahead in 18 of 20 |

On the concert nights the daily loop sells 104 rooms at the old rate before
it can raise; the four-tick loop sells 30. The agent is the same code with
the same thresholds on both markets. The difference is the news.

![The lifestyle hotel on day 25 at 11:00](docs/images/day25.png)

*Day 25 at the lifestyle hotel, 11:00: the concert just announced, the
recommendation, and the model's reason opened under Why.*

Details: [the clock](docs/results.md#the-clock-one-tick-a-day-against-four),
[the clock with intraday news](docs/results.md#the-clock-on-the-world-with-intraday-news).

## What this is when a customer stands behind it

| In the repository | At a customer |
| --- | --- |
| The customer file | Their market: hotels, curves, comp sets, thresholds, calendar |
| The four interfaces | Reservations, rate shop, schedule feed, events calendar |
| The stored tables and `run-day` | The day's snapshot their systems write, and the daily job |
| The clock | The cadence of their feeds |
| The cache and `replay` | The audit trail: every request, every answer, every day rebuildable |

A second market runs from its file with one flag and no change to the agent:
`hotel-market --customer customers/harbour.toml --seed 7 --template`. Its
20-seed gain is +$4,815 a seed, ahead in 18 of 20.

## What the world taught me

- When competitors follow the hotel's raises, the agent reads each moved comp
  median as news and raises again, and the never-cut rule beats it by $54,602
  a seed.
- The convention made little difference, because it is announced 35 days out
  and the convention hotel has most of those nights booked by then, so the
  plans earn only $614 a seed on its dates.
- Pricing four times a day instead of once only paid off where news arrived
  during the day, adding $2,101 a seed on the market with intraday news and
  $40 on the demo market.

Details: [the rule-based control](docs/results.md#the-rule-based-control),
[the convention](docs/results.md#the-convention-without-the-competitors-raise).

## What I'd build next

[docs/prd-v2-next-steps.md](docs/prd-v2-next-steps.md) is my design for the
next version, and none of it is built. It starts from five gaps in this
version, and the first is that the model sees a plan and its numbers and
nothing else, so it can't check why a plan might be wrong. The design splits
the model's job in two. An investigator, which is a model with read-only
tools, looks up what a revenue manager would check before acting, such as the
last week's bookings against the forecast, the comp median at each of the last
five shops and the hotel's own recent changes on those nights. It records what
it found but can't choose an action. A decider reads that record and chooses
to recommend the plan, hold it or send it to a person, and code checks the
choice before anything changes.

The proposed decider is TypeSafe's Jev, which returns one typed choice with a
probability for each option. The current reviewer uses the same interface, so
the benchmark can compare the two on the same evidence. Three fixes need no
model, such as ignoring a comp move that follows our own change, so they come
first. Each part ships only if the benchmark shows it beats the simpler thing
it replaces. All of it is controlled by a setting, so every figure in this
README can still be reproduced.

## How it was built

The project started from a PRD, which is kept unchanged in
[docs/prd.md](docs/prd.md). After that, CLAUDE.md was the live spec, and each
prompt built one module with its tests. A checker keeps the knowledge graph
under [kg/](kg/) consistent with the code. The project had three adversarial
reads before anyone else saw it.

## Read more

- [docs/results.md](docs/results.md): every experiment, one table each.
- [docs/reviewers.md](docs/reviewers.md): the model as a reviewer.
- [docs/limits.md](docs/limits.md): what this does not model, and the next version.
- [docs/prd-v2-next-steps.md](docs/prd-v2-next-steps.md): the design for the next version, not yet built.
- [docs/commands.md](docs/commands.md): every command and make target.
- [docs/schedule-feed.md](docs/schedule-feed.md): the air schedule feed as modelled.
- [kg/README.md](kg/README.md): the knowledge graph's legend.