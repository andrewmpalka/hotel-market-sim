# Results

One RES node per experiment. Each node says what ran, with its command, and
gives the headline figures. Its `Table:` field names the table in
`docs/results.md` that holds the rest, by the start of the table's caption.
Every figure comes from this simulator, whose demand formula the agent shares,
so the figures test the machinery and are not a forecast ([[UNK-08]]).

A RES node is [C] when a test pins at least one of its figures. It is [O] when
no test does: the run was made once and recorded. It is [H] when a later
design replaced the run, and it then links to the run that replaced it. The
decisions ([[DEC-01]] onwards) keep at most one headline figure each and link
here for the rest.

### RES-01 [C] The default agent on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20`: the agent against the fixed-rate run on each seed, with template reasons and the simulator's elasticity. The runs cover stay dates 0 to 149.
- Result: the agent run earns +$32,899 more contribution a seed, from +$13,479 to +$52,809. It is ahead in 20 of 20 seeds.
- Detail: room revenue falls $22,861 a seed, and the agent changes 179 rates in all. The accepted plans' estimates sum to 1.04 times the realised gain ($681,054 against $657,979).
- Table: docs/results.md, "Seeds 1 to 20 in the default mode"
- Evidence: test_the_default_mode_still_gives_a_20_seed_mean_of_32899
- Links: [[DEC-21]], [[DEC-36]], [[DEC-38]], [[MEA-05]], [[RES-02]], [[RES-06]]

### RES-02 [C] Seed 7 in the default mode
- Ran: `hotel-market --seed 7 --template`, both runs of seed 7 with template reasons in the default mode.
- Result: the agent run earns +$28,818 of contribution (+0.2%) and $35,019 less room revenue than the fixed-rate run.
- Flags: 113 flags on days 0 to 59. 7 change a rate, 49 are held because no change beats hold, and 57 are held under the $250 minimum. The day-40 take-back at the airport hotel ($132) is one of the 57.
- Pairs: the 93 hotel-nights the agent changed carry the whole gain, +1.6% on them. The other 507 book identically in both runs.
- Fixed rates: occupancy over stay dates 0 to 59 is 75.7%, 76.0%, 76.6% and 83.7% by hotel. Stay dates 140 to 149 end 78% to 91% full, and the emptiest of those nights is 57% full.
- Table: docs/results.md, "Seed 7, days 0 to 59", "Seed 7 over only the 93", "Seed 7 with fixed rates"
- Evidence: test_the_default_mode_still_gives_28818_on_seed_7, test_every_other_pair_books_the_same_in_both_runs, test_fixed_rate_occupancy_is_between_60_and_90_percent_for_stay_dates_0_to_59
- Links: [[DEC-05]], [[DEC-12]], [[DEC-17]], [[DEC-22]], [[SHK-04]], [[DAT-20]], [[MOD-12]], [[RES-01]]

### RES-03 [O] A wrong elasticity, fixed:1.0 and fixed:2.0, on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --elasticity true --elasticity fixed:1.0 --elasticity fixed:2.0`, each arm against the same fixed-rate runs, template reasons.
- Result: fixed:1.0 earns +$8,438 a seed, ahead in 14 of 20, with 515 rate changes. fixed:2.0 earns +$9,551, ahead in 18 of 20, with 486.
- Detail: a wrong value loses about three quarters of the true arm's gain. The accepted plans' estimates are 38.7 and 13.0 times the realised gain.
- Table: docs/results.md, "Seeds 1 to 20 per elasticity arm"
- Links: [[DEC-38]], [[CON-06]], [[RES-01]], [[RES-04]], [[RES-06]], [[UNK-07]]

### RES-04 [O] A learned elasticity, learn:1.0 and learn:2.0, on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --elasticity learn:1.0 --elasticity learn:2.0`, each arm against the same fixed-rate runs, template reasons.
- Result: learn:1.0 earns +$14,141 a seed, ahead in 16 of 20, with 373 rate changes. learn:2.0 earns +$16,258, ahead in 20 of 20, with 418.
- Detail: learning wins back about a quarter of what a wrong value loses. The accepted plans' estimates are 18.3 and 5.2 times the realised gain.
- Estimates: by day 59 the per-hotel means reach 1.36 to 1.45 from a prior of 1.0. From 2.0 they reach 1.55 to 1.68, and on days 10 and 20 they still sit near the prior.
- Checked: test_plain_learn_mode_gives_the_same_results_as_before pins seed 7 of the learn:1.0 arm at +$2,931 and 17 rate changes.
- Table: docs/results.md, "Seeds 1 to 20 per elasticity arm", "The learning agent's day-59 elasticity estimates"
- Links: [[DEC-38]], [[MOD-16]], [[RES-03]], [[RES-05]], [[RES-10]], [[UNK-07]]

