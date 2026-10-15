# Unknowns

What is not known, each with a best guess. A best guess is marked as one and
is not evidence. A node here follows the evidence rule: it becomes [C] only
when a test confirms the answer, and it becomes [H] when a run settled it
and a RES node records the run. A claim that no test can confirm stays [U].

### UNK-01 [C] How the live model decides, compared with the template
- Was unknown: no run had asked the model. Every number in the README's Results section came from the template, which accepts every plan.
- Before: four live runs of seed 7 on world v1 accepted all 28 plans ([[RES-08]]), and the world v2 run of 2026-10-15 accepted all 6 ([[RES-09]]). The decisions and the contribution change were the template's each time.
- Reasons: the reasons differed by request format. The fourth format, with each range as one phrase, copied every phrase whole ([[DEC-44]]). The world v2 run restated three gains and paraphrased an earlier change.
- Kept: the figures here come from the recorded world v2 run of seed 7, kept as [[DAT-29]]. The world v1 runs are quoted from the sessions that made them.
- Measured: on seeds 1 to 20 of world v2, Opus declines 230 plans at fixed:1.0 and 40 at fixed:2.0 ([[RES-16]], [[RES-17]]). Sonnet declines 8 and 5, Haiku none, and none declines in the true mode ([[RES-18]]).
- Learn: Opus declines 58 plans in the four arms with no reaction and 28 reacting ([[RES-34]] to [[RES-37]]). Haiku declines 4 and Sonnet 4. Opus's rate falls as the standard error rises ([[RES-38]]).
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_recorded_live_run_replays_without_a_key_and_gives_19796
- Links: [[MOD-09]], [[MOD-22]], [[DAT-29]], [[DEC-36]], [[DEC-44]], [[FRK-04]], [[RES-08]], [[RES-16]], [[RES-17]], [[RES-18]], [[RES-34]], [[RES-35]], [[RES-36]], [[RES-37]]

### UNK-02 [C] Whether the enum schema behaves as expected against the live API
- Was unknown: the per-request schema ([[DEC-34]]) had been tested with a fake client only.
- Measured: in the recorded live run of seed 7 ([[DAT-29]]), all 4 answers parsed as JSON and chose an allowed option. The check of the answer therefore never raised ([[RES-09]]).
- Calls: every call ended with the stop reason end_turn, none was refused and none fell back to another model. The four world v1 runs of the same seed, not kept, did the same over 28 calls.
- Invalid: Sonnet gave the first invalid answer seen live, on seed 1 at fixed:1.0, day 40. It left an entry out; a retry fixed it. It did so in six requests, one of them twice, in a failed run and its rerun. Opus and Haiku never did.
- Schema: the decisions are an object with one required property per entry id ([[DEC-34]]). The API refused an array bound of 2 with a 400 on 2026-10-12, and allows a required property. An omission is now unrepresentable.
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_schema_limits_ids_and_choices_to_the_requests_options, test_claude_client_sends_the_request_and_handles_a_refusal
- Links: [[DEC-34]], [[MOD-09]], [[MOD-22]], [[DAT-29]], [[RES-09]], [[RES-18]]

### UNK-03 [H] Whether the container image builds and its tests pass
- Was unknown: the Dockerfile had not been built. The machine the code was written on had no container daemon running.
- Closed by: [[RES-20]]
- Result: the image built on Python 3.11, 3.12 and 3.14 on 2026-10-12 and passed the suite on each. A seed-7 run inside it reproduced the native decisions.jsonl.
- Links: [[DEC-28]], [[RES-20]]

### UNK-04 [H] Whether the suite passes on Python 3.12 and 3.13
- Was unknown: only Python 3.11 had run the suite. The hosted runs that would have covered the others never started ([[DEC-29]]).
- Closed by: [[RES-15]]
- Result: the full suite passed on Python 3.12.6 and on 3.13.7 on 2026-10-12, the slow 20-seed check included.
- Links: [[DEC-30]], [[RES-15]]

### UNK-05 [U] How a change in arriving passengers turns into hotel demand in a real market
- Unknown: the simulator makes demand rise by the hotel's air share times the fractional change in arriving passengers, which is a modelling choice; the load factors are another ([[DEC-63]]).
- Best guess: the real link is weaker than one for one and lagged. It differs by hotel more than the air shares alone say.
- Resolves when: never within this repository; it holds no real data ([[DEC-35]]).
- Links: [[MOD-04]], [[SHK-02]]

