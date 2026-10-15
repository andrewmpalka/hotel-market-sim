# Results

Seeds 1 to 20 in the default mode: the agent run against the fixed-rate run, stay dates 0 to 149, run on 2026-10-15 on world v2 with `hotel-market --seeds 1 20 --template`. The reasons are the template's, and candidates are scored on contribution with the simulator's elasticity. The template is a stand-in that answers in the model's place when there is no key; it says yes to every plan and writes a reason from the entry's own figures. The last two rows are the standard deviation across the seeds and the standard error of the mean.

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

Accepted plans at the two downtown hotels by seed, read from the same sweep's decisions files, run on 2026-10-15 on world v2. It is a lookup for the walkthrough, not a result: a seed with no such plan reads none, and seed 7 is one of the three. The day-10 plans are the convention's, raised on the day it is announced; the others are pace plans on a single stay date.

| Seed | Day | Hotel | Stay dates | Cause | Plan |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 2 | 58 | Downtown convention hotel | 106 | ahead of pace | raise 5% on Tue |
| 3 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 4 | - | none | - | - | - |
| 5 | 10 | Downtown convention hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 6 | 39 | Downtown full-service hotel | 45 | ahead of pace | raise 10% on Thu |
| 7 | - | none | - | - | - |
| 8 | 10 | Downtown convention hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 8 | 54 | Downtown full-service hotel | 99 | ahead of pace | raise 10% on Tue |
| 9 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 10 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 11 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 5% on Thu, Sat |
| 11 | 51 | Downtown convention hotel | 114 | ahead of pace | raise 5% on Wed |
| 12 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 5% on Sat; raise 10% on Thu |
| 13 | 10 | Downtown convention hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 14 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 14 | 54 | Downtown convention hotel | 120 | ahead of pace | raise 10% on Tue |
| 15 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 16 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 5% on Fri; raise 10% on Thu |
| 17 | 10 | Downtown full-service hotel | 45 to 48 | comp median up, event announced | raise 10% on Thu |
| 17 | 42 | Downtown convention hotel | 45 | ahead of pace | raise 10% on Thu |
| 18 | 20 | Downtown convention hotel | 85 | ahead of pace, seats up | raise 5% on Tue |
| 19 | - | none | - | - | - |
| 20 | 10 | Downtown convention hotel | 45 to 48 | comp median up, event announced | raise 5% on Thu |
| 20 | 20 | Downtown full-service hotel | 72 | ahead of pace, seats up | raise 10% on Wed |
| 20 | 36 | Downtown convention hotel | 45 | ahead of pace | raise 10% on Thu |

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

Four live runs of seed 7 on world v1 (commit b178e7b) in the default mode with claude-opus-5-5, one per request format. Each made seven calls and said yes to every plan. The last was the recorded run under tests/fixtures/live_seed7/ until the world v2 run below replaced it. Cost is at list prices of $4 and $20 per million tokens.

| Request format | Input tokens | Cost | Kept |
| --- | ---: | ---: | --- |
| Bare numbers | 20,329 | $0.12 | no |
| A signed display string next to each raw value | 37,107 | $0.18 | no |
| Display strings alone, each range as a named pair | 24,219 | $0.14 | no |
| Display strings alone, each range as one phrase | 21,148 | $0.12 | until world v2 |

The recorded live run of seed 7, made on 2026-10-15 on world v2 with `make live-audit SEED=7` and recorded with `python scripts/live_audit.py --seed 7 --record-fixture`. The model chose the template's option on every entry, so the contribution change is the template run's. The audit lists five figures in the reasons that it cannot match to a request phrase. Three are per-day gains that the request holds as "$2,780 more than holding" and the reason wrote as "$2,780 on Monday". Two are the day and the rooms of an earlier change: the request's line "day 18: raised 10% to $264 on Sat 75; since then 2 rooms booked against 1 expected" came back as "Since our day 18 raise to $264, 2 rooms have booked against 1 expected", although the prompt says to cite these lines as written.

| Measure | Value |
| --- | ---: |
| Model calls | 4, on days 18, 20 and 23 |
| Plans accepted | 6 of 6 |
| Input tokens | 15,469 (1,936 to 7,474 a call) |
| Output tokens | 1,034 (131 to 493 a call) |
| Time in the model | 18 s (3.0 to 5.7 s a call, median 4.5 s) |
| Whole run, both simulations | 19 s |
| Cost at list prices | $0.08 |
| Prompt cache read or written | none |
| Contribution change | +$19,796, the template run's |
| Figures the audit cannot match to a request phrase | 5 |
| Sentences without a request figure | 4 |

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