### RES-05 [O] The cautious rule on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --elasticity learn:1.0 --elasticity learn:2.0 --cautious`, each arm against the same fixed-rate runs, template reasons.
- Result: learn:1.0 cautious earns +$25,076 a seed (+$8,406 to +$53,535), ahead in 20 of 20, with 299 changes. learn:2.0 cautious earns +$17,634 (+$5,839 to +$27,585), 20 of 20, with 240.
- Detail: from a prior of 1.0 the rule keeps 76% of the true arm's gain, against 43% without it. From 2.0 it keeps 54% against 49%, and the estimates are 7.7 and 2.5 times the gain.
- Rejected: 3,294 and 2,681 candidates beat hold at the estimate but lost at one end of the band. From 1.0 most rejections are raises at the high end, and from 2.0 cuts at the low end.
- Minimum: a per-weekday $250 minimum on top of the band moves the means by $8 and $16 a seed. The band does the work ([[DEC-43]]).
- Table: docs/results.md, "Seeds 1 to 20 per elasticity arm", "The cautious rule with and without"
- Links: [[DEC-39]], [[DEC-43]], [[CON-11]], [[RES-04]], [[RES-06]], [[RES-13]]

### RES-06 [O] Where the gain came from, by arm
- Ran: every sweep of seeds 1 to 20 reports the shock plans apart from every other plan ([[RUL-55]]). The shock plans are those the convention (day 10) and the new flights (day 20) raised.
- Result: in the true arm 97 shock plans earn +$632,532 over the 20 seeds, and 82 other plans earn +$25,447. The shock plans therefore give 96% of the gain.
- Detail: in every arm nearly all of the gain sits in the shock plans. The hundreds of other changes a wrong elasticity provokes earn almost nothing.
- Table: docs/results.md, "Where each arm's gain came from"
- Links: [[DAT-24]], [[RUL-55]], [[SHK-01]], [[SHK-02]], [[RES-01]], [[RES-03]], [[RES-04]], [[RES-05]]

### RES-07 [O] The revenue target on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --target revenue`, with the simulator's elasticity and the template. The arm runs against the same fixed-rate runs as the contribution target.
- Result: the revenue target earns +$211,445 of room revenue a seed, ahead in 20 of 20. That is about 1% of the fixed-rate revenue. It earns +$461 of contribution, ahead in 11 of 20.
- Detail: it changes 659 rates against the contribution target's 179. On seed 7, 65 of its 85 changed days of the week are 5% cuts. The raises sit on nights that sell out.
- Estimates: the accepted plans' estimates sum to 0.99 of the realised revenue gain ($4,191,156 against $4,228,903). $4,144,589 of the gain comes from the 130 shock plans, where the agent cut rates.
- Table: docs/results.md, "Seeds 1 to 20 with the simulator's elasticity and the template, each target"
- Links: [[DEC-41]], [[RUL-58]], [[FRK-01]], [[CON-07]], [[MEA-04]], [[RES-01]]

### RES-08 [C] Four live runs of seed 7, one per request format
- Ran: `python scripts/live_audit.py --seed 7` four times with claude-opus-5-5, the request format changing between the runs ([[DEC-44]]).
- Result: each run makes the same 7 calls as the template run. The model accepts all 7 plans every time, 28 of 28, so contribution ends at +$28,818 each time.
- Tokens: the input was 20,329 tokens with bare numbers and 37,107 with a raw value beside each display string. It was 24,219 with display strings and named-pair ranges, and 21,148 with each range as one phrase.
- Reasons: the first run wrote figures its own way and added claims the entry does not make. The second put direction words on signs, and the third joined range ends with its own words. The fourth copied every phrase whole.
- Kept: only the fourth run is recorded, as [[DAT-29]]; the first three are quoted from the session that made them.
- Table: docs/results.md, "Four live runs of seed 7"
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_recorded_live_run_replays_without_a_key_and_gives_28818
- Links: [[DEC-44]], [[UNK-01]], [[UNK-02]], [[MOD-22]], [[RES-09]]

