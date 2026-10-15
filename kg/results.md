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
- Ran: `hotel-market --seeds 1 20 --template` on 2026-10-15 on world v2: the agent against the fixed-rate run on each seed, with template reasons and the simulator's elasticity. The runs cover stay dates 0 to 149.
- Result: the agent run earns +$16,164 more contribution a seed, from +$11,589 to +$23,394. It is ahead in 20 of 20 seeds, a sign test's p <0.001.
- Spread: the standard deviation across the seeds is $3,166 and the standard error of the mean $708 ([[DEC-60]]). Room revenue falls $27,684 a seed, with a standard deviation of $4,231.
- Detail: the agent changes 106 rates in all. The accepted plans' estimates over holding sum to +$391,434 against +$323,281 realised. On their 1,528 nights the plans' estimates sum to +$19,861,514 against +$19,472,613 earned, 0.98 of it.
- Table: docs/results.md, "Seeds 1 to 20 in the default mode"
- Downtown: the lookup table "Accepted plans at the two downtown hotels by seed" in docs/results.md lists each seed's accepted plans at the two downtown hotels, with the day and the cause. Seed 7 has none.
- Evidence: test_the_default_mode_gives_the_pinned_20_seed_mean
- Links: [[DEC-21]], [[DEC-36]], [[DEC-38]], [[MEA-05]], [[RES-02]], [[RES-06]]

### RES-02 [C] Seed 7 in the default mode
- Ran: `hotel-market --seed 7 --template` on 2026-10-15 on world v2, both runs of seed 7 with template reasons in the default mode.
- Result: the agent run earns +$19,796 of contribution (+2.0%) and $21,324 less room revenue than the fixed-rate run. The two downtown hotels change no rate at this seed.
- Flags: 117 flags on days 0 to 59. 6 change a rate, 101 are held because no change beats hold, and 10 are held under the $250 minimum. One minimum-stay advice is given, on day 39.
- Pairs: the 70 hotel-nights the agent changed carry the whole gain, at the lifestyle and airport hotels. The other 530 book identically in both runs.
- Fixed rates: occupancy over stay dates 0 to 59 is 75.2%, 74.6%, 75.4% and 83.8% by hotel. Stay dates 140 to 149 end 77% to 96% full, and the emptiest of those nights is 60% full.
- Table: docs/results.md, "Seed 7, days 0 to 59", "Seed 7: room revenue and contribution per hotel", "Seed 7 over only the 70", "Seed 7 with fixed rates"
- Evidence: test_the_default_mode_gives_the_pinned_seed_7_figure, test_every_other_pair_books_the_same_in_both_runs, test_fixed_rate_occupancy_is_between_60_and_90_percent_for_stay_dates_0_to_59
- Links: [[DEC-05]], [[DEC-12]], [[DEC-17]], [[DEC-22]], [[SHK-04]], [[DAT-20]], [[MOD-12]], [[RES-01]]

### RES-03 [O] A wrong elasticity, fixed:1.0 and fixed:2.0, on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --template --elasticity true --elasticity fixed:1.0 --elasticity fixed:2.0` on 2026-10-15 on world v2, each arm against the same fixed-rate runs.
- Result: fixed:1.0 earns -$6,265 a seed, ahead in 3 of 20, with 766 rate changes. fixed:2.0 earns -$2,687, ahead in 6 of 20, with 566.
- Detail: on world v2 a wrong value loses money against the true arm's +$16,164. The shock plans earn -$138,974 and -$57,555 over the seeds, the other plans +$13,682 and +$3,823.
- Table: docs/results.md, "Seeds 1 to 20 per elasticity arm"
- Links: [[DEC-38]], [[CON-06]], [[RES-01]], [[RES-04]], [[RES-06]], [[UNK-07]]

### RES-04 [O] A learned elasticity, learn:1.0 and learn:2.0, on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --template --elasticity learn:1.0 --elasticity learn:2.0` on 2026-10-15 on world v2, each arm against the same fixed-rate runs.
- Result: learn:1.0 earns +$804 a seed, ahead in 11 of 20, with 510 rate changes. learn:2.0 earns +$2,416, ahead in 13 of 20, with 398.
- Detail: learning wins back little of what a wrong value loses on world v2, where the shop noise moves the ratio every day. The shock plans earn -$1,818 and +$33,752 over the seeds.
- Estimates: by day 59 the per-hotel means reach 1.42 to 1.49 from a prior of 1.0 and 1.52 to 1.75 from 2.0, against a true value of 1.5.
- Checked: test_plain_learn_mode_gives_the_same_results_as_before pins seed 7 of the learn:1.0 arm.
- Table: docs/results.md, "Seeds 1 to 20 per elasticity arm", "The learning agent's day-59 elasticity estimates"
- Links: [[DEC-38]], [[MOD-16]], [[RES-03]], [[RES-05]], [[RES-10]], [[UNK-07]]

### RES-05 [O] The cautious rule on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --template --elasticity learn:1.0 --elasticity learn:2.0 --cautious` on 2026-10-15 on world v2, each arm against the same fixed-rate runs.
- Result: learn:1.0 cautious earns +$12,527 a seed (+$1,658 to +$21,698), ahead in 20 of 20, with 295 changes. learn:2.0 cautious earns +$2,018, 12 of 20, with 213.
- Detail: from a prior of 1.0 the rule keeps 77% of the true arm's gain, against 5% without it. From 2.0 it keeps 12% against 15%.
- Rejected: 3,446 and 2,733 candidates beat hold at the estimate but lost at one end of the band.
- Minimum: the per-weekday $250 minimum of the first rule is gone ([[DEC-43]]); its world v1 figures stay in docs/results.md as measured on world v1.
- Table: docs/results.md, "Seeds 1 to 20 per elasticity arm", "The cautious rule with and without"
- Links: [[DEC-39]], [[DEC-43]], [[CON-11]], [[RES-04]], [[RES-06]], [[RES-13]]