The suite on each Python version. The run of 2026-10-12 came from a fresh virtual environment with the slow tests included and passed 235 tests on both versions. The counts below were refreshed on 2026-10-15 on world v2 from the plain suite, with numpy 2.5.4, pandas 3.0.6 and duckdb 1.5.6 on both, and anthropic 1.13.0 on 3.12.6 and 1.14.0 on 3.13.7. The nine slow tests are skipped, and so are the five demo-page tests wherever the environment has the dev extra alone, which is what `make setup` installs: the fresh-copy row ran `make setup` and then `make test` in a copy of the repository with its history and without .venv, and the five ran once `make demo` had installed streamlit. `make test-all` on 3.12.6, the nine slow tests included, gave 386 passed on 2026-10-15, after the live run of seed 7 was re-recorded on world v2.

| Python | Command | Result |
| --- | --- | --- |
| 3.12.6 | `python -m pytest` | 377 passed, 9 skipped |
| 3.12.6 | `make setup` then `make test` in a fresh copy, the dev extra alone | 372 passed, 14 skipped |
| 3.13.7 | `python -m pytest` | 372 passed, 14 skipped |

The live answers under cache/ are the only copy of about $86 of model calls on each world, so they are archived as a dated tar outside the repository, with the archive's sha256 and a per-file list beside it. The archive of 2026-10-15 is cache-2026-10-15-0406.tar.gz under ~/backups/hotel-market-sim, 8,203 files with the sha256 ab3b5f7a6f49e81a81716ed9baa626efee668f79be5328ebd5d77addb6c3d9c6, and it restores with `tar -xzf` from the repository root. The world v2 benchmark of 2026-10-15 is archived the same way as cache-v2-2026-10-15-1040.tar.gz, 8,146 files with the sha256 f13dbef4f14d49638b4c5e34dc17c18501effd3e9628a5d8a43e5ee4496ebda7, and the world v1 cache it replaced sits beside it as cache-v1-2026-10-15.

The container image on each Python version, built on 2026-10-12. Docker 28.4.0 ran on an aarch64 Ubuntu VM with 4 CPUs and 4 GiB. Each image ran the suite from its copy of the repository, and the 3.12 image ran seed 7 with the template. pandas 3.0.6, duckdb 1.5.6 and anthropic 1.13.0 were installed on every version, and every dependency came as a wheel, 3.14 included. The images were not rebuilt; the native plain suite has since grown to 357 passed and 9 skipped.

| Python | numpy | Build | Image | Tests | Suite time | Seed-7 run | decisions.jsonl |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| 3.11.15 | 2.4.6 | 24 s | 615 MB | 278 passed, 3 skipped | 45 s | | |
| 3.12.13 | 2.5.4 | 24 s | 592 MB | 278 passed, 3 skipped | 45 s | 1.6 s | matched the native run on world v1; on world v2 the native checksum is 263387b3 on this machine's numpy 2.5.4 and pandas 3.0.6, and a Linux run on numpy 2.5.3 and pandas 3.0.5 gave 8faafad0 with the same decisions; it was 19b766b8 on world v1 once the plan records gained two fields, and 8ce570ea when the image ran |
| 3.14.8 | 2.5.4 | 24 s | 600 MB | 278 passed, 3 skipped | 45 s | | |

## The benchmark of the reviewers


`hotel-market bench --seeds 1 20`, run on 2026-10-15 on world v2. For every seed, the command makes the fixed-rate run once. It then makes one agent run per elasticity mode and reviewer. The reviewers are the template, the oracle reviewer, claude-opus-5-5, claude-sonnet-5-5 and claude-haiku-5-5, and each arm has its own cache folder. The live calls were made first, one process per model and seed range: seeds 1 to 3, then seeds 4 to 20 in six ranges of up to three seeds, sixteen processes at a time. The command that printed the tables read every folder's cache and made no call. The fixed modes' 4,006 calls cost $37.19 at list prices.

In every table, mean change and range are the contribution change against the fixed-rate run, SD is the standard deviation of the per-seed changes, SE is the standard error of their mean, and p is a two-sided sign test on the seeds ahead, which is the chance that a fair coin gives a count at least as far from half. Ahead counts the seeds where the reviewer beat it. Flags counts the flags the arm raised over the seeds, pace flags those with a pace cause, and rate changes the changes the arm made. Regret is the oracle arm's mean minus the reviewer's. Recovered is the reviewer's gain over the template as a share of the oracle's. Accept, precision, recall, F1 and $ recall are the decline measures against the oracle's labels, pooled over the seeds. Invalid counts calls with a bad attempt. Calls, tokens, median seconds and cost are the arm's, from its calls.jsonl, at list prices.