### RES-09 [C] The recorded live run of seed 7, measured
- Ran: the fourth live run of [[RES-08]]; its cache and its calls.jsonl are kept as [[DAT-29]].
- Result: the 7 calls used 21,148 input tokens (1,744 to 3,923 a call) and 1,713 output tokens (124 to 524). They cost $0.12 at list prices of $4 and $20 per million tokens.
- Time: the model took 32 s in all, 2.9 to 7.4 s a call with a median of 3.5 s. The whole run with both simulations took 37 s, and no prompt cache was read or written.
- Calls: every call ended with the stop reason end_turn. None was refused and none fell back to another model. Every answer parsed and named the entry's id and an allowed choice.
- Table: docs/results.md, "The recorded live run of seed 7"
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit
- Links: [[UNK-09]], [[UNK-02]], [[DAT-29]], [[MOD-22]], [[RUL-46]]

### RES-10 [C] The estimator against known elasticities
- Ran: seed 7 in learn:1.5 mode with the simulator's ELASTICITY set to 1.0, 1.5 and 2.0 in turn. Each hotel's day-59 estimate is compared with the truth.
- Result: every estimate lands within 1.6 standard errors of the truth on seeds 7 and 3, where the test allows three.
- Detail: on seed 7 the standard errors are 0.16 to 0.31 and each hotel has about 5,300 observations by day 59.
- Variation: in a fixed-rate run the observations' log rate ratio has a standard deviation of 0.011 to 0.027 by hotel. The agent's own rate changes therefore supply most of the usable variation.
- Alone: on seed 7 those changes are 12% of the lifestyle and 37% of the airport observations. Without them the bookings would pin the elasticity near 0.2 downtown and 0.9 to 1.2 at the other two hotels.
- Table: docs/results.md, "The estimator against known elasticities", "Spread of the log rate ratio"
- Evidence: test_the_day_59_estimate_recovers_the_simulators_elasticity, test_the_prior_holds_the_estimate_when_the_ratio_never_moves
- Links: [[MOD-16]], [[DEC-38]], [[FRK-05]], [[UNK-07]], [[RES-04]]

### RES-11 [H] Seed 7 under the first agent designs
- Ran: seed 7 with the first full agent. It had weekday rate factors, one candidate for all of a flag's stay dates and no minimum. Expected bookings were capped at the unsold rooms.
- Result: +$26,420 of contribution with 23 rate changes, several worth under $10, 8 of which lost money. The lifestyle hotel gained +$12,514, mostly on Fridays and Saturdays.
- Detail: one stay date, the full-service hotel's 46, was changed five times across days 10 to 44. Each change came after its hold had expired.
- Then: with flat rates, a plan per day of the week and the $250 minimum, the gain fell to +$22,894. The lifestyle hotel's fell to +$5,832, with 10 changes and 22 flags held under the minimum.
- Replaced by: [[RES-12]]
- Table: docs/results.md, "Seed 7 under earlier designs"
- Links: [[DEC-06]], [[DEC-15]], [[DEC-16]], [[DEC-17]], [[DEC-18]], [[DEC-19]]

### RES-12 [H] Seed 7 and seeds 1 to 20 with the capped estimate
- Ran: the agent with its estimated bookings capped at the unsold rooms ([[DEC-20]]), before E[min(N, unsold)].
- Result: seed 7 earned +$22,894 and the 20-seed mean was +$27,350. The agent was ahead in 20 of 20 seeds both before and after the change.
- Detail: the cap understated the day-20 airport plan by about half ($3,849 against $8,012 with booking noise counted). It overstated the three biggest convention plans by $356 to $575 each, and held the 97%-full Wednesdays and Fridays.
- Then: with the exact estimate seed 7 went to +$28,818 and the mean to +$32,899. The day-20 airport plan raises every night but Saturday and is worth $10,627.
- Replaced by: [[RES-01]]
- Table: docs/results.md, "Seed 7 under earlier designs"
- Links: [[DEC-19]], [[DEC-20]], [[DEC-21]], [[RES-02]]

### RES-13 [H] The cautious rule as first built
- Ran: `hotel-market --seeds 1 20 --elasticity learn:1.0 --elasticity learn:2.0 --cautious` with the first rule. That rule also asked each day of the week to be worth $250 on its own.
- Result: learn:1.0 cautious earned +$25,084 a seed with 299 changes and 1,205 candidates rejected at an end. learn:2.0 cautious earned +$17,618 with 229 changes and 766 rejected.
- Detail: a diagnostic of the band alone gave +$25,076 and +$17,634 on the same seeds. The per-day minimum did almost nothing, so [[DEC-43]] removed it.
- Rejections: on seeds 1, 2 and 7, 151 of 159 rejections from a prior of 1.0 were high-end raises. From 2.0, 65 of 108 were cuts at the low end. The rule held 294 and 393 days of the week that plain mode changed.
- Gain: from 1.0 the shock plans earned $487,235 of $501,683 from 103 changes. From 2.0 they earned $290,380. The rule cut the other plans from 291 to 158, while their take rose from $30,370 to $61,983.
- Replaced by: [[RES-05]]
- Table: docs/results.md, "The cautious rule with and without"
- Links: [[DEC-39]], [[DEC-43]], [[CON-11]]