### RES-06 [O] Where the gain came from, by arm
- Ran: every sweep of seeds 1 to 20 reports the shock plans apart from every other plan ([[RUL-55]]), on 2026-10-15 on world v2. The shock plans are those the convention (day 10) and the new flights (day 20) raised.
- Result: in the true arm 63 shock plans earn +$302,280 over the 20 seeds, and 43 other plans earn +$21,001. The shock plans therefore give 94% of the gain.
- Detail: in the true arm the plans' estimates for the 1,528 nights they changed sum to +$19,861,514 against +$19,472,613 earned after the decisions, 0.98 of it. A wrong elasticity's other changes earn little or lose.
- Table: docs/results.md, "Where each arm's gain came from"
- Links: [[DAT-24]], [[RUL-55]], [[SHK-01]], [[SHK-02]], [[RES-01]], [[RES-03]], [[RES-04]], [[RES-05]]

### RES-07 [O] The revenue target on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --template --target revenue` on 2026-10-15 on world v2, with the simulator's elasticity and the template. The arm runs against the same fixed-rate runs as the contribution target.
- Result: the revenue target earns +$179,333 of room revenue a seed, ahead in 20 of 20. That is about 0.8% of the fixed-rate revenue. It earns -$8,214 of contribution.
- Detail: it changes 805 rates against the contribution target's 106. +$3,417,461 of the revenue gain comes from the 145 shock plans.
- Estimates: the accepted plans' estimates sum to 1.01 of the realised revenue gain (+$3,608,913 against +$3,586,668).
- Table: docs/results.md, "Seeds 1 to 20 with the simulator's elasticity and the template, each target"
- Links: [[DEC-41]], [[RUL-58]], [[FRK-01]], [[CON-07]], [[MEA-04]], [[RES-01]]

### RES-08 [C] Four live runs of seed 7, one per request format
- Ran: `python scripts/live_audit.py --seed 7` four times with claude-opus-5-5, the request format changing between the runs ([[DEC-44]]). It is measured on world v1 (commit b178e7b); the world v2 run is [[RES-09]].
- Result: each run makes the same 7 calls as the template run. The model accepts all 7 plans every time, 28 of 28, so contribution ends at +$28,818 each time.
- Tokens: the input was 20,329 tokens with bare numbers and 37,107 with a raw value beside each display string. It was 24,219 with display strings and named-pair ranges, and 21,148 with each range as one phrase.
- Reasons: the first run wrote figures its own way and added claims the entry does not make. The second put direction words on signs, and the third joined range ends with its own words. The fourth copied every phrase whole.
- Kept: the fourth run was recorded as [[DAT-29]] until the world v2 run replaced it on 2026-10-15; all four are now quoted from the sessions that made them.
- Table: docs/results.md, "Four live runs of seed 7"
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_recorded_live_run_replays_without_a_key_and_gives_19796
- Links: [[DEC-44]], [[UNK-01]], [[UNK-02]], [[MOD-22]], [[RES-09]]

### RES-09 [C] The recorded live run of seed 7, measured
- Ran: `make live-audit SEED=7` on 2026-10-15 on world v2 with claude-opus-5-5; its cache and its calls.jsonl are kept as [[DAT-29]]. The model chose the template's option on every entry.
- Result: the 4 calls used 15,469 input tokens (1,936 to 7,474 a call) and 1,034 output tokens (131 to 493). They cost $0.08 at list prices of $4 and $20 per million tokens.
- Time: the model took 18 s in all, 3.0 to 5.7 s a call with a median of 4.5 s. The whole run with both simulations took 19 s, and no prompt cache was read or written.
- Calls: every call ended with the stop reason end_turn. None was refused and none fell back to another model. Every answer parsed and named the entry's id and an allowed choice.
- Audit: 6 plans accepted, none declined. 5 figures match no request phrase: three per-day gains restated as "$2,780 on Monday" and an earlier change paraphrased. 4 sentences hold no request figure.
- Table: docs/results.md, "The recorded live run of seed 7"
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit
- Links: [[UNK-09]], [[UNK-02]], [[DAT-29]], [[MOD-22]], [[RUL-46]]

### RES-10 [C] The estimator against known elasticities
- Ran: seed 7 in learn:1.5 mode with the simulator's ELASTICITY set to 1.0, 1.5 and 2.0 in turn, on 2026-10-15 on world v2. Each hotel's day-59 estimate is compared with the truth.
- Result: every estimate lands within three standard errors of the truth, where the test allows three; the airport hotel at 1.0 and the full-service hotel at 2.0 sit the furthest.
- Detail: on seed 7 the standard errors are 0.13 to 0.27 and each hotel has about 5,300 observations by day 59.
- Variation: in a fixed-rate run the observations' log rate ratio has a standard deviation of 0.012 to 0.027 by hotel. Since world v2 the shop noise moves the ratio every day, and the agent's own rate changes add to it.
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
- Ran: `python -m pytest --slow` from a fresh virtual environment on Python 3.12.6 and 3.13.7 on 2026-10-12. On 2026-10-15, on world v2, `python -m pytest` on both and `make test-all` on 3.12.6, with numpy 2.5.4 and pandas 3.0.6.
- Result: the full suite gave 386 passed on 3.12.6, the plain one 377 passed with 9 skipped. The plain suite on 3.13.7 gave 372 passed with 14 skipped, without the demo extra, after the seed-7 re-record.
- Detail: the package was also installed and run against numpy 1.26 and pandas 2.2, the lower bounds in pyproject.toml. A seed-7 run then reproduced decisions.jsonl byte for byte ([[DEC-28]]).
- Table: docs/results.md, "The suite on each Python version"
- Links: [[UNK-04]], [[DEC-28]], [[DEC-30]]


