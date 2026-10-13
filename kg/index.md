# Index

Every node on one line: ID, status, name and file. `python kg_check.py
--write-index` writes this file from the node files, and the check fails when
it differs from what that would write. `README.md` is the legend.

## Modules (`modules.md`)

- MOD-01 [C] schedule.py — src/hotel_market/schedule.py
- MOD-02 [C] world.py — src/hotel_market/world.py
- MOD-03 [C] shocks.py — src/hotel_market/shocks.py
- MOD-04 [C] demand.py — src/hotel_market/demand.py
- MOD-05 [C] shops.py — src/hotel_market/shops.py
- MOD-06 [C] bookings.py — src/hotel_market/bookings.py
- MOD-07 [C] detect.py — src/hotel_market/detect.py
- MOD-08 [C] plan.py — src/hotel_market/plan.py
- MOD-09 [C] model.py — src/hotel_market/model.py
- MOD-10 [C] agent.py — src/hotel_market/agent.py
- MOD-11 [C] text.py — src/hotel_market/text.py
- MOD-12 [C] cli.py — src/hotel_market/cli.py
- MOD-13 [C] __init__.py — src/hotel_market/__init__.py
- MOD-14 [C] __main__.py — src/hotel_market/__main__.py
- MOD-15 [C] kg_check.py — kg_check.py
- MOD-16 [C] estimate.py — src/hotel_market/estimate.py
- MOD-17 [C] sources.py — src/hotel_market/sources.py
- MOD-18 [C] forecast.py — src/hotel_market/forecast.py
- MOD-19 [C] simulated.py — src/hotel_market/simulated.py
- MOD-20 [C] customer.py — src/hotel_market/customer.py
- MOD-21 [C] stored.py — src/hotel_market/stored.py
- MOD-22 [C] scripts/live_audit.py — scripts/live_audit.py
- MOD-23 [C] bench.py — src/hotel_market/bench.py
- MOD-24 [C] scripts/median_path.py — scripts/median_path.py
- MOD-25 [C] policy.py — src/hotel_market/policy.py
- MOD-26 [C] demo_data.py — src/hotel_market/demo_data.py
- MOD-27 [C] demo_page.py — src/hotel_market/demo_page.py
- MOD-28 [C] scripts/demo_screenshots.py — scripts/demo_screenshots.py

## Data (`data.md`)

