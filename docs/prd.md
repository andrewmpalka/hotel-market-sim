# Hotel market simulator: product requirements

## The problem

A central revenue manager for four hotels of one brand sees the same signals
every day. Bookings run ahead of or behind the curve, competitors move their
rates, an event is announced, an airline files new flights or cancels a route.
Each signal might deserve a rate change, and most do not. The manager cannot
read every stay date of every hotel every day, so the work is to find the stay
dates where something changed, work out what a change would be worth, and say
why in words the manager can read.

Nothing in this project uses real data. I wanted to show that the loop works,
that it can be tested, and that a model's part in it can be measured, before
any real feed is involved. So the project is two things. A simulator of one
made-up market produces the signals. An agent reads the simulated feeds each
day and recommends rate changes.

## Who it is for

The user inside the simulation is one central revenue manager who covers all
four hotels. The user outside the simulation is a developer who has to stand
this up for a new customer, change its market without touching the agent, and
explain every number it produces.

## Goals

1. Every number the agent acts on is computed by code. The model chooses
   between options code built and writes the reason, and nothing else.
2. Two runs with the same seed and settings produce the same bookings and the
   same decisions, so a change in the agent can be compared booking for
   booking against the run without it.
3. Nothing uses information before the day it becomes known. Every lookup
   takes the day it is made on. A flight counts from the day it is filed, an
   event from the day it is announced, a competitor's rate from the day it is
   shopped.
4. The agent reads its data through interfaces that stand for the feeds a
   real revenue system has, so that a customer's systems can replace the
   simulator without a change above the interface.
5. Everything specific to the market lives in one customer file. The
   constants that describe the simulator stay in code.
6. The model's answers are cached by a digest of the request, so a rerun is
   free and exact, and the tests run offline with a template, a stand-in that
   answers in the model's place when there is no key; it says yes to every
   plan and writes a reason from the entry's figures.
7. The result is reported as it comes out. No rule is tuned to force a gain.

## Non-goals

- No real market, hotel, airline or booking. The schedule rows follow a
  published data dictionary's column names, and every row is synthetic.
- No web application. The one interface is a read-only page over a file the
  daily command writes.
- No database server. The stored tables are a file.
- No room types, group blocks, cancellations, no-shows or length of stay in
  the first versions. The minimum-stay recommendation is advice only.
- No post-training. The model is a reviewer, and its value is measured, not
  assumed.

## The world

Four hotels in one made-up city. Each has a room count, a start rate, a share
of guests who arrive by air, a normal occupancy, seven day-of-week factors
and four competitors at fixed offsets from its start rate, so each hotel
starts level with its comp median. Every occupied room costs one third of the
start rate to service, and contribution is room revenue minus that cost.

Bookings arrive along a booking curve over the 90 days before a stay date, as
Poisson draws around expected demand, and demand responds to the hotel's rate
against its comp median with a constant elasticity. The agent decides on
days 0 to 59, and the booking loop runs to day 149 with rates frozen so every
stay date is complete.

Four shocks become known on fixed days. A convention on day 10, which lifts
demand at the two downtown hotels and moves their comp sets the same day. New
flights filed on day 20. A competitor rate cut seen in the day-30 shop. A
route suspension filed on day 40. The schedule feed carries three traps that
give a wrong seat count if ignored, which is what a real feed does.

## What the agent does each day

It computes six numbers for every hotel and stay date in the window, flags
the rows where one crossed a threshold, merges consecutive flagged dates into
one flag, builds hold, raise 5%, raise 10% and lower 5% for each flag,
estimates each on the rooms still unsold with the chance of a sell-out
counted, picks the best per day of the week, queues the plan only if it is
worth a minimum over holding, asks the model once per hotel per day, applies
accepted rates from tomorrow, and holds changed dates for seven days.

## Modules, in build order

Each module was one prompt, built with its tests, and reviewed before the
next. The order follows the data.

1. world: the hotel and competitor types and the calendar.
2. shocks: the convention and the competitor cut.
3. demand: the simulator's expected demand.
4. shops: competitor rates and medians from a seeded shop.
5. bookings: the curve, the preload and the daily loop.
6. detect: the numbers, the flags and the hold.
7. plan, model, agent: the candidates and estimates, the call with its cache
   and template, and the daily loop.
8. cli: both runs, the decisions file, the daily queues and the summary.
9. estimate: a learned elasticity, for the modes where the agent is not told
   it.
10. sources, forecast, simulated: the boundary, the agent's own demand
    model, and the simulator behind the interfaces.
11. customer: the market file.
12. stored: the interfaces over stored tables, and the day-by-day commands.

Later versions added the benchmark of the model as a reviewer with an oracle
grader, a rule-based control, the demo page, and the knowledge graph that
maps the repository for agents.

## Done when

- The schedule module gives the right seat count with the traps in the data,
  and summing another way gives a wrong one.
- A fixed-rate run ends with occupancy between 60% and 90% at every hotel.
- Each of the four shocks produces a flag within three days of becoming
  known.
- Two runs with the same seed give identical decisions files.
- Replaying a day makes no model call and prints the same queue.
- The summary reports room revenue and contribution for both runs, counted
  over every stay date and again over only the pairs where a rate changed.
- With the agent's elasticity set apart from the simulator's, the learned
  estimate lands within three standard errors of the truth by day 59.

## How success is measured

Contribution against the fixed-rate run over 20 seeds, with the spread. The
same against a rule that prices on the same flags with no estimate and no
model, because frozen rates are not a fair control. The model's own part,
measured by a benchmark where a perfect reviewer sets the ceiling and each
model is scored on which plans it declines. And determinism, which is a test
and not a measure.

## Risks and open questions, as written before the build

- The agent's forecast is the simulator's own formula, so every headline
  figure is a perfect-information result. It measures the loop, not a
  forecast. The demand-bias experiment is there to show what a forecast
  error does.
- The elasticity is one constant. A real market has many.
- Air seats move hotel demand by a share times a fractional change, with no
  ramp or lag. That is a modelling choice.
- With the cost at a third of the rate and this elasticity, the start rate is
  already the best rate on a night that will not sell out, so the agent can
  only gain on scarce nights. That is a property of the world, and the
  results have to be read with it.
- A model that says yes to every plan looks the same as one that judges well
  whenever the plans are right. The benchmark has to make the plans wrong to
  see the difference.

## Versions

- v0, modules 1 to 8. A working loop with the template, one seed, both runs.
- v1, modules 9 to 12. Elasticity learning, the boundary, the customer file,
  the stored tables.
- v2. The reviewer benchmark, the rule-based control, the demo page, the
  knowledge graph, an adversarial review by three reviewer profiles and the
  fixes it produced, on 14 and 15 October 2026.
- v3. A world that earns its headline (market-level price response,
  per-hotel curves, a rate shop that moves, a seat link with a load factor),
  past decisions and outcomes in the record, repricing on a configurable
  clock (docs/results.md, The clock), and a second market run with one flag
  and no change to the agent (docs/results.md, The second market), then a
  last adversarial read by the same three reader profiles on 16 October 2026,
  before the repository was frozen.