### RES-16 [C] The reviewers at fixed:1.0 on seeds 1 to 20
- Ran: `hotel-market bench --seeds 1 20` on 2026-10-15 on world v2. Each seed: the fixed-rate run, then the template, the oracle and the three models in each mode. The tables were printed from the caches with no call.
- Detail: the live calls ran first, one process per command: seeds 1 to 3, then seeds 4 to 20 in six ranges of up to three seeds, sixteen processes at a time. Each arm's cache folder holds its calls.jsonl.
- Result: the template earns -$6,265 a seed and the oracle +$13,107 while accepting 11% of the plans. Opus earns +$305, ahead in 8 of 20, a recovered share of 0.34. Sonnet earns -$6,184 and Haiku -$6,265.
- Declines: Opus declines 230 plans with precision 1.00 and recall 0.31; its dollar-weighted recall is 0.33. Sonnet declines 8 plans with precision 1.00 and recall 0.01. Haiku declines none.
- Gap: the oracle's +$13,107 at fixed:1.0 stands next to the true mode's +$16,164 ([[RES-01]]). The $19,372 a seed between the template and the oracle is the value a reviewer can recover. Opus's regret is $12,802 a seed.
- Table: docs/results.md, "Seeds 1 to 20 at a fixed elasticity of 1.0"
- Evidence: test_the_offline_bench_on_20_seeds_pins_the_benchmarks_headline
- Links: [[DEC-47]], [[DEC-48]], [[DEC-49]], [[MEA-12]], [[RES-01]], [[RES-03]], [[RES-19]], [[UNK-01]]

### RES-17 [C] The reviewers at fixed:2.0 on seeds 1 to 20
- Ran: the same command as [[RES-16]], the fixed:2.0 arms, on 2026-10-15 on world v2.
- Result: the template earns -$2,687 a seed and the oracle +$6,006 while accepting 13% of the plans. Opus earns -$2,442, a recovered share of 0.03. Sonnet earns -$2,681 and Haiku -$2,687.
- Declines: Opus declines 40 plans with precision 0.93 and recall 0.08. Sonnet declines 5 plans with precision 1.00 and recall 0.01. Haiku declines none. The oracle declines 87% of the plans in this mode.
- Table: docs/results.md, "Seeds 1 to 20 at a fixed elasticity of 2.0"
- Evidence: test_the_offline_bench_on_20_seeds_pins_the_benchmarks_headline
- Links: [[RES-16]], [[RES-03]], [[DEC-47]], [[DEC-49]], [[UNK-01]]

### RES-18 [O] The reviewers in the true mode on seeds 1 to 20
- Ran: the same command as [[RES-16]], the true-mode arms, on 2026-10-15 on world v2.
- Result: every reviewer earns +$16,164 a seed, ahead in 20 of 20, the figure of [[RES-01]]. No model declines a plan, so the mode cannot separate them ([[DEC-47]]).
- Calls: 93 calls a model. Opus costs $1.68, Sonnet $0.85 and Haiku $0.07 at list prices, with median latencies of 3.4, 2.7 and 4.3 s. Invalid answers: 0.
- Table: docs/results.md, "Seeds 1 to 20 in the true mode"
- Links: [[RES-01]], [[RES-16]], [[DEC-47]], [[UNK-01]], [[UNK-02]], [[UNK-09]]

### RES-19 [O] The reviewers ranked across the mismatched modes
- Ran: the same command as [[RES-16]]; the ranking pools the fixed:1.0 and fixed:2.0 arms, 40 per reviewer, on 2026-10-15 on world v2.
- Result: the oracle earns +$9,557 a seed. Opus earns -$1,068, a recovered share of 0.24, with precision 0.99 and recall 0.23. The template earns -$4,476, Sonnet -$4,432 and Haiku -$4,476.
- Cost: over the two modes Opus makes 1,313 calls for $24.33, Sonnet 1,205 for $9.48 and Haiku 1,201 for $0.78. The fixed benchmark's 4,006 calls cost $37.19 at list prices ([[RUL-80]]).
- Table: docs/results.md, "The reviewers ranked across the mismatched modes"
- Links: [[RES-16]], [[RES-17]], [[DEC-48]], [[MEA-12]], [[UNK-09]]

### RES-20 [O] The container image on each Python version
- Ran: `make image PYTHON=3.11`, `make image` (3.12) and `make image PYTHON=3.14`, then `make docker-test` on each, on 2026-10-12. Docker 28.4.0 ran on an aarch64 Ubuntu VM with 4 CPUs and 4 GiB.
- Result: each image builds in 24 s and passes 278 tests with 3 skipped, the slow ones, in about 45 s. The 3.12 image runs seed 7 in 1.6 s, and its decisions.jsonl matches the native run's sha256.
- Detail: every dependency came as a wheel on all three Pythons, 3.14 included. pip took numpy 2.4.6 on 3.11 and 2.5.4 on 3.12 and 3.14. pandas 3.0.6, duckdb 1.5.6 and anthropic 1.13.0 are the same everywhere.
- Sizes: the images are 615 MB, 592 MB and 600 MB on 3.11, 3.12 and 3.14. The suite inside the image runs from its copy of the repository. The demo file and the schema lookups expect the repository root.
- Refreshed: the images were not rebuilt. On world v2 the native seed-7 checksum is 263387b3 on numpy 2.5.4 and pandas 3.0.6. A Linux run on numpy 2.5.3 and pandas 3.0.5 gave 8faafad0 with the same decisions.
- Table: docs/results.md, "The container image on each Python version"
- Links: [[UNK-03]], [[DEC-28]], [[RES-15]]