### UNK-06 [U] The real cost to service an occupied room
- Unknown: one third of the start rate ([[RUL-61]]) is a scenario choice. It makes the start rates best on ordinary nights.
- Best guess: lower as a share at the airport hotel and higher at the lifestyle hotel. Any other value makes every starting rate wrong and turns the agent into a corrector of starting rates.
- Resolves when: never within this repository.
- Links: [[DEC-12]], [[FRK-01]], [[DEC-41]]

### UNK-07 [U] The real price elasticity, and what the learned estimate does and does not settle
- Unknown: the real elasticity of any hotel. 1.5 is assumed in the simulator ([[RUL-21]]) and, in the default mode, handed to the agent as an oracle ([[RUL-56]]).
- Settled: the agent recovers a value it is not told ([[DEC-38]], [[RES-10]]). Day-59 estimates from 1.0 or 2.0 land at 1.36 to 1.68 ([[RES-04]]). What a wrong value costs is measured ([[RES-03]] to [[RES-05]]), which closed [[FRK-02]].
- Reacting: the simulator's 1.5 fits a hotel whose competitors never move. Under the reaction the true mode is too timid. The learner's lower estimate raises more and is right to ([[RES-26]]). A reacting market needs the effective one.
- Live: the live reviewers' declines do not follow the standard error. The rate per group is flat ([[RES-38]]). It is 0% to 4% with no reaction and 6% to 9% in the reacting arm. The declines key on the cause and the band's display.
- Not settled: whether a real market's bookings obey one elasticity at all ([[UNK-14]]). The same one across stay dates, days out and guest segments is less likely still.
- Measured: a constant level error lands in the intercept, and --level feeds it back ([[DEC-50]], [[DEC-54]], [[RES-29]]). A weekday or event error lands in the slope by two to three standard errors, because it moves with the rate ratio.
- Best guess: between 1 and 2 at a real hotel, different by hotel and by distance to arrival. The estimator learns only where the hotel has moved its own rate by several per cent across most of its bookings ([[FRK-05]]).
- Resolves when: never within this repository.

### UNK-08 [U] Whether the measured gains say anything about a real hotel
- Unknown: the agent shares the simulator's demand formula and booking curve in every mode. In the default mode it is also handed the simulator's elasticity, so it knows price response exactly only there ([[DEC-38]]).
- Best guess: no. The numbers show that the loop detects, scores, decides and records correctly, and nothing more. They are a test of the machinery.
- Measured: at a demand bias of 0.9 the default mode keeps +$1,913 a seed of its +$32,899 ([[RES-21]]). At 1.1 it earns +$112,082 ([[RES-22]]). A learner that feeds its fitted level back recovers nothing at 0.9 ([[RES-29]], [[DEC-54]]).
- Resolves when: never within this repository.
- Links: [[DEC-36]], [[DEC-38]], [[DEC-50]], [[RES-21]], [[RES-22]], [[UNK-05]], [[UNK-07]]

### UNK-09 [C] What a live run costs and how long it takes
- Was unknown: no live call had been made from this repository. The guess was about seven calls, a few cents to under a dollar, and under a minute.
- Measured: seed 7 in the default mode makes 4 calls on world v2, on days 18, 20 and 23. The recorded run cost $0.08 at list prices in a run of 19 seconds ([[RES-09]]).
- Formats: the four world v1 runs of the same seed, with other request formats, made 7 calls each and cost $0.12 to $0.18 ([[RES-08]]).
- Scope: a declined plan would change later flags and so the number of calls. A learn-mode run adds nothing to the calls, only to the estimates.
- Bench: per seed, Opus costs $0.41 at fixed:1.0, $0.42 at fixed:2.0 and $0.14 in the true mode. Sonnet costs $0.17, $0.17 and $0.07 a seed, Haiku a cent or two. An arm is a mode and a reviewer over all the seeds ([[RES-19]]).
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_claude_client_sends_the_request_and_handles_a_refusal
- Links: [[UNK-01]], [[RUL-46]], [[MOD-22]], [[DAT-29]], [[DEC-44]], [[RES-09]], [[RES-19]]

### UNK-10 [U] Whether sql/schema.sql runs on a cloud warehouse as written
- Unknown: the schema ([[DAT-28]]) was written for DuckDB and read against the documentation of BigQuery, Snowflake and Redshift. It has not been run on any of them ([[RES-14]]).
- Best guess: the changes its head lists are the only ones, the type names and the PRIMARY KEY clauses first among them. The row writers in [[MOD-21]] would need each warehouse's own client.
- Resolves when: someone runs the file on one of them.
- Links: [[DAT-28]], [[MOD-21]], [[DEC-42]]