- DAT-01 [C] The schedule table — src/hotel_market/schedule.py
- DAT-02 [C] Seats by day, seat change and seat revision — src/hotel_market/schedule.py
- DAT-03 [C] Route and Shock — src/hotel_market/schedule.py
- DAT-04 [C] Hotel, Competitor and the customer's hotels — src/hotel_market/world.py
- DAT-05 [C] Event and RateCut — src/hotel_market/shocks.py
- DAT-06 [C] The rate shop — src/hotel_market/shops.py
- DAT-07 [C] Books — src/hotel_market/bookings.py
- DAT-08 [C] The detect table — src/hotel_market/detect.py
- DAT-09 [C] Flag — src/hotel_market/detect.py
- DAT-10 [C] StayDate — src/hotel_market/plan.py
- DAT-11 [C] Candidate — src/hotel_market/plan.py
- DAT-12 [C] WeekdayGroup — src/hotel_market/plan.py
- DAT-13 [C] FlagNumbers and Range — src/hotel_market/plan.py
- DAT-14 [C] Entry — src/hotel_market/plan.py
- DAT-15 [C] Advice — src/hotel_market/agent.py
- DAT-16 [C] The model request — src/hotel_market/model.py
- DAT-17 [C] The cache record — src/hotel_market/model.py
- DAT-18 [C] A decisions.jsonl line — src/hotel_market/plan.py
- DAT-19 [C] SeedResult — src/hotel_market/cli.py
- DAT-20 [C] Comparison — src/hotel_market/cli.py
- DAT-21 [C] Pricing — src/hotel_market/plan.py
- DAT-22 [C] ElasticityMode — src/hotel_market/agent.py
- DAT-23 [C] Observations and Estimate — src/hotel_market/estimate.py
- DAT-24 [C] ArmResult — src/hotel_market/cli.py
- DAT-25 [C] The four sources — src/hotel_market/sources.py
- DAT-26 [C] BookingHistory — src/hotel_market/sources.py
- DAT-27 [C] Customer — src/hotel_market/customer.py
- DAT-28 [C] The stored tables — sql/schema.sql
- DAT-29 [C] The recorded live run — tests/fixtures/live_seed7/
- DAT-30 [C] The call record — src/hotel_market/model.py
- DAT-31 [C] DeclineCounts — src/hotel_market/bench.py
- DAT-32 [C] Reviewer — src/hotel_market/bench.py
- DAT-33 [C] The demo file — sql/demo.sql

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
- RUL-12 [C] SIM_DAYS — src/hotel_market/world.py
- RUL-13 [C] LOOKAHEAD_DAYS — src/hotel_market/world.py
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
- RUL-68 [C] days_out — customers/demo.toml
- RUL-69 [C] share — customers/demo.toml
- RUL-109 [C] RATE_AXIS — src/hotel_market/demo_data.py
- RUL-110 [C] GAIN_TICK_DAYS — src/hotel_market/demo_data.py
- RUL-115 [C] PLOT_HEIGHTS — src/hotel_market/demo_page.py
- Labels: RUL-06, RUL-07, RUL-08, RUL-09, RUL-10, RUL-89, RUL-93, RUL-31, RUL-32, RUL-33, RUL-34, RUL-35, RUL-36, RUL-37, RUL-38, RUL-41, RUL-42, RUL-44, RUL-45, RUL-49, RUL-46, RUL-47, RUL-75, RUL-78, RUL-79, RUL-48, RUL-55, RUL-74, RUL-86, RUL-94, RUL-100, RUL-101, RUL-72, RUL-73, RUL-70, RUL-71, RUL-57, RUL-103, RUL-104, RUL-105, RUL-106, RUL-107, RUL-108, RUL-111, RUL-112, RUL-113, RUL-114, RUL-116, RUL-117

## Shocks (`shocks.md`)

- SHK-01 [C] The convention — src/hotel_market/shocks.py
- SHK-02 [C] The new flights — src/hotel_market/schedule.py
- SHK-03 [C] The competitor rate cut — src/hotel_market/shocks.py
- SHK-04 [C] The route suspension — src/hotel_market/schedule.py
- SHK-05 [C] The upgauge — src/hotel_market/schedule.py
- SHK-06 [C] The frequency cut — src/hotel_market/schedule.py
- SHK-07 [C] The churn — src/hotel_market/schedule.py

## Concepts (`concepts.md`)

- CON-01 [C] Booking curve — kg/concepts.md
- CON-02 [C] Pace — kg/concepts.md
- CON-03 [C] Competitor set — kg/concepts.md
- CON-04 [C] Competitor median — kg/concepts.md
- CON-05 [C] Rate ratio — kg/concepts.md
- CON-06 [C] Elasticity — kg/concepts.md
- CON-07 [C] Contribution — kg/concepts.md
- CON-08 [C] Value at stake — kg/concepts.md
- CON-09 [C] Sell-out — kg/concepts.md
- CON-10 [C] Hold period — kg/concepts.md
- CON-11 [C] The cautious rule — kg/concepts.md

## Measures (`measures.md`)

- MEA-01 [C] Occupancy — kg/measures.md
- MEA-02 [C] Average rate — kg/measures.md
- MEA-03 [C] Revenue per available room — kg/measures.md
- MEA-04 [C] Room revenue — kg/measures.md
- MEA-05 [C] Contribution — kg/measures.md
- MEA-06 [C] Regret — kg/measures.md
- MEA-07 [C] Accept rate — kg/measures.md
- MEA-08 [C] Decline precision — kg/measures.md
- MEA-09 [C] Decline recall — kg/measures.md
- MEA-10 [C] Decline F1 — kg/measures.md
- MEA-11 [C] Dollar-weighted decline recall — kg/measures.md
- MEA-12 [C] Recovered share — kg/measures.md
- MEA-13 [C] Decline rate by standard-error group — kg/measures.md
- MEA-14 [C] Plans on recently changed dates — kg/measures.md

## Sources (`sources.md`)