### RES-21 [C] Seeds 1 to 20 at a demand bias of 0.9
- Ran: `hotel-market bench --seeds 1 20 --template --demand-bias 0.9 --elasticity true --elasticity fixed:1.0 --elasticity learn:1.0` on 2026-10-15 on world v2. The same command with `--elasticity learn:1.0 --cautious` ran the cautious arm.
- Result: the true mode earns +$1,069 a seed (sd $3,270, se $731), ahead in 12 of 20, p 0.50, against +$16,164 at 1.0 ([[RES-23]]). Say-yes-to-everything earns -$25,072 at fixed:1.0 and -$15,174 at learn:1.0.
- Flags: the true mode raises 4648 flags over the 20 seeds, 85% with a pace cause, and changes 63 rates. Say-yes-to-everything at fixed:1.0 changes 1448.
- Estimates: the learn:1.0 arm's day-59 estimates are 1.40 to 1.51 by hotel, against 1.42 to 1.49 at 1.0. The cautious arm's are 1.36 to 1.50.
- Oracle: the oracle earns +$321 to +$613 in the mismatched modes and accepts 1% to 5% of the plans there.
- Table: docs/results.md, "Seeds 1 to 20 at a demand bias of 0.9"
- Evidence: test_the_demand_bias_runs_pin_their_headline
- Links: [[DEC-50]], [[DEC-60]], [[RUL-82]], [[RES-22]], [[RES-23]], [[UNK-07]], [[UNK-08]]

### RES-22 [C] Seeds 1 to 20 at a demand bias of 1.1
- Ran: the two commands of [[RES-21]] with `--demand-bias 1.1`, on 2026-10-15 on world v2.
- Result: the true mode earns +$66,687 a seed, ahead in 20 of 20; say-yes-to-everything earns +$47,451 at fixed:1.0 and +$56,213 at learn:1.0. The oracle earns +$66,455 to +$63,660 in the mismatched modes.
- Flags: the true mode raises 11132 flags over the 20 seeds, 93% with a pace cause. It changes 343 rates against 106 at 1.0. The start rates were set for a smaller market, so the dates run ahead of pace.
- Estimates: the learn:1.0 arm's day-59 estimates are 1.43 to 1.50 by hotel, against 1.42 to 1.49 at 1.0 ([[RES-23]]). The cautious arm's are 1.40 to 1.48.
- Table: docs/results.md, "Seeds 1 to 20 at a demand bias of 1.1"
- Evidence: test_the_demand_bias_runs_pin_their_headline
- Links: [[DEC-50]], [[RUL-82]], [[RES-21]], [[RES-23]], [[UNK-07]], [[UNK-08]]

### RES-23 [C] The same arms at the default demand bias of 1.0
- Ran: the two commands of [[RES-21]] with `--demand-bias 1.0`, on 2026-10-15 on world v2. The run read no cache and made no call.
- Result: the true, fixed:1.0 and template learn arms repeat [[RES-01]], [[RES-03]], [[RES-04]] and [[RES-05]] to the dollar. They earn +$16,164, -$6,265, +$804 and +$12,527 a seed.
- Oracle: in learn:1.0 the oracle earns +$13,199 a seed and accepts 17% of the plans. In the cautious arm it earns +$14,854 and accepts 32%.
- Flags: the true mode raises 2009 flags over the 20 seeds, 67% with a pace cause. Say-yes-to-everything at fixed:1.0 raises 1099 and changes 766 rates, each holding its stay dates for seven days ([[RUL-66]]).
- Table: docs/results.md, "Seeds 1 to 20 at the default demand bias of 1.0"
- Evidence: test_the_offline_bench_on_20_seeds_pins_the_benchmarks_headline, test_the_default_mode_gives_the_pinned_20_seed_mean
- Links: [[DEC-50]], [[RUL-82]], [[RES-01]], [[RES-04]], [[RES-05]], [[RES-16]], [[RES-21]], [[RES-22]]

### RES-24 [C] The competitor reaction on seeds 1 to 20
- Ran: `hotel-market bench --seeds 1 20 --template --react --elasticity true` and the same with `--elasticity learn:1.0 --cautious`, on 2026-10-15 on world v2, where the market elasticity is 1.0 by default.
- Result: in the true mode every arm earns +$35,324 a seed against the fixed-rate run, 2.2 times the +$16,164 without the reaction ([[RES-01]]). The cautious learn arm earns +$65,216 accepting all.
- Why: bookings follow the rate against the comp median ([[RUL-21]]); since world v2 demand also falls with the median's level. A half-followed raise still costs few rooms, and the moved median raises a new flag.
- Repeats: the true mode changes 119 rates against 106 without the reaction. 427 of its 898 comp-median flags follow the hotels' own changes, and 23 stay dates change twice within 14 days. The cautious learn arm changes 535 twice.
- Oracle: told the reaction and the market elasticity, the oracle accepts 100% of the cautious arm's plans and earns +$65,216 a seed, +$0 against accepting all.
- Table: docs/results.md, "Seeds 1 to 20 with the reaction on"
- Evidence: test_the_reacting_runs_pin_their_headline
- Links: [[DEC-51]], [[DEC-37]], [[RES-01]], [[RES-05]], [[RES-23]], [[RES-25]], [[UNK-11]]