### RES-14 [O] The stored tables' timings
- Ran: `hotel-market run-day --seed 7 --as-of 59 --from 0` through a DuckDB file, timed during development. The tests that drive it were timed too.
- Result: the 60-day run through the tables takes about 6 seconds. One day on its own takes under a second, most of it the simulator's playback.
- Detail: inserting rows one statement at a time took 2.5 seconds per 3,000 rows. A day's rows therefore go in as one frame. Reading the events table once per detect row made a day take 2 seconds. Each source now reads a day once.
- Versions: the schema ran on DuckDB 1.2 and 1.5. It was read against the documentation of BigQuery, Snowflake and Redshift and not run on them ([[UNK-10]]).
- Table: docs/results.md, "Timings of the stored tables"
- Links: [[DEC-42]], [[MOD-21]], [[DAT-28]], [[UNK-10]]

### RES-15 [O] The suite on each Python version
- Ran: `python -m pytest --slow` from a fresh virtual environment on Python 3.12.6 and on 3.13.7, on 2026-10-12. The environments had numpy 2.5.4, pandas 3.0.6, duckdb 1.5.6 and anthropic 1.13.0.
- Result: 235 tests passed on both versions, the slow 20-seed check included; the suite had run on Python 3.11 before.
- Detail: the package was also installed and run against numpy 1.26 and pandas 2.2, the lower bounds in pyproject.toml. A seed-7 run then reproduced decisions.jsonl byte for byte ([[DEC-28]]).
- Table: docs/results.md, "The suite on each Python version"
- Links: [[UNK-04]], [[DEC-28]], [[DEC-30]]

### RES-16 [C] The reviewers at fixed:1.0 on seeds 1 to 20
- Ran: `hotel-market bench --seeds 1 20` on 2026-10-12. Each seed has the fixed-rate run, then the template, the oracle and each of the three models in each mode. The run read every arm's cache and made no call.
- Detail: the live calls were made first, in parallel chunks of seeds. Seeds 1 to 3 ran as one process per model, then seeds 4 to 20 in seven chunks. Each arm's cache folder holds its calls.jsonl.
- Result: the template earns +$8,438 a seed and the oracle +$30,588 while accepting 15% of the plans. Opus earns +$14,584, ahead in 17 of 20, with a recovered share of 0.28. Sonnet and Haiku accept every plan and tie with the template.
- Declines: Opus declines 47 plans with precision 1.00 and count recall 0.14. Its dollar-weighted recall is 0.25, so the one in seven it caught were the costlier ones. 36 are the day-40 raise on stay dates 70 to 90 after the seat cut.
- Gap: the oracle's +$30,588 at fixed:1.0 stands next to the true mode's +$32,899 ([[RES-01]]). The $22,150 a seed between the template and the oracle is the value a reviewer can recover. Opus's regret is $16,004 a seed.
- Table: docs/results.md, "Seeds 1 to 20 at a fixed elasticity of 1.0"
- Evidence: test_the_offline_bench_on_20_seeds_pins_the_benchmarks_headline
- Links: [[DEC-47]], [[DEC-48]], [[DEC-49]], [[MEA-12]], [[RES-01]], [[RES-03]], [[RES-19]], [[UNK-01]]

### RES-17 [C] The reviewers at fixed:2.0 on seeds 1 to 20
- Ran: the same command as [[RES-16]], the fixed:2.0 arms.
- Result: the template earns +$9,551 a seed and the oracle +$23,058 while accepting 29% of the plans. Opus earns +$9,557 with one decline, which the oracle shares, so its recall is 0.00. Sonnet and Haiku tie with the template.
- Declines: Opus's one decline holds a 5% cut worth $340 on a date ahead of pace, on seed 4, day 53. The oracle declines 71% of the plans in this mode, most of them cuts.
- Table: docs/results.md, "Seeds 1 to 20 at a fixed elasticity of 2.0"
- Evidence: test_the_offline_bench_on_20_seeds_pins_the_benchmarks_headline
- Links: [[RES-16]], [[RES-03]], [[DEC-47]], [[DEC-49]], [[UNK-01]]