- SRC-01 [C] Bookings — kg/sources.md
- SRC-02 [C] Competitor rate shops — kg/sources.md
- SRC-03 [C] Air schedules — kg/sources.md
- SRC-04 [C] Events — kg/sources.md

## Decisions (`decisions.md`)

### Market and agent design

- DEC-01 [C] Code computes every number; the model only chooses and writes — kg/decisions.md
- DEC-02 [C] Nothing is used before the day it becomes known — kg/decisions.md
- DEC-03 [C] The day-0 preload: bookings made before the run starts — kg/decisions.md
- DEC-04 [C] seat_revision is the seat trigger; seat_change is carried for the text — kg/decisions.md
- DEC-05 [C] The booking loop plays out to day 149 with rates frozen from day 60 — kg/decisions.md
- DEC-06 [C] The 7-day hold after an accepted rate change — kg/decisions.md
- DEC-07 [C] A pace flag needs a gap beyond both 10% of rooms and 3 standard deviations — kg/decisions.md
- DEC-08 [H] The convention's peak night was fixed at stay date 46 — kg/decisions.md
- DEC-09 [C] The peak night is computed from expected demand as of the day the event becomes known — kg/decisions.md
- DEC-10 [C] A minimum stay is advice only, never simulated — kg/decisions.md
- DEC-11 [H] The rule "seats up, so raise the rate" — kg/decisions.md
- DEC-12 [C] Contribution with a room cost is the target, and the start rate is best on ordinary nights — kg/decisions.md
- DEC-13 [C] Every flag gets scored candidates, with hold as the default — kg/decisions.md
- DEC-14 [C] The airport hotel's base occupancy is 0.85; the other three are 0.75 — kg/decisions.md
- DEC-15 [H] Rates followed the day of the week — kg/decisions.md
- DEC-16 [C] Flat rates: starting and competitor rates do not follow the day of the week — kg/decisions.md
- DEC-17 [C] A plan must be worth at least $250 over holding to enter the queue — kg/decisions.md
- DEC-18 [H] One candidate moved all of a flag's stay dates together — kg/decisions.md
- DEC-19 [C] The best candidate is chosen separately for each day of the week within a flag — kg/decisions.md
- DEC-20 [H] Expected bookings were capped at the unsold rooms — kg/decisions.md
- DEC-21 [C] Estimated bookings are the exact expectation E[min(N, unsold)] for a Poisson N — kg/decisions.md
- DEC-22 [C] One random number per booking draw, fixed by the seed before the run — kg/decisions.md
- DEC-26 [H] AGENT_ELASTICITY is the agent's own constant and never imports the simulator's — kg/decisions.md
- DEC-35 [C] Every number is synthetic, and the schedule's columns follow a published data dictionary — kg/decisions.md
- DEC-36 [C] The summary reports what the run produces; the rules are not tuned to force a gain — kg/decisions.md
- DEC-37 [C] Competitor noise is drawn once per competitor and stay date, so a comp median moves only on a shock — kg/decisions.md
- DEC-38 [C] The agent can learn its elasticity from the bookings; the default stays the simulator's value — kg/decisions.md
- DEC-39 [C] The cautious rule: a learning agent changes a rate only where the change beats holding across its band — kg/decisions.md
- DEC-43 [C] One minimum rule: the cautious rule tests the band alone, and the minimum applies to the plan as in every mode — kg/decisions.md
- DEC-44 [C] The request carries a display string in place of every figure, with its direction in words and each range as one phrase, and the prompt tells the model to copy the phrases whole and state only what the entry shows — kg/decisions.md
- DEC-45 [T] Each model request carries the hotel's past decisions and their outcomes — kg/decisions.md
- DEC-46 [T] The agent reprices when data arrives during the day — kg/decisions.md
- DEC-49 [C] The benchmark measures the reviewer in the mismatched modes — kg/decisions.md
- DEC-50 [C] A demand bias the agent never sees is the demand-level twin of a fixed elasticity — kg/decisions.md
- DEC-51 [C] Competitors can follow the hotel's rate changes, as an opt-in arm — kg/decisions.md
- DEC-52 [C] The share elasticity alone made a matched raise free, so the market can answer the comp median's level — kg/decisions.md
- DEC-53 [C] The air schedule's filings are a named scenario, and the churn files what a feed files — kg/decisions.md
- DEC-54 [C] A learning agent can feed the fitted demand level back into its forecast — kg/decisions.md
- DEC-55 [C] A rule-based control is the fair comparison, because frozen rates never move — kg/decisions.md

