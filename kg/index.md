# Index

Every node on one line: ID, status and name, with the file for a constant.
`python kg_check.py --write-index` writes this file from the node files, and
the check fails when it differs from what that would write or when this file
passes 3,000 words. `README.md` is the legend. The table counts each file's
nodes and its words, len(text.split()) over the file.

| File | Nodes | Words |
| --- | ---: | ---: |
| modules.md | 32 | 4,521 |
| data.md | 33 | 4,689 |
| rules.md | 134 | 5,865 |
| shocks.md | 9 | 1,033 |
| concepts.md | 12 | 1,370 |
| measures.md | 14 | 962 |
| sources.md | 4 | 855 |
| decisions.md | 71 | 10,610 |
| results.md | 45 | 7,681 |
| forks.md | 14 | 2,037 |
| unknowns.md | 16 | 2,172 |
| every node file | 384 | 41,795 |
| index.md | | 2,999 |

## Modules (`modules.md`)

- MOD-01 [C] schedule.py
- MOD-02 [C] world.py
- MOD-03 [C] shocks.py
- MOD-04 [C] demand.py
- MOD-05 [C] shops.py
- MOD-06 [C] bookings.py
- MOD-07 [C] detect.py
- MOD-08 [C] plan.py
- MOD-09 [C] model.py
- MOD-10 [C] agent.py
- MOD-11 [C] text.py
- MOD-12 [C] cli.py
- MOD-13 [C] __init__.py
- MOD-14 [C] __main__.py
- MOD-15 [C] kg_check.py
- MOD-16 [C] estimate.py
- MOD-17 [C] sources.py
- MOD-18 [C] forecast.py
- MOD-19 [C] simulated.py
- MOD-20 [C] customer.py
- MOD-21 [C] stored.py
- MOD-22 [C] scripts/live_audit.py
- MOD-23 [C] bench.py
- MOD-24 [C] scripts/median_path.py
- MOD-25 [C] policy.py
- MOD-26 [C] demo_data.py
- MOD-27 [C] demo_page.py
- MOD-28 [C] scripts/demo_screenshots.py
- MOD-29 [C] scripts/no_comp_raise.py
- MOD-30 [C] scripts/measures.py
- MOD-31 [C] scripts/tick_sweep.py
- MOD-32 [C] scripts/tick_lag.py

## Data (`data.md`)

- DAT-01 [C] The schedule table
- DAT-02 [C] Seats and passengers by day, with their change and revision
- DAT-03 [C] Route and Shock
- DAT-04 [C] Hotel, Competitor and the customer's hotels
- DAT-05 [C] Event and RateCut
- DAT-06 [C] The rate shop
- DAT-07 [C] Books
- DAT-08 [C] The detect table
- DAT-09 [C] Flag
- DAT-10 [C] StayDate
- DAT-11 [C] Candidate
- DAT-12 [C] WeekdayGroup
- DAT-13 [C] FlagNumbers and Range
- DAT-14 [C] Entry
- DAT-15 [C] Advice
- DAT-16 [C] The model request
- DAT-17 [C] The cache record
- DAT-18 [C] A decisions.jsonl line
- DAT-19 [C] SeedResult
- DAT-20 [C] Comparison
- DAT-21 [C] Pricing
- DAT-22 [C] ElasticityMode
- DAT-23 [C] Observations and Estimate
- DAT-24 [C] ArmResult
- DAT-25 [C] The four sources
- DAT-26 [C] BookingHistory
- DAT-27 [C] Customer
- DAT-28 [C] The stored tables
- DAT-29 [C] The recorded live runs
- DAT-30 [C] The call record
- DAT-31 [C] DeclineCounts
- DAT-32 [C] Reviewer
- DAT-33 [C] The demo file

## Rules and constants (`rules.md`)