### RES-18 [O] The reviewers in the true mode on seeds 1 to 20
- Ran: the same command as [[RES-16]], the true-mode arms.
- Result: every reviewer earns +$32,899 a seed, ahead in 20 of 20, the figure of [[RES-01]]. No model declines a plan, so the mode cannot separate them ([[DEC-47]]).
- Calls: 174 calls a model. Opus costs $2.83, Sonnet $1.31 and Haiku $0.11 at list prices, with median latencies of 4.3, 2.5 and 4.2 s. Sonnet's one request with invalid answers counts twice, a failed run and its rerun ([[UNK-02]]).
- Table: docs/results.md, "Seeds 1 to 20 in the true mode"
- Links: [[RES-01]], [[RES-16]], [[DEC-47]], [[UNK-01]], [[UNK-02]], [[UNK-09]]

### RES-19 [O] The reviewers ranked across the mismatched modes
- Ran: the same command as [[RES-16]]; the ranking pools the fixed:1.0 and fixed:2.0 arms, 40 per reviewer.
- Result: the oracle earns +$26,823 a seed. Opus earns +$12,071, a recovered share of 0.17, with precision 1.00 and recall 0.08. The template, Sonnet and Haiku earn +$8,994, since the two models accept every plan.
- Cost: over the two modes Opus makes 936 calls for $16.60, Sonnet 940 for $6.99 and Haiku 940 for $0.58. The whole benchmark's 3,338 calls cost $28.42 at list prices ([[RUL-80]]).
- Table: docs/results.md, "The reviewers ranked across the mismatched modes"
- Links: [[RES-16]], [[RES-17]], [[DEC-48]], [[MEA-12]], [[UNK-09]]

### RES-20 [O] The container image on each Python version
- Ran: `make image PYTHON=3.11`, `make image` (3.12) and `make image PYTHON=3.14`, then `make docker-test` on each, on 2026-10-12. Docker 28.4.0 ran on an aarch64 Ubuntu VM with 4 CPUs and 4 GiB.
- Result: each image builds in 24 s and passes 278 tests with 3 skipped, the slow ones, in about 45 s. The 3.12 image runs seed 7 in 1.6 s, and its decisions.jsonl matches the native run's sha256.
- Detail: every dependency came as a wheel on all three Pythons, 3.14 included. pip took numpy 2.4.6 on 3.11 and 2.5.4 on 3.12 and 3.14. pandas 3.0.6, duckdb 1.5.6 and anthropic 1.13.0 are the same everywhere.
- Sizes: the images are 615 MB, 592 MB and 600 MB on 3.11, 3.12 and 3.14. The suite inside the image runs from its copy of the repository. The demo file and the schema lookups expect the repository root.
- Table: docs/results.md, "The container image on each Python version"
- Links: [[UNK-03]], [[DEC-28]], [[RES-15]]

### RES-21 [C] Seeds 1 to 20 at a demand bias of 0.9
- Ran: `hotel-market bench --seeds 1 20 --template --demand-bias 0.9 --elasticity true --elasticity fixed:1.0 --elasticity learn:1.0` on 2026-10-12. The same command with `--elasticity learn:1.0 --cautious` ran the cautious arm.
- Result: the true mode earns +$1,913 a seed, ahead in 12 of 20, against +$32,899 at 1.0 ([[RES-23]]). Accept-all loses $25,179 a seed at fixed:1.0 and $14,376 at learn:1.0. The oracle earns +$2,334 to +$2,748 in every mode.
- Flags: each arm raises 2,541 to 3,230 flags over the 20 seeds, and 90% to 93% carry a pace cause. The true mode at 1.0 raises 1,952, 88% with a pace cause. Accept-all at fixed:1.0 changes 886 rates.
- Estimates: the learn:1.0 arm's day-59 estimates are 1.36 to 1.46 by hotel, against 1.36 to 1.45 at 1.0. The cautious arm's are 1.26 to 1.48, against 1.28 to 1.43. The level error landed in the intercept ([[UNK-07]]).
- Oracle: the oracle accepts 4% to 10% of the plans in the mismatched modes. Its learn arms therefore barely move a rate. Their day-59 estimates stay at 1.05 to 1.31, near the prior.
- Table: docs/results.md, "Seeds 1 to 20 at a demand bias of 0.9"
- Evidence: test_the_demand_bias_runs_pin_their_headline
- Links: [[DEC-50]], [[RUL-82]], [[RES-22]], [[RES-23]], [[UNK-07]], [[UNK-08]]