### RES-25 [C] The comp median's path on seed 7 with the reaction on
- Ran: `python scripts/median_path.py --seed 7 --react --hotel lifestyle --stays 75 75 --days 16 25` on 2026-10-15 on world v2.
- Result: on world v2 the downtown hotels change nothing on the convention nights at seed 7. The first accepted plan is the lifestyle hotel's day-18 raise of 10% on stay date 75, in force from day 19; a second raise follows on day 20.
- Reaction: on day 22 the median moves half of the first change, $12.00, and on day 24 half of the whole change from the start rate, $25.20, over the shop noise that moves it every day.
- Table: docs/results.md, "Seed 7 with the reaction on"
- Evidence: test_the_median_follows_the_hotels_change_after_the_lag
- Links: [[DEC-51]], [[RES-24]], [[RES-02]], [[SHK-01]], [[MOD-24]]

### RES-26 [C] The market elasticity with the reaction on, seeds 1 to 20
- Ran: `hotel-market bench --seeds 1 20 --template --react --market-elasticity E --elasticity true` at E = 0.0 and 0.5 on 2026-10-15 on world v2; 1.0 is [[RES-24]]. The same with `--elasticity learn:1.0 --cautious` ran the cautious arms.
- Result: the true mode earns +$87,519 a seed at 0.0, +$58,275 at 0.5 and +$35,324 at 1.0. Its rate changes are 236, 164 and 119, and the dates changed twice within 14 days 95, 46 and 23.
- Cautious: the cautious learn arm earns +$224,222, +$141,469 and +$65,216 accepting all. Its changes are 963, 822 and 734.
- Oracle: told the reaction and the value, the oracle is the ceiling over the agent's own candidates. In the cautious arm it earns +$224,302, +$141,469 and +$65,216, accepting 100%, 100% and 100% of the plans.
- Estimates: the cautious arms' day-59 estimates are 1.31 to 1.42, 1.31 to 1.46 and 1.29 to 1.47 by hotel, with the market term in the estimator's baseline ([[UNK-07]]).
- Table: docs/results.md, "Seeds 1 to 20 with the reaction on at a market elasticity"
- Evidence: test_the_market_elasticity_runs_pin_their_headline
- Links: [[DEC-52]], [[DEC-51]], [[RES-24]], [[RES-27]], [[UNK-07]], [[UNK-11]], [[UNK-15]]

### RES-27 [C] The day-30 competitor cut on seed 7 by market elasticity
- Ran: `python scripts/median_path.py --seed 7 --hotel full-service --stays 37 39 --days 29 39 --market-elasticity E` at E = 0.0, 0.5 and 1.0, the default, on 2026-10-15 on world v2. The reaction was off.
- Result: two competitors cut 20% from shop day 30 ([[SHK-03]]). The median falls about a tenth on the three stay dates, over the daily shop noise. The hotel holds $190 and changes nothing on them.
- Rooms: by day 39 the hotel sells 196, 182, 165 rooms on stays 37 to 39 at 0.0, 198, 183, 168 at 0.5 and 199, 184, 170 at 1.0. A cheaper market draws more demand as the elasticity rises, so the cut costs the hotel less.
- Table: docs/results.md, "Seed 7 at a market elasticity of 0.0, 0.5 and 1.0"
- Evidence: test_a_market_elasticity_softens_a_competitor_cut_for_the_hotel
- Links: [[DEC-52]], [[RES-26]], [[SHK-03]], [[MOD-24]]

### RES-28 [C] The churn on seeds 1 to 20
- Ran: `hotel-market --seeds 1 20 --template --churn` and `hotel-market --seeds 1 20 --template`, then `hotel-market --seeds 1 20 --template --scenario upgauge`, on 2026-10-15 on world v2.
- Result: with the churn the agent raises 199 seat flags over the 20 seeds against 199 without it. The filing days are 200 against 40. It changes 108 rates against 106.
- Gain: the churn's block swaps move seats, and so passengers, for weeks, so the gain is +$17,848 a seed against +$16,164 ([[RES-01]]). The upgauge scenario earns +$5,913 with 201 seat flags and 84 changes.
- Finding: the churn stays under the threshold by construction, so the flag count is no finding. The finding is that the detector keys on the day-over-day passenger revision, which the churn test pins.
- Table: docs/results.md, "Seeds 1 to 20 with the churn"
- Evidence: test_the_churn_and_the_upgauge_runs_pin_their_headline
- Links: [[DEC-53]], [[SHK-05]], [[SHK-06]], [[SHK-07]], [[RES-01]]

### RES-29 [C] The fitted level fed back at a demand bias of 0.9
- Ran: `hotel-market bench --seeds 1 20 --template --demand-bias 0.9 --elasticity learn:1.0 --level` and the same with `--level --cautious`, on 2026-10-15 on world v2. The plain learn arms are [[RES-21]]'s.
- Result: the level is 0.90 to 0.90 by day 59 at every hotel. Say-yes-to-everything earns -$13,700 a seed with it against -$15,174 without, and the cautious arm -$3,534 against -$4,122.
- Why: the level fixes the forecast, and the flags fall from 5420 to 1538. The loss is the prior elasticity's: it prices the shock raises as cheaper than they are with a tenth less demand.
- Ceiling: the oracle earns +$664 and +$999 a seed on the level arms' candidates. The true mode earns +$1,069 there ([[RES-21]]), so there was little to recover.
- Table: docs/results.md, "Seeds 1 to 20 at a demand bias of 0.9, the learning agent with and without the fitted level"
- Evidence: test_the_level_runs_pin_their_headline
- Links: [[DEC-54]], [[RES-21]], [[RES-30]], [[RES-31]], [[RES-32]], [[UNK-07]], [[UNK-08]]

