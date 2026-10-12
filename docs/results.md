# Results

Seeds 1 to 20 in the default mode: the agent run against the fixed-rate run over stay dates 0 to 149, template reasons, candidates scored on contribution with the simulator's elasticity.

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

Seed 7 over only the 93 hotel and stay-date pairs where the agent changed a rate (pairs per hotel in brackets).

| Hotel | Revenue, fixed | Revenue, agent | Change | Contribution, fixed | Contribution, agent | Change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Downtown convention hotel (3) | 262,460 | 259,921 | -2,539 | 174,973 | 178,888 | +3,915 (+2.2%) |
| Downtown full-service hotel (21) | 908,770 | 898,472 | -10,298 | 605,847 | 612,332 | +6,485 (+1.1%) |
| Lifestyle hotel (17) | 468,000 | 470,472 | +2,472 | 312,000 | 325,112 | +13,112 (+4.2%) |
| Airport hotel (52) | 989,800 | 965,146 | -24,654 | 659,867 | 665,173 | +5,306 (+0.8%) |
| All four hotels | 2,629,030 | 2,594,011 | -35,019 | 1,752,687 | 1,781,505 | +28,818 (+1.6%) |

Seeds 1 to 20 per elasticity arm, each against the same fixed-rate runs; Estimated / realised is the accepted plans' estimated gain over holding, summed over the seeds, divided by the realised gain, and Rejected at an end counts a cautious arm's candidates that were ahead of hold at the estimate but behind at one end of the band.

| Elasticity | Mean gain per seed | Range | Seeds ahead | Rate changes | Estimated / realised | Rejected at an end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| true (1.5, the simulator's) | +$32,899 | +$13,479 to +$52,809 | 20 of 20 | 179 | 1.04 | |
| fixed:1.0 | +$8,438 | -$13,029 to +$39,143 | 14 of 20 | 515 | 38.7 | |
| fixed:2.0 | +$9,551 | -$6,734 to +$25,474 | 18 of 20 | 486 | 13.0 | |
| learn:1.0 | +$14,141 | -$6,839 to +$45,818 | 16 of 20 | 373 | 18.3 | |
| learn:1.0 --cautious | +$25,076 | +$8,406 to +$53,535 | 20 of 20 | 299 | 7.7 | 3,294 |
| learn:2.0 | +$16,258 | +$2,393 to +$34,480 | 20 of 20 | 418 | 5.2 | |
| learn:2.0 --cautious | +$17,634 | +$5,839 to +$27,585 | 20 of 20 | 240 | 2.5 | 2,681 |

Where each arm's gain came from, summed over the 20 seeds: the plans the convention (day 10) and the new flights (day 20) raised, then every other plan.

| Elasticity | Shock plans | Gain on their stay dates | Other plans | Gain on theirs |
| --- | ---: | ---: | ---: | ---: |
| true | 97 | +$632,532 | 82 | +$25,447 |
| fixed:1.0 | 124 | +$142,871 | 391 | +$25,881 |
| fixed:2.0 | 126 | +$174,985 | 360 | +$16,038 |
| learn:1.0 | 123 | +$259,736 | 250 | +$23,075 |
| learn:1.0 --cautious | 103 | +$487,196 | 196 | +$14,322 |
| learn:2.0 | 127 | +$294,785 | 291 | +$30,370 |
| learn:2.0 --cautious | 72 | +$292,857 | 168 | +$59,831 |

The learning agent's day-59 elasticity estimates, as the range over the four hotels of each hotel's mean across the 20 seeds, against a true value of 1.5.

| Prior | Day-59 estimate, by hotel |
| ---: | --- |
| 1.0 | 1.36 to 1.45 |
| 2.0 | 1.55 to 1.68 |

The cautious rule with and without a $250 minimum per day of the week, seeds 1 to 20; the band alone is the rule that stayed.

| Arm | Band alone | Band and a minimum per day of the week |
| --- | ---: | ---: |
| learn:1.0 --cautious | +$25,076 | +$25,084 |
| learn:2.0 --cautious | +$17,634 | +$17,618 |

Seeds 1 to 20 with the simulator's elasticity and the template, each target against the same fixed-rate runs; the last two columns are in the target's own measure.

| Target | Mean contribution change | Mean revenue change | Seeds ahead on contribution | Rate changes | Accepted plans' estimate | Realised |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| contribution | +$32,899 | -$22,861 | 20 of 20 | 179 | +$681,054 | +$657,979 |
| revenue | +$461 | +$211,445 | 11 of 20 | 659 | +$4,191,156 | +$4,228,903 |

Four live runs of seed 7 in the default mode with claude-opus-5-5, one per request format, seven calls each, every plan accepted every time; only the last is recorded, under tests/fixtures/live_seed7/. Cost is at list prices of $4 and $20 per million tokens.

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