Seeds 1 to 20 at a fixed elasticity of 1.0, each reviewer against the fixed-rate run.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | -6,265 | 6,944 | 1,553 | -17,084 to +11,323 | 3/20 | 0.0026 | 1099 | 432 | 766 | +19,372 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| oracle | +13,107 | 3,766 | 842 | +7,752 to +19,404 | 20/20 | <0.001 | 1709 | 1037 | 150 | +0 | 1.00 | 0.11 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| claude-opus-5-5 | +305 | 7,307 | 1,634 | -12,295 to +13,219 | 8/20 | 0.50 | 1108 | 440 | 638 | +12,802 | 0.34 | 0.74 | 1.00 | 0.31 | 0.47 | 0.33 | 0 | 793 | 2,114,920/283,889 | 4.2 | $14.14 |
| claude-sonnet-5-5 | -6,184 | 6,986 | 1,562 | -16,608 to +11,323 | 4/20 | 0.012 | 1095 | 428 | 761 | +19,291 | 0.00 | 0.99 | 1.00 | 0.01 | 0.02 | 0.01 | 0 | 699 | 1,925,472/142,567 | 2.7 | $5.28 |
| claude-haiku-5-5 | -6,265 | 6,944 | 1,553 | -17,084 to +11,323 | 3/20 | 0.0026 | 1099 | 432 | 766 | +19,372 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 696 | 1,919,469/484,285 | 4.0 | $0.43 |

Seeds 1 to 20 at a fixed elasticity of 2.0, each reviewer against the fixed-rate run.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | -2,687 | 4,119 | 921 | -10,801 to +3,231 | 6/20 | 0.12 | 2586 | 1906 | 566 | +8,693 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| oracle | +6,006 | 4,090 | 914 | -1,042 to +15,350 | 19/20 | <0.001 | 2343 | 1669 | 104 | +0 | 1.00 | 0.13 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| claude-opus-5-5 | -2,442 | 4,270 | 955 | -10,331 to +4,309 | 5/20 | 0.041 | 2564 | 1885 | 540 | +8,448 | 0.03 | 0.93 | 0.93 | 0.08 | 0.15 | 0.06 | 0 | 520 | 1,576,883/194,028 | 4.5 | $10.19 |
| claude-sonnet-5-5 | -2,681 | 4,172 | 933 | -10,801 to +3,231 | 6/20 | 0.12 | 2586 | 1906 | 562 | +8,687 | 0.00 | 0.99 | 1.00 | 0.01 | 0.02 | 0.01 | 0 | 506 | 1,546,607/110,905 | 2.9 | $4.20 |
| claude-haiku-5-5 | -2,687 | 4,119 | 921 | -10,801 to +3,231 | 6/20 | 0.12 | 2586 | 1906 | 566 | +8,693 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 505 | 1,543,520/390,266 | 4.3 | $0.35 |

Seeds 1 to 20 in the true mode, each reviewer against the fixed-rate run.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +16,164 | 3,166 | 708 | +11,589 to +23,394 | 20/20 | <0.001 | 2009 | 1337 | 106 | +0 | - | 1.00 | - | - | - | - | - | - | - | - | - |
| oracle | +16,164 | 3,166 | 708 | +11,589 to +23,394 | 20/20 | <0.001 | 2009 | 1337 | 106 | +0 | - | 1.00 | - | - | - | - | - | - | - | - | - |
| claude-opus-5-5 | +16,164 | 3,166 | 708 | +11,589 to +23,394 | 20/20 | <0.001 | 2009 | 1337 | 106 | +0 | - | 1.00 | - | - | - | - | 0 | 93 | 306,235/22,719 | 3.4 | $1.68 |
| claude-sonnet-5-5 | +16,164 | 3,166 | 708 | +11,589 to +23,394 | 20/20 | <0.001 | 2009 | 1337 | 106 | +0 | - | 1.00 | - | - | - | - | 0 | 97 | 321,704/20,349 | 2.7 | $0.85 |
| claude-haiku-5-5 | +16,164 | 3,166 | 708 | +11,589 to +23,394 | 20/20 | <0.001 | 2009 | 1337 | 106 | +0 | - | 1.00 | - | - | - | - | 0 | 97 | 321,704/76,520 | 4.3 | $0.07 |

The reviewers ranked across the mismatched modes, fixed:1.0 and fixed:2.0, on seeds 1 to 20.