### RES-30 [C] The fitted level fed back at the default demand bias
- Ran: the two commands of [[RES-29]] with `--demand-bias 1.0`, on 2026-10-15 on world v2. The plain learn arms are [[RES-23]]'s.
- Result: the level is 0.99 to 1.00 by hotel on day 59. Say-yes-to-everything earns +$825 a seed against +$804 without the level, and the cautious arm +$12,346 against +$12,527.
- Cost: the oracle's ceiling on the level arms is +$13,171 and +$14,352.
- Table: docs/results.md, "Seeds 1 to 20 at the default demand bias of 1.0, the same arms"
- Evidence: test_the_default_mode_gives_the_pinned_20_seed_mean
- Links: [[DEC-54]], [[RES-23]], [[RES-29]], [[RES-31]], [[RES-32]]

### RES-31 [C] The fitted level fed back at a demand bias of 1.1
- Ran: the two commands of [[RES-29]] with `--demand-bias 1.1`, on 2026-10-15 on world v2. The plain learn arms are [[RES-22]]'s.
- Result: the level is 1.09 to 1.10 by day 59. Say-yes-to-everything earns +$55,518 a seed against +$56,213 without the level, and the cautious arm +$60,005 against +$60,666.
- Why: the corrected pace baseline removes raises on dates the start rates underprice: 683 changes against 1007. Those raises paid ([[RES-22]]).
- Table: docs/results.md, "Seeds 1 to 20 at a demand bias of 1.1, the same arms"
- Evidence: test_the_level_runs_pin_their_headline
- Links: [[DEC-54]], [[RES-22]], [[RES-29]], [[RES-30]], [[RES-32]]

### RES-32 [C] The fitted level fed back in the reacting market at 0.5
- Ran: `hotel-market bench --seeds 1 20 --template --react --market-elasticity 0.5 --elasticity learn:1.0`, then with `--level` and with `--level --cautious`, on 2026-10-15 on world v2. The cautious plain arm is [[RES-26]]'s.
- Result: the level is 0.99 to 1.00 by day 59. Say-yes-to-everything earns +$304,114 a seed with it against +$302,095 without, and the cautious arm +$139,141 against +$141,469.
- Ratchet: the plain learner changes 1959 rates and the oracle, told the reaction, accepts 96% of them. That is the ratchet at its fullest, which [[FRK-09]] holds.
- Table: docs/results.md, "Seeds 1 to 20 with the reaction on at a market elasticity of 0.5, the same arms"
- Evidence: test_the_level_runs_pin_their_headline
- Links: [[DEC-54]], [[DEC-52]], [[RES-26]], [[RES-29]], [[FRK-09]]

### RES-33 [C] The agent against the pace and the rules policies
- Ran: `hotel-market bench --seeds 1 20 --template --policy P --demand-bias B --elasticity true` for P = pace and rules, at B = 0.9, 1.0 and 1.1, and with `--react --market-elasticity 0.5` in place of the bias, on 2026-10-15 on world v2.
- Result: in the default world the rules policy earns +$9,008 a seed over frozen rates from 6857 stay dates changed. The agent's +$16,164 is +$7,156 against it, ahead in 19 of 20.
- Pace: the pace policy earns +$1,432 there from 348 changes, and the agent's margin over it is +$14,732. It acts on no event or seat flag ([[DEC-55]]).
- Biases: at 0.9 the rules policy earns -$2,177 and the agent +$3,246 a seed against it. At 1.1 it earns +$44,928 from 8315 changes, and the agent's +$66,687 is +$21,759 against it.
- Reacting: with the reaction on at a market elasticity of 0.5, the rules policy earns +$83,273. The agent's +$58,275 is -$24,998 against it, ahead in 0 of 20. The policy changes 6968 stay dates against the agent's 164.
- Table: docs/results.md, "Seeds 1 to 20 in the true mode against the pace, the rules and the never-cut policies"
- Evidence: test_the_rule_based_control_runs_pin_their_headline
- Links: [[DEC-55]], [[DEC-11]], [[MOD-25]], [[RES-01]], [[RES-21]], [[RES-22]], [[RES-26]], [[FRK-11]]

### RES-34 [C] The reviewers at learn:1.0 on seeds 1 to 20
- Ran: `hotel-market bench --seeds 1 20 --elasticity learn:1.0 --elasticity learn:2.0 --model claude-opus-5-5 --model claude-haiku-5-5` on 2026-10-15 on world v2. Sonnet ran at learn:1.0 alone, in its own command.
- Detail: the live calls ran with the fixed arms', one process per command and seed range. The projection from seeds 1 to 3 priced the learn set at $43.85; it came to $48.73 ([[RES-39]]).
- Result: the template earns +$804 a seed and the oracle +$13,199 while accepting 17% of the plans. Opus earns +$2,049, a recovered share of 0.10. Sonnet earns +$803 and Haiku +$783.
- Declines: Opus declines 41 plans with precision 1.00 and recall 0.11. Sonnet declines 4 plans with precision 1.00 and recall 0.01. Haiku declines 2 plans with precision 1.00 and recall 0.01.
- Estimates: the day-59 estimates are 1.42 to 1.49 by hotel under the template and 1.28 to 1.43 under the oracle ([[RES-04]]).
- Table: docs/results.md, "Seeds 1 to 20 at a learned elasticity from a prior of 1.0, each reviewer"
- Evidence: test_the_learn_arms_pin_their_headline
- Links: [[RES-04]], [[RES-16]], [[RES-35]], [[RES-38]], [[RES-39]], [[DEC-47]], [[MEA-12]], [[UNK-01]]