- RUL-01 [C] Code computes every number — kg/rules.md
- RUL-02 [C] Every run takes a seed — kg/rules.md
- RUL-03 [C] Nothing is used before the day it becomes known — kg/rules.md
- RUL-04 [C] SIM_START — src/hotel_market/schedule.py
- RUL-05 [C] HORIZON_DAYS — src/hotel_market/schedule.py
- RUL-11 [C] EQUIPMENT — src/hotel_market/schedule.py
- RUL-90 [C] CHURN_STREAM — src/hotel_market/schedule.py
- RUL-91 [C] CHURN_WEEKS — src/hotel_market/schedule.py
- RUL-92 [C] CHURN_SHIFTS — src/hotel_market/schedule.py
- RUL-95 [C] CHURN_BLOCK — src/hotel_market/schedule.py
- RUL-125 [C] LOAD_FACTOR — src/hotel_market/schedule.py
- RUL-126 [C] RAMP_LOAD_FACTORS — src/hotel_market/schedule.py
- RUL-127 [C] RAMP_DAYS — src/hotel_market/schedule.py
- RUL-12 [C] SIM_DAYS — src/hotel_market/world.py
- RUL-13 [C] LOOKAHEAD_DAYS — src/hotel_market/world.py
- RUL-128 [C] TICKS_PER_DAY — src/hotel_market/world.py
- RUL-129 [C] SHOP_TICK — src/hotel_market/world.py
- RUL-130 [C] FILING_TICK — src/hotel_market/world.py
- RUL-131 [H] EVENT_TICK — kg/rules.md
- RUL-14 [H] FLOOR_SHARE — kg/rules.md
- RUL-15 [H] CEILING_SHARE — kg/rules.md
- RUL-16 [H] COST_SHARE — kg/rules.md
- RUL-17 [H] COMP_RATE_OFFSETS — kg/rules.md
- RUL-18 [H] DOW_FACTORS — kg/rules.md
- RUL-23 [H] CURVE_DAYS_OUT — kg/rules.md
- RUL-24 [H] CURVE_SHARE — kg/rules.md
- RUL-25 [H] HOTEL_ROW — kg/rules.md
- RUL-82 [C] DEMAND_BIAS — src/hotel_market/demand.py
- RUL-87 [C] MARKET_ELASTICITY — src/hotel_market/demand.py
- RUL-19 [C] NOISE — src/hotel_market/shops.py
- RUL-20 [C] NOISE_STREAM — src/hotel_market/shops.py
- RUL-83 [C] REACTION_SHARE — src/hotel_market/shops.py
- RUL-84 [C] REACTION_LAG — src/hotel_market/shops.py
- RUL-21 [C] ELASTICITY — src/hotel_market/bookings.py
- RUL-22 [C] BOOKING_STREAM — src/hotel_market/bookings.py
- RUL-132 [C] TICK_STREAM — src/hotel_market/bookings.py
- RUL-88 [C] ORACLE_MARKET_ELASTICITY — src/hotel_market/forecast.py
- RUL-26 [H] PACE_SHARE — kg/rules.md
- RUL-27 [H] PACE_NOISE_SD — kg/rules.md
- RUL-28 [H] SEAT_THRESHOLD — kg/rules.md
- RUL-29 [H] MEDIAN_THRESHOLD — kg/rules.md
- RUL-30 [H] HOLD_DAYS — kg/rules.md
- RUL-39 [H] AGENT_ELASTICITY — kg/rules.md
- RUL-56 [C] ORACLE_ELASTICITY — src/hotel_market/plan.py
- RUL-40 [H] MIN_VALUE_AT_STAKE — kg/rules.md
- RUL-43 [C] CANDIDATES — src/hotel_market/plan.py
- RUL-54 [C] BAND_STANDARD_ERRORS — src/hotel_market/plan.py
- RUL-76 [C] RETRIES — src/hotel_market/model.py
- RUL-77 [C] BACKOFF_SECONDS — src/hotel_market/model.py
- RUL-50 [C] PRIOR_SD — src/hotel_market/estimate.py
- RUL-51 [C] ELASTICITY_MIN — src/hotel_market/estimate.py
- RUL-52 [C] ELASTICITY_MAX — src/hotel_market/estimate.py
- RUL-96 [C] LEVEL_OBSERVATIONS — src/hotel_market/estimate.py
- RUL-97 [C] LEVEL_MIN — src/hotel_market/estimate.py
- RUL-98 [C] LEVEL_MAX — src/hotel_market/estimate.py
- RUL-53 [C] REPORT_DAYS — src/hotel_market/cli.py
- RUL-124 [C] market.elasticity — customers/demo.toml
- RUL-81 [C] BENCH_MODES — src/hotel_market/cli.py
- RUL-85 [C] REPEAT_WINDOW — src/hotel_market/cli.py
- RUL-80 [C] PRICES — src/hotel_market/bench.py
- RUL-99 [C] POLICY_STEP — src/hotel_market/policy.py
- RUL-102 [C] STANDARD_ERROR_EDGES — src/hotel_market/bench.py
- RUL-58 [C] target — customers/demo.toml
- RUL-59 [C] floor_share — customers/demo.toml
- RUL-60 [C] ceiling_share — customers/demo.toml
- RUL-61 [C] cost_share — customers/demo.toml
- RUL-62 [C] pace_share — customers/demo.toml
- RUL-63 [C] pace_noise_sd — customers/demo.toml
- RUL-64 [C] seat_threshold — customers/demo.toml
- RUL-65 [C] median_threshold — customers/demo.toml
- RUL-66 [C] hold_days — customers/demo.toml
- RUL-67 [C] min_value_at_stake — customers/demo.toml
- RUL-68 [C] booking_curve.days_out — customers/demo.toml
- RUL-69 [C] booking_curve.share — customers/demo.toml
- RUL-109 [C] RATE_AXIS — src/hotel_market/demo_data.py
- RUL-110 [C] GAIN_TICK_DAYS — src/hotel_market/demo_data.py
- RUL-115 [C] PLOT_HEIGHTS — src/hotel_market/demo_page.py
- RUL-120 [C] AXIS_LABEL_SIZE — src/hotel_market/demo_page.py
- RUL-121 [C] TILE_SIZES — src/hotel_market/demo_page.py
- Labels: RUL-06, RUL-07, RUL-08, RUL-09, RUL-10, RUL-89, RUL-93, RUL-133, RUL-134, RUL-31, RUL-32, RUL-33, RUL-34, RUL-35, RUL-36, RUL-37, RUL-38, RUL-41, RUL-42, RUL-44, RUL-45, RUL-49, RUL-46, RUL-47, RUL-75, RUL-78, RUL-79, RUL-48, RUL-55, RUL-74, RUL-122, RUL-86, RUL-94, RUL-100, RUL-101, RUL-72, RUL-73, RUL-70, RUL-71, RUL-57, RUL-103, RUL-104, RUL-105, RUL-106, RUL-107, RUL-108, RUL-111, RUL-112, RUL-113, RUL-114, RUL-116, RUL-117, RUL-123, RUL-118, RUL-119