| Rank | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | oracle | +9,557 | 5,291 | 837 | -1,042 to +19,404 | 39/40 | <0.001 | 4052 | 2706 | 254 | +0 | 1.00 | 0.12 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| 2 | claude-opus-5-5 | -1,068 | 6,068 | 960 | -12,295 to +13,219 | 13/40 | 0.038 | 3672 | 2325 | 1178 | +10,625 | 0.24 | 0.81 | 0.99 | 0.23 | 0.37 | 0.24 | 0 | 1313 | 3,691,803/477,917 | 4.4 | $24.33 |
| 3 | claude-sonnet-5-5 | -4,432 | 5,950 | 941 | -16,608 to +11,323 | 10/40 | 0.0022 | 3681 | 2334 | 1323 | +13,989 | 0.00 | 0.99 | 1.00 | 0.01 | 0.02 | 0.01 | 0 | 1205 | 3,472,079/253,472 | 2.7 | $9.48 |
| 4 | template | -4,476 | 5,920 | 936 | -17,084 to +11,323 | 9/40 | <0.001 | 3685 | 2338 | 1332 | +14,032 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| 5 | claude-haiku-5-5 | -4,476 | 5,920 | 936 | -17,084 to +11,323 | 9/40 | <0.001 | 3685 | 2338 | 1332 | +14,032 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 1201 | 3,462,989/874,551 | 4.1 | $0.78 |

At a fixed elasticity of 1.0, saying yes to every plan earns -$6,265 a seed, and the oracle earns +$13,107 while accepting 11% of the plans, so $19,372 a seed is open to a reviewer. Opus earns +$305, ahead of the fixed-rate run in 8 of 20 seeds, a recovered share of 0.34. Opus declines 230 plans with precision 1.00 and recall 0.31, and its dollar-weighted recall is 0.33. Sonnet declines 8 plans with precision 1.00 and recall 0.01, and Haiku declines no plan. At a fixed elasticity of 2.0, saying yes to every plan earns -$2,687 and the oracle +$6,006 while accepting 13%. Opus declines 40 plans with precision 0.93 and recall 0.08, Sonnet declines 5 plans with precision 1.00 and recall 0.01, and Haiku declines no plan. In the true mode every plan is scored with the simulator's own elasticity, so saying yes to every plan is correct: every reviewer earns the template's +$16,164 a seed, and no model declines a plan. The fixed modes' 4,006 calls cost $37.19 at list prices. Over the whole benchmark 0 calls were retried and 0 failed.

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

At 0.9 the agent expects 11% more demand than arrives, so every raise sells fewer rooms than its estimate says. The default mode's gain falls from +$16,164 to +$1,069 a seed, ahead in 12 of 20 seeds, and saying yes to every plan at a wrong elasticity loses money: -$25,072 at fixed:1.0 and -$15,174 at learn:1.0. In the mismatched modes the oracle accepts 1% to 5% of the plans. At 1.1 the default mode earns +$66,687 a seed, ahead in 20 of 20, because the start rates were set for a smaller market and the dates run ahead of pace. The learning agent's day-59 estimates are 1.40 to 1.51 at 0.9 and 1.43 to 1.50 at 1.1 against 1.42 to 1.49 at 1.0, so the demand-level error mostly lands in the estimator's intercept, as estimate.py intends.

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

`hotel-market bench --seeds 1 20 --template --react --market-elasticity E --elasticity true` and the same command with `--elasticity learn:1.0 --cautious`, run on 2026-10-15 on world v2 at E = 0.0 and 0.5; the rows at 1.0 are the reaction tables above, because 1.0 is the customer file's default since world v2. The option multiplies expected demand by the comp median as shopped that day over the comp set's starting level, the median of its base rates, to the power of minus E. The agent is told E and every plan record carries it. The oracle re-scores each plan with E and with the share of a change the competitors follow, so it is the ceiling again over the agent's own candidates, with the reaction scored as immediate where the simulator applies it three days later. The columns are those of the reaction table, and oracle gap is the oracle arm's mean change minus say-yes-to-everything's.

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

The level is learned at once and closely: by day 59 the factor is 0.90 to 0.90 at a bias of 0.9, 1.09 to 1.10 at 1.1, 0.99 to 1.00 at 1.0 and 0.99 to 1.00 in the reacting market. At 0.9 it cuts the flags from 5420 to 1538 over the 20 seeds, because the pace baseline no longer expects rooms that never come. Saying yes to every plan there earns -$13,700 a seed with the level against -$15,174 without it, and the cautious arm -$3,534 against -$4,122; the true mode earns +$1,069 there, so the opportunity in a market a tenth smaller is small for every arm. At 1.0 the level arms earn +$825 and +$12,346 against +$804 and +$12,527 without it. At 1.1 they earn +$55,518 and +$60,005 against +$56,213 and +$60,666: the corrected pace baseline removes raises on dates the start rates underprice, and the agent acts only on a flag, so a market that is simply larger raises none, the gap FRK-11 holds. With the reaction on at 0.5 the plain learner earns +$302,095 a seed from 1959 rate changes, the level arms +$304,114 and +$139,141, and the cautious arm without the level +$141,469; the ratchet FRK-09 holds is at its fullest in the plain learner.

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