### RES-35 [C] The reviewers at learn:1.0 with the cautious rule
- Ran: the commands of [[RES-34]] with `--cautious`, on 2026-10-15 on world v2, with the display [[DEC-56]] fixed before the run.
- Result: the template earns +$12,527 a seed and the oracle +$14,854 while accepting 32% of the plans. Opus earns +$12,561, Sonnet +$12,527 and Haiku +$12,269. The day-59 estimates are 1.36 to 1.46 under the template ([[RES-05]]).
- Declines: Opus declines 5 plans with precision 1.00 and recall 0.03. Sonnet declines none. Haiku declines 1 plan with precision 0.00 and recall 0.00.
- History: on world v1 the first display rounded a band-end gain under $5 to "the same as holding", and the three models declined such plans as a failed rule. [[DEC-56]] writes the gain to the dollar and states the rule's verdict.
- Table: docs/results.md, "Seeds 1 to 20 at a learned elasticity from a prior of 1.0 with the cautious rule, each reviewer"
- Evidence: test_the_learn_arms_pin_their_headline
- Links: [[RES-05]], [[RES-34]], [[RES-36]], [[RES-38]], [[CON-11]], [[DEC-39]], [[DEC-56]], [[MOD-08]], [[MOD-11]], [[UNK-01]]

### RES-36 [C] The reviewers at learn:2.0, with and without the cautious rule
- Ran: the commands of [[RES-34]] and [[RES-35]], the learn:2.0 arms, on 2026-10-15 on world v2. Opus and Haiku ran them; Sonnet did not.
- Plain: the template earns +$2,416 a seed and the oracle +$7,190 while accepting 28%. Opus earns +$2,812 with 12 plans declined and Haiku +$2,457 with 1.
- Cautious: the template earns +$2,018 and the oracle +$4,132 while accepting 31%. Opus earns +$2,018 with 0 plans declined and Haiku +$2,018 with 0.
- Estimates: the day-59 estimates are 1.52 to 1.75 by hotel without the rule and 1.55 to 1.91 with it, under the template.
- Table: docs/results.md, "Seeds 1 to 20 at a learned elasticity from a prior of 2.0"
- Evidence: test_the_learn_arms_pin_their_headline
- Links: [[RES-04]], [[RES-05]], [[RES-17]], [[RES-34]], [[RES-35]], [[RES-38]], [[UNK-01]]

### RES-37 [C] The reviewers at learn:1.0 cautious in the reacting market at 0.5
- Ran: `hotel-market bench --seeds 1 20 --elasticity learn:1.0 --cautious --react --market-elasticity 0.5 --model claude-opus-5-5` on 2026-10-15 on world v2. The template and the oracle ran beside Opus.
- Result: the template earns +$141,469 a seed ([[RES-26]]) and the oracle +$141,469 while accepting 100% of the plans. Opus earns +$139,231 with 28 plans declined, $2,238 a seed under accepting all.
- Recent: Opus is shown 583 plans on stay dates the hotel changed within 14 days and holds 27 ([[MEA-14]]). The oracle holds 0 of 582. Opus's dates changed twice are 602 against the template's 609.
- Request: since world v2 the request lists the hotel's earlier changes on the stay dates, each with the rooms booked since against the rooms expected ([[DEC-45]]), which [[FRK-09]] asked for.
- Table: docs/results.md, "Seeds 1 to 20 at a learned elasticity from a prior of 1.0 with the cautious rule, the reaction"
- Evidence: test_the_learn_arms_pin_their_headline
- Links: [[RES-26]], [[RES-33]], [[RES-35]], [[RES-38]], [[FRK-09]], [[DEC-51]], [[DEC-52]], [[MEA-14]], [[UNK-11]]

### RES-38 [O] The decline rate by standard-error group in the learn arms
- Ran: the commands of [[RES-34]] to [[RES-37]] on 2026-10-15 on world v2. The bench prints the groups of [[RUL-102]] for every live arm that declined a plan ([[MEA-13]]).
- Result: Opus from the prior of 1.0 declines 7 of 8 plans under 0.15, 20 of 76 from 0.15 to 0.25, 8 of 93 to 0.35 and 6 of 345 at 0.35 and over. The rate falls as the standard error rises.
- Finding: on world v2 the standard error moves Opus's declines from the prior of 1.0: it declines most of the plans whose estimate rests on little data. On world v1 the rate was flat across the groups.
- Others: Opus from 2.0 declines 8 of 80 from 0.15 to 0.25 and 4 of 264 at 0.35 and over; reacting, 6 of 35, 13 of 174 and 9 of 617. Sonnet and Haiku decline 0 to 2 plans a group.
- Table: docs/results.md, "The decline rate by the standard error of the plan's elasticity"
- Links: [[RUL-102]], [[MEA-13]], [[RES-34]], [[RES-35]], [[RES-36]], [[RES-37]], [[UNK-07]]

### RES-39 [O] The reviewers ranked across the learned modes, and the arms' cost
- Ran: the commands of [[RES-34]] and [[RES-35]] on 2026-10-15 on world v2. Each ranking pools the two priors, 40 seeds per reviewer. Sonnet ran from the prior of 1.0 only, so it is not ranked.
- Plain: the oracle earns +$10,194 a seed accepting 21% of the plans. Opus earns +$2,431 with a recovered share of 0.10, precision 0.98 and recall 0.09. The template earns +$1,610 and Haiku +$1,620.
- Cautious: the oracle earns +$9,493 accepting 32%. Opus earns +$7,289, the template +$7,273 and Haiku +$7,143. Opus's precision is 1.00 and its recall 0.02.
- Cost: the five commands make 3,737 calls for $48.73 at list prices ([[RUL-80]]). The projection from seeds 1 to 3 was $43.85. With the fixed arms the benchmark's 7,743 calls cost $85.92.
- Invalid: 0 records hold a bad attempt. The API refused the first schema's array bound on world v1 ([[UNK-02]]); the schema is now an object with one required decision per entry.
- Table: docs/results.md, "The reviewers ranked across the learned modes", "The learn arms' cost"
- Links: [[RES-19]], [[RES-34]], [[RES-35]], [[RES-36]], [[RES-37]], [[DEC-34]], [[DEC-48]], [[MEA-12]], [[UNK-02]]