## Shocks (`shocks.md`)

- SHK-01 [C] The convention
- SHK-02 [C] The new flights
- SHK-03 [C] The competitor rate cut
- SHK-04 [C] The route suspension
- SHK-05 [C] The upgauge
- SHK-06 [C] The frequency cut
- SHK-07 [C] The churn
- SHK-08 [C] The concert
- SHK-09 [C] The weekend repricing

## Concepts (`concepts.md`)

- CON-01 [C] Booking curve
- CON-02 [C] Pace
- CON-03 [C] Competitor set
- CON-04 [C] Competitor median
- CON-05 [C] Rate ratio
- CON-06 [C] Elasticity
- CON-07 [C] Contribution
- CON-08 [C] Value at stake
- CON-09 [C] Sell-out
- CON-10 [C] Hold period
- CON-11 [C] The cautious rule
- CON-12 [C] The customer's real counterparts

## Measures (`measures.md`)

- MEA-01 [C] Occupancy
- MEA-02 [C] Average rate
- MEA-03 [C] Revenue per available room
- MEA-04 [C] Room revenue
- MEA-05 [C] Contribution
- MEA-06 [C] Regret
- MEA-07 [C] Accept rate
- MEA-08 [C] Decline precision
- MEA-09 [C] Decline recall
- MEA-10 [C] Decline F1
- MEA-11 [C] Dollar-weighted decline recall
- MEA-12 [C] Recovered share
- MEA-13 [C] Decline rate by standard-error group
- MEA-14 [C] Plans on recently changed dates

## Sources (`sources.md`)

- SRC-01 [C] Bookings
- SRC-02 [C] Competitor rate shops
- SRC-03 [C] Air schedules
- SRC-04 [C] Events

## Decisions (`decisions.md`)

### Market and agent design