`hotel-market bench --seeds 1 20 --elasticity learn:1.0 --elasticity learn:2.0 --model claude-opus-5-5 --model claude-haiku-5-5`, the same command with `--cautious`, `hotel-market bench --seeds 1 20 --elasticity learn:1.0 --model claude-sonnet-5-5` with and without `--cautious`, and `hotel-market bench --seeds 1 20 --elasticity learn:1.0 --cautious --react --market-elasticity 0.5 --model claude-opus-5-5`, run on 2026-10-15 on world v2. The template and the oracle run beside the model in every arm. Opus runs the four arms with no reaction and the reacting one. Haiku runs the four arms with no reaction, and Sonnet the two from a prior of 1.0. The live calls ran in the same processes as the fixed arms, one per command and seed range. The projection from their seeds 1 to 3 priced the learn set at $43.85 for seeds 1 to 20, and it came to $48.73. The commands that printed the tables read the caches and made no call.

Seeds 1 to 20 at a learned elasticity from a prior of 1.0, each reviewer against the fixed-rate run.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost | Day-59 estimate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +804 | 8,122 | 1,816 | -14,583 to +14,562 | 11/20 | 0.82 | 1253 | 585 | 510 | +12,395 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - | 1.42 to 1.49 |
| oracle | +13,199 | 4,182 | 935 | +7,752 to +21,079 | 20/20 | <0.001 | 1755 | 1083 | 148 | +0 | 1.00 | 0.17 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - | 1.28 to 1.43 |
| claude-opus-5-5 | +2,049 | 8,463 | 1,892 | -14,583 to +16,771 | 12/20 | 0.50 | 1241 | 573 | 481 | +11,150 | 0.10 | 0.92 | 1.00 | 0.11 | 0.20 | 0.11 | 0 | 476 | 1,421,620/157,885 | 4.0 | $8.84 | 1.42 to 1.49 |
| claude-sonnet-5-5 | +803 | 8,153 | 1,823 | -14,583 to +14,562 | 11/20 | 0.82 | 1247 | 579 | 507 | +12,396 | -0.00 | 0.99 | 1.00 | 0.01 | 0.02 | 0.00 | 0 | 466 | 1,400,877/99,687 | 2.7 | $3.80 | 1.42 to 1.49 |
| claude-haiku-5-5 | +783 | 8,094 | 1,810 | -14,583 to +14,562 | 11/20 | 0.82 | 1253 | 585 | 508 | +12,416 | -0.00 | 1.00 | 1.00 | 0.01 | 0.01 | 0.00 | 0 | 465 | 1,398,906/331,930 | 4.0 | $0.31 | 1.42 to 1.49 |

Seeds 1 to 20 at a learned elasticity from a prior of 1.0 with the cautious rule, each reviewer against the fixed-rate run.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost | Day-59 estimate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +12,527 | 5,265 | 1,177 | +1,658 to +21,698 | 20/20 | <0.001 | 1571 | 902 | 295 | +2,326 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - | 1.36 to 1.46 |
| oracle | +14,854 | 3,672 | 821 | +10,124 to +23,687 | 20/20 | <0.001 | 1882 | 1211 | 138 | +0 | 1.00 | 0.32 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - | 1.32 to 1.43 |
| claude-opus-5-5 | +12,561 | 5,274 | 1,179 | +1,773 to +21,698 | 20/20 | <0.001 | 1567 | 898 | 292 | +2,293 | 0.01 | 0.98 | 1.00 | 0.03 | 0.06 | 0.01 | 0 | 275 | 1,220,483/77,972 | 4.0 | $6.44 | 1.36 to 1.46 |
| claude-sonnet-5-5 | +12,527 | 5,265 | 1,177 | +1,658 to +21,698 | 20/20 | <0.001 | 1571 | 902 | 295 | +2,326 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 273 | 1,215,378/54,538 | 2.6 | $2.98 | 1.36 to 1.46 |
| claude-haiku-5-5 | +12,269 | 5,234 | 1,170 | +1,658 to +21,698 | 20/20 | <0.001 | 1571 | 902 | 294 | +2,585 | -0.11 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 273 | 1,215,382/222,501 | 4.4 | $0.23 | 1.36 to 1.46 |

Seeds 1 to 20 at a learned elasticity from a prior of 2.0, with and without the cautious rule. Each reviewer is against the fixed-rate run.