### RES-40 [C] The agent against the never-cut policy
- Ran: `hotel-market bench --seeds 1 20 --template --policy never-cut --demand-bias B --elasticity true` at B = 0.9, 1.0 and 1.1, and the same with `--react --market-elasticity 0.5` in place of the bias, on 2026-10-15 on world v2.
- Result: in the default world the never-cut policy earns +$10,468 a seed over frozen rates from 5153 stay dates changed. The agent's +$16,164 is +$5,696 against it (sd $5,852, se $1,308), ahead in 18 of 20, p <0.001.
- Cuts: the rules policy earns +$9,008 there ([[RES-33]]), so its cuts cost it about $1,460 a seed. The start rate is the best rate on a night that will not sell out, so every cut loses.
- Biases: at 0.9 the policy earns -$1,847 a seed and the agent is +$2,916 against it, ahead in 14 of 20. At 1.1 it earns +$51,711 from 6645 changes, and the agent's +$66,687 is +$14,976 against it.
- Reacting: with the reaction on at a market elasticity of 0.5, the policy earns +$112,877 from 5266 changes. The agent's +$58,275 is -$54,602 against it, ahead in 0 of 20.
- Table: docs/results.md, "Seeds 1 to 20 in the true mode against the pace, the rules and the never-cut policies"
- Evidence: test_the_rule_based_control_runs_pin_their_headline
- Links: [[DEC-55]], [[DEC-60]], [[RES-33]], [[MOD-25]]

### RES-41 [C] The convention without the competitors' raise
- Ran: `python scripts/no_comp_raise.py --seeds 1 20` on 2026-10-15 on world v2. It runs the template sweep as shipped, then with the convention's competitor raise at 0.0 and its demand uplift still 35%.
- Result: with the raise at zero the mean moves from +$16,164 to +$15,611 a seed (+$11,019 to +$22,581), ahead in 20 of 20. The convention plans earn +$100 a seed on their stay dates, against +$614 with the raise.
- Why: on world v2 the downtown hotels hold most of their convention business before the announcement, and the market's own price response takes back part of what the raise gave, so the raise moves the headline little.
- Sold out: at fixed rates the two downtown hotels sell out 14 of 160 convention nights with the raise and 4 of 160 without it.
- Table: docs/results.md, "Seeds 1 to 20 with the convention's competitor raise"
- Evidence: test_the_raise_at_zero_keeps_the_uplift_and_puts_the_event_back
- Links: [[SHK-01]], [[RUL-21]], [[RES-01]], [[RES-06]], [[MOD-29]], [[DEC-59]]

### RES-42 [C] The default agent in a revenue manager's measures
- Ran: `python scripts/measures.py --seeds 1 20` on 2026-10-15 on world v2. It gives both runs' occupancy, average rate, RevPAR and sold-out share per hotel, and what the agent run gave up and saved a seed.
- Occupancy: 76.9%, 76.5%, 77.0% and 88.9% by hotel at fixed rates, and 76.8%, 76.5%, 76.1% and 86.1% in the agent run. The sold-out share of nights falls from 0.4%, 0.7%, 10.2% and 20.0% to 0.2%, 0.5%, 7.1% and 12.0%.
- RevPAR: $169.07 to $169.07, $145.37 to $145.36, $184.76 to $184.44, $124.50 to $123.53. The agent run gives up 5, 11, 166 and 632 room nights a seed by hotel.
- Break-even: the airport hotel's gain is zero at a room cost of 24.7% of the start rate, the lifestyle hotel's at 14.1% and the full-service hotel's at 18.2%. The convention hotel gains at any cost, because its room revenue rose.
- Table: docs/results.md, "Seeds 1 to 20 in a revenue manager's measures", "Seeds 1 to 20: what the agent run gave up"
- Evidence: test_the_measures_are_the_books_measures_over_the_seeds
- Links: [[MEA-01]], [[MEA-02]], [[MEA-03]], [[RUL-61]], [[RES-01]], [[UNK-06]], [[MOD-30]]

### RES-43 [O] The clock: one tick a day against four on seeds 1 to 20
- Ran: `python scripts/tick_sweep.py --seeds 1 20` on 2026-10-15 on world v2: each seed with the template at --ticks 1 and at --ticks 4, the same world, each against the fixed-rate run ([[MOD-31]]).
- Result: at four ticks the agent earns +$16,204 a seed against +$16,164 at one. The paired difference is +$40 a seed (sd $483, se $108), range -$1,246 to +$1,001, the finer clock ahead in 10 of 20, p 1.0.
- Finding: a finer clock earns nothing in this world, because the world's demand moves once a day except at the shocks, and that is the expected result. It would earn where shops, filings or bookings move within the day.
- Ticks: 4,504 decisions were made at a tick other than the day's last, mostly pace flags read again at every tick, and 86 plans were accepted at one.
- Lag: the first accepted raise after the day-20 filing comes at the filing's own tick in 20 of 20 seeds at both clocks, a lag of 0 ticks; at four ticks that is tick 3 of the day, not its end.
- Table: docs/results.md, "Seeds 1 to 20 at one tick a day and at four"
- Links: [[DEC-67]], [[RUL-128]], [[RUL-130]], [[RES-01]], [[MOD-31]]