- DEC-01 [C] Code computes every number; the model only chooses and writes
- DEC-02 [C] Nothing is used before the day it becomes known
- DEC-03 [C] The day-0 preload: bookings made before the run starts
- DEC-04 [C] The passenger revision is the trigger; the change is carried for the text
- DEC-63 [C] Arriving passengers, not seats, drive demand
- DEC-64 [C] Each hotel's luck and shop noise come from its own stream
- DEC-65 [C] The market's price response is on by default, at 1.0
- DEC-66 [C] Each hotel carries its own booking curve
- DEC-67 [C] A day's bookings are drawn once and split over its ticks
- DEC-05 [C] The booking loop runs to day 149 with rates frozen from day 60
- DEC-06 [C] The 7-day hold after an accepted rate change
- DEC-07 [C] A pace flag needs a gap beyond 10% of rooms and 3 standard deviations
- DEC-08 [H] The convention's peak night was fixed at stay date 46
- DEC-09 [C] The peak night is the expected-demand peak on the event's known day
- DEC-10 [C] A minimum stay is advice only, never simulated
- DEC-11 [H] The rule "seats up, so raise the rate"
- DEC-12 [C] Contribution with a room cost is the target
- DEC-13 [C] Every flag gets scored candidates; hold is the default
- DEC-14 [C] Base occupancy is 0.85 at the airport hotel
- DEC-15 [H] Rates followed the day of the week
- DEC-16 [C] Flat rates ignore the day of the week
- DEC-17 [C] A plan needs $250 over holding to enter the queue
- DEC-18 [H] One candidate moved all of a flag's stay dates together
- DEC-19 [C] The best candidate is chosen per day of the week within a flag
- DEC-20 [H] Expected bookings were capped at the unsold rooms
- DEC-21 [C] Estimated bookings are E[min(N, unsold)] for a Poisson N
- DEC-22 [C] One random number per booking draw, fixed by the seed
- DEC-26 [H] AGENT_ELASTICITY is the agent's own constant
- DEC-35 [C] Every number is synthetic; the schedule's columns follow a published dictionary
- DEC-36 [C] The summary reports what the run produces; nothing is tuned
- DEC-37 [H] Competitor noise drawn once per competitor and stay date
- DEC-62 [C] The shop noise is fresh every shop day
- DEC-38 [C] The agent can learn its elasticity from the bookings
- DEC-39 [C] The cautious rule changes a rate only where it beats hold across the band
- DEC-43 [C] The cautious rule tests the band alone; one minimum applies to the plan
- DEC-44 [C] Every request figure is a display string the prompt says to copy whole
- DEC-45 [C] The tables keep each decision's request, answer and outcome
- DEC-46 [C] The agent reprices when data arrives during the day
- DEC-68 [C] The clock is an option; a tick is a slice of a day
- DEC-49 [C] The benchmark measures the reviewer in the mismatched modes
- DEC-50 [C] A demand bias the agent never sees
- DEC-51 [C] Competitors can follow the hotel's rate changes, as an opt-in arm
- DEC-52 [C] The market can answer the comp median's level
- DEC-53 [C] The filings are a named scenario; the churn files what a feed files
- DEC-54 [C] A learning agent can feed the fitted demand level into its forecast
- DEC-55 [C] A rule-based control is the fair comparison
- DEC-59 [C] The README names the competitors' raise as the convention's source of gain
- DEC-71 [C] The rush books an uplift early
- DEC-69 [C] The market's events and rate cuts live in the customer file

### Engineering

- DEC-23 [C] The cache key is seed, day and hotel, with the request's digest
- DEC-24 [H] Template answers were cached like the model's
- DEC-25 [C] Only the model's answers are cached
- DEC-27 [H] The modules lived flat at the repository root
- DEC-28 [C] The code is the package src/hotel_market, with pyproject.toml and a command
- DEC-29 [H] A hosted workflow ran the tests on every push
- DEC-30 [H] No hosted CI; the checks run locally through make and pytest
- DEC-70 [C] A hosted workflow runs the three checks on every push to main
- DEC-31 [H] One agent.py held the planning, the model call and the daily loop
- DEC-32 [C] The agent is plan.py, model.py and agent.py, with text.py for shared wording
- DEC-33 [C] ruff formats the code at 100 columns, and lint checks the format
- DEC-34 [C] The answer schema lists the request's entry ids and options as enums
- DEC-40 [C] The agent reads only through four interfaces
- DEC-41 [C] Everything specific to the market is a customer file
- DEC-42 [C] Stored tables the agent can run against a day at a time
- DEC-47 [C] The oracle reviewer is a grader outside the agent's path
- DEC-48 [C] The bench is one sweep with a reviewer per arm
- DEC-56 [C] The band verdict is a display field; small band-end gains read to the dollar
- DEC-57 [C] A read-only demo page over a file code writes
- DEC-58 [C] The demo page fits one window, and every date is a calendar date
- DEC-60 [C] Every printed mean carries its spread
- DEC-61 [C] The sources hold only what the day knows, on both routes

## Results (`results.md`)

