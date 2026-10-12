# Results

Seeds 1 to 20 in the default mode: the agent run against the fixed-rate run, stay dates 0 to 149. The reasons are the template's, and candidates are scored on contribution with the simulator's elasticity.

| Seed | Contribution change | Revenue change | Rate changes |
| ---: | ---: | ---: | ---: |
| 1 | +27,675 | -34,122 | 9 |
| 2 | +47,954 | -4,633 | 9 |
| 3 | +31,316 | -36,400 | 8 |
| 4 | +37,739 | -24,378 | 11 |
| 5 | +32,307 | -18,433 | 9 |
| 6 | +37,504 | -20,149 | 13 |
| 7 | +28,818 | -35,019 | 7 |
| 8 | +13,479 | -50,384 | 9 |
| 9 | +31,555 | -20,679 | 7 |
| 10 | +40,536 | -32,347 | 9 |
| 11 | +19,302 | -32,022 | 8 |
| 12 | +36,113 | -5,250 | 9 |
| 13 | +52,809 | -834 | 9 |
| 14 | +41,046 | -4,524 | 8 |
| 15 | +32,640 | -27,780 | 11 |
| 16 | +28,446 | -18,357 | 10 |
| 17 | +35,134 | -26,809 | 11 |
| 18 | +23,252 | -23,951 | 6 |
| 19 | +35,510 | -12,117 | 10 |
| 20 | +24,844 | -29,033 | 6 |
| Mean | +32,899 | -22,861 | |

Seed 7, days 0 to 59: what became of the flags.

| Flags | Changed a rate | Held: no change beat hold | Held: worth under the minimum | Declined by the model | Minimum-stay advice |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 113 | 7 | 49 | 57 | 0 | 1 |

Seed 7 over only the 93 hotel and stay-date pairs where the agent changed a rate. The pairs per hotel are in brackets.

| Hotel | Revenue, fixed | Revenue, agent | Change | Contribution, fixed | Contribution, agent | Change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel (3) | 262,460 | 259,921 | -2,539 | 174,973 | 178,888 | +3,915 (+2.2%) |
| Downtown full-service hotel (21) | 908,770 | 898,472 | -10,298 | 605,847 | 612,332 | +6,485 (+1.1%) |
| Lifestyle hotel (17) | 468,000 | 470,472 | +2,472 | 312,000 | 325,112 | +13,112 (+4.2%) |
| Airport hotel (52) | 989,800 | 965,146 | -24,654 | 659,867 | 665,173 | +5,306 (+0.8%) |
| All four hotels | 2,629,030 | 2,594,011 | -35,019 | 1,752,687 | 1,781,505 | +28,818 (+1.6%) |

Seeds 1 to 20 per elasticity arm, each against the same fixed-rate runs. Estimated / realised is the accepted plans' estimated gain over holding, summed over the seeds, over the realised gain. Rejected at an end counts a cautious arm's candidates ahead of hold at the estimate but behind at an end.