### RES-22 [C] Seeds 1 to 20 at a demand bias of 1.1
- Ran: the two commands of [[RES-21]] with `--demand-bias 1.1`, on 2026-10-12.
- Result: every arm is ahead in 20 of 20. The true mode earns +$112,082 a seed, accept-all +$93,008 at fixed:1.0 and +$98,401 at learn:1.0. The oracle earns +$107,393 to +$107,714 in the mismatched modes.
- Flags: the true mode raises 8,526 flags over the 20 seeds, 97% with a pace cause. It changes 464 rates against 179 at 1.0. The start rates were set for a smaller market, so the dates run ahead of pace.
- Estimates: the learn:1.0 arm's day-59 estimates are 1.39 to 1.49 by hotel, against 1.36 to 1.45 at 1.0 ([[RES-23]]). The cautious arm's are 1.29 to 1.46, against 1.28 to 1.43.
- Table: docs/results.md, "Seeds 1 to 20 at a demand bias of 1.1"
- Evidence: test_the_demand_bias_runs_pin_their_headline
- Links: [[DEC-50]], [[RUL-82]], [[RES-21]], [[RES-23]], [[UNK-07]], [[UNK-08]]

### RES-23 [C] The same arms at the default demand bias of 1.0
- Ran: the two commands of [[RES-21]] with `--demand-bias 1.0`, on 2026-10-12. The run read no cache and made no call.
- Result: the true, fixed:1.0 and template learn arms repeat [[RES-01]], [[RES-16]], [[RES-04]] and [[RES-05]] to the dollar. They earn +$32,899, +$8,438, +$14,141 and +$25,076 a seed. The default run did not change.
- Oracle: in learn:1.0 the oracle earns +$30,828 a seed and accepts 21% of the plans. In the cautious arm it earns +$31,042 and accepts 34%. The bench had not run the learn modes before ([[RES-16]]).
- Flags: the true mode raises 1,952 flags over the 20 seeds, 88% with a pace cause. Accept-all at fixed:1.0 raises 789, because each of its 515 rate changes holds its stay dates for seven days ([[RUL-66]]).
- Table: docs/results.md, "Seeds 1 to 20 at the default demand bias of 1.0"
- Evidence: test_the_offline_bench_on_20_seeds_pins_the_benchmarks_headline, test_the_default_mode_still_gives_a_20_seed_mean_of_32899
- Links: [[DEC-50]], [[RUL-82]], [[RES-01]], [[RES-04]], [[RES-05]], [[RES-16]], [[RES-21]], [[RES-22]]

### RES-24 [C] The competitor reaction on seeds 1 to 20
- Ran: `hotel-market bench --seeds 1 20 --template --react --elasticity true` and the same with `--elasticity learn:1.0 --cautious`, on 2026-10-12.
- Result: in the true mode every arm earns +$111,272 a seed against the fixed-rate run. The reaction leaves that run as it is. That is 3.4 times the +$32,899 without it ([[RES-01]]). The cautious learn arm earns +$298,869 accepting all.
- Why: the simulator's bookings follow the hotel's rate against the comp median ([[RUL-21]]). A raise the competitors half follow costs few rooms, and the moved median raises a new flag. The agent then raises again.
- Repeats: the true mode changes 298 rates against 179 without the reaction. 481 of its 541 comp-median flags follow the hotels' own changes, and 97 stay dates change twice within 14 days. The cautious learn arm changes 734 twice.
- Oracle: the oracle then scored without the reaction ([[DEC-51]]). It accepted 45% of the cautious arm's plans, earned +$129,090 a seed, and so trailed accepting all by $169,780. Told the reaction, it leads again ([[RES-26]]).
- Table: docs/results.md, "Seeds 1 to 20 with the reaction on"
- Evidence: test_the_reacting_runs_pin_their_headline
- Links: [[DEC-51]], [[DEC-37]], [[RES-01]], [[RES-05]], [[RES-23]], [[RES-25]], [[UNK-11]]

### RES-25 [C] The comp median's path on seed 7's convention nights with the reaction on
- Ran: `python scripts/median_path.py --seed 7 --react --hotel convention --stays 45 48 --days 9 15` on 2026-10-12.
- Result: the competitors raise 15% on shop day 10, when the convention is announced ([[SHK-01]]). The agent's day-10 plan takes effect on day 11. It raises 10% on stays 45 and 47 and 5% on 46, and leaves 48.
- Reaction: on day 14 the median moves half of each change and stays there. That is $11.00 on stays 45 and 47 and $5.50 on 46. Stay 48's median does not move.
- Table: docs/results.md, "Seed 7 with the reaction on"
- Evidence: test_the_median_follows_the_hotels_change_after_the_lag
- Links: [[DEC-51]], [[RES-24]], [[RES-02]], [[SHK-01]], [[MOD-24]]