### UNK-11 [U] How competitors react to a rate change and what that does to the revenue target
- Unknown: the simulator's competitors never react ([[CON-03]]). The revenue target's gain ([[RES-07]]) comes from cuts that real competitors might match.
- Best guess: a matched cut gives back most of the revenue gain. The contribution target's raises are less exposed, because a competitor need not follow a raise.
- Measured: with --react, competitors move half of a change three days later ([[DEC-51]]). At a market elasticity of 0.0 the default mode then earns +$111,272 a seed ([[RES-24]]). At 0.5 it earns +$72,229 and at 1.0 +$43,584 ([[RES-26]]).
- Resolves when: never within this repository; a reaction rule is another modelling choice, and --react is one. The market's own response is [[UNK-15]].
- Links: [[CON-03]], [[DEC-41]], [[DEC-51]], [[DEC-52]], [[RES-07]], [[RES-24]], [[RES-26]], [[UNK-05]], [[UNK-15]]

### UNK-12 [U] The effect of cancellations, no-shows, groups and room types
- Unknown: the simulator has none of these ([[DAT-07]]). Every booking stays, every room is the same, and the estimate assumes clean Poisson noise ([[CON-09]]).
- Best guess: real nights sell out less predictably. The chance of a sell-out is then harder to know, and the estimates would be noisier than here.
- Resolves when: never within this repository; [[FRK-03]] is the first step.
- Links: [[DAT-07]], [[CON-09]], [[FRK-03]], [[DEC-21]]

### UNK-13 [U] Whether a 5% cut is enough: the largest cut on the menu is 5%
- Unknown: the candidates cut by at most 5% ([[RUL-43]]), or halfway to a fallen median ([[RUL-42]]). Whether a larger cut ever pays is not measured.
- Best guess: on this market a larger cut rarely pays at an elasticity of 1.5. A cut sells more rooms, and those rooms cost about as much to service as they bring in ([[RES-07]]).
- Resolves when: a run with a 10% cut on the menu is compared with the default on seeds 1 to 20.
- Links: [[RUL-43]], [[RUL-42]], [[DEC-13]], [[RES-07]]

### UNK-14 [U] The bias in an elasticity estimate when a hotel prices to demand
- Unknown: the estimator ([[MOD-16]]) reads the rate as given. A real hotel raises its rate when demand is strong. High rates then come with high bookings, and the slope reads too flat.
- Best guess: the bias pulls a real estimate toward zero. The simulator does not show it, because its agent changes rates only on flags.
- Resolves when: never within this repository; a real estimate would need an instrument or a controlled test ([[FRK-05]]).
- Links: [[MOD-16]], [[UNK-07]], [[FRK-05]], [[DEC-38]]

### UNK-15 [U] The real market-level price elasticity
- Unknown: how much a market's total demand falls when every hotel's rate rises together. Since world v2 the default is 1.0 ([[RUL-87]], [[DEC-65]]): a matched raise loses demand in proportion. --market-elasticity sets another value.
- Measured: at 0.0, 0.5 and 1.0 with the reaction on, the default mode earns +$87,519, +$58,275 and +$35,324 a seed on world v2 ([[RES-26]]). The value sets how much of the ratchet is real.
- Best guess: an inference from general industry knowledge, with nothing here to measure it. Between 0.3 and 1.0 for a city market over 90 days, below the share elasticity of 1.5 ([[RUL-21]]). A guest who must travel still books somewhere.
- Resolves when: never within this repository; it needs market-level demand against market-level rates, with the shocks held apart.
- Links: [[RUL-87]], [[DEC-52]], [[RES-26]], [[UNK-07]], [[UNK-11]], [[FRK-08]]

### UNK-16 [O] What the reviewers do on world v2
- Unknown: whether the world v1 benchmark's findings held on world v2: what the models decline, and what the live run of seed 7 does. Resolved on 2026-10-15 by the reruns below.
- Cost: the benchmark's 7,743 calls cost $85.92 at list prices against the $90 expected, under the $120 gate; the live run of seed 7 $0.08.
- Measured: on world v2 the template earns -$6,265 a seed at fixed:1.0 and the oracle +$13,107; Opus earns +$305 with 230 plans declined, Sonnet -$6,184 with 8 and Haiku -$6,265 with 0 ([[RES-16]]).
- Learn: at learn:1.0 the template earns +$804 and the oracle +$13,199; Opus declines 41, Sonnet 4 and Haiku 2 ([[RES-34]]). The live run of seed 7 accepted all 6 plans ([[RES-09]]).
- Links: [[RES-08]], [[RES-16]], [[RES-34]], [[DAT-29]], [[RUL-80]], [[FRK-12]]