| Mode | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost | Day-59 estimate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| learn:2.0 | template | +2,416 | 5,222 | 1,168 | -8,435 to +9,983 | 13/20 | 0.26 | 2570 | 1892 | 398 | +4,774 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - | 1.52 to 1.75 |
| learn:2.0 | oracle | +7,190 | 3,638 | 814 | +616 to +12,283 | 20/20 | <0.001 | 2246 | 1573 | 126 | +0 | 1.00 | 0.28 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - | 1.58 to 1.77 |
| learn:2.0 | claude-opus-5-5 | +2,812 | 4,942 | 1,105 | -5,571 to +10,026 | 13/20 | 0.26 | 2598 | 1920 | 387 | +4,378 | 0.08 | 0.97 | 0.92 | 0.05 | 0.09 | 0.06 | 0 | 361 | 1,169,973/142,145 | 5.3 | $7.52 | 1.52 to 1.75 |
| learn:2.0 | claude-haiku-5-5 | +2,457 | 5,202 | 1,163 | -8,435 to +9,983 | 14/20 | 0.12 | 2569 | 1891 | 398 | +4,733 | 0.01 | 1.00 | 1.00 | 0.00 | 0.01 | 0.01 | 0 | 362 | 1,170,849/282,735 | 4.4 | $0.26 | 1.52 to 1.75 |
| learn:2.0 --cautious | template | +2,018 | 4,187 | 936 | -8,396 to +10,445 | 12/20 | 0.50 | 2245 | 1569 | 213 | +2,114 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - | 1.55 to 1.91 |
| learn:2.0 --cautious | oracle | +4,132 | 3,173 | 709 | +345 to +11,508 | 20/20 | <0.001 | 2130 | 1457 | 84 | +0 | 1.00 | 0.31 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - | 1.59 to 1.93 |
| learn:2.0 --cautious | claude-opus-5-5 | +2,018 | 4,187 | 936 | -8,396 to +10,445 | 12/20 | 0.50 | 2245 | 1569 | 213 | +2,114 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 198 | 891,511/62,224 | 4.2 | $4.81 | 1.55 to 1.91 |
| learn:2.0 --cautious | claude-haiku-5-5 | +2,018 | 4,187 | 936 | -8,396 to +10,445 | 12/20 | 0.50 | 2245 | 1569 | 213 | +2,114 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | 0 | 198 | 891,511/167,042 | 4.7 | $0.17 | 1.55 to 1.91 |

Seeds 1 to 20 at a learned elasticity from a prior of 1.0 with the cautious rule, the reaction on. The market elasticity is 0.5, and each reviewer is against the fixed-rate run. Recent shown counts the plans on stay dates the hotel changed within the previous 14 days, and recent held the holds among them.

| Reviewer | Mean change | SD | SE | Range | Ahead | p | Rate changes | Regret | Recovered | Accept | Precision | Median flags | Own changes | Changed twice | Recent shown | Recent held | Invalid | Calls | Tokens in/out | Median s | Cost | Day-59 estimate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| template | +141,469 | 78,588 | 17,573 | +46,172 to +318,833 | 20/20 | <0.001 | 822 | +0 | - | 1.00 | - | 1566 | 1138 | 609 | 582 | 0 | - | - | - | - | - | 1.31 to 1.46 |
| oracle | +141,469 | 78,588 | 17,573 | +46,172 to +318,833 | 20/20 | <0.001 | 822 | +0 | - | 1.00 | - | 1566 | 1138 | 609 | 582 | 0 | - | - | - | - | - | 1.31 to 1.46 |
| claude-opus-5-5 | +139,231 | 77,945 | 17,429 | +45,279 to +318,620 | 20/20 | <0.001 | 798 | +2,238 | - | 0.97 | 0.00 | 1543 | 1114 | 602 | 583 | 27 | 0 | 390 | 2,369,773/194,627 | 4.6 | $13.37 | 1.30 to 1.46 |

The decline rate by the standard error of the plan's elasticity, pooled over seeds 1 to 20. The table holds every live arm that declined a plan. Each cell is the plans declined of the plans queued in the group, with the rate in brackets.

| Mode | Reviewer | Under 0.15 | 0.15 to 0.25 | 0.25 to 0.35 | 0.35 and over |
| --- | --- | ---: | ---: | ---: | ---: |
| learn:1.0 | claude-haiku-5-5 | 0 of 3 (0.00) | 0 of 68 (0.00) | 0 of 96 (0.00) | 2 of 343 (0.01) |
| learn:1.0 | claude-opus-5-5 | 7 of 8 (0.88) | 20 of 76 (0.26) | 8 of 93 (0.09) | 6 of 345 (0.02) |
| learn:2.0 | claude-haiku-5-5 | 0 of 1 (0.00) | 0 of 79 (0.00) | 0 of 54 (0.00) | 1 of 265 (0.00) |
| learn:2.0 | claude-opus-5-5 | 0 of 1 (0.00) | 8 of 80 (0.10) | 0 of 54 (0.00) | 4 of 264 (0.02) |
| learn:1.0 | claude-sonnet-5-5 | 1 of 4 (0.25) | 1 of 68 (0.01) | 1 of 96 (0.01) | 1 of 343 (0.00) |
| learn:1.0 --cautious | claude-haiku-5-5 | none queued | 0 of 24 (0.00) | 0 of 45 (0.00) | 1 of 226 (0.00) |
| learn:1.0 --cautious | claude-opus-5-5 | none queued | 1 of 25 (0.04) | 3 of 47 (0.06) | 1 of 225 (0.00) |
| learn:1.0 --cautious, react, market 0.5 | claude-opus-5-5 | none queued | 6 of 35 (0.17) | 13 of 174 (0.07) | 9 of 617 (0.01) |

