# Results

Seeds 1 to 20 in the default mode: the agent run against the fixed-rate run, stay dates 0 to 149, run on 2026-10-15 on world v2 with `hotel-market --seeds 1 20 --template`. The reasons are the template's, and candidates are scored on contribution with the simulator's elasticity. The last two rows are the standard deviation across the seeds and the standard error of the mean.

| Seed | Contribution change | Revenue change | Rate changes |
| ---: | ---: | ---: | ---: |
| 1 | +13,192 | -31,145 | 7 |
| 2 | +15,459 | -26,154 | 7 |
| 3 | +14,716 | -26,510 | 4 |
| 4 | +16,490 | -27,303 | 4 |
| 5 | +12,274 | -34,673 | 3 |
| 6 | +16,846 | -26,388 | 5 |
| 7 | +19,796 | -21,324 | 6 |
| 8 | +20,372 | -24,501 | 4 |
| 9 | +18,347 | -25,287 | 9 |
| 10 | +12,282 | -27,171 | 4 |
| 11 | +16,407 | -34,550 | 6 |
| 12 | +12,172 | -35,118 | 4 |
| 13 | +16,138 | -28,675 | 5 |
| 14 | +17,660 | -28,983 | 4 |
| 15 | +20,024 | -23,653 | 6 |
| 16 | +15,897 | -23,187 | 4 |
| 17 | +23,394 | -21,103 | 6 |
| 18 | +11,589 | -33,071 | 6 |
| 19 | +13,704 | -28,709 | 5 |
| 20 | +16,523 | -26,183 | 7 |
| Mean | +16,164 | -27,684 | |
| SD | 3,166 | 4,231 | |
| SE | 708 | 946 | |

Seed 7, days 0 to 59: what became of the flags, run on 2026-10-15 on world v2 with `hotel-market --seed 7 --template`.

| Flags | Changed a rate | Held: no change beat hold | Held: worth under the minimum | Declined by the model | Minimum-stay advice |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 117 | 6 | 101 | 10 | 0 | 1 |

