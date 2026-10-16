# Known limits

- All data is synthetic, so no real market, airline, hotel or booking appears in
  it.
- The agent's demand forecast and booking curve are the simulator's own. A test
  holds the forecast equal to the simulator's demand at the default demand bias
  of 1.0, and the curve is never learned. The option `--demand-bias F`
  multiplies the simulator's demand by F, which the agent never sees, so its
  forecast is wrong by that factor. At 0.9 the default run keeps +$1,913 a seed
  of its +$32,899, because every raise sells fewer rooms than the agent's
  estimate says. At 1.1 it earns +$112,082 a seed, because the start rates were
  set for a smaller market. The learning agent's day-59 elasticity stays at 1.26
  to 1.49 at both biases, so a level error that is a constant factor lands in
  the estimator's intercept as designed. A weekday or an event error lands in
  the slope instead, by two to three standard errors, because it moves with the
  rate ratio on the dates where the medians and the rates move. The estimator
  learns only where the hotel has moved its own rate by several per cent across
  most of its bookings, so in a run where the hotel barely moves its rate the
  estimate stays near the prior. With `--level` the agent feeds that intercept
  back into its forecast and learns the level by day 10, but the gain at 0.9
  does not recover, because the opportunity shrank: the gain here comes from
  scarcity on the shock dates, and a market a tenth smaller has fewer nights
  that sell out, so the level halved the false pace flags and could not make
  rooms scarce. At 1.1 the level removes the false flags and the correct raises
  go with them, because the agent acts only on a flag and a market that is
  simply larger raises none (docs/results.md).
- By default the agent is handed the simulator's elasticity of 1.5;
  `--elasticity fixed:X` and `learn:X` take it away.
- Demand moves by the hotel's share of guests arriving by air times the change
  in arriving passengers, the seats at each flight's load factor; that link and
  the load factors are modelling choices.
- The minimum-stay recommendation is advice only. The simulator has no length of
  stay, and the advice is not in any estimate or result.
- The estimates assume the simulator's Poisson booking noise; real bookings
  arrive less evenly, with groups, cancellations and no-shows.
- The cost of an occupied room is one third of the start rate, which makes the
  start rate contribution-best on a night that will not sell out.
- The $250 minimum applies to a whole plan, so a small change on one day of the
  week can ride inside a plan that clears the minimum on its other days.
- The rate shop moves every day: each competitor's noise is drawn afresh per
  shop day, so a comp median wanders up to 3% around its starting level between
  shocks, and the median-change flag now meets ordinary shop noise. The comp
  median flags on days when no shock moved a median are counted in
  docs/results.md. The noise is uniform and the same size at every competitor,
  which no real shop is.
- Each hotel has its own booking curve, but the pace baseline is still normal
  demand on that curve with no group base, so "pace" here means that a shock's
  bookings have arrived. The hotels that received the convention and the new
  flights run ahead of pace every day until the stay date, and the pace and
  rules controls therefore price the shocks at one remove.
- The air schedule files two changes by default and, with `--churn`, weekly
  revisions held under the threshold by construction. A second scenario holds an
  upgauge and a frequency cut. A real feed revises in more ways than these, and
  its rows carry an arrival time (docs/schedule-feed.md).
- By default competitors never react, so `--react` makes each competitor move
  half of a hotel's change three days after it takes effect. The market's own
  price response is the customer file's 1.0 since world v2, chosen because a
  market-wide rate rise should lose demand in proportion, and
  `--market-elasticity E` sets another value for a run, with the agent told E.
  On world v1, where the default was 0.0, the reacting run earned +$111,272 a
  seed at an E of 0.0, +$72,229 at 0.5 and +$43,584 at 1.0, against +$32,899
  with neither; what those figures showed, and the loop they exposed, is in the
  market section of docs/results.md.
- There is one rate per hotel and stay date, with no room types, group blocks,
  cancellations or no-shows.
- Without an API key, every plan is accepted. A single run that did not ask for
  the template says so in its first line and names the template in its summary,
  and each decision records the reason source, but a hotel that ran it with a
  missing key would still put every queued raise live under a reason that reads
  like a review. The template is a stand-in that answers in the model's place
  when there is no key; it says yes to every plan and writes a reason from the
  entry's own figures. With a key, a call that still fails after the client's
  retries stops the run with a traceback, and the single-run route then writes
  no decisions file for the days before it.
- A change to the world, such as a fifth hotel or a second event, invalidates
  the pinned tests, the seed-7 recording under tests/fixtures and the live
  benchmark tables. The template sweeps rerun for nothing, a new recording of
  seed 7 costs about $0.08, and the live tables cost about $86 to make again.
- The benchmark ran the live models on seeds 1 to 20 in the fixed and the
  learned modes on 2026-10-15 on world v2 (docs/results.md). Only Opus recovered
  any of the oracle's margin, 34% in a fixed mode and 10% in a learned one;
  Sonnet and Haiku tie with saying yes to every plan. In the reacting market
  Opus held 27 of the 583 plans on dates changed within 14 days, and the oracle
  held none.
- The container image was built on Python 3.11, 3.12 and 3.14 and passed the
  suite on each. A seed-7 run inside it matches the native run
  (docs/results.md).
- The audit's phrase matcher does not recognise a request figure quoted in a
  different phrase, so a reason that writes "$2,780 on Monday" for the request's
  "$2,780 more than holding" is listed as unmatched; the figure is in the
  request, and the seed-7 recording has two such lines.
- On world v2 the convention is mostly on the books before day 0 because of the
  convention hotel's early booking curve, while its uplift applies only to
  demand after day 0, so an event announced on day 10 adds little; the next
  version puts an event known before the run into the preload.
- The seed-7 checksum is a byte-for-byte test on one platform: this machine's
  numpy 2.5.4 and pandas 3.0.6 give 263387b3, and a Linux run on numpy 2.5.3
  and pandas 3.0.5 gave 8faafad0 with the same decisions. The decisions file,
  not its hash, is the cross-platform test.
- The clock is event-driven on a configurable clock, not real time. With
  `--ticks N` each day is cut into N ticks and the agent runs after each, but
  the simulated feeds arrive at fixed ticks: the rate shop at tick 2, the
  airlines' filings at tick 3, the events at tick 4 and the bookings at every
  tick. A shop or a booking carries no timestamp in the feeds, so a tick knows
  only that a feed has landed, not when within the tick. The comp set does not
  react within a day: a reaction, when it is on, reads the hotel's rate three
  days back. On this world a finer clock earns nothing, because the demand
  moves once a day except at the shocks (docs/results.md, The clock); it would
  earn where shops, filings or bookings move within the day. On a finer
  clock the outcomes table still credits a decision with the rooms sold on
  later days, not with the later ticks of its own day.

The next version reprices when data arrives during the day, adds per-weekday
terms to the estimator, and adds cancellations and segments. Since world v2 the
request already lists each hotel's earlier changes on an entry's stay dates,
with the rooms booked since against the rooms expected, and the competitors'
reaction is an option of a run rather than the default.
