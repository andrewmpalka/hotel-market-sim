# Known limits

The figures here are world v2's, measured on 2026-10-15 and 2026-10-16, unless a
limit names world v1.

- All data is synthetic, so no real market, airline, hotel or booking appears in
  it.
- The agent's demand forecast and booking curve are the simulator's own, and the
  curve is never learned. The option `--demand-bias F` multiplies the
  simulator's demand by a factor the agent never sees, and at 0.9 the default
  run keeps +$1,069 a seed of its +$16,164.
- The estimator learns only where the hotel has moved its own rate by several
  per cent across most of its bookings, and otherwise its estimate stays near
  the prior. A level error by a constant factor lands in its intercept as
  designed, but a weekday or an event error lands in the slope, by two to three
  standard errors.
- With `--level` the agent feeds the fitted level back into its forecast and
  learns it by day 10, but the gain at 0.9 does not recover. At 1.1 the level
  removes the false flags, and the correct raises go with them.
- By default the agent is handed the simulator's elasticity of 1.5;
  `--elasticity fixed:X` and `learn:X` take it away.
- Demand moves by the hotel's share of guests arriving by air times the change
  in arriving passengers, the seats at each flight's load factor. That link and
  the load factors are modelling choices.
- The minimum-stay recommendation is advice only. The simulator has no length of
  stay, and the advice is not in any estimate or result.
- The estimates assume the simulator's Poisson booking noise; real bookings
  arrive less evenly, with groups, cancellations and no-shows.
- The cost of an occupied room is one third of the start rate, which makes the
  start rate contribution-best on a night that will not sell out.
- The $250 minimum applies to a whole plan. A small change on one day of the
  week can therefore ride inside a plan that clears the minimum on its other
  days.
- The rate shop draws each competitor's noise afresh every day, so between
  shocks a comp median wanders up to 3% around its starting level. The
  median-change flag therefore meets ordinary shop noise, and that noise is
  uniform and the same size at every competitor, which no real shop is.
- The pace baseline is normal demand on each hotel's own booking curve with no
  group base, so "pace" here means that a shock's bookings have arrived. The
  hotels the convention and the new flights reach remain ahead of pace until the
  stay date, so the pace and rules controls price the shocks at one remove.
- The air schedule files two changes by default, `--churn` adds weekly revisions
  held under the threshold by construction, and a second scenario holds an
  upgauge and a frequency cut. A real feed revises in more ways than these, and
  its rows carry an arrival time (docs/schedule-feed.md).
- By default competitors never react, and `--react` makes each competitor move
  half of a hotel's change three days after it takes effect. The market's own
  price response is the customer file's 1.0, and `--market-elasticity E` sets
  another value for a run, with the agent told E.
- There is one rate per hotel and stay date, with no room types, group blocks,
  cancellations or no-shows.
- Without an API key every plan is accepted, because the template answers in the
  model's place and says yes to every plan. A single run without the template
  flag warns in its first line, but every queued raise would still go live under
  a reason that reads like a review.
- With a key, a call that still fails after the client's retries stops the run
  with a traceback. The single-run route then writes no decisions file for the
  days before it.
- A change to the world, such as a fifth hotel or a second event, invalidates
  the pinned tests, the seed-7 recordings under tests/fixtures and the live
  benchmark tables. The template sweeps rerun for nothing, but the live tables
  cost about $86 to make again.
- In the benchmark only Opus recovered any of the oracle's margin, 34% in a
  fixed mode and 10% in a learned one, while Sonnet and Haiku tie with saying
  yes. In the reacting market Opus held 25 of the 577 plans on dates changed
  within 14 days, and the oracle held none.
- The container image was built before world v2, on Python 3.11, 3.12 and 3.14,
  and passed the suite on each. A seed-7 run inside it matched the native run of
  world v1 (docs/results.md).
- The audit's phrase matcher misses a request figure quoted in another phrase,
  so a reason's "$2,780 on Monday" for the request's "$2,780 more than holding"
  counts as unmatched. The daily seed-7 recording has two such reasons with five
  such figures, and the intraday recording has two more with seven, every one of
  them in the request.
- The convention hotel's early booking curve puts most of the convention on the
  books before day 0, and its uplift applies only to demand after day 0. An
  event announced on day 10 therefore adds little, and a later version puts an
  event known before the run into the preload.
- The seed-7 checksum is a byte-for-byte test on one platform, because this
  machine's numpy 2.5.4 and pandas 3.0.6 give 263387b3 where a Linux run gave
  8faafad0. The decisions were the same on both, so the cross-platform test is
  the decisions file itself.