The reviewers ranked across the learned modes, learn:1.0 and learn:2.0 pooled over 40 seeds, with and without the cautious rule. Sonnet ran from the prior of 1.0 only, so it is not ranked.

| Arms | Rank | Reviewer | Mean change | SD | SE | Range | Ahead | p | Flags | Pace flags | Rate changes | Regret | Recovered | Accept | Precision | Recall | F1 | $ recall | Invalid | Calls | Tokens in/out | Median s | Cost |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| without the rule | 1 | oracle | +10,194 | 4,922 | 778 | +616 to +21,079 | 40/40 | <0.001 | 4001 | 2656 | 274 | +0 | 1.00 | 0.21 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| without the rule | 2 | claude-opus-5-5 | +2,431 | 6,852 | 1,083 | -14,583 to +16,771 | 25/40 | 0.15 | 3839 | 2493 | 868 | +7,764 | 0.10 | 0.94 | 0.98 | 0.09 | 0.16 | 0.10 | 0 | 837 | 2,591,593/300,030 | 4.5 | $16.37 |
| without the rule | 3 | claude-haiku-5-5 | +1,620 | 6,769 | 1,070 | -14,583 to +14,562 | 25/40 | 0.15 | 3822 | 2476 | 906 | +8,574 | 0.00 | 1.00 | 1.00 | 0.01 | 0.01 | 0.00 | 0 | 827 | 2,569,755/614,665 | 4.1 | $0.56 |
| without the rule | 4 | template | +1,610 | 6,789 | 1,073 | -14,583 to +14,562 | 24/40 | 0.27 | 3823 | 2477 | 908 | +8,584 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| with the rule | 1 | oracle | +9,493 | 6,399 | 1,012 | +345 to +23,687 | 40/40 | <0.001 | 4012 | 2668 | 222 | +0 | 1.00 | 0.32 | 1.00 | 1.00 | 1.00 | 1.00 | - | - | - | - | - |
| with the rule | 2 | claude-opus-5-5 | +7,289 | 7,113 | 1,125 | -8,396 to +21,698 | 32/40 | <0.001 | 3812 | 2467 | 505 | +2,204 | 0.01 | 0.99 | 1.00 | 0.02 | 0.03 | 0.01 | 0 | 473 | 2,111,994/140,196 | 4.1 | $11.25 |
| with the rule | 3 | template | +7,273 | 7,097 | 1,122 | -8,396 to +21,698 | 32/40 | <0.001 | 3816 | 2471 | 508 | +2,220 | 0.00 | 1.00 | - | 0.00 | - | 0.00 | - | - | - | - | - |
| with the rule | 4 | claude-haiku-5-5 | +7,143 | 6,988 | 1,105 | -8,396 to +21,698 | 32/40 | <0.001 | 3816 | 2471 | 507 | +2,350 | -0.06 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 471 | 2,106,893/389,543 | 4.6 | $0.41 |

The learn arms' cost at list prices. The first column prices the calls of seeds 1 to 3. The projection is their cost per seed times 20. The last two columns are the cost and the calls of seeds 1 to 20.

| Mode | Model | Seeds 1 to 3 | Projected, seeds 1 to 20 | Measured, seeds 1 to 20 | Calls |
| --- | --- | ---: | ---: | ---: | ---: |
| learn:1.0 | claude-opus-5-5 | $1.22 | $8.16 | $8.84 | 476 |
| learn:1.0 | claude-sonnet-5-5 | $0.54 | $3.61 | $3.80 | 466 |
| learn:1.0 | claude-haiku-5-5 | $0.04 | $0.29 | $0.31 | 465 |
| learn:1.0 --cautious | claude-opus-5-5 | $0.90 | $6.02 | $6.44 | 275 |
| learn:1.0 --cautious | claude-sonnet-5-5 | $0.42 | $2.77 | $2.98 | 273 |
| learn:1.0 --cautious | claude-haiku-5-5 | $0.03 | $0.21 | $0.23 | 273 |
| learn:2.0 | claude-opus-5-5 | $1.06 | $7.06 | $7.52 | 361 |
| learn:2.0 | claude-haiku-5-5 | $0.04 | $0.24 | $0.26 | 362 |
| learn:2.0 --cautious | claude-opus-5-5 | $0.78 | $5.17 | $4.81 | 198 |
| learn:2.0 --cautious | claude-haiku-5-5 | $0.03 | $0.18 | $0.17 | 198 |
| learn:1.0 --cautious, react, market 0.5 | claude-opus-5-5 | $1.52 | $10.14 | $13.37 | 390 |
| every arm |  | $6.58 | $43.85 | $48.73 | 3,737 |