### Engineering

- DEC-23 [C] The cache is keyed by seed, day and hotel, and each file records a digest of its request — kg/decisions.md
- DEC-24 [H] Template answers were cached like the model's — kg/decisions.md
- DEC-25 [C] Only the model's answers are cached; the template is a function of the request — kg/decisions.md
- DEC-27 [H] The modules lived flat at the repository root — kg/decisions.md
- DEC-28 [C] The code is the package src/hotel_market, with pyproject.toml and a console command — kg/decisions.md
- DEC-29 [H] A hosted workflow ran the tests on every push — kg/decisions.md
- DEC-30 [C] No hosted CI; the checks run locally through make and pytest — kg/decisions.md
- DEC-31 [H] One agent.py held the planning, the model call and the daily loop — kg/decisions.md
- DEC-32 [C] The agent is three modules: plan.py, model.py and agent.py, with text.py for shared wording — kg/decisions.md
- DEC-33 [C] ruff formats the code at 100 columns, and the format check is part of lint — kg/decisions.md
- DEC-34 [C] The answer schema lists the request's own entry ids and options as enums — kg/decisions.md
- DEC-40 [C] The agent reads data only through four interfaces; the simulator is one implementation — kg/decisions.md
- DEC-41 [C] Everything specific to the market is a customer file, and the target is one of its settings — kg/decisions.md
- DEC-42 [C] The feeds and the agent's output are stored tables keyed by as_of_day, and the agent can run one day at a time against them — kg/decisions.md
- DEC-47 [C] The oracle reviewer is a grader outside the agent's path — kg/decisions.md
- DEC-48 [C] The bench is one sweep with a reviewer per arm — kg/decisions.md
- DEC-56 [C] The cautious band's verdict is a display field, and a band-end gain under $10 reads to the dollar — kg/decisions.md
- DEC-57 [C] A read-only demo page over a file code writes — kg/decisions.md
- DEC-58 [C] The demo page fits one window, and every date on it is a calendar date — kg/decisions.md

## Results (`results.md`)

- RES-01 [C] The default agent on seeds 1 to 20 — kg/results.md
- RES-02 [C] Seed 7 in the default mode — kg/results.md
- RES-03 [O] A wrong elasticity, fixed:1.0 and fixed:2.0, on seeds 1 to 20 — kg/results.md
- RES-04 [O] A learned elasticity, learn:1.0 and learn:2.0, on seeds 1 to 20 — kg/results.md
- RES-05 [O] The cautious rule on seeds 1 to 20 — kg/results.md
- RES-06 [O] Where the gain came from, by arm — kg/results.md
- RES-07 [O] The revenue target on seeds 1 to 20 — kg/results.md
- RES-08 [C] Four live runs of seed 7, one per request format — kg/results.md
- RES-09 [C] The recorded live run of seed 7, measured — kg/results.md
- RES-10 [C] The estimator against known elasticities — kg/results.md
- RES-11 [H] Seed 7 under the first agent designs — kg/results.md
- RES-12 [H] Seed 7 and seeds 1 to 20 with the capped estimate — kg/results.md
- RES-13 [H] The cautious rule as first built — kg/results.md
- RES-14 [O] The stored tables' timings — kg/results.md
- RES-15 [O] The suite on each Python version — kg/results.md
- RES-16 [C] The reviewers at fixed:1.0 on seeds 1 to 20 — kg/results.md
- RES-17 [C] The reviewers at fixed:2.0 on seeds 1 to 20 — kg/results.md
- RES-18 [O] The reviewers in the true mode on seeds 1 to 20 — kg/results.md
- RES-19 [O] The reviewers ranked across the mismatched modes — kg/results.md
- RES-20 [O] The container image on each Python version — kg/results.md
- RES-21 [C] Seeds 1 to 20 at a demand bias of 0.9 — kg/results.md
- RES-22 [C] Seeds 1 to 20 at a demand bias of 1.1 — kg/results.md
- RES-23 [C] The same arms at the default demand bias of 1.0 — kg/results.md
- RES-24 [C] The competitor reaction on seeds 1 to 20 — kg/results.md
- RES-25 [C] The comp median's path on seed 7's convention nights with the reaction on — kg/results.md
- RES-26 [C] The market elasticity with the reaction on, seeds 1 to 20 — kg/results.md
- RES-27 [C] The day-30 competitor cut on seed 7 at a market elasticity of 0.0 and 0.5 — kg/results.md
- RES-28 [C] The churn on seeds 1 to 20 — kg/results.md
- RES-29 [C] The fitted level fed back at a demand bias of 0.9 — kg/results.md
- RES-30 [C] The fitted level fed back at the default demand bias — kg/results.md
- RES-31 [C] The fitted level fed back at a demand bias of 1.1 — kg/results.md
- RES-32 [C] The fitted level fed back with the reaction on at a market elasticity of 0.5 — kg/results.md
- RES-33 [C] The agent against the pace and the rules policies on seeds 1 to 20 — kg/results.md
- RES-34 [C] The reviewers at learn:1.0 on seeds 1 to 20 — kg/results.md
- RES-35 [C] The reviewers at learn:1.0 with the cautious rule on seeds 1 to 20 — kg/results.md
- RES-36 [C] The reviewers at learn:2.0, with and without the cautious rule, on seeds 1 to 20 — kg/results.md
- RES-37 [C] The reviewers at learn:1.0 cautious with the reaction on at a market elasticity of 0.5 — kg/results.md
- RES-38 [O] The decline rate by standard-error group in the learn arms — kg/results.md
- RES-39 [O] The reviewers ranked across the learned modes, and the learn arms' cost — kg/results.md