| Elasticity | Mean gain per seed | Range | Seeds ahead | Rate changes | Estimated / realised | Rejected at an end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| true (1.5, the simulator's) | +$32,899 | +$13,479 to +$52,809 | 20 of 20 | 179 | 1.04 | |
| fixed:1.0 | +$8,438 | -$13,029 to +$39,143 | 14 of 20 | 515 | 38.7 | |
| fixed:2.0 | +$9,551 | -$6,734 to +$25,474 | 18 of 20 | 486 | 13.0 | |
| learn:1.0 | +$14,141 | -$6,839 to +$45,818 | 16 of 20 | 373 | 18.3 | |
| learn:1.0 --cautious | +$25,076 | +$8,406 to +$53,535 | 20 of 20 | 299 | 7.7 | 3,294 |
| learn:2.0 | +$16,258 | +$2,393 to +$34,480 | 20 of 20 | 418 | 5.2 | |
| learn:2.0 --cautious | +$17,634 | +$5,839 to +$27,585 | 20 of 20 | 240 | 2.5 | 2,681 |

Where each arm's gain came from, summed over the 20 seeds. The first group is the plans the convention (day 10) and the new flights (day 20) raised. The second is every other plan.

| Elasticity | Shock plans | Gain on their stay dates | Other plans | Gain on theirs |
| --- | ---: | ---: | ---: | ---: |
| true | 97 | +$632,532 | 82 | +$25,447 |
| fixed:1.0 | 124 | +$142,871 | 391 | +$25,881 |
| fixed:2.0 | 126 | +$174,985 | 360 | +$16,038 |
| learn:1.0 | 123 | +$259,736 | 250 | +$23,075 |
| learn:1.0 --cautious | 103 | +$487,196 | 196 | +$14,322 |
| learn:2.0 | 127 | +$294,785 | 291 | +$30,370 |
| learn:2.0 --cautious | 72 | +$292,857 | 168 | +$59,831 |

The learning agent's day-59 elasticity estimates against a true value of 1.5. Each figure is the range over the four hotels of each hotel's mean across the 20 seeds.

| Prior | Day-59 estimate, by hotel |
| ---: | --- |
| 1.0 | 1.36 to 1.45 |
| 2.0 | 1.55 to 1.68 |

The cautious rule with and without a $250 minimum per day of the week, seeds 1 to 20. The band alone is the rule that stayed. Its rejection count includes every candidate ahead of hold at the estimate, including those worth less than $250.

| Arm | Band alone: mean gain | Rate changes | Rejected at an end | With a minimum per day of the week: mean gain | Rate changes | Rejected at an end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| learn:1.0 --cautious | +$25,076 | 299 | 3,294 | +$25,084 | 299 | 1,205 |
| learn:2.0 --cautious | +$17,634 | 240 | 2,681 | +$17,618 | 229 | 766 |

Seeds 1 to 20 with the simulator's elasticity and the template, each target against the same fixed-rate runs. The last two columns are in the target's own measure.

| Target | Mean contribution change | Mean revenue change | Seeds ahead on contribution | Rate changes | Accepted plans' estimate | Realised |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| contribution | +$32,899 | -$22,861 | 20 of 20 | 179 | +$681,054 | +$657,979 |
| revenue | +$461 | +$211,445 | 11 of 20 | 659 | +$4,191,156 | +$4,228,903 |

Four live runs of seed 7 in the default mode with claude-opus-5-5, one per request format. Each made seven calls and accepted every plan. Only the last is recorded, under tests/fixtures/live_seed7/. Cost is at list prices of $4 and $20 per million tokens.

| Request format | Input tokens | Cost | Kept |
| --- | ---: | ---: | --- |
| Bare numbers | 20,329 | $0.12 | no |
| A signed display string next to each raw value | 37,107 | $0.18 | no |
| Display strings alone, each range as a named pair | 24,219 | $0.14 | no |
| Display strings alone, each range as one phrase | 21,148 | $0.12 | yes |

The recorded live run of seed 7.

| Measure | Value |
| --- | ---: |
| Model calls | 7, on days 10, 20, 27 and 34 |
| Plans accepted | 7 of 7 |
| Input tokens | 21,148 (1,744 to 3,923 a call) |
| Output tokens | 1,713 (124 to 524 a call) |
| Time in the model | 32 s (2.9 to 7.4 s a call, median 3.5 s) |
| Whole run, both simulations | 37 s |
| Cost at list prices | $0.12 |
| Prompt cache read or written | none |
| Contribution change | +$28,818, the template run's |

Seed 7 with fixed rates: occupancy by hotel over stay dates 0 to 59 and over 140 to 149. The last column is the emptiest of those last ten nights.

| Hotel | Occupancy, stay dates 0 to 59 | Occupancy, stay dates 140 to 149 | Emptiest night, 140 to 149 |
| --- | ---: | ---: | ---: |
| Downtown convention hotel | 75.7% | 83.4% | 70% (stay date 144) |
| Downtown full-service hotel | 76.0% | 84.2% | 73% (stay date 146) |
| Lifestyle hotel | 76.6% | 77.9% | 57% (stay date 147) |
| Airport hotel | 83.7% | 91.2% | 79% (stay date 145) |

Seed 7 under earlier designs, before the current estimate. The last row is the current design. Its 20-seed mean is for the same design over seeds 1 to 20.

| Design | Contribution change, seed 7 | Rate changes | Flags held under the minimum | 20-seed mean |
| --- | ---: | ---: | ---: | ---: |
| Weekday rate factors, one candidate per flag, no minimum, estimate capped at the unsold rooms | +$26,420 | 23 (8 lost money) | | |
| Flat rates, a plan per day of the week, the $250 minimum, estimate capped at the unsold rooms | +$22,894 | 10 | 22 | +$27,350 |
| The same with the exact estimate E[min(N, unsold)] | +$28,818 | 7 | 57 | +$32,899 |

The estimator against known elasticities: seed 7 in learn mode from a prior of 1.5. The simulator's elasticity is set to each true value in turn. Each cell is the day-59 estimate at that hotel, with its standard error in brackets.

| True elasticity | Downtown convention | Downtown full-service | Lifestyle | Airport |
| ---: | ---: | ---: | ---: | ---: |
| 1.0 | 1.25 (0.16) | 0.85 (0.20) | 0.99 (0.21) | 1.28 (0.31) |
| 1.5 | 1.56 (0.17) | 1.64 (0.22) | 1.48 (0.22) | 1.50 (0.30) |
| 2.0 | 1.98 (0.17) | 2.03 (0.21) | 1.64 (0.25) | 1.61 (0.31) |

Spread of the log rate ratio in the estimator's observations by hotel. The run is the fixed-rate run of seed 7 as of day 59.

| Hotel | Standard deviation of log(rate / comp median) | Observations |
| --- | ---: | ---: |
| Downtown convention hotel | 0.025 | 5,307 |
| Downtown full-service hotel | 0.027 | 5,305 |
| Lifestyle hotel | 0.011 | 5,305 |
| Airport hotel | 0.013 | 5,306 |

Timings of the stored tables, measured once during development on the development machine.

| Operation | Time |
| --- | --- |
| One day through `hotel-market run-day` | under a second, most of it the simulator's playback |
| Days 0 to 59 through `hotel-market run-day --from 0` | about 6 seconds |
| Inserting a day's rows one statement at a time (replaced by one frame per day) | 2.5 seconds per 3,000 rows |
| Reading the events table once per detect row (replaced by one read per day) | 2 seconds a day |

The suite on each Python version, run from a fresh virtual environment on 2026-10-12. The environment had numpy 2.5.4, pandas 3.0.6, duckdb 1.5.6 and anthropic 1.13.0.

| Python | Command | Result |
| --- | --- | --- |
| 3.12.6 | `python -m pytest --slow` | 235 passed |
| 3.13.7 | `python -m pytest --slow` | 235 passed |

The container image on each Python version, built on 2026-10-12. Docker 28.4.0 ran on an aarch64 Ubuntu VM with 4 CPUs and 4 GiB. Each image ran the suite from its copy of the repository, and the 3.12 image ran seed 7 with the template. pandas 3.0.6, duckdb 1.5.6 and anthropic 1.13.0 were installed on every version, and every dependency came as a wheel, 3.14 included.

| Python | numpy | Build | Image | Tests | Suite time | Seed-7 run | decisions.jsonl |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| 3.11.15 | 2.4.6 | 24 s | 615 MB | 278 passed, 3 skipped | 45 s | | |
| 3.12.13 | 2.5.4 | 24 s | 592 MB | 278 passed, 3 skipped | 45 s | 1.6 s | matches the native run, sha256 8ce570ea |
| 3.14.8 | 2.5.4 | 24 s | 600 MB | 278 passed, 3 skipped | 45 s | | |

## The benchmark of the reviewers

`hotel-market bench --seeds 1 20`, run on 2026-10-12. For every seed, the command makes the fixed-rate run once. It then makes one agent run per elasticity mode and reviewer. The reviewers are the template, the oracle reviewer, claude-opus-5-5, claude-sonnet-5-5 and claude-haiku-5-5, and each arm has its own cache folder. The live calls were made first, in parallel chunks of seeds. Seeds 1 to 3 ran as one process per model, then seeds 4 to 20 in seven chunks. The command that printed the tables read every folder's cache and made no call. After duplicate records from reruns were dropped, 3,338 calls cost $28.42 at list prices.

In every table, mean change and range are the contribution change against the fixed-rate run. Ahead counts the seeds where the reviewer beat it. Regret is the oracle arm's mean minus the reviewer's. Recovered is the reviewer's gain over the template as a share of the oracle's. Accept, precision, recall, F1 and $ recall are the decline measures against the oracle's labels, pooled over the seeds. Invalid counts calls with a bad attempt. Calls, tokens, median latency and cost come from the arm's call records at list prices.

Seeds 1 to 20 at a fixed elasticity of 1.0, each reviewer against the fixed-rate run.

| Reviewer | Mean change | Range | Ahead | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +8,438 | -13,029 to +39,143 | 14/20 | +22,150 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| oracle | +30,588 | +12,725 to +54,182 | 20/20 | +0 | 1.00 | 0.15 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| claude-opus-5-5 | +14,584 | -6,058 to +42,551 | 17/20 | +16,004 | 0.28 | 0.91 | 1.00 | 0.14 | 0.24 | 0.25 | 0 | 479 | 1,259,730/156,252 | 4.8 | $8.16 |
| claude-sonnet-5-5 | +8,438 | -13,029 to +39,143 | 14/20 | +22,150 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 3 | 484 | 1,279,944/94,336 | 2.5 | $3.50 |
| claude-haiku-5-5 | +8,438 | -13,029 to +39,143 | 14/20 | +22,150 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 484 | 1,268,430/324,033 | 3.9 | $0.29 |

Seeds 1 to 20 at a fixed elasticity of 2.0, each reviewer against the fixed-rate run.

| Reviewer | Mean change | Range | Ahead | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +9,551 | -6,734 to +25,474 | 18/20 | +13,507 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| oracle | +23,058 | +9,869 to +37,962 | 20/20 | +0 | 1.00 | 0.29 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| claude-opus-5-5 | +9,557 | -6,734 to +25,474 | 18/20 | +13,501 | 0.00 | 1.00 | 1.00 | 0.00 | 0.01 | 0.00 | 0 | 457 | 1,257,011/170,296 | 5.6 | $8.43 |
| claude-sonnet-5-5 | +9,551 | -6,734 to +25,474 | 18/20 | +13,507 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 2 | 456 | 1,262,490/95,932 | 2.8 | $3.48 |
| claude-haiku-5-5 | +9,551 | -6,734 to +25,474 | 18/20 | +13,507 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 456 | 1,255,268/323,231 | 4.0 | $0.29 |

Seeds 1 to 20 in the true mode, each reviewer against the fixed-rate run.

| Reviewer | Mean change | Range | Ahead | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +32,899 | +13,479 to +52,809 | 20/20 | +0 | - | 1.00 | - | - | - | - | - | - | - | - | - |
| oracle | +32,899 | +13,479 to +52,809 | 20/20 | +0 | - | 1.00 | - | - | - | - | - | - | - | - | - |
| claude-opus-5-5 | +32,899 | +13,479 to +52,809 | 20/20 | +0 | - | 1.00 | - | - | - | - | 0 | 174 | 477,553/46,137 | 4.3 | $2.83 |
| claude-sonnet-5-5 | +32,899 | +13,479 to +52,809 | 20/20 | +0 | - | 1.00 | - | - | - | - | 1 | 174 | 482,097/34,791 | 2.5 | $1.31 |
| claude-haiku-5-5 | +32,899 | +13,479 to +52,809 | 20/20 | +0 | - | 1.00 | - | - | - | - | 0 | 174 | 477,553/125,061 | 4.2 | $0.11 |

The reviewers ranked across the mismatched modes, fixed:1.0 and fixed:2.0, on seeds 1 to 20.

| Rank | Reviewer | Mean change | Range | Ahead | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | oracle | +26,823 | +9,869 to +54,182 | 40/40 | +0 | 1.00 | 0.20 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| 2 | claude-opus-5-5 | +12,071 | -6,734 to +42,551 | 35/40 | +14,752 | 0.17 | 0.95 | 1.00 | 0.08 | 0.15 | 0.14 | 0 | 936 | 2,516,741/326,548 | 5.2 | $16.60 |
| 3 | template | +8,994 | -13,029 to +39,143 | 32/40 | +17,829 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| 4 | claude-sonnet-5-5 | +8,994 | -13,029 to +39,143 | 32/40 | +17,829 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 5 | 940 | 2,542,434/190,268 | 2.6 | $6.99 |
| 5 | claude-haiku-5-5 | +8,994 | -13,029 to +39,143 | 32/40 | +17,829 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 940 | 2,523,698/647,264 | 4.0 | $0.58 |

Opus declined 47 plans at a fixed elasticity of 1.0, and the oracle agreed with every one. The day-40 raise of 10% on all seven days for stay dates 70 to 90 is 36 of the 47. Every declined plan was a raise. At a fixed elasticity of 2.0, Opus declined one plan, a 5% cut on a date ahead of pace. Sonnet and Haiku declined no plan in any mode. Sonnet answered for one entry when the request held two in seven calls across six of its 1,114 requests. A retry fixed five of them at once. The sixth request failed three tries in one run and answered on the rerun, so the table counts it twice.