From a prior of 1.0, saying yes to every plan earns +$804 a seed. The oracle earns +$13,199 while accepting 17% of the plans, so $12,395 a seed is open to a reviewer. Opus earns +$2,049, a recovered share of 0.10. Opus declines 41 plans with precision 1.00 and recall 0.11, Sonnet declines 4 plans with precision 1.00 and recall 0.01, and Haiku declines 2 plans with precision 1.00 and recall 0.01. With the cautious rule, saying yes to every plan earns +$12,527 and the oracle +$14,854 while accepting 32%. Opus declines 5 plans with precision 1.00 and recall 0.03, Sonnet declines no plan, and Haiku declines 1 plan with precision 0.00 and recall 0.00. From a prior of 2.0, saying yes to every plan earns +$2,416 without the rule and +$2,018 with it; Opus declines 12 and 0, and Haiku 1 and 0. In the reacting market at a market elasticity of 0.5, saying yes to every plan earns +$141,469 a seed and the oracle +$141,469. Opus earns +$139,231 with 28 plans declined. It is shown 583 plans on stay dates the hotel changed within the previous 14 days and holds 27 of them; the oracle holds 0 of 582. Since world v2 the request lists the hotel's earlier changes on those dates with the rooms booked since against the rooms expected. The decline rate falls as the standard error of the plan's elasticity rises: from the prior of 1.0 Opus declines 7 of the 8 plans whose estimate has a standard error under 0.15, 20 of 76 from 0.15 to 0.25, 8 of 93 to 0.35 and 6 of 345 above, where on world v1 the rate was flat across the groups. The five commands made 3,737 calls for $48.73 at list prices. Opus's five arms cost $40.98, Sonnet's two $6.78 and Haiku's four $0.97. The projection from seeds 1 to 3 was $43.85.

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

## The clock: one tick a day against four

`python scripts/tick_sweep.py --seeds 1 20`, run on 2026-10-15 on world v2. Each seed runs twice with the template: at `--ticks 1`, the daily loop, and at `--ticks 4`, where each day is cut into four ticks, the rate shop lands at tick 2, the airlines' filings at tick 3, the events at tick 4 and the bookings at every tick, and the agent runs after each tick, reading the feeds as of that tick. The world is the same in both runs, and a fixed-rate run books the same rooms at either clock, because each day's bookings are drawn once and assigned to ticks from the hotel's own stream; the two runs differ only in when the agent saw the day's data and acted. Decisions off the last tick counts the entries decided at a tick other than the day's last, and accepted off the last tick the plans accepted among them. The lag is counted in ticks from the tick the day-20 filing lands at to the first accepted raise with a seats cause on the stay dates it changed, averaged over the seeds with one.

Seeds 1 to 20 at one tick a day and at four, the template in the true mode, each against the fixed-rate run, run on 2026-10-15 on world v2.

| Ticks a day | Mean change a seed | SD | SE | Range | Ahead | p | Decisions off the last tick | Accepted off the last tick | Seeds with a raise after the day-20 filing | Mean lag in ticks |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | +$16,164 | 3,166 | 708 | +$11,589 to +$23,394 | 20 of 20 | <0.001 | 0 | 0 | 20 of 20 | 0.00 |
| 4 | +$16,204 | 3,113 | 696 | +$12,242 to +$23,524 | 20 of 20 | <0.001 | 4504 | 86 | 20 of 20 | 0.00 |

Paired difference, 4 ticks minus 1: mean +$40 a seed (sd 483, se 108), range -$1,246 to +$1,001, the finer clock ahead in 10 of 20 seeds, sign test p 1.0.

A finer clock earns nothing in this world: the paired difference is +$40 a seed with a standard error of $108, the finer clock ahead in 10 seeds of 20, which a sign test puts at p 1.0, because the world's demand moves once a day except at the shocks, and that is the expected result. The 4,504 decisions off the last tick are mostly pace flags the agent reads again at every tick, and 86 plans were accepted at a tick other than the last. The lag from the day-20 filing to the first accepted raise on its stay dates is 0 ticks at both clocks: the raise comes at the tick the filing lands, which at four ticks is three quarters of the way through the day rather than its end. A finer clock would earn in worlds where shops, filings or bookings move within the day, which this world's feeds do not.
