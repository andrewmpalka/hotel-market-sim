# Unknowns

What is not known, each with a best guess. A best guess is marked as one and
is not evidence. A node here follows the evidence rule: it becomes [C] only
when a test confirms the answer, and it becomes [H] when a run settled it
and a RES node records the run. A claim that no test can confirm stays [U].

### UNK-01 [C] How the live model decides, compared with the template
- Was unknown: no run had asked the model. Every number in the README's Results section came from the template, which accepts every plan.
- Measured: four live runs of seed 7 in the default mode with claude-opus-5-5 accepted all 28 plans ([[RES-08]]). The decisions and the contribution change were therefore the template's each time.
- Reasons: the reasons differed by request format. The fourth format, with each range as one phrase, copied every phrase whole ([[DEC-44]]).
- Kept: the figures here come from one recorded run of seed 7, the fourth, kept as [[DAT-29]]. The first three runs are quoted from the session that made them.
- Not measured: whether the model ever declines a plan, on other seeds or with a learned elasticity. 28 of 28 accepted says nothing about that.
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_recorded_live_run_replays_without_a_key_and_gives_28818
- Links: [[MOD-09]], [[MOD-22]], [[DAT-29]], [[DEC-36]], [[DEC-44]], [[FRK-04]], [[RES-08]]

### UNK-02 [C] Whether the enum schema behaves as expected against the live API
- Was unknown: the per-request schema ([[DEC-34]]) had been tested with a fake client only.
- Measured: in the recorded live run of seed 7 ([[DAT-29]]), all 7 answers parsed as JSON and chose an allowed option. The check of the answer therefore never raised ([[RES-09]]).
- Calls: every call ended with the stop reason end_turn, none was refused and none fell back to another model. The three earlier runs of the same seed, not kept, did the same over 21 calls.
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_schema_limits_ids_and_choices_to_the_requests_options, test_claude_client_sends_the_request_and_handles_a_refusal
- Links: [[DEC-34]], [[MOD-09]], [[MOD-22]], [[DAT-29]], [[RES-09]]

### UNK-03 [U] Whether the container image builds and its tests pass
- Unknown: the Dockerfile has not been built. The machine the code was written on has no container daemon running.
- Best guess: it builds and the tests pass. The same non-editable install from the same files was exercised in a virtual environment. The suite passed from another directory.
- Resolves when: make image and make docker-test run on a machine with a daemon.
- Links: [[DEC-28]]

### UNK-04 [U] Whether the suite passes on Python 3.12 and 3.13
- Unknown: only Python 3.11 has run the suite. The hosted runs that would have covered the others never started ([[DEC-29]]).
- Best guess: it passes. The code uses nothing beyond Python 3.11, and the dependencies publish wheels for both versions.
- Resolves when: the suite is run on either version.
- Links: [[DEC-30]]

### UNK-05 [U] How a change in arriving seats turns into hotel demand in a real market
- Unknown: the simulator makes demand rise by the hotel's air share times the fractional seat change, which is a modelling choice.
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
- Settled: inside this simulator the agent can recover a value it is not told ([[DEC-38]], [[MOD-16]], [[RES-10]]). From a prior of 1.0 or 2.0, its day-59 estimates land at 1.36 to 1.68 by hotel ([[RES-04]]).
- Error: the standard error says how little the data pin it down. It is 0.12 to 0.31 on day 59 when the agent has been changing rates. When it has not, it is 0.4 to 0.5, the prior's own width.
- Cost: what a wrong value costs, and what learning wins back, is measured ([[RES-03]], [[RES-04]], [[RES-05]]). That closed [[FRK-02]].
- Not settled: whether a real market's bookings obey one elasticity at all ([[UNK-14]]). The same one across stay dates, days out and guest segments is less likely still.
- Baseline: the estimator takes the simulator's own demand formula as its baseline. A real baseline error lands in the intercept only if it is a constant factor.
- Best guess: between 1 and 2 at a real hotel, different by hotel and by distance to arrival. It is not recoverable from a run in which the hotel's own rate barely moves. The estimate needs the rate to move to learn anything.
- Resolves when: never within this repository.

### UNK-08 [U] Whether the measured gains say anything about a real hotel
- Unknown: the agent shares the simulator's demand formula, booking curve and elasticity, so it knows exactly how guests respond.
- Best guess: no. The numbers show that the loop detects, scores, decides and records correctly, and nothing more. They are a test of the machinery.
- Resolves when: never within this repository.
- Links: [[DEC-36]], [[UNK-05]], [[UNK-07]]

### UNK-09 [C] What a live run costs and how long it takes
- Was unknown: no live call had been made from this repository. The guess was about seven calls, a few cents to under a dollar, and under a minute.
- Measured: seed 7 in the default mode makes 7 calls, on days 10, 20, 27 and 34. The recorded run cost $0.12 at list prices in a run of 37 seconds ([[RES-09]]).
- Formats: the three earlier runs of the same seed, with other request formats, cost $0.12 to $0.18 ([[RES-08]]).
- Scope: a declined plan would change later flags and so the number of calls. A learn-mode run adds nothing to the calls, only to the estimates.
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_claude_client_sends_the_request_and_handles_a_refusal
- Links: [[UNK-01]], [[RUL-46]], [[MOD-22]], [[DAT-29]], [[DEC-44]], [[RES-09]]

### UNK-10 [U] Whether sql/schema.sql runs on a cloud warehouse as written
- Unknown: the schema ([[DAT-28]]) was written for DuckDB and read against the documentation of BigQuery, Snowflake and Redshift. It has not been run on any of them ([[RES-14]]).
- Best guess: the changes its head lists are the only ones, the type names and the PRIMARY KEY clauses first among them. The row writers in [[MOD-21]] would need each warehouse's own client.
- Resolves when: someone runs the file on one of them.
- Links: [[DAT-28]], [[MOD-21]], [[DEC-42]]

### UNK-11 [U] How competitors react to a rate change, and what that does to the revenue-target result
- Unknown: the simulator's competitors never react ([[CON-03]]). The revenue target's gain ([[RES-07]]) comes from cuts that real competitors might match.
- Best guess: a matched cut gives back most of the revenue gain. The contribution target's raises are less exposed, because a competitor need not follow a raise.
- Resolves when: never within this repository; a reaction rule would be another modelling choice.
- Links: [[CON-03]], [[DEC-41]], [[RES-07]], [[UNK-05]]

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

### UNK-14 [U] The bias in an elasticity estimate when a real hotel changes its rate in response to demand
- Unknown: the estimator ([[MOD-16]]) reads the rate as given. A real hotel raises its rate when demand is strong. High rates then come with high bookings, and the slope reads too flat.
- Best guess: the bias pulls a real estimate toward zero. The simulator does not show it, because its agent changes rates only on flags.
- Resolves when: never within this repository; a real estimate would need an instrument or a controlled test ([[FRK-05]]).
- Links: [[MOD-16]], [[UNK-07]], [[FRK-05]], [[DEC-38]]