- RES-01 [C] The default agent on seeds 1 to 20
- RES-02 [C] Seed 7 in the default mode
- RES-03 [O] A wrong elasticity on seeds 1 to 20
- RES-04 [O] A learned elasticity on seeds 1 to 20
- RES-05 [O] The cautious rule on seeds 1 to 20
- RES-06 [O] Where the gain came from, by arm
- RES-07 [O] The revenue target on seeds 1 to 20
- RES-08 [C] Four live runs of seed 7, one per request format
- RES-09 [C] The recorded live runs of seed 7, measured
- RES-10 [C] The estimator against known elasticities
- RES-11 [H] Seed 7 under the first agent designs
- RES-12 [H] Seed 7 and seeds 1 to 20 with the capped estimate
- RES-13 [H] The cautious rule as first built
- RES-14 [O] The stored tables' timings
- RES-15 [O] The suite on each Python version
- RES-16 [C] The reviewers at fixed:1.0 on seeds 1 to 20
- RES-17 [C] The reviewers at fixed:2.0 on seeds 1 to 20
- RES-18 [O] The reviewers in the true mode on seeds 1 to 20
- RES-19 [O] The reviewers ranked across the mismatched modes
- RES-20 [O] The container image on each Python version
- RES-21 [C] Seeds 1 to 20 at a demand bias of 0.9
- RES-22 [C] Seeds 1 to 20 at a demand bias of 1.1
- RES-23 [C] The same arms at the default demand bias of 1.0
- RES-24 [C] The competitor reaction on seeds 1 to 20
- RES-25 [C] The comp median's path on seed 7, reaction on
- RES-26 [C] The market elasticity with the reaction on
- RES-27 [C] The day-30 competitor cut on seed 7 by market elasticity
- RES-28 [C] The churn on seeds 1 to 20
- RES-29 [C] The fitted level fed back at a demand bias of 0.9
- RES-30 [C] The fitted level fed back at the default demand bias
- RES-31 [C] The fitted level fed back at a demand bias of 1.1
- RES-32 [C] The fitted level fed back, reacting market at 0.5
- RES-33 [C] The agent against the pace and the rules policies
- RES-34 [C] The reviewers at learn:1.0 on seeds 1 to 20
- RES-35 [C] The reviewers at learn:1.0 with the cautious rule
- RES-36 [C] The reviewers at learn:2.0
- RES-37 [C] The reviewers at learn:1.0 cautious, reacting
- RES-38 [O] The decline rate by standard-error group, learn arms
- RES-39 [O] The reviewers ranked across the learned modes
- RES-40 [C] The agent against the never-cut policy
- RES-41 [C] The convention without the competitors' raise
- RES-42 [C] The default agent in a revenue manager's measures
- RES-43 [O] The clock: one tick a day against four
- RES-45 [O] The clock with intraday news
- RES-44 [O] The default agent on the second market, seeds 1 to 20

## Open forks (`forks.md`)

- FRK-01 [H] Revenue or contribution as the target
- FRK-02 [H] Setting AGENT_ELASTICITY apart from the simulator's ELASTICITY
- FRK-03 [O] A length-of-stay model
- FRK-04 [O] Swapping the model for a local one
- FRK-05 [O] Deliberate price tests, to learn the elasticity faster
- FRK-06 [O] A read-only dashboard over the stored tables
- FRK-07 [O] Reviewers from other providers
- FRK-08 [O] A market response as the default
- FRK-09 [O] A comp move that follows our change as a flag cause
- FRK-10 [O] An arrival time column
- FRK-11 [O] A periodic re-plan beside the anomaly flags
- FRK-12 [H] Per-hotel booking curves in the customer file
- FRK-13 [H] The stored route refuses a later day
- FRK-14 [O] An event known before the run goes into the preload

## Unknowns (`unknowns.md`)

- UNK-01 [C] How the live model decides, compared with the template
- UNK-02 [C] Whether the enum schema behaves as expected against the live API
- UNK-03 [H] Whether the container image builds and its tests pass
- UNK-04 [H] Whether the suite passes on Python 3.12 and 3.13
- UNK-05 [U] How arriving passengers turn into hotel demand in a real market
- UNK-06 [U] The real cost to service an occupied room
- UNK-07 [U] The real price elasticity
- UNK-08 [U] Whether the measured gains say anything about a real hotel
- UNK-09 [C] What a live run costs and takes
- UNK-10 [U] Whether sql/schema.sql runs on a cloud warehouse unchanged
- UNK-11 [U] How competitors react to a rate change
- UNK-12 [U] The effect of cancellations, no-shows, groups and room types
- UNK-13 [U] Whether a 5% cut, the largest on the menu, is enough
- UNK-14 [U] The estimate's bias when a hotel prices to demand
- UNK-15 [U] The real market-level price elasticity
- UNK-16 [O] What the reviewers do on world v2