- The loop is event-driven on a configurable clock, and nothing in it happens in
  real time. With `--ticks N` the agent runs after each of N ticks a day, and
  each simulated feed lands at a fixed tick unless the customer file names one.
- A shop or a booking carries no timestamp in the feeds, so a tick knows that a
  feed has landed and nothing about when within the tick. The comp set never
  reacts within a day, because the reaction, when it is on, reads the hotel's
  rate three days back.
- On the demo market a finer clock earns nothing, because the demand moves once
  a day except at the shocks. On the intraday market it earns +$2,101 a seed,
  because the concert's rush books within the day.
- The outcomes table credits a decision only with rooms sold on later days, even
  on a finer clock, so the rest of its own day is left out.
- An event's rush is a share of its uplift spread evenly over the ticks from the
  announcement to the end of the next day. The simulator therefore knows how
  many rooms a tick books and nothing about when within the tick they came.
- The intraday market is a second file, customers/demo-intraday.toml, and a file
  that names no tick for its news lands it where the slots put it.
- An event's competitor raise follows the tick the event is known at, so a shop
  earlier in that day shows the old rates. An event with no named tick shows its
  raise in every shop of its day, as before.
- The request's seat_change and seat_revision fields carry arriving-passenger
  figures under their world v1 names, so a recorded reason may say seats where
  the page's news line says passengers. The names are request fields and stay.
- The cache keys a market by the name field of its customer file, so two files
  that share a name share cache/<name>/. A keyed run of the second then stops
  with StaleCache until one of them is renamed.
- The hosted workflow installs the dev extra alone on a runner with no browser,
  so the five demo-page tests and the two screenshot tests skip there. They run
  only where make demo has installed streamlit and a Chromium is present.

<details><summary>Notes</summary>

At a demand bias of 0.9 every raise sells fewer rooms than the agent's estimate
says, which is why the default run keeps so little. At 1.1 it earns +$66,687 a
seed, because the start rates were set for a smaller market. A test holds the
forecast equal to the simulator's demand at the default demand bias of 1.0.

The learning agent's day-59 elasticity stays at 1.40 to 1.51 at a bias of 0.9
and 1.43 to 1.50 at 1.1, which shows the level error landing in the intercept. A
weekday or an event error moves with the rate ratio on the dates where the
medians and the rates move, so it lands in the slope instead.

The gain at 0.9 does not recover because the opportunity shrank. The gain here
comes from scarcity on the shock dates, and a market a tenth smaller has fewer
nights that sell out. The level cut the flags from 5420 to 1538 over the 20
seeds, but it could not make rooms scarce. At 1.1 the correct raises go because
the agent acts only on a flag, and a market that is simply larger raises none
([docs/results.md](results.md#the-intercept-fed-back)).

The comp median flags on days when no shock moved a median are counted in
[docs/results.md](results.md).

The market response of 1.0 is the default since world v2, chosen because a
market-wide rate rise should lose demand in proportion. On world v1, where the
default was 0.0, the reacting run earned +$111,272 a seed at an E of 0.0,
+$72,229 at 0.5 and +$43,584 at 1.0. Without either, the run earned +$32,899,
and the market section of
[docs/results.md](results.md#the-market-level-price-response) says what those
figures showed and the loop they exposed.

A single run that did not ask for the template also names the template in its
summary, and each decision records the reason source. The template writes its
reason from the entry's own figures.

A new recording of seed 7 costs about $0.08 on the daily clock and $0.20 on the
intraday market.

The benchmark ran the live models on seeds 1 to 20 in the fixed and the learned
modes ([docs/results.md](results.md#the-benchmark-of-the-reviewers)).

The checksum is the first eight hex digits of the sha256 of decisions.jsonl
after `hotel-market --seed 7 --template`. The Linux run used numpy 2.5.3 and
pandas 3.0.5.

Without a named tick the rate shop lands at tick 2, the airlines' filings at
tick 3, the events at the day's last tick and the bookings at every tick.

The clock figures are in
[docs/results.md](results.md#the-clock-one-tick-a-day-against-four) and in its
[intraday section](results.md#the-clock-on-the-world-with-intraday-news).

Keeping the intraday news in a second file leaves the pinned default market, its
recording and its checksum unchanged.

</details>

The next version is a design in
[docs/prd-v2-next-steps.md](prd-v2-next-steps.md), and none of it is built. It
leaves the simulator and the planner's choice of rates as they are, and it
changes how a plan is checked before it goes ahead. A later version adds
per-weekday terms to the estimator, adds cancellations and segments, and puts an
event known before the run into the preload. The request already lists each
hotel's earlier changes on an entry's stay dates, with the rooms booked since
against the rooms expected. The competitors' reaction is already an option that
a run turns on.
