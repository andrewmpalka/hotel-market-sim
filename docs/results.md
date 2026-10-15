# Results

Seeds 1 to 20 in the default mode: the agent run against the fixed-rate run, stay dates 0 to 149. The reasons are the template's, and candidates are scored on contribution with the simulator's elasticity. The last two rows are the standard deviation across the seeds and the standard error of the mean.

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
| SD | 9,185 | 12,777 | |
| SE | 2,054 | 2,857 | |

Seed 7, days 0 to 59: what became of the flags.

| Flags | Changed a rate | Held: no change beat hold | Held: worth under the minimum | Declined by the model | Minimum-stay advice |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 113 | 7 | 49 | 57 | 0 | 1 |

Comp-median flags over seeds 1 to 20 in the default mode, from the same sweep: those on a day a scripted shock moved a median (10, the convention's competitor raise, and 30, the rate cut) and those on every other day, where only the shop noise moved it. Since world v2 the rate shop moves every day, so the 5% threshold meets ordinary noise. Measured on 2026-10-15 with `hotel-market --seeds 1 20 --template`.

| Median flags | On a shock day | On other days |
| ---: | ---: | ---: |
| 523 | 80 | 443 |

Seed 7: room revenue and contribution per hotel, the fixed-rate run against the agent run, stay dates 0 to 149.

| Hotel | Revenue, fixed | Revenue, agent | Change | Contribution, fixed | Contribution, agent | Change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel | 10,370,360 | 10,367,821 | -2,539 | 6,913,573 | 6,917,488 | +3,915 (+0.1%) |
| Downtown full-service hotel | 5,532,800 | 5,522,502 | -10,298 | 3,688,533 | 3,695,019 | +6,485 (+0.2%) |
| Lifestyle hotel | 3,371,280 | 3,373,752 | +2,472 | 2,247,520 | 2,260,632 | +13,112 (+0.6%) |
| Airport hotel | 2,774,800 | 2,750,146 | -24,654 | 1,849,867 | 1,855,173 | +5,306 (+0.3%) |
| All four hotels | 22,049,240 | 22,014,221 | -35,019 | 14,699,493 | 14,728,311 | +28,818 (+0.2%) |

Seed 7 over only the 93 hotel and stay-date pairs where the agent changed a rate. The pairs per hotel are in brackets.

| Hotel | Revenue, fixed | Revenue, agent | Change | Contribution, fixed | Contribution, agent | Change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel (3) | 262,460 | 259,921 | -2,539 | 174,973 | 178,888 | +3,915 (+2.2%) |
| Downtown full-service hotel (21) | 908,770 | 898,472 | -10,298 | 605,847 | 612,332 | +6,485 (+1.1%) |
| Lifestyle hotel (17) | 468,000 | 470,472 | +2,472 | 312,000 | 325,112 | +13,112 (+4.2%) |
| Airport hotel (52) | 989,800 | 965,146 | -24,654 | 659,867 | 665,173 | +5,306 (+0.8%) |
| All four hotels | 2,629,030 | 2,594,011 | -35,019 | 1,752,687 | 1,781,505 | +28,818 (+1.6%) |

Seeds 1 to 20 per elasticity arm, each against the same fixed-rate runs. Estimated / realised is the accepted plans' estimated gain over holding, summed over the seeds, over the realised gain. Rejected at an end counts a cautious arm's candidates ahead of hold at the estimate but behind at an end.

| Elasticity | Mean gain per seed | SD | SE | Range | Seeds ahead | p | Rate changes | Estimated / realised | Rejected at an end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| true (1.5, the simulator's) | +$32,899 | $9,185 | $2,054 | +$13,479 to +$52,809 | 20 of 20 | <0.001 | 179 | 1.04 |  |
| fixed:1.0 | +$8,438 | $13,180 | $2,947 | -$13,029 to +$39,143 | 14 of 20 | 0.12 | 515 | 38.7 |  |
| fixed:2.0 | +$9,551 | $7,736 | $1,730 | -$6,734 to +$25,474 | 18 of 20 | <0.001 | 486 | 13.0 |  |
| learn:1.0 | +$14,141 | $15,084 | $3,373 | -$6,839 to +$45,818 | 16 of 20 | 0.012 | 373 | 18.3 |  |
| learn:1.0 --cautious | +$25,076 | $11,507 | $2,573 | +$8,406 to +$53,535 | 20 of 20 | <0.001 | 299 | 7.7 | 3,294 |
| learn:2.0 | +$16,258 | $8,550 | $1,912 | +$2,393 to +$34,480 | 20 of 20 | <0.001 | 418 | 5.2 |  |
| learn:2.0 --cautious | +$17,634 | $5,712 | $1,277 | +$5,839 to +$27,585 | 20 of 20 | <0.001 | 240 | 2.5 | 2,681 |

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

| Target | Mean contribution change | SD | SE | Mean revenue change | Seeds ahead on contribution | p | Rate changes | Accepted plans' estimate | Realised |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| contribution | +$32,899 | $9,185 | $2,054 | -$22,861 | 20 of 20 | <0.001 | 179 | +$681,054 | +$657,979 |
| revenue | +$461 | $7,861 | $1,758 | +$211,445 | 11 of 20 | 0.82 | 659 | +$4,191,156 | +$4,228,903 |

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

The suite on each Python version. The run of 2026-10-12 came from a fresh virtual environment with the slow tests included and passed 235 tests on both versions. The counts below were refreshed on 2026-10-14 from the plain suite, with numpy 2.5.4, pandas 3.0.6, duckdb 1.5.6 and anthropic 1.13.0 on both. The nine slow tests are skipped, and so are the five demo-page tests wherever the environment has the dev extra alone, which is what `make setup` installs: the fresh-clone row was measured on 2026-10-14 by a reviewer, and the five ran once `make demo` had installed streamlit. `make test-all` on 3.12.6, the nine slow tests included, gave 366 passed on 2026-10-14.

| Python | Command | Result |
| --- | --- | --- |
| 3.12.6 | `python -m pytest` | 357 passed, 9 skipped |
| 3.12.6 | `make setup` then `make test` in a fresh clone, the dev extra alone | 353 passed, 14 skipped |
| 3.13.7 | `python -m pytest` | 352 passed, 14 skipped |

The live answers under cache/ are the only copy of about $86 of model calls, so they are archived as a dated tar outside the repository, with the archive's sha256 and a per-file list beside it. The archive of 2026-10-15 is cache-2026-10-15-0406.tar.gz under ~/backups/hotel-market-sim, 8,203 files with the sha256 ab3b5f7a6f49e81a81716ed9baa626efee668f79be5328ebd5d77addb6c3d9c6, and it restores with `tar -xzf` from the repository root.

The container image on each Python version, built on 2026-10-12. Docker 28.4.0 ran on an aarch64 Ubuntu VM with 4 CPUs and 4 GiB. Each image ran the suite from its copy of the repository, and the 3.12 image ran seed 7 with the template. pandas 3.0.6, duckdb 1.5.6 and anthropic 1.13.0 were installed on every version, and every dependency came as a wheel, 3.14 included. The images were not rebuilt; the native plain suite has since grown to 357 passed and 9 skipped.

| Python | numpy | Build | Image | Tests | Suite time | Seed-7 run | decisions.jsonl |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| 3.11.15 | 2.4.6 | 24 s | 615 MB | 278 passed, 3 skipped | 45 s | | |
| 3.12.13 | 2.5.4 | 24 s | 592 MB | 278 passed, 3 skipped | 45 s | 1.6 s | matched the native run; the native checksum is 19b766b8 since the plan records gained two fields, and was 8ce570ea when the image ran |
| 3.14.8 | 2.5.4 | 24 s | 600 MB | 278 passed, 3 skipped | 45 s | | |

## The benchmark of the reviewers

`hotel-market bench --seeds 1 20`, run on 2026-10-12. For every seed, the command makes the fixed-rate run once. It then makes one agent run per elasticity mode and reviewer. The reviewers are the template, the oracle reviewer, claude-opus-5-5, claude-sonnet-5-5 and claude-haiku-5-5, and each arm has its own cache folder. The live calls were made first, in parallel chunks of seeds. Seeds 1 to 3 ran as one process per model, then seeds 4 to 20 in seven chunks. The command that printed the tables read every folder's cache and made no call. After duplicate records from reruns were dropped, 3,338 calls cost $28.42 at list prices.

In every table, mean change and range are the contribution change against the fixed-rate run, SD is the standard deviation of the per-seed changes, SE is the standard error of their mean, and p is a two-sided sign test on the seeds ahead, which is the chance that a fair coin gives a count at least as far from half. Ahead counts the seeds where the reviewer beat it. Every table was reprinted on 2026-10-15 from the template and the cache with no model call, and a row whose cache no longer matches the request, because it was measured before a later change to the request, keeps its mean and has no SD, SE or p. Regret is the oracle arm's mean minus the reviewer's. Recovered is the reviewer's gain over the template as a share of the oracle's. Accept, precision, recall, F1 and $ recall are the decline measures against the oracle's labels, pooled over the seeds. Invalid counts calls with a bad attempt. Calls, tokens, median latency and cost come from the arm's call records at list prices.

Seeds 1 to 20 at a fixed elasticity of 1.0, each reviewer against the fixed-rate run.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +8,438 | 13,180 | 2,947 | -13,029 to +39,143 | 14/20 | 0.12 | +22,150 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| oracle | +30,588 | 10,172 | 2,274 | +12,725 to +54,182 | 20/20 | <0.001 | +0 | 1.00 | 0.15 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| claude-opus-5-5 | +14,584 | 13,466 | 3,011 | -6,058 to +42,551 | 17/20 | 0.0026 | +16,004 | 0.28 | 0.91 | 1.00 | 0.14 | 0.24 | 0.25 | 0 | 479 | 1,259,730/156,252 | 4.8 | $8.16 |
| claude-sonnet-5-5 | +8,438 | 13,180 | 2,947 | -13,029 to +39,143 | 14/20 | 0.12 | +22,150 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 3 | 484 | 1,279,944/94,336 | 2.5 | $3.50 |
| claude-haiku-5-5 | +8,438 | 13,180 | 2,947 | -13,029 to +39,143 | 14/20 | 0.12 | +22,150 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 484 | 1,268,430/324,033 | 3.9 | $0.29 |

Seeds 1 to 20 at a fixed elasticity of 2.0, each reviewer against the fixed-rate run.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +9,551 | 7,736 | 1,730 | -6,734 to +25,474 | 18/20 | <0.001 | +13,507 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| oracle | +23,058 | 8,032 | 1,796 | +9,869 to +37,962 | 20/20 | <0.001 | +0 | 1.00 | 0.29 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| claude-opus-5-5 | +9,557 | 7,740 | 1,731 | -6,734 to +25,474 | 18/20 | <0.001 | +13,501 | 0.00 | 1.00 | 1.00 | 0.00 | 0.01 | 0.00 | 0 | 457 | 1,257,011/170,296 | 5.6 | $8.43 |
| claude-sonnet-5-5 | +9,551 | 7,736 | 1,730 | -6,734 to +25,474 | 18/20 | <0.001 | +13,507 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 2 | 456 | 1,262,490/95,932 | 2.8 | $3.48 |
| claude-haiku-5-5 | +9,551 | 7,736 | 1,730 | -6,734 to +25,474 | 18/20 | <0.001 | +13,507 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 456 | 1,255,268/323,231 | 4.0 | $0.29 |

Seeds 1 to 20 in the true mode, each reviewer against the fixed-rate run.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +32,899 | 9,185 | 2,054 | +13,479 to +52,809 | 20/20 | <0.001 | +0 | - | 1.00 | - | - | - | - | - | - | - | - | - |
| oracle | +32,899 | 9,185 | 2,054 | +13,479 to +52,809 | 20/20 | <0.001 | +0 | - | 1.00 | - | - | - | - | - | - | - | - | - |
| claude-opus-5-5 | +32,899 | 9,185 | 2,054 | +13,479 to +52,809 | 20/20 | <0.001 | +0 | - | 1.00 | - | - | - | - | 0 | 174 | 477,553/46,137 | 4.3 | $2.83 |
| claude-sonnet-5-5 | +32,899 | 9,185 | 2,054 | +13,479 to +52,809 | 20/20 | <0.001 | +0 | - | 1.00 | - | - | - | - | 1 | 174 | 482,097/34,791 | 2.5 | $1.31 |
| claude-haiku-5-5 | +32,899 | 9,185 | 2,054 | +13,479 to +52,809 | 20/20 | <0.001 | +0 | - | 1.00 | - | - | - | - | 0 | 174 | 477,553/125,061 | 4.2 | $0.11 |

The reviewers ranked across the mismatched modes, fixed:1.0 and fixed:2.0, on seeds 1 to 20.

| Rank | Reviewer | Mean change | SD | SE | Range | Ahead | p | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | oracle | +26,823 | 9,817 | 1,552 | +9,869 to +54,182 | 40/40 | <0.001 | +0 | 1.00 | 0.20 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| 2 | claude-opus-5-5 | +12,071 | 11,136 | 1,761 | -6,734 to +42,551 | 35/40 | <0.001 | +14,752 | 0.17 | 0.95 | 1.00 | 0.08 | 0.15 | 0.14 | 0 | 936 | 2,516,741/326,548 | 5.2 | $16.60 |
| 3 | template | +8,994 | 10,682 | 1,689 | -13,029 to +39,143 | 32/40 | <0.001 | +17,829 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| 4 | claude-sonnet-5-5 | +8,994 | 10,682 | 1,689 | -13,029 to +39,143 | 32/40 | <0.001 | +17,829 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 5 | 940 | 2,542,434/190,268 | 2.6 | $6.99 |
| 5 | claude-haiku-5-5 | +8,994 | 10,682 | 1,689 | -13,029 to +39,143 | 32/40 | <0.001 | +17,829 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 940 | 2,523,698/647,264 | 4.0 | $0.58 |

Opus declined 47 plans at a fixed elasticity of 1.0, and the oracle agreed with every one. The day-40 raise of 10% on all seven days for stay dates 70 to 90 is 36 of the 47. Every declined plan was a raise. At a fixed elasticity of 2.0, Opus declined one plan, a 5% cut on a date ahead of pace. Sonnet and Haiku declined no plan in any mode. Sonnet answered for one entry when the request held two in seven calls across six of its 1,114 requests. A retry fixed five of them at once. The sixth request failed three tries in one run and answered on the rerun, so the table counts it twice.

## The demand bias

`hotel-market bench --seeds 1 20 --template --demand-bias F --elasticity true --elasticity fixed:1.0 --elasticity learn:1.0`, and the same command with `--elasticity learn:1.0 --cautious`, run on 2026-10-12 at F = 0.9, 1.1 and 1.0. The option multiplies the simulator's demand by F, the day-0 preload included. The agent never sees F, so its forecast is wrong by that factor in every mode. The oracle reviewer, which is told F, stays the simulator's truth. Each arm is measured against the fixed-rate run at the same bias.

In every table, mean change and range are the contribution change per seed against the fixed-rate run, and ahead counts the seeds where the arm beat it. Flags counts the flags the arm raised over the 20 seeds, and pace flags those with a pace cause. Rate changes counts the plans that changed a rate, and accept is the share of queued plans the reviewer accepted. The day-59 estimate is the learning agent's elasticity on day 59, as the range over the four hotels of each hotel's mean across the seeds. The true value is 1.5.

Seeds 1 to 20 at a demand bias of 0.9, the template and the oracle in four modes, each against the fixed-rate run at the same bias.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Accept | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| true | template | +1,913 | 3,782 | 846 | -4,369 to +8,664 | 12/20 | 0.50 | 3170 | 2937 | 98 | 1.00 | - |
| true | oracle | +2,334 | 3,819 | 854 | -2,600 to +8,664 | 13/20 | 0.26 | 3147 | 2914 | 90 | 0.90 | - |
| fixed:1.0 | template | -25,179 | 9,567 | 2,139 | -38,823 to -8,387 | 0/20 | <0.001 | 2541 | 2297 | 886 | 1.00 | - |
| fixed:1.0 | oracle | +2,546 | 3,587 | 802 | -4,343 to +10,199 | 17/20 | 0.0026 | 2757 | 2525 | 66 | 0.04 | - |
| learn:1.0 | template | -14,376 | 8,869 | 1,983 | -36,881 to -237 | 0/20 | <0.001 | 3230 | 2986 | 484 | 1.00 | 1.36 to 1.46 |
| learn:1.0 | oracle | +2,654 | 3,611 | 808 | -4,343 to +10,199 | 17/20 | 0.0026 | 2758 | 2526 | 69 | 0.05 | 1.05 to 1.24 |
| learn:1.0 --cautious | template | -4,280 | 7,477 | 1,672 | -19,310 to +9,584 | 6/20 | 0.12 | 3152 | 2914 | 284 | 1.00 | 1.26 to 1.48 |
| learn:1.0 --cautious | oracle | +2,748 | 4,318 | 965 | -4,541 to +10,419 | 14/20 | 0.12 | 2952 | 2720 | 82 | 0.10 | 1.10 to 1.31 |

Seeds 1 to 20 at a demand bias of 1.1, the same arms.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Accept | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| true | template | +112,082 | 16,449 | 3,678 | +76,253 to +159,750 | 20/20 | <0.001 | 8526 | 8257 | 464 | 1.00 | - |
| true | oracle | +112,082 | 16,449 | 3,678 | +76,253 to +159,750 | 20/20 | <0.001 | 8526 | 8257 | 464 | 1.00 | - |
| fixed:1.0 | template | +93,008 | 20,176 | 4,511 | +49,906 to +145,523 | 20/20 | <0.001 | 2000 | 1754 | 1184 | 1.00 | - |
| fixed:1.0 | oracle | +107,529 | 19,349 | 4,327 | +67,163 to +158,039 | 20/20 | <0.001 | 4177 | 3926 | 623 | 0.20 | - |
| learn:1.0 | template | +98,401 | 19,561 | 4,374 | +62,387 to +150,804 | 20/20 | <0.001 | 3446 | 3197 | 898 | 1.00 | 1.39 to 1.49 |
| learn:1.0 | oracle | +107,393 | 20,124 | 4,500 | +67,292 to +165,267 | 20/20 | <0.001 | 4620 | 4367 | 604 | 0.32 | 1.37 to 1.46 |
| learn:1.0 --cautious | template | +105,522 | 18,532 | 4,144 | +68,692 to +154,130 | 20/20 | <0.001 | 5750 | 5486 | 839 | 1.00 | 1.29 to 1.46 |
| learn:1.0 --cautious | oracle | +107,714 | 19,642 | 4,392 | +70,497 to +157,310 | 20/20 | <0.001 | 6294 | 6031 | 662 | 0.48 | 1.29 to 1.44 |

Seeds 1 to 20 at the default demand bias of 1.0, the same arms, as the reference. The template rows repeat the earlier tables, and the oracle's learn arms are new.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Accept | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| true | template | +32,899 | 9,185 | 2,054 | +13,479 to +52,809 | 20/20 | <0.001 | 1952 | 1726 | 179 | 1.00 | - |
| true | oracle | +32,899 | 9,185 | 2,054 | +13,479 to +52,809 | 20/20 | <0.001 | 1952 | 1726 | 179 | 1.00 | - |
| fixed:1.0 | template | +8,438 | 13,180 | 2,947 | -13,029 to +39,143 | 14/20 | 0.12 | 789 | 566 | 515 | 1.00 | - |
| fixed:1.0 | oracle | +30,588 | 10,172 | 2,274 | +12,725 to +54,182 | 20/20 | <0.001 | 1559 | 1336 | 186 | 0.15 | - |
| learn:1.0 | template | +14,141 | 15,084 | 3,373 | -6,839 to +45,818 | 16/20 | 0.012 | 1082 | 859 | 373 | 1.00 | 1.36 to 1.45 |
| learn:1.0 | oracle | +30,828 | 10,016 | 2,240 | +13,813 to +54,182 | 20/20 | <0.001 | 1584 | 1361 | 188 | 0.21 | 1.22 to 1.38 |
| learn:1.0 --cautious | template | +25,076 | 11,507 | 2,573 | +8,406 to +53,535 | 20/20 | <0.001 | 1515 | 1290 | 299 | 1.00 | 1.28 to 1.43 |
| learn:1.0 --cautious | oracle | +31,042 | 9,575 | 2,141 | +12,679 to +55,153 | 20/20 | <0.001 | 1799 | 1575 | 201 | 0.34 | 1.25 to 1.35 |

At 0.9 the agent expects 11% more demand than arrives, so every raise sells fewer rooms than its estimate says. The default mode's gain falls from +$32,899 to +$1,913 a seed, and accepting every plan at a wrong elasticity now loses money. In the mismatched modes the oracle holds 90% or more of the plans. At 1.1 every arm gains, because the start rates were set for a smaller market and the dates run ahead of pace. The learning agent's day-59 estimates move by 0.05 or less from the 1.0 values, so the demand-level error landed in the estimator's intercept, as estimate.py intends. The oracle's learn arms at 0.9 end at 1.05 to 1.31, because the oracle held most plans and the rates barely moved.

## The competitor reaction

`hotel-market bench --seeds 1 20 --template --react --elasticity true` and the same command with `--elasticity learn:1.0 --cautious`, run on 2026-10-12. With `--react`, each competitor moves half of a hotel's change from its start rate three days after the change takes effect. The shop on a day reads the hotel's rate in force three days earlier from the Books' own log, so nothing is used before it is known. The reaction leaves the fixed-rate run as it is, because that run never changes a rate. The columns are those of the demand-bias tables. Median flags counts the flags with a comp-median cause, own changes those among them that the hotels' own changes caused, and changed twice the stay dates changed twice or more within 14 days.

Seeds 1 to 20 with the reaction on, the template and the oracle in the true mode and the cautious learning mode, each against the fixed-rate run. The oracle's cautious row is the first run's, before the oracle was told the reaction, so it has no spread.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Median flags | Own changes | Changed twice | Accept | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| true | template | +111,272 | 15,119 | 3,381 | +89,756 to +147,250 | 20/20 | <0.001 | 2498 | 1811 | 298 | 541 | 481 | 97 | 1.00 | - |
| true | oracle | +111,272 | 15,119 | 3,381 | +89,756 to +147,250 | 20/20 | <0.001 | 2498 | 1811 | 298 | 541 | 481 | 97 | 1.00 | - |
| learn:1.0 --cautious | template | +298,869 | 112,831 | 25,230 | +124,847 to +528,068 | 20/20 | <0.001 | 2913 | 1417 | 890 | 1363 | 1303 | 734 | 1.00 | 1.23 to 1.41 |
| learn:1.0 --cautious | oracle | +129,090 | - | - | +83,945 to +169,143 | 20/20 | - | 2429 | 1617 | 417 | 670 | 610 | 219 | 0.45 | 1.18 to 1.34 |

Seed 7 with the reaction on: the convention hotel's rate in force and its comp median on the convention nights, stay dates 45 to 48, by shop day. The competitors raise 15% on day 10, when the convention is announced. The agent's day-10 plan takes effect on day 11, and the competitors move half of it on day 14.

| Shop day | Stay 45 rate | Median | Stay 46 rate | Median | Stay 47 rate | Median | Stay 48 rate | Median |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 220.00 | 224.14 | 220.00 | 222.41 | 220.00 | 215.60 | 220.00 | 214.17 |
| 10 | 220.00 | 257.76 | 220.00 | 255.77 | 220.00 | 247.94 | 220.00 | 246.30 |
| 11 | 242.00 | 257.76 | 231.00 | 255.77 | 242.00 | 247.94 | 220.00 | 246.30 |
| 12 | 242.00 | 257.76 | 231.00 | 255.77 | 242.00 | 247.94 | 220.00 | 246.30 |
| 13 | 242.00 | 257.76 | 231.00 | 255.77 | 242.00 | 247.94 | 220.00 | 246.30 |
| 14 | 242.00 | 268.76 | 231.00 | 261.27 | 242.00 | 258.94 | 220.00 | 246.30 |
| 15 | 242.00 | 268.76 | 231.00 | 261.27 | 242.00 | 258.94 | 220.00 | 246.30 |

With the reaction on, the default mode earns 3.4 times its gain without it, +$111,272 against +$32,899 a seed, and changes 298 rates against 179. The simulator's bookings follow the hotel's rate against the comp median and never the level the two reach together, so a raise the competitors half follow costs the hotel few rooms. The moved median then raises a new flag on the same dates, the hold lifts for it, and the agent raises again. In the true mode 481 of the 541 comp-median flags follow the hotels' own changes, and 97 stay dates change twice within 14 days. The cautious learning arm starts from an elasticity of 1.0, so it expects a raise to cost less than it does. It changes 890 rates, 734 of them twice within 14 days, and earns +$298,869 a seed. The oracle scores every plan without the reaction, so it holds 55% of that arm's plans and earns $169,780 a seed less than accepting all. With the reaction on it is no longer the ceiling.

## The market-level price response

`hotel-market bench --seeds 1 20 --template --react --market-elasticity E --elasticity true` and the same command with `--elasticity learn:1.0 --cautious`, run on 2026-10-12 at E = 0.0, 0.5 and 1.0. The option multiplies expected demand by the comp median as shopped that day over its starting level for that stay date, to the power of minus E. The starting level is the median with no shock and no reaction. The agent is told E and every plan record carries it. The oracle re-scores each plan with E and with the share of a change the competitors follow, so it is the ceiling again over the agent's own candidates, with the reaction scored as immediate where the simulator applies it three days later. The columns are those of the reaction table, and oracle gap is the oracle arm's mean change minus accept-all's.

Seeds 1 to 20 with the reaction on at a market elasticity of 0.0, 0.5 and 1.0, the template and the oracle in the true mode and the cautious learning mode, each against the fixed-rate run. The cautious rows at 0.5 and 1.0 come from a rerun after the estimator's baseline gained the market term.

| Market elasticity | Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Median flags | Own changes | Changed twice | Oracle gap | Day-59 estimate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | true | template | +111,272 | 15,119 | 3,381 | +89,756 to +147,250 | 20/20 | <0.001 | 298 | 541 | 481 | 97 | +0 | - |
| 0.0 | true | oracle | +111,272 | 15,119 | 3,381 | +89,756 to +147,250 | 20/20 | <0.001 | 298 | 541 | 481 | 97 | - | - |
| 0.0 | learn:1.0 --cautious | template | +298,869 | 112,831 | 25,230 | +124,847 to +528,068 | 20/20 | <0.001 | 890 | 1363 | 1303 | 734 | +676 | 1.23 to 1.41 |
| 0.0 | learn:1.0 --cautious | oracle | +299,545 | 113,249 | 25,323 | +124,847 to +528,068 | 20/20 | <0.001 | 888 | 1363 | 1303 | 734 | - | 1.23 to 1.42 |
| 0.5 | true | template | +72,229 | 11,715 | 2,619 | +51,792 to +92,918 | 20/20 | <0.001 | 207 | 505 | 445 | 46 | +0 | - |
| 0.5 | true | oracle | +72,229 | 11,715 | 2,619 | +51,792 to +92,918 | 20/20 | <0.001 | 207 | 505 | 445 | 46 | - | - |
| 0.5 | learn:1.0 --cautious | template | +198,089 | 80,371 | 17,972 | +77,536 to +336,986 | 20/20 | <0.001 | 784 | 1378 | 1318 | 702 | +400 | 1.22 to 1.42 |
| 0.5 | learn:1.0 --cautious | oracle | +198,488 | 80,600 | 18,023 | +77,536 to +336,986 | 20/20 | <0.001 | 780 | 1378 | 1318 | 702 | - | 1.22 to 1.42 |
| 1.0 | true | template | +43,584 | 9,030 | 2,019 | +29,018 to +58,908 | 20/20 | <0.001 | 161 | 489 | 429 | 25 | +0 | - |
| 1.0 | true | oracle | +43,584 | 9,030 | 2,019 | +29,018 to +58,908 | 20/20 | <0.001 | 161 | 489 | 429 | 25 | - | - |
| 1.0 | learn:1.0 --cautious | template | +99,883 | 32,523 | 7,272 | +43,857 to +153,820 | 20/20 | <0.001 | 696 | 1332 | 1272 | 646 | +709 | 1.23 to 1.42 |
| 1.0 | learn:1.0 --cautious | oracle | +100,592 | 32,217 | 7,204 | +43,857 to +153,820 | 20/20 | <0.001 | 692 | 1332 | 1272 | 646 | - | 1.23 to 1.41 |

Seed 7 at a market elasticity of 0.0 and 0.5 with no reaction: the full-service hotel's rate, its comp median before and after the day-30 cut, and the rooms it sold on the cut's stay dates, 37 to 39, by day 39.

| Market elasticity | Stay date | Rate | Median before the cut | Median after | Rooms sold by day 39 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 | 37 | 190.00 | 188.51 | 170.10 | 182 |
| 0.0 | 38 | 190.00 | 191.80 | 173.46 | 202 |
| 0.0 | 39 | 190.00 | 185.57 | 167.51 | 161 |
| 0.5 | 37 | 190.00 | 188.51 | 170.10 | 183 |
| 0.5 | 38 | 190.00 | 191.80 | 173.46 | 206 |
| 0.5 | 39 | 190.00 | 185.57 | 167.51 | 165 |

By default the market has no price response of its own, so a raise that every hotel matches costs no rooms. The market table shows two different things. The first is a price effect that is correct: competitors that follow half of a raise lower the hotel's effective own-price elasticity below 1.5, because its rate against the median moves only half as far as its rate. A raise therefore pays more in that world than it does against competitors that never move, and the gain that remains at a market elasticity of 1.0, +$43,584 a seed against +$32,899 with no reaction, is the agent's correct response to it. The true-mode agent prices with 1.5, the elasticity of a hotel whose competitors never move, so under the reaction it is too timid. The learner's lower estimate raises more, and the oracle, told the reaction, confirms it is right to. The simulator's elasticity is therefore the right decision parameter only when the comp set stands still, and a reacting market needs the effective one. The second is a fault: the competitors' answer to the hotel's own change arrives three days later, the detector reads it as news, the hold lifts, and the agent raises again on the same dates. Its measure is the stay dates changed twice within 14 days, which the market term cut from 97 to 25 and did not remove. FRK-09 is the open question for the rest, whether a comp move that follows our own change should count as a flag cause at all. The oracle, told the reaction, accepts almost every plan at 0.0 and beats accept-all by $400 to $709 a seed in the cautious arm. That arm's day-59 estimates stay at 1.22 to 1.42 by hotel at every value, because the estimator's baseline carries the market term. In the first run of this table it did not, and the estimates drifted to 1.45 to 1.70 at 1.0, because the market's answer to a moved median read as price response. On the day-30 cut the cheaper market draws more demand at 0.5, so the full-service hotel sells one to four more rooms on each of the three stay dates than at 0.0.

## The air schedule's filings

`hotel-market --seeds 1 20 --churn` and `hotel-market --seeds 1 20`, run on 2026-10-12, then `hotel-market --seeds 1 20 --scenario upgauge`. With `--churn` the airline files weekly revisions drawn from the seed on days 7 to 56: an equipment swap of two to three weeks between codes within 24 seats a flight of each other, and a departure-time change for a fortnight. A day then moves at most 96 seats against a threshold of 212. The scenario option replaces the default's two filings with another list. The upgauge scenario files an upgauge of the MSP route to 738s on day 15 and a cut of the ORD route to two daily flights on day 35. Filings counts the days the airline filed something through day 59, summed over the seeds, and seat flags the flags with a seat cause.

Seeds 1 to 20 with the churn, the default and the upgauge scenario, the template in the true mode, each against the fixed-rate run.

| Arm | Mean change | SD | SE | Range | Ahead | p | Filings | Seat flags | Rate changes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| default | +32,899 | 9,185 | 2,054 | +13,479 to +52,809 | 20/20 | <0.001 | 40 | 173 | 179 |
| default with the churn | +34,974 | 9,535 | 2,132 | +15,179 to +53,131 | 20/20 | <0.001 | 200 | 173 | 184 |
| upgauge | +21,083 | 8,994 | 2,011 | +4,178 to +36,862 | 20/20 | <0.001 | 40 | 182 | 177 |

The churn adds 160 filing days over the 20 seeds and raises no seat flag. That is by construction, because every revision stays under the threshold, so the absence of seat flags proves nothing. The finding is that a filing as such never reaches the detector, which keys on the day-over-day seat revision. The test test_a_detector_that_fires_on_any_revision_is_caught_by_the_churn pins it by holding the seat flags to the same two days with the churn as without. The block swaps move seats for two to three weeks at a time, so the gain moves by $2,075 a seed and the agent makes five more rate changes with no extra seat flag. The churn therefore reached the agent's decisions through the seat change in its demand forecast, and none of it came through the detector. That is the designed path, because DEC-04 keeps the seat change for the forecast and the revision for the flag, and this is the first run where the two paths visibly part. The upgauge scenario earns less than the default, because its two filings move fewer seats than the default's new flights and suspension.

## The intercept fed back

`hotel-market bench --seeds 1 20 --template --demand-bias B --elasticity learn:1.0 --level` and the same command with `--level --cautious`, at B = 0.9, 1.0 and 1.1, run on 2026-10-12, then the same two arms and a plain `learn:1.0` with `--react --market-elasticity 0.5`. With `--level` a learning agent scales its demand forecast, the pace baseline included, by the demand level its fit found, which is exp(intercept), once the fit has 500 observations and clamped to 0.5 to 2.0 as the elasticity is clamped. The plain learn rows repeat the demand-bias tables and the market table. Day-59 level is the factor each hotel scaled its forecast by on day 59, as the range over the hotels of each hotel's mean across the seeds.

Seeds 1 to 20 at a demand bias of 0.9, the learning agent with and without the fitted level fed back, the template and the oracle, each against the fixed-rate run at the same bias.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Accept | Day-59 estimate | Day-59 level |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| learn:1.0 | template | -14,376 | 8,869 | 1,983 | -36,881 to -237 | 0/20 | <0.001 | 484 | 1.00 | 1.36 to 1.46 | - |
| learn:1.0 | oracle | +2,654 | 3,611 | 808 | -4,343 to +10,199 | 17/20 | 0.0026 | 69 | 0.05 | 1.05 to 1.24 | - |
| learn:1.0 --cautious | template | -4,280 | 7,477 | 1,672 | -19,310 to +9,584 | 6/20 | 0.12 | 284 | 1.00 | 1.26 to 1.48 | - |
| learn:1.0 --cautious | oracle | +2,748 | 4,318 | 965 | -4,541 to +10,419 | 14/20 | 0.12 | 82 | 0.10 | 1.10 to 1.31 | - |
| learn:1.0 --level | template | -15,244 | 8,248 | 1,844 | -35,251 to +146 | 1/20 | <0.001 | 373 | 1.00 | 1.36 to 1.45 | 0.89 to 0.90 |
| learn:1.0 --level | oracle | +3,087 | 2,571 | 575 | -292 to +8,637 | 19/20 | <0.001 | 83 | 0.06 | 1.08 to 1.39 | 0.90 to 0.90 |
| learn:1.0 --level --cautious | template | -3,348 | 6,186 | 1,383 | -14,362 to +12,177 | 5/20 | 0.041 | 252 | 1.00 | 1.27 to 1.44 | 0.90 to 0.90 |
| learn:1.0 --level --cautious | oracle | +3,512 | 2,857 | 639 | +130 to +10,391 | 20/20 | <0.001 | 87 | 0.12 | 1.08 to 1.40 | 0.90 to 0.90 |

Seeds 1 to 20 at the default demand bias of 1.0, the same arms.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Accept | Day-59 estimate | Day-59 level |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| learn:1.0 | template | +14,141 | 15,084 | 3,373 | -6,839 to +45,818 | 16/20 | 0.012 | 373 | 1.00 | 1.36 to 1.45 | - |
| learn:1.0 | oracle | +30,828 | 10,016 | 2,240 | +13,813 to +54,182 | 20/20 | <0.001 | 188 | 0.21 | 1.22 to 1.38 | - |
| learn:1.0 --cautious | template | +25,076 | 11,507 | 2,573 | +8,406 to +53,535 | 20/20 | <0.001 | 299 | 1.00 | 1.28 to 1.43 | - |
| learn:1.0 --cautious | oracle | +31,042 | 9,575 | 2,141 | +12,679 to +55,153 | 20/20 | <0.001 | 201 | 0.34 | 1.25 to 1.35 | - |
| learn:1.0 --level | template | +14,097 | 15,157 | 3,389 | -6,962 to +48,409 | 15/20 | 0.041 | 378 | 1.00 | 1.36 to 1.45 | 0.99 to 1.00 |
| learn:1.0 --level | oracle | +30,729 | 9,701 | 2,169 | +13,711 to +53,916 | 20/20 | <0.001 | 190 | 0.21 | 1.22 to 1.38 | 0.99 to 1.00 |
| learn:1.0 --level --cautious | template | +24,317 | 12,082 | 2,702 | +3,408 to +54,167 | 20/20 | <0.001 | 306 | 1.00 | 1.28 to 1.43 | 0.99 to 1.00 |
| learn:1.0 --level --cautious | oracle | +31,026 | 9,530 | 2,131 | +13,045 to +55,478 | 20/20 | <0.001 | 205 | 0.35 | 1.25 to 1.36 | 0.99 to 1.00 |

Seeds 1 to 20 at a demand bias of 1.1, the same arms.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Accept | Day-59 estimate | Day-59 level |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| learn:1.0 | template | +98,401 | 19,561 | 4,374 | +62,387 to +150,804 | 20/20 | <0.001 | 898 | 1.00 | 1.39 to 1.49 | - |
| learn:1.0 | oracle | +107,393 | 20,124 | 4,500 | +67,292 to +165,267 | 20/20 | <0.001 | 604 | 0.32 | 1.37 to 1.46 | - |
| learn:1.0 --cautious | template | +105,522 | 18,532 | 4,144 | +68,692 to +154,130 | 20/20 | <0.001 | 839 | 1.00 | 1.29 to 1.46 | - |
| learn:1.0 --cautious | oracle | +107,714 | 19,642 | 4,392 | +70,497 to +157,310 | 20/20 | <0.001 | 662 | 0.48 | 1.29 to 1.44 | - |
| learn:1.0 --level | template | +95,731 | 21,610 | 4,832 | +57,267 to +154,634 | 20/20 | <0.001 | 553 | 1.00 | 1.38 to 1.49 | 1.09 to 1.10 |
| learn:1.0 --level | oracle | +99,916 | 20,014 | 4,475 | +60,448 to +151,233 | 20/20 | <0.001 | 411 | 0.51 | 1.37 to 1.47 | 1.09 to 1.10 |
| learn:1.0 --level --cautious | template | +103,121 | 18,090 | 4,045 | +66,053 to +142,889 | 20/20 | <0.001 | 458 | 1.00 | 1.31 to 1.43 | 1.09 to 1.10 |
| learn:1.0 --level --cautious | oracle | +104,079 | 17,760 | 3,971 | +66,871 to +142,889 | 20/20 | <0.001 | 406 | 0.77 | 1.31 to 1.43 | 1.09 to 1.10 |

Seeds 1 to 20 with the reaction on at a market elasticity of 0.5, the same arms.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Accept | Day-59 estimate | Day-59 level |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| learn:1.0 | template | +399,538 | 78,373 | 17,525 | +269,949 to +551,229 | 20/20 | <0.001 | 2257 | 1.00 | 1.37 to 1.47 | - |
| learn:1.0 | oracle | +421,571 | 65,139 | 14,566 | +288,947 to +551,229 | 20/20 | <0.001 | 2104 | 0.91 | 1.37 to 1.48 | - |
| learn:1.0 --cautious | template | +198,089 | 80,371 | 17,972 | +77,536 to +336,986 | 20/20 | <0.001 | 784 | 1.00 | 1.22 to 1.42 | - |
| learn:1.0 --cautious | oracle | +198,488 | 80,600 | 18,023 | +77,536 to +336,986 | 20/20 | <0.001 | 780 | 0.99 | 1.22 to 1.42 | - |
| learn:1.0 --level | template | +399,596 | 78,815 | 17,624 | +284,402 to +551,028 | 20/20 | <0.001 | 2265 | 1.00 | 1.37 to 1.47 | 0.99 to 1.00 |
| learn:1.0 --level | oracle | +421,471 | 66,257 | 14,815 | +290,560 to +551,028 | 20/20 | <0.001 | 2115 | 0.91 | 1.37 to 1.49 | 0.99 to 1.00 |
| learn:1.0 --level --cautious | template | +202,454 | 81,776 | 18,286 | +77,767 to +337,631 | 20/20 | <0.001 | 771 | 1.00 | 1.23 to 1.43 | 0.99 to 1.00 |
| learn:1.0 --level --cautious | oracle | +202,853 | 81,971 | 18,329 | +77,767 to +337,631 | 20/20 | <0.001 | 767 | 0.99 | 1.23 to 1.43 | 0.99 to 1.00 |

The level is learned at once and exactly. By day 10 the factor is 0.90 at a bias of 0.9, 1.10 at 1.1 and 1.00 in the reacting market, and it stays there. It halves the flags at 0.9, from 3,230 to 1,537 over the 20 seeds, because the pace baseline no longer expects rooms that never come. The gain at 0.9 does not recover, because the opportunity shrank. Accepting every plan earns -$15,244 a seed with the level against -$14,376 without it, and the cautious arm -$3,348 against -$4,280. The true-mode agent earns +$1,913 there and the oracle's ceiling on the learner's plans is about +$3,000, since the gain in this simulator comes from scarcity on the shock dates, and a market a tenth smaller has fewer nights that sell out. The level halved the false pace flags, which is what it could do, and it could not make rooms scarce. At 1.0 the level is 0.99 to 1.00, and the arms lose $44 and $759 a seed to its noise. At 1.1 they lose $2,670 and $2,401, and that loss shows a design limit rather than a fault in the level. The uncorrected agent raised on pace flags that were false, and the raises paid because the market was larger than the start rates assume. Once the level removed the false flags, the correct raises went with them, because the agent acts only on a flag, and a market that is simply larger raises none. FRK-11 holds the periodic re-plan that would close that gap. With the reaction on at 0.5 the level is 1.00 and changes little: $58 and $4,365 a seed. The plain learner in that market changes 2,257 rates and earns +$399,538 a seed, the ratchet at its fullest, which FRK-09 holds.

## The rule-based control

`hotel-market bench --seeds 1 20 --template --policy P --demand-bias B --elasticity true` at B = 0.9, 1.0 and 1.1, and the same command with `--react --market-elasticity 0.5` in place of the bias, for P = pace and P = rules, run on 2026-10-12, and for P = never-cut, run on 2026-10-14. The pace policy raises 5% on every stay date that runs ahead of pace by the detect threshold and lowers 5% on every one behind it, with the same hold, floor and ceiling as the agent, and no estimate and no model. The rules policy keeps those steps and adds the rules the agent's first design retired: it raises 5% on an event flag's dates and on a seat-up flag's dates, and lowers 5% on a seat-cut flag's dates. The never-cut policy keeps the rules policy's raises and never lowers, because in this market the start rate is already the best rate on a night that will not sell out, so every cut the rules policy makes loses money. Each policy runs beside each arm on the same seed, and the table gives each arm's gain against frozen rates next to its gain against the policy. Ahead counts the seeds where the arm beat the policy, and changes the stay dates the policy changed over the 20 seeds.

Seeds 1 to 20 in the true mode against the pace, the rules and the never-cut policies, under each demand bias and in the reacting market, the template and the oracle, each against the fixed-rate run and against the policy.

| Policy | World | Reviewer | Against frozen rates | Against the policy | SD | SE | Ahead of it | p | The policy against frozen rates | SD | SE | Policy changes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pace | bias 0.9 | template | +1,913 | -101 | 3,269 | 731 | 7/20 | 0.26 | +2,015 | 2,081 | 465 | 694 |
| pace | bias 0.9 | oracle | +2,334 | +319 | 3,280 | 733 | 8/20 | 0.50 | +2,015 | 2,081 | 465 | 694 |
| pace | bias 1.0 | template | +32,899 | +21,437 | 7,870 | 1,760 | 20/20 | <0.001 | +11,462 | 4,257 | 952 | 653 |
| pace | bias 1.0 | oracle | +32,899 | +21,437 | 7,870 | 1,760 | 20/20 | <0.001 | +11,462 | 4,257 | 952 | 653 |
| pace | bias 1.1 | template | +112,082 | +67,466 | 10,435 | 2,333 | 20/20 | <0.001 | +44,616 | 10,700 | 2,393 | 2505 |
| pace | bias 1.1 | oracle | +112,082 | +67,466 | 10,435 | 2,333 | 20/20 | <0.001 | +44,616 | 10,700 | 2,393 | 2505 |
| pace | react, market 0.5 | template | +72,229 | +59,986 | 10,969 | 2,453 | 20/20 | <0.001 | +12,243 | 3,664 | 819 | 597 |
| pace | react, market 0.5 | oracle | +72,229 | +59,986 | 10,969 | 2,453 | 20/20 | <0.001 | +12,243 | 3,664 | 819 | 597 |
| rules | bias 0.9 | template | +1,913 | +1,256 | 5,041 | 1,127 | 13/20 | 0.26 | +657 | 6,267 | 1,401 | 7277 |
| rules | bias 0.9 | oracle | +2,334 | +1,677 | 5,145 | 1,151 | 13/20 | 0.26 | +657 | 6,267 | 1,401 | 7277 |
| rules | bias 1.0 | template | +32,899 | +10,043 | 6,688 | 1,495 | 17/20 | 0.0026 | +22,856 | 6,784 | 1,517 | 7123 |
| rules | bias 1.0 | oracle | +32,899 | +10,043 | 6,688 | 1,495 | 17/20 | 0.0026 | +22,856 | 6,784 | 1,517 | 7123 |
| rules | bias 1.1 | template | +112,082 | +32,214 | 7,966 | 1,781 | 20/20 | <0.001 | +79,869 | 15,375 | 3,438 | 8385 |
| rules | bias 1.1 | oracle | +112,082 | +32,214 | 7,966 | 1,781 | 20/20 | <0.001 | +79,869 | 15,375 | 3,438 | 8385 |
| rules | react, market 0.5 | template | +72,229 | -32,914 | 10,856 | 2,428 | 0/20 | <0.001 | +105,144 | 5,877 | 1,314 | 7091 |
| rules | react, market 0.5 | oracle | +72,229 | -32,914 | 10,856 | 2,428 | 0/20 | <0.001 | +105,144 | 5,877 | 1,314 | 7091 |
| never-cut | bias 0.9 | template | +1,913 | +2,374 | 5,855 | 1,309 | 14/20 | 0.12 | -461 | 7,238 | 1,618 | 5107 |
| never-cut | bias 0.9 | oracle | +2,334 | +2,795 | 5,795 | 1,296 | 14/20 | 0.12 | -461 | 7,238 | 1,618 | 5107 |
| never-cut | bias 1.0 | template | +32,899 | +8,119 | 6,620 | 1,480 | 17/20 | 0.0026 | +24,780 | 8,345 | 1,866 | 5416 |
| never-cut | bias 1.0 | oracle | +32,899 | +8,119 | 6,620 | 1,480 | 17/20 | 0.0026 | +24,780 | 8,345 | 1,866 | 5416 |
| never-cut | bias 1.1 | template | +112,082 | +26,148 | 7,838 | 1,753 | 20/20 | <0.001 | +85,934 | 17,014 | 3,804 | 6704 |
| never-cut | bias 1.1 | oracle | +112,082 | +26,148 | 7,838 | 1,753 | 20/20 | <0.001 | +85,934 | 17,014 | 3,804 | 6704 |
| never-cut | react, market 0.5 | template | +72,229 | -68,820 | 10,862 | 2,429 | 0/20 | <0.001 | +141,050 | 6,911 | 1,545 | 5387 |
| never-cut | react, market 0.5 | oracle | +72,229 | -68,820 | 10,862 | 2,429 | 0/20 | <0.001 | +141,050 | 6,911 | 1,545 | 5387 |

A fixed-rate run is a control that never moves, so every gain against it includes what a hotel's own rules would have earned anyway. A policy that acts on the same flags is the fairer yardstick, and the never-cut policy is the one the README quotes first, with the rules policy after it, because the pace policy skips every flag that is not a pace flag. It cannot act on the convention or the new flights when they become known, and those two shocks carry 96% of the default gain, so against it the agent was beaten on the part of the problem the control was never given. In the default world the rules policy earns +$22,856 a seed from 7,123 stay dates changed, and the agent's +$32,899 against frozen rates is +$10,043 against it, ahead in 17 of 20. The pace policy earns +$11,462 there, from the pace flags alone. At a bias of 0.9 the rules policy earns +$657 and the agent +$1,256 against it, because the opportunity there is small for both. At 1.1 the rules policy earns +$79,869 from 8,385 stay dates changed, because a market a tenth larger runs ahead of pace almost everywhere, and the agent's +$112,082 is +$32,214 against it. In the reacting market the rules policy earns +$105,144 and the agent's +$72,229 is -$32,914 against it, behind in every seed: the policy changes 7,091 stay dates against the agent's 207 and rides the ratchet further. The never-cut policy earns +$24,780 a seed in the default world from 5,416 stay dates changed, and the agent's lead over it is +$8,119, ahead in 17 of 20, so the cuts cost the rules policy about $1,900 a seed and the README quotes the lead over the control that never gives money away. At a bias of 0.9 the never-cut policy loses $461 a seed, because a market a tenth smaller runs behind pace and the flags it still acts on are the false ones ahead, and at 1.1 it earns +$85,934. In the reacting market it earns +$141,050 from 5,387 changes and beats the agent by $68,820 in every seed, because nothing it does ever pulls a rate back, so it rides the ratchet further than the cutting policy. All three policies are anomaly-driven as the agent is: they act only on a flag, so they share the blind spot FRK-11 records, and a market that is simply larger raises nothing for any of them.

## The reviewers in learn mode

`hotel-market bench --seeds 1 20 --elasticity learn:1.0 --elasticity learn:2.0 --model claude-opus-5-5 --model claude-haiku-5-5`, the same command with `--cautious`, `hotel-market bench --seeds 1 20 --elasticity learn:1.0 --model claude-sonnet-5-5` with and without `--cautious`, and `hotel-market bench --seeds 1 20 --elasticity learn:1.0 --cautious --react --market-elasticity 0.5 --model claude-opus-5-5`, run on 2026-10-12. The template and the oracle run beside the model in every arm. Opus runs the four arms with no reaction and the reacting one. Haiku runs the four arms with no reaction, and Sonnet the two from a prior of 1.0. The live calls ran first, in parallel chunks of seeds. Seeds 1 to 3 ran as one process per command. The projection from their calls priced seeds 1 to 20 at $42.31, under the $60 gate set for the run. Seeds 4 to 20 then ran in ten chunks, two seed ranges per command. The commands that printed the tables read every cache and made no call. The columns are those of the fixed-elasticity tables, with the rate changes and the day-59 estimate added. The estimate is the range of the per-hotel means on day 59, as in the demand-bias tables.

The answer schema changed before these runs. The first schema bounded the decisions array to the number of entries. The API refused every request with two or more entries, because it supports array bounds of 0 and 1 only. With the bound at 1, Sonnet answered for one entry when a request held two. The schema is now an object with one required decision per entry id, so an omission cannot parse. Every record with a bad attempt in the tables is seed 1's first two-entry request under the earlier schemas. The rerun answered each.

Seeds 1 to 20 at a learned elasticity from a prior of 1.0, each reviewer against the fixed-rate run.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost | Day-59 estimate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| template | +14,141 | 15,084 | 3,373 | -6,839 to +45,818 | 16/20 | 0.012 | 373 | +16,687 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - | 1.36 to 1.45 |
| oracle | +30,828 | 10,016 | 2,240 | +13,813 to +54,182 | 20/20 | <0.001 | 188 | +0 | 1.00 | 0.21 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - | 1.22 to 1.38 |
| claude-opus-5-5 | +14,869 | 15,461 | 3,457 | -6,839 to +48,419 | 16/20 | 0.012 | 366 | +15,959 | 0.04 | 0.98 | 1.00 | 0.04 | 0.07 | 0.05 | 1 | 358 | 1,057,320/131,217 | 4.4 | $6.85 | 1.37 to 1.45 |
| claude-sonnet-5-5 | +14,141 | 15,084 | 3,373 | -6,839 to +45,818 | 16/20 | 0.012 | 373 | +16,687 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 1 | 358 | 1,057,337/76,502 | 2.5 | $2.88 | 1.36 to 1.45 |
| claude-haiku-5-5 | +14,141 | 15,084 | 3,373 | -6,839 to +45,818 | 16/20 | 0.012 | 373 | +16,687 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 358 | 1,057,337/253,584 | 3.9 | $0.23 | 1.36 to 1.45 |

Seeds 1 to 20 at a learned elasticity from a prior of 1.0 with the cautious rule, each reviewer against the fixed-rate run. The three model rows are the rerun after the display fix described below. The template and the oracle do not read the display, so their rows did not change.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost | Day-59 estimate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| template | +25,076 | 11,507 | 2,573 | +8,406 to +53,535 | 20/20 | <0.001 | 299 | +5,966 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - | 1.28 to 1.43 |
| oracle | +31,042 | 9,575 | 2,141 | +12,679 to +55,153 | 20/20 | <0.001 | 201 | +0 | 1.00 | 0.34 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - | 1.25 to 1.35 |
| claude-opus-5-5 | +25,076 | 11,507 | 2,573 | +8,406 to +53,535 | 20/20 | <0.001 | 299 | +5,966 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 284 | 1,314,166/89,043 | 3.8 | $7.04 | 1.28 to 1.43 |
| claude-sonnet-5-5 | +25,076 | 11,507 | 2,573 | +8,406 to +53,535 | 20/20 | <0.001 | 299 | +5,966 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 284 | 1,314,166/56,449 | 2.4 | $3.19 | 1.28 to 1.43 |
| claude-haiku-5-5 | +25,076 | 11,507 | 2,573 | +8,406 to +53,535 | 20/20 | <0.001 | 299 | +5,966 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 284 | 1,314,166/231,971 | 4.3 | $0.25 | 1.28 to 1.43 |

Seeds 1 to 20 at a learned elasticity from a prior of 2.0, with and without the cautious rule. Each reviewer is against the fixed-rate run. The two cautious model rows kept their first run, from before the display fix, so they have no spread.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| learn:2.0 | template | +16,258 | 8,550 | 1,912 | +2,393 to +34,480 | 20/20 | <0.001 | 418 | +8,536 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - | 1.55 to 1.68 |
| learn:2.0 | oracle | +24,794 | 8,569 | 1,916 | +8,723 to +44,493 | 20/20 | <0.001 | 227 | +0 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - | 1.61 to 1.68 |
| learn:2.0 | claude-opus-5-5 | +16,524 | 8,520 | 1,905 | +2,393 to +34,480 | 20/20 | <0.001 | 413 | +8,270 | 0.03 | 0.99 | 1.00 | 0.03 | 0.05 | 0.02 | 0 | 390 | 1,128,766/150,317 | 5.2 | $7.52 | 1.55 to 1.68 |
| learn:2.0 | claude-haiku-5-5 | +16,258 | 8,550 | 1,912 | +2,393 to +34,480 | 20/20 | <0.001 | 418 | +8,536 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 390 | 1,129,517/301,737 | 4.3 | $0.26 | 1.55 to 1.68 |
| learn:2.0 --cautious | template | +17,634 | 5,712 | 1,277 | +5,839 to +27,585 | 20/20 | <0.001 | 240 | +965 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - | 1.59 to 1.84 |
| learn:2.0 --cautious | oracle | +18,599 | 5,674 | 1,269 | +7,773 to +29,516 | 20/20 | <0.001 | 169 | +0 | 1.00 | 0.52 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - | 1.62 to 1.92 |
| learn:2.0 --cautious | claude-opus-5-5 | +17,644 | - | - | +5,839 to +27,585 | 20/20 | - | 237 | +955 | 0.01 | 0.98 | 0.80 | 0.06 | 0.10 | 0.00 | 0 | 234 | 942,853/89,872 | 5.6 | $5.57 | 1.59 to 1.84 |
| learn:2.0 --cautious | claude-haiku-5-5 | +17,601 | - | - | +5,178 to +27,585 | 20/20 | - | 236 | +999 | -0.03 | 0.97 | 0.71 | 0.07 | 0.13 | 0.01 | 0 | 235 | 945,928/209,508 | 4.8 | $0.20 | 1.59 to 1.84 |

Seeds 1 to 20 at a learned elasticity from a prior of 1.0 with the cautious rule, the reaction on. The market elasticity is 0.5, and each reviewer is against the fixed-rate run. The Opus row was measured before the display fix, so it has no spread. Recent shown counts the queued plans on stay dates the hotel changed within the previous 14 days. Recent held counts those among them the reviewer declined. The other columns are those of the reaction tables.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Regret | Recovered | Accept | Precision | Median flags | Own changes | Changed twice | Recent shown | Recent held | Invalid | Calls | Tokens in/out | Median s | Cost | Day-59 estimate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| template | +198,089 | 80,371 | 17,972 | +77,536 to +336,986 | 20/20 | <0.001 | 784 | +400 | 0.00 | 1.00 | - | 1378 | 1318 | 702 | 556 | 0 | - | - | - | - | - | 1.22 to 1.42 |
| oracle | +198,488 | 80,600 | 18,023 | +77,536 to +336,986 | 20/20 | <0.001 | 780 | +0 | 1.00 | 0.99 | 1.00 | 1378 | 1318 | 702 | 556 | 1 | - | - | - | - | - | 1.22 to 1.42 |
| claude-opus-5-5 | +192,265 | - | - | +77,536 to +332,153 | 20/20 | - | 737 | +6,224 | -14.58 | 0.94 | 0.00 | 1327 | 1267 | 675 | 556 | 43 | 1 | 368 | 2,246,509/196,380 | 5.0 | $12.91 | 1.23 to 1.41 |

The decline rate by the standard error of the plan's elasticity, pooled over seeds 1 to 20. The table holds every live arm that declined a plan, as measured before the display fix. After it the arms from 1.0 with the cautious rule declined nothing. Each cell is the plans declined of the plans queued in the group, with the rate.

| Mode | Reviewer | Under 0.15 | 0.15 to 0.25 | 0.25 to 0.35 | 0.35 and over |
| --- | --- | ---: | ---: | ---: | ---: |
| learn:1.0 | claude-opus-5-5 | none queued | 3 of 95 (0.03) | 3 of 95 (0.03) | 1 of 183 (0.01) |
| learn:1.0 --cautious | claude-opus-5-5 | none queued | 0 of 41 (0.00) | 1 of 72 (0.01) | 4 of 190 (0.02) |
| learn:1.0 --cautious | claude-sonnet-5-5 | none queued | 0 of 41 (0.00) | 0 of 72 (0.00) | 2 of 189 (0.01) |
| learn:1.0 --cautious | claude-haiku-5-5 | none queued | 0 of 41 (0.00) | 3 of 76 (0.04) | 7 of 189 (0.04) |
| learn:2.0 | claude-opus-5-5 | none queued | 0 of 76 (0.00) | 3 of 122 (0.02) | 1 of 219 (0.00) |
| learn:2.0 --cautious | claude-opus-5-5 | none queued | 0 of 14 (0.00) | 2 of 61 (0.03) | 3 of 167 (0.02) |
| learn:2.0 --cautious | claude-haiku-5-5 | none queued | 0 of 14 (0.00) | 2 of 61 (0.03) | 5 of 168 (0.03) |
| learn:1.0 --cautious, react, market 0.5 | claude-opus-5-5 | 0 of 5 (0.00) | 4 of 46 (0.09) | 13 of 212 (0.06) | 32 of 523 (0.06) |

The reviewers ranked across the learned modes, learn:1.0 and learn:2.0 pooled over 40 seeds, with and without the cautious rule. The cautious pair is as measured before the display fix, so its rows have no spread. Sonnet ran from the prior of 1.0 only, so it appears in the mode tables and in no ranking.

| Arms | Rank | Reviewer | Mean change | SD | SE | Range | Ahead | p | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| without the rule | 1 | oracle | +27,811 | 9,694 | 1,533 | +8,723 to +54,182 | 40/40 | <0.001 | +0 | 1.00 | 0.31 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| without the rule | 2 | claude-opus-5-5 | +15,696 | 12,350 | 1,953 | -6,839 to +48,419 | 36/40 | <0.001 | +12,114 | 0.04 | 0.99 | 1.00 | 0.03 | 0.06 | 0.04 | 1 | 748 | 2,186,086/281,534 | 4.8 | $14.38 |
| without the rule | 3 | template | +15,199 | 12,150 | 1,921 | -6,839 to +45,818 | 36/40 | <0.001 | +12,612 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| without the rule | 4 | claude-haiku-5-5 | +15,199 | 12,150 | 1,921 | -6,839 to +45,818 | 36/40 | <0.001 | +12,612 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 748 | 2,186,854/555,321 | 4.1 | $0.50 |
| with the rule | 1 | oracle | +24,821 | - | - | +7,773 to +55,153 | 40/40 | - | +0 | 1.00 | 0.41 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| with the rule | 2 | claude-opus-5-5 | +21,360 | - | - | +5,839 to +53,535 | 40/40 | - | +3,461 | 0.00 | 0.98 | 0.80 | 0.04 | 0.08 | 0.01 | 1 | 521 | 2,187,810/190,620 | 5.0 | $12.56 |
| with the rule | 3 | template | +21,355 | - | - | +5,839 to +53,535 | 40/40 | - | +3,465 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| with the rule | 4 | claude-haiku-5-5 | +21,337 | - | - | +5,178 to +53,039 | 40/40 | - | +3,484 | -0.01 | 0.97 | 0.76 | 0.07 | 0.13 | 0.01 | 0 | 524 | 2,197,470/466,731 | 4.7 | $0.45 |

The learn arms' cost at list prices. The first column prices the calls of seeds 1 to 3. The projection is their cost per seed times 20. The last two columns are the cost and the calls of seeds 1 to 20.

| Mode | Model | Seeds 1 to 3 | Projected, seeds 1 to 20 | Measured, seeds 1 to 20 | Calls |
| --- | --- | ---: | ---: | ---: | ---: |
| learn:1.0 | claude-opus-5-5 | $1.02 | $6.77 | $6.85 | 358 |
| learn:1.0 | claude-sonnet-5-5 | $0.41 | $2.71 | $2.88 | 358 |
| learn:1.0 | claude-haiku-5-5 | $0.03 | $0.22 | $0.23 | 358 |
| learn:1.0 --cautious | claude-opus-5-5 | $1.02 | $6.78 | $6.99 | 287 |
| learn:1.0 --cautious | claude-sonnet-5-5 | $0.45 | $2.99 | $3.07 | 286 |
| learn:1.0 --cautious | claude-haiku-5-5 | $0.04 | $0.24 | $0.25 | 289 |
| learn:2.0 | claude-opus-5-5 | $1.08 | $7.21 | $7.52 | 390 |
| learn:2.0 | claude-haiku-5-5 | $0.04 | $0.25 | $0.26 | 390 |
| learn:2.0 --cautious | claude-opus-5-5 | $0.61 | $4.03 | $5.57 | 234 |
| learn:2.0 --cautious | claude-haiku-5-5 | $0.02 | $0.15 | $0.20 | 235 |
| learn:1.0 --cautious, react, market 0.5 | claude-opus-5-5 | $1.64 | $10.95 | $12.91 | 368 |
| every arm | | $6.35 | $42.31 | $46.76 | 3,553 |

From a prior of 1.0, accepting every plan earns +$14,141 a seed. The oracle earns +$30,828 while accepting 21% of the plans, so $16,687 a seed is open to a reviewer. Opus recovers 4% of it. It declines 7 plans in 20 seeds, and the oracle agrees with every one. Six are the day-40 raise of 10% on every day for stay dates 70 to 90 after the seat cut. That is the plan Opus held 36 times at a fixed elasticity of 1.0. Its reasons say that the dates are behind pace and priced above the median. One reason calls the raise "too small to justify pricing further above the market while bookings trail pace". The seventh decline is a day-0 raise on a date behind pace. Its reason says the estimate "rests on an elasticity of 1 learned from 0 observations". From a prior of 2.0, Opus declines 4 plans, each the day-40 cut of 5% on the same dates. The oracle agrees with each. Sonnet and Haiku accept every plan in both arms and tie with the template. Under every reviewer the day-59 estimates are within 0.01 of the template's, because few declines change few bookings.

The cautious arms showed a second kind of decline in the first run. The cautious rule changes a rate only where the change beats holding at both ends of the band. The request showed the gain at each end to the nearest $10, as it shows every estimate. A gain under $5 at an end therefore read "the same as holding", although the code's rule, which asks for more than zero, had passed it. The models read the display as a failed rule. From the prior of 1.0, Opus declined 5 plans, Haiku 10 and Sonnet 2. On seed 7, day 29, all three declined the same airport raise on that reading. Opus wrote that it "does not beat holding at both ends as the cautious rule requires". The oracle agreed with 4 of Opus's 5. Haiku's run was within $3 a seed of the template's and Sonnet's within $128. That was the request's fault, and the benchmark found it. The request now writes a gain at an end of the band to the dollar under $10. It also states the rule's verdict for each candidate as a phrase the model copies, such as "beats holding at both ends of the band" (DEC-56). The three arms from 1.0 reran on seeds 1 to 20 with the new requests. Every model accepted every plan, and each ties with the template at +$25,076. The rerun made 852 calls for $10.48. The arms from 2.0 kept their first run. There the same reading declined 5 cuts for Opus and 7 for Haiku at the low end. Those were worth +$10 and -$33 a seed, so every cautious run stays within $130 a seed of accepting all.

The standard error did not move the declines. From 1.0, Opus declines 3% of the plans with a standard error under 0.35 and 1% of the rest. Before the display fix the cautious arms declined 0% to 4% in every group. The reacting arm declined 9%, 6% and 6%. The one plan whose estimate rested on no observation, with a standard error of 0.5, was declined. Every other decline named a cause or the band's display.

In the reacting market the rules control earns +$105,144 a seed against the agent's +$72,229. The control wins in that world because of the loop: it raises again on every comp move that followed its own raise. The reviewer arm is where a model can decline the second raise on dates it raised a week before. Opus was shown 556 plans on stay dates the hotel had changed within the previous 14 days. It held 43 of them, 8%, against 6 of the 230 other plans, 3%. Its reasons never name the earlier raise, because the request carries no history of the hotel's own changes. The tables now keep each decision's request, answer and outcome (DEC-45), and the next version puts that history into the request. Forty of the 49 cite the band's display as the first run showed it and quote "the same as holding at the high end of the elasticity band". A second raise lands there more often, because the hotel already sits 5% above the median it moved. The oracle, told the reaction and the market elasticity, holds 1 of the 556 and accepts 99% of the plans. In this simulator the second raise pays. Opus's holds therefore cost $5,824 a seed against accepting all and $6,224 against the oracle. Its stay dates changed twice fall from 702 to 675. Opus does not decline the second raise as such. The 43 holds are the before measurement for FRK-09's fix.

The five commands made 3,553 calls for $46.76 at list prices. Opus's five arms cost $39.84, Sonnet's two $5.95 and Haiku's four $0.94. The projection from seeds 1 to 3 was $42.31. The reacting arm and the cautious arm from 2.0 came in $1.96 and $1.54 over their projections. Their later seeds made more calls a seed than their first three. The rerun of the three cautious arms from 1.0 after the display fix made 852 calls for $10.48.

## The convention without the competitors' raise

`python scripts/no_comp_raise.py --seeds 1 20`, run on 2026-10-15. The script runs the template sweep as shipped and then again with the convention's competitor raise set to 0.0 and its demand uplift left at 35%, and it puts the shipped event back afterwards. A convention plan is an accepted plan whose causes include the event's announcement, and its gain is the contribution change on the stay dates it changed. The last column counts the convention nights, four at each of the two downtown hotels, that sold out at fixed rates over the 20 seeds.

Seeds 1 to 20 with the convention's competitor raise as shipped and at zero, the template in the true mode, each against the fixed-rate run.

| Competitors' raise | Mean change a seed | Range | Ahead | Convention plans accepted | Gain on their stay dates a seed | Convention nights sold out at fixed rates |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 15% | +$32,899 | +$13,479 to +$52,809 | 20 of 20 | 40 | +$14,018 | 79 of 160 |
| 0% | +$19,480 | +$8,462 to +$31,031 | 20 of 20 | 17 | +$538 | 10 of 160 |

With the raise at zero the mean falls from +$32,899 to +$19,480 a seed and the convention plans earn +$538 a seed on their stay dates instead of +$14,018, so most of the convention's share of the headline comes from the competitors' raise and not from the demand uplift. A hotel that holds its rate while its comp set raises 15% sits 13% below the median, and the rate ratio then sends it 1.15 to the power 1.5, or 23% more, of the bookings still to come, which is why 79 of the 160 convention nights sell out at fixed rates with the raise and 10 without it.

## In a revenue manager's measures

`python scripts/measures.py --seeds 1 20`, run on 2026-10-15. Each measure is per hotel over stay dates 0 to 149 and is the mean over the 20 seeds, with the fixed-rate run beside the agent run. The second table divides the 20-seed totals by 20: the room nights the agent run gave up, their share of the hotel's capacity, the change in room revenue, the room cost saved on those nights and the contribution gained. The last column is the cost per occupied room, as a share of the start rate, at which the hotel's gain would be zero. The gain is positive above that share, and a hotel whose room revenue rose gains at any cost, so its share prints below zero.

Seeds 1 to 20 in a revenue manager's measures: occupancy, average rate, RevPAR and the share of sold-out nights per hotel, the fixed-rate run and the agent run, each the mean over the seeds.

| Hotel | Occupancy, fixed | Occupancy, agent | Average rate, fixed | Average rate, agent | RevPAR, fixed | RevPAR, agent | Sold-out nights, fixed | Sold-out nights, agent |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel | 78.4% | 78.2% | $220.00 | $220.58 | $172.54 | $172.55 | 1.9% | 0.7% |
| Downtown full-service hotel | 77.6% | 77.3% | $190.00 | $190.56 | $147.36 | $147.35 | 2.2% | 0.6% |
| Lifestyle hotel | 77.2% | 76.3% | $240.00 | $242.61 | $185.29 | $185.05 | 11.6% | 7.0% |
| Airport hotel | 88.9% | 86.2% | $140.00 | $143.36 | $124.46 | $123.61 | 20.8% | 12.3% |

Seeds 1 to 20: what the agent run gave up and saved a seed, per hotel, and the cost share at which the gain is zero.

| Hotel | Room nights given up a seed | Share of capacity | Room revenue change a seed | Room cost saved a seed | Contribution gained a seed | Cost share at which the gain is zero |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel | 121 | 0.20% | +$687 | +$8,892 | +$9,579 | -2.6% |
| Downtown full-service hotel | 85 | 0.23% | -$64 | +$5,402 | +$5,338 | 0.4% |
| Lifestyle hotel | 167 | 0.93% | -$4,396 | +$13,396 | +$9,000 | 10.9% |
| Airport hotel | 602 | 2.67% | -$19,088 | +$28,070 | +$8,982 | 22.7% |

The agent gives up rooms at every hotel, and RevPAR is flat at the two downtown hotels and lower at the other two, so the gain is room cost not paid rather than revenue earned. The airport hotel's gain holds only while the cost of an occupied room is above 22.7% of the rate, and the lifestyle hotel's only above 10.9%, while the two downtown hotels gain at any cost because their room revenue rose or barely fell.