### RES-26 [C] The market elasticity with the reaction on, seeds 1 to 20
- Ran: `hotel-market bench --seeds 1 20 --template --react --market-elasticity E --elasticity true` at E = 0.0, 0.5 and 1.0, on 2026-10-12. The same command with `--elasticity learn:1.0 --cautious` ran the cautious arms.
- Result: the true mode earns +$111,272 a seed at 0.0, +$72,229 at 0.5 and +$43,584 at 1.0. Every arm is ahead in 20 of 20. Its rate changes fall from 298 to 207 and 161. The dates changed twice within 14 days fall from 97 to 46 and 25.
- Cautious: the cautious learn arm earns +$298,869, +$198,089 and +$99,883 accepting all. Its changes fall with the elasticity, from 890 to 696, and the dates changed twice from 734 to 646.
- Oracle: told the reaction and the value, the oracle is the ceiling again. It beats accepting all by $400 to $709 a seed in the cautious arm. In the true mode it accepts every plan and ties.
- Estimates: the cautious arms at 0.5 and 1.0 were rerun with the market term in the estimator's baseline. Their day-59 estimates then stay at 1.22 to 1.42 by hotel. Without the term they drifted to 1.45 to 1.70 at 1.0 ([[UNK-07]]).
- Table: docs/results.md, "Seeds 1 to 20 with the reaction on at a market elasticity"
- Evidence: test_the_market_elasticity_runs_pin_their_headline
- Links: [[DEC-52]], [[DEC-51]], [[RES-24]], [[RES-27]], [[UNK-07]], [[UNK-11]], [[UNK-15]]

### RES-27 [C] The day-30 competitor cut on seed 7 at a market elasticity of 0.0 and 0.5
- Ran: `python scripts/median_path.py --seed 7 --hotel full-service --stays 37 39 --days 29 39 --market-elasticity 0.5` on 2026-10-12. The same command ran at 0.0. The reaction was off.
- Result: two competitors cut 20% from shop day 30 ([[SHK-03]]). The median falls 9.6% to 9.8% on the three stay dates. The hotel holds $190 and changes nothing on them.
- Rooms: by day 39 the hotel sells 182, 202 and 161 rooms on stays 37 to 39 at 0.0. At 0.5 it sells 183, 206 and 165. A cheaper market draws more demand at 0.5, so the cut costs the hotel less.
- Table: docs/results.md, "Seed 7 at a market elasticity of 0.0 and 0.5"
- Evidence: test_a_market_elasticity_softens_a_competitor_cut_for_the_hotel
- Links: [[DEC-52]], [[RES-26]], [[SHK-03]], [[MOD-24]]

### RES-28 [C] The churn on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --churn` and `hotel-market --seeds 1 20`, then `hotel-market --seeds 1 20 --scenario upgauge`, on 2026-10-12.
- Result: with the churn the agent raises 173 seat flags over the 20 seeds, the same as without it. The filing days are 200 against 40. It changes 184 rates against 179.
- Gain: the churn's block swaps move seats for weeks, so the gain is +$34,974 a seed against +$32,899 ([[RES-01]]). The upgauge scenario earns +$21,083 with 182 seat flags and 177 changes.
- Finding: the churn stays under the threshold by construction, so the equal flag count is no finding. The finding is that the detector keys on the day-over-day seat revision, which the churn test pins.
- Table: docs/results.md, "Seeds 1 to 20 with the churn"
- Evidence: test_the_churn_and_the_upgauge_runs_pin_their_headline
- Links: [[DEC-53]], [[SHK-05]], [[SHK-06]], [[SHK-07]], [[RES-01]]

### RES-29 [C] The fitted level fed back at a demand bias of 0.9
- Ran: `hotel-market bench --seeds 1 20 --template --demand-bias 0.9 --elasticity learn:1.0 --level` and the same with `--level --cautious`, on 2026-10-12. The plain learn arms are [[RES-21]]'s.
- Result: the level is 0.90 by day 10 at every hotel. Accept-all earns -$15,244 a seed with it against -$14,376 without, and the cautious arm -$3,348 against -$4,280. The gain does not recover.
- Why: the level fixes the forecast, and the flags fall from 3,230 to 1,537. The loss is the prior elasticity's. It prices the shock raises as cheaper than they are with a tenth less demand.
- Ceiling: the oracle earns +$3,087 and +$3,512 a seed on the level arms' candidates. On the plain arms' it earns +$2,654 and +$2,748. The true mode earns +$1,913 there ([[RES-21]]), so there was little to recover.
- Table: docs/results.md, "Seeds 1 to 20 at a demand bias of 0.9, the learning agent with and without the fitted level"
- Evidence: test_the_level_runs_pin_their_headline
- Links: [[DEC-54]], [[RES-21]], [[RES-30]], [[RES-31]], [[RES-32]], [[UNK-07]], [[UNK-08]]