## Open forks (`forks.md`)

- FRK-01 [H] Revenue or contribution as the target — kg/forks.md
- FRK-02 [H] Setting AGENT_ELASTICITY apart from the simulator's ELASTICITY — kg/forks.md
- FRK-03 [O] A length-of-stay model — kg/forks.md
- FRK-04 [O] Swapping the model for a locally hosted one — kg/forks.md
- FRK-05 [O] Deliberate price tests, to learn the elasticity faster — kg/forks.md
- FRK-06 [O] A read-only dashboard over the stored tables — kg/forks.md
- FRK-07 [O] Reviewers from other providers — kg/forks.md
- FRK-08 [O] A market response as the default — kg/forks.md
- FRK-09 [O] A comp move that follows our own change as a flag cause — kg/forks.md
- FRK-10 [O] An arrival time column — kg/forks.md
- FRK-11 [O] A periodic re-plan beside the anomaly flags — kg/forks.md

## Unknowns (`unknowns.md`)

- UNK-01 [C] How the live model decides, compared with the template — kg/unknowns.md
- UNK-02 [C] Whether the enum schema behaves as expected against the live API — kg/unknowns.md
- UNK-03 [H] Whether the container image builds and its tests pass — kg/unknowns.md
- UNK-04 [H] Whether the suite passes on Python 3.12 and 3.13 — kg/unknowns.md
- UNK-05 [U] How a change in arriving seats turns into hotel demand in a real market — kg/unknowns.md
- UNK-06 [U] The real cost to service an occupied room — kg/unknowns.md
- UNK-07 [U] The real price elasticity, and what the learned estimate does and does not settle — kg/unknowns.md
- UNK-08 [U] Whether the measured gains say anything about a real hotel — kg/unknowns.md
- UNK-09 [C] What a live run costs and how long it takes — kg/unknowns.md
- UNK-10 [U] Whether sql/schema.sql runs on a cloud warehouse as written — kg/unknowns.md
- UNK-11 [U] How competitors react to a rate change, and what that does to the revenue-target result — kg/unknowns.md
- UNK-12 [U] The effect of cancellations, no-shows, groups and room types — kg/unknowns.md
- UNK-13 [U] Whether a 5% cut is enough: the largest cut on the menu is 5% — kg/unknowns.md
- UNK-14 [U] The bias in an elasticity estimate when a real hotel changes its rate in response to demand — kg/unknowns.md
- UNK-15 [U] The real market-level price elasticity — kg/unknowns.md