Comp-median flags over seeds 1 to 20 in the default mode, from the same sweep: those on a day a scripted shock moved a median (10, the convention's competitor raise, and 30, the rate cut) and those on every other day, where only the shop noise moved it. Since world v2 the rate shop moves every day, so the 5% threshold meets ordinary noise. Measured on 2026-10-15 on world v2 with `hotel-market --seeds 1 20 --template`.

| Median flags | On a shock day | On other days |
| ---: | ---: | ---: |
| 496 | 80 | 416 |

Seed 7: room revenue and contribution per hotel, the fixed-rate run against the agent run, stay dates 0 to 149, run on 2026-10-15 on world v2.

| Hotel | Revenue, fixed | Revenue, agent | Change | Contribution, fixed | Contribution, agent | Change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel | 10,146,840 | 10,146,840 | +0 | 6,764,560 | 6,764,560 | +0 (+0.0%) |
| Downtown full-service hotel | 5,447,300 | 5,447,300 | +0 | 3,631,533 | 3,631,533 | +0 (+0.0%) |
| Lifestyle hotel | 3,324,480 | 3,328,951 | +4,471 | 2,216,320 | 2,229,991 | +13,671 (+0.6%) |
| Airport hotel | 2,809,380 | 2,783,585 | -25,795 | 1,872,920 | 1,879,045 | +6,125 (+0.3%) |
| All four hotels | 21,728,000 | 21,706,676 | -21,324 | 14,485,333 | 14,505,130 | +19,796 (+0.1%) |

Seed 7 over only the 70 hotel and stay-date pairs where the agent changed a rate, run on 2026-10-15 on world v2. The pairs per hotel are in brackets.

| Hotel | Revenue, fixed | Revenue, agent | Change | Contribution, fixed | Contribution, agent | Change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel (0) | 0 | 0 | +0 | 0 | 0 | +0 |
| Downtown full-service hotel (0) | 0 | 0 | +0 | 0 | 0 | +0 |
| Lifestyle hotel (17) | 453,120 | 457,591 | +4,471 | 302,080 | 315,751 | +13,671 (+4.5%) |
| Airport hotel (53) | 1,030,400 | 1,004,605 | -25,795 | 686,933 | 693,058 | +6,125 (+0.9%) |
| All four hotels | 1,483,520 | 1,462,196 | -21,324 | 989,013 | 1,008,810 | +19,796 (+2.0%) |

Seeds 1 to 20 per elasticity arm, each against the same fixed-rate runs, run on 2026-10-15 on world v2 with `hotel-market --seeds 1 20 --template --elasticity true --elasticity fixed:1.0 --elasticity fixed:2.0 --elasticity learn:1.0 --elasticity learn:2.0` and the same with `--elasticity learn:1.0 --elasticity learn:2.0 --cautious`. Estimated / realised is the accepted plans' estimated gain over holding, summed over the seeds, over the realised gain. Rejected at an end counts a cautious arm's candidates ahead of hold at the estimate but behind at an end.

| Elasticity | Mean gain per seed | SD | SE | Range | Seeds ahead | p | Rate changes | Estimated / realised | Rejected at an end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| true (1.5, the simulator's) | +$16,164 | $3,166 | $708 | +$11,589 to +$23,394 | 20 of 20 | <0.001 | 106 | 1.21 |  |
| fixed:1.0 | -$6,265 | $6,944 | $1,553 | -$17,084 to +$11,323 | 3 of 20 | 0.0026 | 766 | -44.0 |  |
| fixed:2.0 | -$2,687 | $4,119 | $921 | -$10,801 to +$3,231 | 6 of 20 | 0.12 | 566 | -39.1 |  |
| learn:1.0 | +$804 | $8,122 | $1,816 | -$14,583 to +$14,562 | 11 of 20 | 0.82 | 510 | 248.4 |  |
| learn:1.0 --cautious | +$12,527 | $5,265 | $1,177 | +$1,658 to +$21,698 | 20 of 20 | <0.001 | 295 | 10.1 | 3,446 |
| learn:2.0 | +$2,416 | $5,222 | $1,168 | -$8,435 to +$9,983 | 13 of 20 | 0.26 | 398 | 26.0 |  |
| learn:2.0 --cautious | +$2,018 | $4,187 | $936 | -$8,396 to +$10,445 | 12 of 20 | 0.50 | 213 | 17.4 | 2,733 |

Where each arm's gain came from, summed over the 20 seeds, run on 2026-10-15 on world v2. The first group is the plans the convention (day 10) and the new flights (day 20) raised. The second is every other plan.

| Elasticity | Shock plans | Gain on their stay dates | Other plans | Gain on theirs |
| --- | ---: | ---: | ---: | ---: |
| true | 63 | +$302,280 | 43 | +$21,001 |
| fixed:1.0 | 143 | -$138,974 | 623 | +$13,682 |
| fixed:2.0 | 139 | -$57,555 | 427 | +$3,823 |
| learn:1.0 | 143 | -$1,818 | 367 | +$17,902 |
| learn:1.0 --cautious | 99 | +$242,898 | 196 | +$7,652 |
| learn:2.0 | 133 | +$33,752 | 265 | +$14,571 |
| learn:2.0 --cautious | 60 | +$10,405 | 153 | +$29,955 |

What the accepted plans' nights came to, summed over the 20 seeds, run on 2026-10-15 on world v2: each plan's estimate for the night, the contribution on the rooms then unsold, against what the rooms sold after the decision earned on it. The sweep computes these from the run's own books as the stored outcomes table records them.

| Elasticity | Nights changed | Estimated | Realised | Realised / estimated |
| --- | ---: | ---: | ---: | ---: |
| true | 1,528 | +$19,861,514 | +$19,472,613 | 0.98 |
| fixed:1.0 | 7,218 | +$121,943,362 | +$113,413,893 | 0.93 |
| fixed:2.0 | 5,969 | +$102,158,792 | +$97,954,323 | 0.96 |
| learn:1.0 | 6,687 | +$112,088,008 | +$106,508,314 | 0.95 |
| learn:1.0 --cautious | 3,064 | +$49,026,356 | +$46,142,320 | 0.94 |
| learn:2.0 | 5,426 | +$91,773,051 | +$89,074,240 | 0.97 |
| learn:2.0 --cautious | 1,556 | +$26,407,231 | +$25,270,377 | 0.96 |

The learning agent's day-59 elasticity estimates against a true value of 1.5, run on 2026-10-15 on world v2. Each figure is the range over the four hotels of each hotel's mean across the 20 seeds.

| Prior | Day-59 estimate, by hotel |
| ---: | --- |
| 1.0 | 1.42 to 1.49 |
| 2.0 | 1.52 to 1.75 |

The cautious rule with and without a $250 minimum per day of the week, seeds 1 to 20. Measured on world v1 (commit b178e7b): the per-day minimum rule no longer exists, so the table is not rerun; the band alone on world v2 is in the arm table above. The band alone is the rule that stayed. Its rejection count includes every candidate ahead of hold at the estimate, including those worth less than $250.

| Arm | Band alone: mean gain | Rate changes | Rejected at an end | With a minimum per day of the week: mean gain | Rate changes | Rejected at an end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| learn:1.0 --cautious | +$25,076 | 299 | 3,294 | +$25,084 | 299 | 1,205 |
| learn:2.0 --cautious | +$17,634 | 240 | 2,681 | +$17,618 | 229 | 766 |

Seeds 1 to 20 with the simulator's elasticity and the template, each target against the same fixed-rate runs, run on 2026-10-15 on world v2 with `hotel-market --seeds 1 20 --template` and the same with `--target revenue`. The last two columns are in the target's own measure.

| Target | Mean contribution change | SD | SE | Mean revenue change | Seeds ahead on contribution | p | Rate changes | Accepted plans' estimate | Realised |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| contribution | +$16,164 | $3,166 | $708 | -$27,684 | 20 of 20 | <0.001 | 106 | +$391,434 | +$323,281 |
| revenue | -$8,214 | $4,500 | $1,006 | +$179,333 | 0 of 20 | <0.001 | 805 | +$3,608,913 | +$3,586,668 |

### Measured on world v1 (commit b178e7b)

The two tables below are the live runs of world v1 and are not rerun until a live run re-records seed 7 on world v2 (`make live-audit SEED=7`, then `python scripts/live_audit.py --seed 7 --record-fixture`).

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

### Measured on world v2

Seed 7 with fixed rates: occupancy by hotel over stay dates 0 to 59 and over 140 to 149, measured on 2026-10-15 on world v2. The last column is the emptiest of those last ten nights.

| Hotel | Occupancy, stay dates 0 to 59 | Occupancy, stay dates 140 to 149 | Emptiest night, 140 to 149 |
| --- | ---: | ---: | ---: |
| Downtown convention hotel | 75.2% | 81.0% | 61% (stay date 144) |
| Downtown full-service hotel | 74.6% | 84.2% | 71% (stay date 145) |
| Lifestyle hotel | 75.4% | 76.9% | 60% (stay date 148) |
| Airport hotel | 83.8% | 96.1% | 79% (stay date 145) |

Seed 7 under earlier designs, before the current estimate, Measured on world v1 (commit b178e7b). The last row is the design as it stood on world v1, whose world v2 figures are in the first tables. Its 20-seed mean is for the same design over seeds 1 to 20.

| Design | Contribution change, seed 7 | Rate changes | Flags held under the minimum | 20-seed mean |
| --- | ---: | ---: | ---: | ---: |
| Weekday rate factors, one candidate per flag, no minimum, estimate capped at the unsold rooms | +$26,420 | 23 (8 lost money) | | |
| Flat rates, a plan per day of the week, the $250 minimum, estimate capped at the unsold rooms | +$22,894 | 10 | 22 | +$27,350 |
| The same with the exact estimate E[min(N, unsold)] | +$28,818 | 7 | 57 | +$32,899 |

The estimator against known elasticities: seed 7 in learn mode from a prior of 1.5, measured on 2026-10-15 on world v2. The simulator's elasticity is set to each true value in turn. Each cell is the day-59 estimate at that hotel, with its standard error in brackets.

| True elasticity | Downtown convention | Downtown full-service | Lifestyle | Airport |
| ---: | ---: | ---: | ---: | ---: |
| 1.0 | 0.85 (0.13) | 1.32 (0.27) | 1.02 (0.21) | 0.90 (0.19) |
| 1.5 | 1.30 (0.14) | 1.33 (0.22) | 1.35 (0.22) | 1.52 (0.23) |
| 2.0 | 2.03 (0.17) | 1.54 (0.23) | 1.77 (0.26) | 1.91 (0.24) |

Spread of the log rate ratio in the estimator's observations by hotel, measured on 2026-10-15 on world v2. The run is the fixed-rate run of seed 7 as of day 59; since world v2 the shop noise moves the ratio every day.

| Hotel | Standard deviation of log(rate / comp median) | Observations |
| --- | ---: | ---: |
| Downtown convention hotel | 0.026 | 5,310 |
| Downtown full-service hotel | 0.027 | 5,310 |
| Lifestyle hotel | 0.012 | 5,302 |
| Airport hotel | 0.012 | 5,304 |

Timings of the stored tables, measured once during development on the development machine.

| Operation | Time |
| --- | --- |
| One day through `hotel-market run-day` | under a second, most of it the simulator's playback |
| Days 0 to 59 through `hotel-market run-day --from 0` | about 6 seconds |
| Inserting a day's rows one statement at a time (replaced by one frame per day) | 2.5 seconds per 3,000 rows |
| Reading the events table once per detect row (replaced by one read per day) | 2 seconds a day |

The suite on each Python version. The run of 2026-10-12 came from a fresh virtual environment with the slow tests included and passed 235 tests on both versions. The counts below were refreshed on 2026-10-15 on world v2 from the plain suite, with numpy 2.5.4, pandas 3.0.6 and duckdb 1.5.6 on both, and anthropic 1.13.0 on 3.12.6 and 1.14.0 on 3.13.7. The nine slow tests are skipped, and so are the five demo-page tests wherever the environment has the dev extra alone, which is what `make setup` installs: the fresh-copy row ran `make setup` and then `make test` in a copy of the repository with its history and without .venv, and the five ran once `make demo` had installed streamlit. The two xfailed tests read the recorded live run of seed 7, which was made on world v1; they pass again once `make live-audit SEED=7` and then `python scripts/live_audit.py --seed 7 --record-fixture` re-record it. `make test-all` on 3.12.6, the nine slow tests included, gave 383 passed and the 2 xfailed on 2026-10-15.

| Python | Command | Result |
| --- | --- | --- |
| 3.12.6 | `python -m pytest` | 374 passed, 9 skipped, 2 xfailed |
| 3.12.6 | `make setup` then `make test` in a fresh copy, the dev extra alone | 369 passed, 14 skipped, 2 xfailed |
| 3.13.7 | `python -m pytest` | 369 passed, 14 skipped, 2 xfailed |

The live answers under cache/ are the only copy of about $86 of model calls, so they are archived as a dated tar outside the repository, with the archive's sha256 and a per-file list beside it. The archive of 2026-10-15 is cache-2026-10-15-0406.tar.gz under ~/backups/hotel-market-sim, 8,203 files with the sha256 ab3b5f7a6f49e81a81716ed9baa626efee668f79be5328ebd5d77addb6c3d9c6, and it restores with `tar -xzf` from the repository root.

The container image on each Python version, built on 2026-10-12. Docker 28.4.0 ran on an aarch64 Ubuntu VM with 4 CPUs and 4 GiB. Each image ran the suite from its copy of the repository, and the 3.12 image ran seed 7 with the template. pandas 3.0.6, duckdb 1.5.6 and anthropic 1.13.0 were installed on every version, and every dependency came as a wheel, 3.14 included. The images were not rebuilt; the native plain suite has since grown to 357 passed and 9 skipped.

| Python | numpy | Build | Image | Tests | Suite time | Seed-7 run | decisions.jsonl |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| 3.11.15 | 2.4.6 | 24 s | 615 MB | 278 passed, 3 skipped | 45 s | | |
| 3.12.13 | 2.5.4 | 24 s | 592 MB | 278 passed, 3 skipped | 45 s | 1.6 s | matched the native run on world v1; the native checksum is 263387b3 on world v2, was 19b766b8 on world v1 once the plan records gained two fields, and 8ce570ea when the image ran |
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

`hotel-market bench --seeds 1 20 --template --demand-bias F --elasticity true --elasticity fixed:1.0 --elasticity learn:1.0`, and the same command with `--elasticity learn:1.0 --cautious`, run on 2026-10-15 on world v2 at F = 0.9, 1.1 and 1.0. The option multiplies the simulator's demand by F, the day-0 preload included. The agent never sees F, so its forecast is wrong by that factor in every mode. The oracle reviewer, which is told F, stays the simulator's truth. Each arm is measured against the fixed-rate run at the same bias.

In every table, mean change and range are the contribution change per seed against the fixed-rate run, and ahead counts the seeds where the arm beat it. Flags counts the flags the arm raised over the 20 seeds, and pace flags those with a pace cause. Rate changes counts the plans that changed a rate, and accept is the share of queued plans the reviewer accepted. The day-59 estimate is the learning agent's elasticity on day 59, as the range over the four hotels of each hotel's mean across the seeds. The true value is 1.5.

Seeds 1 to 20 at a demand bias of 0.9, the template and the oracle in four modes, each against the fixed-rate run at the same bias.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Accept | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| true | template | +1,069 | 3,270 | 731 | -4,911 to +8,596 | 12/20 | 0.50 | 4648 | 3961 | 63 | 1.00 | - |
| true | oracle | +1,590 | 2,744 | 613 | -3,265 to +7,520 | 15/20 | 0.041 | 4596 | 3909 | 47 | 0.60 | - |
| fixed:1.0 | template | -25,072 | 10,013 | 2,239 | -40,139 to -3,904 | 0/20 | <0.001 | 4099 | 3401 | 1448 | 1.00 | - |
| fixed:1.0 | oracle | +321 | 997 | 223 | -910 to +3,863 | 12/20 | 0.50 | 4510 | 3823 | 35 | 0.01 | - |
| learn:1.0 | template | -15,174 | 9,363 | 2,094 | -29,025 to +4,266 | 1/20 | <0.001 | 5420 | 4726 | 798 | 1.00 | 1.40 to 1.51 |
| learn:1.0 | oracle | +251 | 754 | 169 | -910 to +2,458 | 12/20 | 0.50 | 4510 | 3823 | 36 | 0.02 | 1.12 to 1.47 |
| learn:1.0 --cautious | template | -4,122 | 4,936 | 1,104 | -11,914 to +3,973 | 4/20 | 0.012 | 4718 | 4027 | 454 | 1.00 | 1.36 to 1.50 |
| learn:1.0 --cautious | oracle | +613 | 1,942 | 434 | -2,949 to +4,834 | 13/20 | 0.26 | 4567 | 3880 | 54 | 0.05 | 1.19 to 1.47 |

Seeds 1 to 20 at a demand bias of 1.1, the same arms.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Accept | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| true | template | +66,687 | 8,267 | 1,849 | +53,554 to +85,231 | 20/20 | <0.001 | 11132 | 10382 | 343 | 1.00 | - |
| true | oracle | +66,896 | 8,094 | 1,810 | +53,554 to +85,231 | 20/20 | <0.001 | 11130 | 10380 | 340 | 0.99 | - |
| fixed:1.0 | template | +47,451 | 7,025 | 1,571 | +32,357 to +61,978 | 20/20 | <0.001 | 2520 | 1808 | 1524 | 1.00 | - |
| fixed:1.0 | oracle | +66,455 | 9,032 | 2,020 | +50,457 to +80,997 | 20/20 | <0.001 | 7419 | 6690 | 620 | 0.11 | - |
| learn:1.0 | template | +56,213 | 11,852 | 2,650 | +40,081 to +75,047 | 20/20 | <0.001 | 4702 | 3984 | 1007 | 1.00 | 1.43 to 1.50 |
| learn:1.0 | oracle | +64,606 | 9,987 | 2,233 | +48,213 to +83,812 | 20/20 | <0.001 | 7894 | 7162 | 544 | 0.18 | 1.41 to 1.51 |
| learn:1.0 --cautious | template | +60,666 | 10,863 | 2,429 | +37,870 to +78,464 | 20/20 | <0.001 | 7467 | 6729 | 837 | 1.00 | 1.40 to 1.48 |
| learn:1.0 --cautious | oracle | +63,660 | 9,789 | 2,189 | +38,299 to +74,657 | 20/20 | <0.001 | 9517 | 8775 | 536 | 0.27 | 1.38 to 1.46 |

Seeds 1 to 20 at the default demand bias of 1.0, the same arms, as the reference. The template rows repeat the earlier tables.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Accept | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| true | template | +16,164 | 3,166 | 708 | +11,589 to +23,394 | 20/20 | <0.001 | 2009 | 1337 | 106 | 1.00 | - |
| true | oracle | +16,164 | 3,166 | 708 | +11,589 to +23,394 | 20/20 | <0.001 | 2009 | 1337 | 106 | 1.00 | - |
| fixed:1.0 | template | -6,265 | 6,944 | 1,553 | -17,084 to +11,323 | 3/20 | 0.0026 | 1099 | 432 | 766 | 1.00 | - |
| fixed:1.0 | oracle | +13,107 | 3,766 | 842 | +7,752 to +19,404 | 20/20 | <0.001 | 1709 | 1037 | 150 | 0.11 | - |
| learn:1.0 | template | +804 | 8,122 | 1,816 | -14,583 to +14,562 | 11/20 | 0.82 | 1253 | 585 | 510 | 1.00 | 1.42 to 1.49 |
| learn:1.0 | oracle | +13,199 | 4,182 | 935 | +7,752 to +21,079 | 20/20 | <0.001 | 1755 | 1083 | 148 | 0.17 | 1.28 to 1.43 |
| learn:1.0 --cautious | template | +12,527 | 5,265 | 1,177 | +1,658 to +21,698 | 20/20 | <0.001 | 1571 | 902 | 295 | 1.00 | 1.36 to 1.46 |
| learn:1.0 --cautious | oracle | +14,854 | 3,672 | 821 | +10,124 to +23,687 | 20/20 | <0.001 | 1882 | 1211 | 138 | 0.32 | 1.32 to 1.43 |

At 0.9 the agent expects 11% more demand than arrives, so every raise sells fewer rooms than its estimate says. The default mode's gain falls from +$16,164 to +$1,069 a seed, ahead in 12 of 20 seeds, and accepting every plan at a wrong elasticity loses money: -$25,072 at fixed:1.0 and -$15,174 at learn:1.0. In the mismatched modes the oracle accepts 1% to 5% of the plans. At 1.1 the default mode earns +$66,687 a seed, ahead in 20 of 20, because the start rates were set for a smaller market and the dates run ahead of pace. The learning agent's day-59 estimates are 1.40 to 1.51 at 0.9 and 1.43 to 1.50 at 1.1 against 1.42 to 1.49 at 1.0, so the demand-level error mostly lands in the estimator's intercept, as estimate.py intends.

## The competitor reaction

`hotel-market bench --seeds 1 20 --template --react --elasticity true` and the same command with `--elasticity learn:1.0 --cautious`, run on 2026-10-15 on world v2, where the market's own price response is 1.0 by default. With `--react`, each competitor moves half of a hotel's change from its start rate three days after the change takes effect. The shop on a day reads the hotel's rate in force three days earlier from the Books' own log, so nothing is used before it is known. The reaction leaves the fixed-rate run as it is, because that run never changes a rate. The columns are those of the demand-bias tables. Median flags counts the flags with a comp-median cause, own changes those among them that the hotels' own changes caused, and changed twice the stay dates changed twice or more within 14 days.

Seeds 1 to 20 with the reaction on, the template and the oracle in the true mode and the cautious learning mode, each against the fixed-rate run. The oracle is told the reaction and the market elasticity.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Median flags | Own changes | Changed twice | Accept | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| true | template | +35,324 | 3,348 | 749 | +31,088 to +41,841 | 20/20 | <0.001 | 2405 | 1338 | 119 | 898 | 427 | 23 | 1.00 | - |
| true | oracle | +35,324 | 3,348 | 749 | +31,088 to +41,841 | 20/20 | <0.001 | 2405 | 1338 | 119 | 898 | 427 | 23 | 1.00 | - |
| learn:1.0 --cautious | template | +65,216 | 30,310 | 6,778 | +28,426 to +134,913 | 20/20 | <0.001 | 2628 | 983 | 734 | 1490 | 1054 | 535 | 1.00 | 1.29 to 1.47 |
| learn:1.0 --cautious | oracle | +65,216 | 30,310 | 6,778 | +28,426 to +134,913 | 20/20 | <0.001 | 2628 | 983 | 734 | 1490 | 1054 | 535 | 1.00 | 1.29 to 1.47 |

Seed 7 with the reaction on, run on 2026-10-15 on world v2 with `python scripts/median_path.py --seed 7 --react --hotel lifestyle --stays 75 75 --days 16 25`: the lifestyle hotel's rate in force and its comp median on stay date 75, a Saturday, by shop day. On world v2 the downtown hotels change nothing on the convention nights at seed 7, so the first accepted plan is the lifestyle hotel's day-18 raise of 10%, in force from day 19, and a second raise on day 20, in force from day 21. The competitors move half of each three days later, on days 22 and 24, while the daily shop noise moves the median every day.

| Shop day | Stay 75 rate | Median |
| ---: | ---: | ---: |
| 16 | 240.00 | 241.81 |
| 17 | 240.00 | 237.22 |
| 18 | 240.00 | 235.93 |
| 19 | 264.00 | 238.68 |
| 20 | 264.00 | 241.79 |
| 21 | 290.40 | 237.79 |
| 22 | 290.40 | 253.48 |
| 23 | 290.40 | 249.57 |
| 24 | 290.40 | 264.87 |
| 25 | 290.40 | 265.08 |

With the reaction on, the default mode earns +$35,324 a seed against +$16,164 without it, 2.2 times its gain, and changes 119 rates against 106. The simulator's bookings follow the hotel's rate against the comp median, and since world v2 the market's demand also falls with the median's level, so a raise the competitors half follow still costs the hotel few rooms. The moved median raises a new flag on the same dates, the hold lifts for it, and the agent raises again. In the true mode 427 of the 898 comp-median flags follow the hotels' own changes, and 23 stay dates change twice within 14 days. The cautious learning arm starts from an elasticity of 1.0, so it expects a raise to cost less than it does. It changes 734 rates, 535 of them twice within 14 days, and earns +$65,216 a seed. The oracle, told the reaction and the market elasticity, accepts 100% of that arm's plans and earns +$65,216.

## The market-level price response

`hotel-market bench --seeds 1 20 --template --react --market-elasticity E --elasticity true` and the same command with `--elasticity learn:1.0 --cautious`, run on 2026-10-15 on world v2 at E = 0.0 and 0.5; the rows at 1.0 are the reaction tables above, because 1.0 is the customer file's default since world v2. The option multiplies expected demand by the comp median as shopped that day over the comp set's starting level, the median of its base rates, to the power of minus E. The agent is told E and every plan record carries it. The oracle re-scores each plan with E and with the share of a change the competitors follow, so it is the ceiling again over the agent's own candidates, with the reaction scored as immediate where the simulator applies it three days later. The columns are those of the reaction table, and oracle gap is the oracle arm's mean change minus accept-all's.

Seeds 1 to 20 with the reaction on at a market elasticity of 0.0, 0.5 and 1.0, the template and the oracle in the true mode and the cautious learning mode, each against the fixed-rate run.

| Market elasticity | Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Median flags | Own changes | Changed twice | Oracle gap | Day-59 estimate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | true | template | +87,519 | 7,486 | 1,674 | +75,032 to +99,751 | 20/20 | <0.001 | 236 | 968 | 500 | 95 | +$0 | - |
| 0.0 | true | oracle | +87,519 | 7,486 | 1,674 | +75,032 to +99,751 | 20/20 | <0.001 | 236 | 968 | 500 | 95 | - | - |
| 0.0 | learn:1.0 --cautious | template | +224,222 | 122,725 | 27,442 | +76,005 to +509,033 | 20/20 | <0.001 | 963 | 1634 | 1208 | 742 | +$80 | 1.31 to 1.42 |
| 0.0 | learn:1.0 --cautious | oracle | +224,302 | 122,623 | 27,419 | +77,612 to +509,033 | 20/20 | <0.001 | 962 | 1634 | 1208 | 742 | - | 1.31 to 1.42 |
| 0.5 | true | template | +58,275 | 5,849 | 1,308 | +46,958 to +68,764 | 20/20 | <0.001 | 164 | 925 | 456 | 46 | +$0 | - |
| 0.5 | true | oracle | +58,275 | 5,849 | 1,308 | +46,958 to +68,764 | 20/20 | <0.001 | 164 | 925 | 456 | 46 | - | - |
| 0.5 | learn:1.0 --cautious | template | +141,469 | 78,588 | 17,573 | +46,172 to +318,833 | 20/20 | <0.001 | 822 | 1566 | 1138 | 609 | +$0 | 1.31 to 1.46 |
| 0.5 | learn:1.0 --cautious | oracle | +141,469 | 78,588 | 17,573 | +46,172 to +318,833 | 20/20 | <0.001 | 822 | 1566 | 1138 | 609 | - | 1.31 to 1.46 |
| 1.0 | true | template | +35,324 | 3,348 | 749 | +31,088 to +41,841 | 20/20 | <0.001 | 119 | 898 | 427 | 23 | +$0 | - |
| 1.0 | true | oracle | +35,324 | 3,348 | 749 | +31,088 to +41,841 | 20/20 | <0.001 | 119 | 898 | 427 | 23 | - | - |
| 1.0 | learn:1.0 --cautious | template | +65,216 | 30,310 | 6,778 | +28,426 to +134,913 | 20/20 | <0.001 | 734 | 1490 | 1054 | 535 | +$0 | 1.29 to 1.47 |
| 1.0 | learn:1.0 --cautious | oracle | +65,216 | 30,310 | 6,778 | +28,426 to +134,913 | 20/20 | <0.001 | 734 | 1490 | 1054 | 535 | - | 1.29 to 1.47 |

Seed 7 at a market elasticity of 0.0, 0.5 and 1.0 with no reaction, run on 2026-10-15 on world v2 with `python scripts/median_path.py --seed 7 --hotel full-service --stays 37 39 --days 29 39 --market-elasticity E` (1.0 is the default): the full-service hotel's rate, its comp median on the day before and the day of the day-30 cut, and the rooms it sold on the cut's stay dates, 37 to 39, by day 39.

| Market elasticity | Stay date | Rate | Median before the cut | Median after | Rooms sold by day 39 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 | 37 | 190.00 | 189.56 | 168.64 | 196 |
| 0.0 | 38 | 190.00 | 189.04 | 173.41 | 182 |
| 0.0 | 39 | 190.00 | 189.22 | 169.93 | 165 |
| 0.5 | 37 | 190.00 | 189.56 | 168.64 | 198 |
| 0.5 | 38 | 190.00 | 189.04 | 173.41 | 183 |
| 0.5 | 39 | 190.00 | 189.22 | 169.93 | 168 |
| 1.0 | 37 | 190.00 | 189.56 | 168.64 | 199 |
| 1.0 | 38 | 190.00 | 189.04 | 173.41 | 184 |
| 1.0 | 39 | 190.00 | 189.22 | 169.93 | 170 |

Since world v2 the market has a price response of its own, 1.0 by default, so a raise that every hotel matches now costs rooms. In the reacting market the true mode earns +$87,519 a seed at a market elasticity of 0.0, +$58,275 at 0.5 and +$35,324 at 1.0, the default, against +$16,164 with no reaction. Its rate changes fall from 236 to 164 and 119, and the dates changed twice within 14 days from 95 to 46 and 23. The cautious learning arm earns +$224,222, +$141,469 and +$65,216. Two things show in the table. The first is a price effect: competitors that follow half of a raise lower the hotel's effective own-price elasticity below 1.5, because its rate against the median moves only half as far as its rate, so a raise pays more in that world than against competitors that never move, and the market term takes part of that back. The second is the loop: the competitors' answer to the hotel's own change arrives three days later, the detector reads it as news, the hold lifts, and the agent raises again on the same dates. FRK-09 is the open question whether a comp move that follows our own change should count as a flag cause at all. On the day-30 cut the cheaper market draws more demand as the elasticity rises: by day 39 the full-service hotel sells 196, 182, 165 rooms on stays 37 to 39 at 0.0, 198, 183, 168 at 0.5 and 199, 184, 170 at 1.0.

## The air schedule's filings

`hotel-market --seeds 1 20 --template --churn` and `hotel-market --seeds 1 20 --template`, run on 2026-10-15 on world v2, then `hotel-market --seeds 1 20 --template --scenario upgauge`. With `--churn` the airline files weekly revisions drawn from the seed on days 7 to 56: an equipment swap of two to three weeks between codes within 24 seats a flight of each other, and a departure-time change for a fortnight. A day then moves at most 96 seats, 77 passengers at the mature load factor, against a threshold of 5%. The scenario option replaces the default's two filings with another list. The upgauge scenario files an upgauge of the MSP route to 738s on day 15 and a cut of the ORD route to two daily flights on day 35. Filings counts the days the airline filed something through day 59, summed over the seeds, and seat flags the flags with a seat cause.

Seeds 1 to 20 with the churn, the default and the upgauge scenario, the template in the true mode, each against the fixed-rate run.

| Arm | Mean change | SD | SE | Range | Ahead | p | Filings | Seat flags | Rate changes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| default | +16,164 | 3,166 | 708 | +11,589 to +23,394 | 20/20 | <0.001 | 40 | 199 | 106 |
| default with the churn | +17,848 | 3,628 | 811 | +13,161 to +25,286 | 20/20 | <0.001 | 200 | 199 | 108 |
| upgauge | +5,913 | 4,472 | 1,000 | -1,123 to +12,574 | 17/20 | 0.0026 | 40 | 201 | 84 |

The churn adds 160 filing days over the 20 seeds and raises 199 seat flags against 199 without it. That is by construction, because every revision stays under the threshold, so the count proves nothing. The finding is that a filing as such never reaches the detector, which keys on the day-over-day passenger revision. The test test_a_detector_that_fires_on_any_revision_is_caught_by_the_churn pins it by holding the seat flags to the same two days with the churn as without. The block swaps move seats, and so passengers, for two to three weeks at a time, so the gain moves from +$16,164 to +$17,848 a seed and the rate changes from 106 to 108. The churn therefore reached the agent's decisions through the passenger change in its demand forecast, and none of it came through the detector. That is the designed path, because DEC-04 keeps the change for the forecast and the revision for the flag. The upgauge scenario earns +$5,913, ahead in 17 of 20 seeds, because its two filings move fewer seats than the default's new flights and suspension, and an upgauge of a route that flew before the run keeps its mature load factor.

## The intercept fed back

`hotel-market bench --seeds 1 20 --template --demand-bias B --elasticity learn:1.0 --level` and the same command with `--level --cautious`, at B = 0.9, 1.0 and 1.1, run on 2026-10-15 on world v2, then the same two arms and a plain `learn:1.0` with `--react --market-elasticity 0.5`. With `--level` a learning agent scales its demand forecast, the pace baseline included, by the demand level its fit found, which is exp(intercept), once the fit has 500 observations and clamped to 0.5 to 2.0 as the elasticity is clamped. The plain learn rows repeat the demand-bias tables and the market table. Day-59 level is the factor each hotel scaled its forecast by on day 59, as the range over the hotels of each hotel's mean across the seeds.

Seeds 1 to 20 at a demand bias of 0.9, the learning agent with and without the fitted level fed back, the template and the oracle, each against the fixed-rate run at the same bias.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Accept | Day-59 estimate | Day-59 level |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| learn:1.0 | template | -15,174 | 9,363 | 2,094 | -29,025 to +4,266 | 1/20 | <0.001 | 798 | 1.00 | 1.40 to 1.51 | - |
| learn:1.0 | oracle | +251 | 754 | 169 | -910 to +2,458 | 12/20 | 0.50 | 36 | 0.02 | 1.12 to 1.47 | - |
| learn:1.0 --cautious | template | -4,122 | 4,936 | 1,104 | -11,914 to +3,973 | 4/20 | 0.012 | 454 | 1.00 | 1.36 to 1.50 | - |
| learn:1.0 --cautious | oracle | +613 | 1,942 | 434 | -2,949 to +4,834 | 13/20 | 0.26 | 54 | 0.05 | 1.19 to 1.47 | - |
| learn:1.0 --level | template | -13,700 | 9,346 | 2,090 | -29,760 to +3,006 | 1/20 | <0.001 | 583 | 1.00 | 1.39 to 1.50 | 0.90 to 0.90 |
| learn:1.0 --level | oracle | +664 | 1,187 | 265 | -440 to +4,881 | 12/20 | 0.50 | 30 | 0.02 | 1.04 to 1.47 | 0.90 to 0.90 |
| learn:1.0 --level --cautious | template | -3,534 | 4,645 | 1,039 | -12,811 to +4,602 | 4/20 | 0.012 | 287 | 1.00 | 1.28 to 1.51 | 0.90 to 0.90 |
| learn:1.0 --level --cautious | oracle | +999 | 1,489 | 333 | -696 to +4,881 | 13/20 | 0.26 | 34 | 0.06 | 1.03 to 1.47 | 0.90 to 0.90 |

Seeds 1 to 20 at the default demand bias of 1.0, the same arms.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Accept | Day-59 estimate | Day-59 level |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| learn:1.0 | template | +804 | 8,122 | 1,816 | -14,583 to +14,562 | 11/20 | 0.82 | 510 | 1.00 | 1.42 to 1.49 | - |
| learn:1.0 | oracle | +13,199 | 4,182 | 935 | +7,752 to +21,079 | 20/20 | <0.001 | 148 | 0.17 | 1.28 to 1.43 | - |
| learn:1.0 --cautious | template | +12,527 | 5,265 | 1,177 | +1,658 to +21,698 | 20/20 | <0.001 | 295 | 1.00 | 1.36 to 1.46 | - |
| learn:1.0 --cautious | oracle | +14,854 | 3,672 | 821 | +10,124 to +23,687 | 20/20 | <0.001 | 138 | 0.32 | 1.32 to 1.43 | - |
| learn:1.0 --level | template | +825 | 8,113 | 1,814 | -14,618 to +14,687 | 10/20 | 1.0 | 509 | 1.00 | 1.41 to 1.50 | 0.99 to 1.00 |
| learn:1.0 --level | oracle | +13,171 | 4,081 | 913 | +7,944 to +21,415 | 20/20 | <0.001 | 142 | 0.16 | 1.29 to 1.43 | 0.99 to 1.00 |
| learn:1.0 --level --cautious | template | +12,346 | 5,025 | 1,124 | +531 to +18,556 | 20/20 | <0.001 | 309 | 1.00 | 1.35 to 1.49 | 1.00 to 1.00 |
| learn:1.0 --level --cautious | oracle | +14,352 | 3,885 | 869 | +4,832 to +20,796 | 20/20 | <0.001 | 144 | 0.32 | 1.32 to 1.44 | 1.00 to 1.00 |

Seeds 1 to 20 at a demand bias of 1.1, the same arms.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Accept | Day-59 estimate | Day-59 level |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| learn:1.0 | template | +56,213 | 11,852 | 2,650 | +40,081 to +75,047 | 20/20 | <0.001 | 1007 | 1.00 | 1.43 to 1.50 | - |
| learn:1.0 | oracle | +64,606 | 9,987 | 2,233 | +48,213 to +83,812 | 20/20 | <0.001 | 544 | 0.18 | 1.41 to 1.51 | - |
| learn:1.0 --cautious | template | +60,666 | 10,863 | 2,429 | +37,870 to +78,464 | 20/20 | <0.001 | 837 | 1.00 | 1.40 to 1.48 | - |
| learn:1.0 --cautious | oracle | +63,660 | 9,789 | 2,189 | +38,299 to +74,657 | 20/20 | <0.001 | 536 | 0.27 | 1.38 to 1.46 | - |
| learn:1.0 --level | template | +55,518 | 11,696 | 2,615 | +37,533 to +78,758 | 20/20 | <0.001 | 683 | 1.00 | 1.41 to 1.49 | 1.09 to 1.10 |
| learn:1.0 --level | oracle | +59,123 | 9,713 | 2,172 | +45,511 to +80,151 | 20/20 | <0.001 | 401 | 0.35 | 1.41 to 1.51 | 1.09 to 1.10 |
| learn:1.0 --level --cautious | template | +60,005 | 10,175 | 2,275 | +37,465 to +78,782 | 20/20 | <0.001 | 491 | 1.00 | 1.39 to 1.50 | 1.09 to 1.10 |
| learn:1.0 --level --cautious | oracle | +61,929 | 8,796 | 1,967 | +47,785 to +78,299 | 20/20 | <0.001 | 361 | 0.55 | 1.38 to 1.50 | 1.09 to 1.10 |

Seeds 1 to 20 with the reaction on at a market elasticity of 0.5, the same arms.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Accept | Day-59 estimate | Day-59 level |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| learn:1.0 | template | +302,095 | 49,932 | 11,165 | +192,044 to +365,140 | 20/20 | <0.001 | 1959 | 1.00 | 1.39 to 1.50 | - |
| learn:1.0 | oracle | +317,039 | 41,918 | 9,373 | +246,976 to +377,999 | 20/20 | <0.001 | 1877 | 0.96 | 1.39 to 1.52 | - |
| learn:1.0 --cautious | template | +141,469 | 78,588 | 17,573 | +46,172 to +318,833 | 20/20 | <0.001 | 822 | 1.00 | 1.31 to 1.46 | - |
| learn:1.0 --cautious | oracle | +141,469 | 78,588 | 17,573 | +46,172 to +318,833 | 20/20 | <0.001 | 822 | 1.00 | 1.31 to 1.46 | - |
| learn:1.0 --level | template | +304,114 | 50,279 | 11,243 | +193,679 to +368,317 | 20/20 | <0.001 | 1993 | 1.00 | 1.39 to 1.50 | 0.99 to 1.00 |
| learn:1.0 --level | oracle | +318,944 | 41,886 | 9,366 | +248,285 to +378,733 | 20/20 | <0.001 | 1907 | 0.96 | 1.38 to 1.52 | 0.99 to 1.00 |
| learn:1.0 --level --cautious | template | +139,141 | 78,512 | 17,556 | +34,930 to +318,605 | 20/20 | <0.001 | 859 | 1.00 | 1.29 to 1.47 | 1.00 to 1.00 |
| learn:1.0 --level --cautious | oracle | +139,300 | 78,334 | 17,516 | +34,930 to +318,605 | 20/20 | <0.001 | 858 | 1.00 | 1.29 to 1.47 | 1.00 to 1.00 |

The level is learned at once and closely: by day 59 the factor is 0.90 to 0.90 at a bias of 0.9, 1.09 to 1.10 at 1.1, 0.99 to 1.00 at 1.0 and 0.99 to 1.00 in the reacting market. At 0.9 it cuts the flags from 5420 to 1538 over the 20 seeds, because the pace baseline no longer expects rooms that never come. Accepting every plan there earns -$13,700 a seed with the level against -$15,174 without it, and the cautious arm -$3,534 against -$4,122; the true mode earns +$1,069 there, so the opportunity in a market a tenth smaller is small for every arm. At 1.0 the level arms earn +$825 and +$12,346 against +$804 and +$12,527 without it. At 1.1 they earn +$55,518 and +$60,005 against +$56,213 and +$60,666: the corrected pace baseline removes raises on dates the start rates underprice, and the agent acts only on a flag, so a market that is simply larger raises none, the gap FRK-11 holds. With the reaction on at 0.5 the plain learner earns +$302,095 a seed from 1959 rate changes, the level arms +$304,114 and +$139,141, and the cautious arm without the level +$141,469; the ratchet FRK-09 holds is at its fullest in the plain learner.

## The rule-based control

`hotel-market bench --seeds 1 20 --template --policy P --demand-bias B --elasticity true` at B = 0.9, 1.0 and 1.1, and the same command with `--react --market-elasticity 0.5` in place of the bias, for P = pace, rules and never-cut, run on 2026-10-15 on world v2. The pace policy raises 5% on every stay date that runs ahead of pace by the detect threshold and lowers 5% on every one behind it, with the same hold, floor and ceiling as the agent, and no estimate and no model. The rules policy keeps those steps and adds the rules the agent's first design retired: it raises 5% on an event flag's dates and on a seat-up flag's dates, and lowers 5% on a seat-cut flag's dates. The never-cut policy keeps the rules policy's raises and never lowers, because in this market the start rate is already the best rate on a night that will not sell out, so every cut the rules policy makes loses money. Each policy runs beside each arm on the same seed, and the table gives each arm's gain against frozen rates next to its gain against the policy. Ahead counts the seeds where the arm beat the policy, and changes the stay dates the policy changed over the 20 seeds.

Seeds 1 to 20 in the true mode against the pace, the rules and the never-cut policies, under each demand bias and in the reacting market, the template and the oracle, each against the fixed-rate run and against the policy.

| Policy | World | Reviewer | Against frozen rates | Against the policy | SD | SE | Ahead of it | p | The policy against frozen rates | SD | SE | Policy changes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pace | bias 0.9 | template | +1,069 | +2,050 | 3,795 | 849 | 13/20 | 0.26 | -981 | 1,425 | 319 | 621 |
| pace | bias 0.9 | oracle | +1,590 | +2,571 | 3,351 | 749 | 14/20 | 0.12 | -981 | 1,425 | 319 | 621 |
| pace | bias 1.0 | template | +16,164 | +14,732 | 2,972 | 665 | 20/20 | <0.001 | +1,432 | 1,334 | 298 | 348 |
| pace | bias 1.0 | oracle | +16,164 | +14,732 | 2,972 | 665 | 20/20 | <0.001 | +1,432 | 1,334 | 298 | 348 |
| pace | bias 1.1 | template | +66,687 | +48,017 | 7,050 | 1,576 | 20/20 | <0.001 | +18,670 | 6,081 | 1,360 | 2361 |
| pace | bias 1.1 | oracle | +66,896 | +48,226 | 7,089 | 1,585 | 20/20 | <0.001 | +18,670 | 6,081 | 1,360 | 2361 |
| pace | react, market 0.5 | template | +58,275 | +52,931 | 6,024 | 1,347 | 20/20 | <0.001 | +5,344 | 1,651 | 369 | 443 |
| pace | react, market 0.5 | oracle | +58,275 | +52,931 | 6,024 | 1,347 | 20/20 | <0.001 | +5,344 | 1,651 | 369 | 443 |
| rules | bias 0.9 | template | +1,069 | +3,246 | 4,589 | 1,026 | 15/20 | 0.041 | -2,177 | 4,912 | 1,098 | 7313 |
| rules | bias 0.9 | oracle | +1,590 | +3,766 | 4,919 | 1,100 | 15/20 | 0.041 | -2,177 | 4,912 | 1,098 | 7313 |
| rules | bias 1.0 | template | +16,164 | +7,156 | 5,021 | 1,123 | 19/20 | <0.001 | +9,008 | 4,849 | 1,084 | 6857 |
| rules | bias 1.0 | oracle | +16,164 | +7,156 | 5,021 | 1,123 | 19/20 | <0.001 | +9,008 | 4,849 | 1,084 | 6857 |
| rules | bias 1.1 | template | +66,687 | +21,759 | 6,156 | 1,377 | 20/20 | <0.001 | +44,928 | 6,727 | 1,504 | 8315 |
| rules | bias 1.1 | oracle | +66,896 | +21,968 | 6,246 | 1,397 | 20/20 | <0.001 | +44,928 | 6,727 | 1,504 | 8315 |
| rules | react, market 0.5 | template | +58,275 | -24,998 | 7,415 | 1,658 | 0/20 | <0.001 | +83,273 | 5,607 | 1,254 | 6968 |
| rules | react, market 0.5 | oracle | +58,275 | -24,998 | 7,415 | 1,658 | 0/20 | <0.001 | +83,273 | 5,607 | 1,254 | 6968 |
| never-cut | bias 0.9 | template | +1,069 | +2,916 | 4,646 | 1,039 | 14/20 | 0.12 | -1,847 | 6,540 | 1,462 | 4981 |
| never-cut | bias 0.9 | oracle | +1,590 | +3,436 | 5,557 | 1,243 | 14/20 | 0.12 | -1,847 | 6,540 | 1,462 | 4981 |
| never-cut | bias 1.0 | template | +16,164 | +5,696 | 5,852 | 1,308 | 18/20 | <0.001 | +10,468 | 5,902 | 1,320 | 5153 |
| never-cut | bias 1.0 | oracle | +16,164 | +5,696 | 5,852 | 1,308 | 18/20 | <0.001 | +10,468 | 5,902 | 1,320 | 5153 |
| never-cut | bias 1.1 | template | +66,687 | +14,976 | 6,003 | 1,342 | 20/20 | <0.001 | +51,711 | 7,258 | 1,623 | 6645 |
| never-cut | bias 1.1 | oracle | +66,896 | +15,185 | 6,100 | 1,364 | 20/20 | <0.001 | +51,711 | 7,258 | 1,623 | 6645 |
| never-cut | react, market 0.5 | template | +58,275 | -54,602 | 7,202 | 1,610 | 0/20 | <0.001 | +112,877 | 6,235 | 1,394 | 5266 |
| never-cut | react, market 0.5 | oracle | +58,275 | -54,602 | 7,202 | 1,610 | 0/20 | <0.001 | +112,877 | 6,235 | 1,394 | 5266 |

A fixed-rate run is a control that never moves, so every gain against it includes what a hotel's own rules would have earned anyway. A policy that acts on the same flags is the fairer yardstick, and the never-cut policy is the one the README quotes first, with the rules policy after it, because the pace policy skips every flag that is not a pace flag. In the default world on 2026-10-15 the never-cut policy earns +$10,468 a seed over frozen rates from 5153 stay dates changed, and the agent's +$16,164 against frozen rates is +$5,696 against it, ahead in 18/20, p <0.001. The rules policy earns +$9,008 from 6857 changes, and the agent is +$7,156 against it, ahead in 19/20. The pace policy earns +$1,432 from the pace flags alone, and the agent is +$14,732 against it. At a bias of 0.9 the never-cut policy earns -$1,847 and the agent is +$2,916 against it; at 1.1 it earns +$51,711 from 6645 changes, because a market a tenth larger runs ahead of pace almost everywhere, and the agent's +$66,687 is +$14,976 against it. In the reacting market at a market elasticity of 0.5 the never-cut policy earns +$112,877 from 5266 changes and the rules policy +$83,273; the agent's +$58,275 is -$54,602 against the first and -$24,998 against the second, because a policy that raises on every comp move that followed its own raise rides the ratchet further than the agent. All three policies are anomaly-driven as the agent is: they act only on a flag, so they share the blind spot FRK-11 records, and a market that is simply larger raises nothing for any of them.

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

`python scripts/no_comp_raise.py --seeds 1 20`, run on 2026-10-15 on world v2. The script runs the template sweep as shipped and then again with the convention's competitor raise set to 0.0 and its demand uplift left at 35%, and it puts the shipped event back afterwards. A convention plan is an accepted plan whose causes include the event's announcement, and its gain is the contribution change on the stay dates it changed. The last column counts the convention nights, four at each of the two downtown hotels, that sold out at fixed rates over the 20 seeds.

Seeds 1 to 20 with the convention's competitor raise as shipped and at zero, the template in the true mode, each against the fixed-rate run, run on 2026-10-15 on world v2.

| Competitors' raise | Mean change a seed | Range | Ahead | Convention plans accepted | Gain on their stay dates a seed | Convention nights sold out at fixed rates |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 15% | +$16,164 | +$11,589 to +$23,394 | 20 of 20 | 14 | +$614 | 14 of 160 |
| 0% | +$15,611 | +$11,019 to +$22,581 | 20 of 20 | 2 | +$100 | 4 of 160 |

With the raise at zero the mean moves from +$16,164 to +$15,611 a seed. The convention plans, 14 over the 20 seeds with the raise and 2 without it, earn +$614 and +$100 a seed on their stay dates, and the downtown hotels sell out 14 of 160 convention nights at fixed rates with the raise and 4 of 160 without it. On world v2 the two downtown hotels hold most of their convention business as group blocks before the announcement, and the market's own price response takes back part of what the competitors' raise used to give, so the convention's share of the headline is small either way and the raise moves it little.

## In a revenue manager's measures

`python scripts/measures.py --seeds 1 20`, run on 2026-10-15 on world v2. Each measure is per hotel over stay dates 0 to 149 and is the mean over the 20 seeds, with the fixed-rate run beside the agent run. The second table divides the 20-seed totals by 20: the room nights the agent run gave up, their share of the hotel's capacity, the change in room revenue, the room cost saved on those nights and the contribution gained. The last column is the cost per occupied room, as a share of the start rate, at which the hotel's gain would be zero. The gain is positive above that share, and a hotel whose room revenue rose gains at any cost, so its share prints below zero.

Seeds 1 to 20 in a revenue manager's measures: occupancy, average rate, RevPAR and the share of sold-out nights per hotel, the fixed-rate run and the agent run, each the mean over the seeds, run on 2026-10-15 on world v2.

| Hotel | Occupancy, fixed | Occupancy, agent | Average rate, fixed | Average rate, agent | RevPAR, fixed | RevPAR, agent | Sold-out nights, fixed | Sold-out nights, agent |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel | 76.9% | 76.8% | $220.00 | $220.03 | $169.07 | $169.07 | 0.4% | 0.2% |
| Downtown full-service hotel | 76.5% | 76.5% | $190.00 | $190.06 | $145.37 | $145.36 | 0.7% | 0.5% |
| Lifestyle hotel | 77.0% | 76.1% | $240.00 | $242.50 | $184.76 | $184.44 | 10.2% | 7.1% |
| Airport hotel | 88.9% | 86.1% | $140.00 | $143.44 | $124.50 | $123.53 | 20.0% | 12.0% |

Seeds 1 to 20: what the agent run gave up and saved a seed, per hotel, and the cost share at which the gain is zero, run on 2026-10-15 on world v2.

| Hotel | Room nights given up a seed | Share of capacity | Room revenue change a seed | Room cost saved a seed | Contribution gained a seed | Cost share at which the gain is zero |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel | 5 | 0.01% | +$163 | +$392 | +$556 | -13.9% |
| Downtown full-service hotel | 11 | 0.03% | -$368 | +$674 | +$306 | 18.2% |
| Lifestyle hotel | 166 | 0.92% | -$5,628 | +$13,300 | +$7,672 | 14.1% |
| Airport hotel | 632 | 2.81% | -$21,851 | +$29,482 | +$7,630 | 24.7% |

The agent gives up rooms at every hotel, 5, 11, 166 and 632 room nights a seed by hotel, and RevPAR is flat at the two downtown hotels and lower at the other two, so the gain is room cost not paid rather than revenue earned. The airport hotel's gain holds only while the cost of an occupied room is above 24.7% of the rate, the lifestyle hotel's above 14.1% and the full-service hotel's above 18.2%, while the convention hotel gains at any cost because its room revenue rose.