### RES-30 [C] The fitted level fed back at the default demand bias
- Ran: the two commands of [[RES-29]] with `--demand-bias 1.0`, on 2026-10-12. The plain learn arms are [[RES-23]]'s.
- Result: the level is 0.99 to 1.00 by hotel on day 59. Accept-all earns +$14,097 a seed against +$14,141 without the level, and the cautious arm +$24,317 against +$25,076.
- Cost: the arms lose $44 and $759 a seed to the level's noise. The oracle's ceiling stays at +$30,729 and +$31,026.
- Table: docs/results.md, "Seeds 1 to 20 at the default demand bias of 1.0, the same arms"
- Evidence: test_the_default_mode_still_gives_a_20_seed_mean_of_32899
- Links: [[DEC-54]], [[RES-23]], [[RES-29]], [[RES-31]], [[RES-32]]

### RES-31 [C] The fitted level fed back at a demand bias of 1.1
- Ran: the two commands of [[RES-29]] with `--demand-bias 1.1`, on 2026-10-12. The plain learn arms are [[RES-22]]'s.
- Result: the level is 1.10 by day 10. Accept-all earns +$95,731 a seed against +$98,401 without the level, and the cautious arm +$103,121 against +$105,522.
- Why: the corrected pace baseline removes raises on dates the start rates underprice: 553 changes against 898. Those raises paid ([[RES-22]]).
- Table: docs/results.md, "Seeds 1 to 20 at a demand bias of 1.1, the same arms"
- Evidence: test_the_level_runs_pin_their_headline
- Links: [[DEC-54]], [[RES-22]], [[RES-29]], [[RES-30]], [[RES-32]]

### RES-32 [C] The fitted level fed back with the reaction on at a market elasticity of 0.5
- Ran: `hotel-market bench --seeds 1 20 --template --react --market-elasticity 0.5 --elasticity learn:1.0`, then with `--level` and with `--level --cautious`, on 2026-10-12. The cautious plain arm is [[RES-26]]'s rerun.
- Result: the level is 1.00 by day 10 and changes little. Accept-all earns +$399,596 a seed with it against +$399,538 without, and the cautious arm +$202,454 against +$198,089.
- Ratchet: the plain learner changes 2,257 rates and the oracle, told the reaction, accepts 91% of them. That is the ratchet at its fullest, which [[FRK-09]] holds.
- Table: docs/results.md, "Seeds 1 to 20 with the reaction on at a market elasticity of 0.5, the same arms"
- Evidence: test_the_level_runs_pin_their_headline
- Links: [[DEC-54]], [[DEC-52]], [[RES-26]], [[RES-29]], [[FRK-09]]

### RES-33 [C] The agent against the pace and the rules policies on seeds 1 to 20
- Ran: `hotel-market bench --seeds 1 20 --template --policy P --demand-bias B --elasticity true` for P = pace and rules. B ran at 0.9, 1.0 and 1.1. The same ran with `--react --market-elasticity 0.5` in place of the bias, on 2026-10-12.
- Result: in the default world the rules policy earns +$22,856 a seed over frozen rates from 7,123 stay dates changed. The agent's +$32,899 is +$10,043 against it, ahead in 17 of 20.
- Pace: the pace policy earns +$11,462 there from 653 changes, and the agent's margin over it is +$21,437. It acts on no event or seat flag ([[DEC-55]]).
- Biases: at 0.9 the rules policy earns +$657 and the agent +$1,256 a seed against it. At 1.1 it earns +$79,869 from 8,385 changes, and the agent's +$112,082 is +$32,214 against it.
- Reacting: with the reaction on at a market elasticity of 0.5, the rules policy earns +$105,144. The agent's +$72,229 is -$32,914 against it, behind in every seed. The policy changes 7,091 stay dates against the agent's 207.
- Table: docs/results.md, "Seeds 1 to 20 in the true mode against the pace and the rules policies"
- Evidence: test_the_rule_based_control_runs_pin_their_headline
- Links: [[DEC-55]], [[DEC-11]], [[MOD-25]], [[RES-01]], [[RES-21]], [[RES-22]], [[RES-26]], [[FRK-11]]
