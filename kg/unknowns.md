# Unknowns

What is not known, each with a best guess. A best guess is marked as one and
is not evidence; a node here becomes [C] only when a test or a commit
confirms it.

### UNK-01 [C] How the live model decides, compared with the template
- Was unknown: no run had asked the model; every number in the README's Results section came from the template, which accepts every plan.
- Measured: four live runs of seed 7 in the default mode with claude-opus-5-5 (scripts/live_audit.py, [[MOD-22]]), one with bare numbers in the request, one with a signed display string next to each raw value, one with display strings alone and the direction in words, one with each range as one phrase ([[DEC-44]]). Each made the same 7 calls as the template run (days 10, 20, 27 and 34, one entry each) and the model accepted all 7 plans every time, 28 of 28, so the decisions and the contribution change, +$28,818, were the template's each time. The reasons differed: the first run's wrote the figures the model's own way and added claims the entry does not make; the second's copied the strings but put direction words on top of the signs; the third's copied every phrase whole but joined the ends of each range with words of its own; the fourth's copied every phrase and every range whole, listed a plan's gains by day with "more than holding" once, every sentence quoting a figure from the request, written as "we", with event names in lower case. The figures here come from one recorded run of seed 7, the fourth, kept as [[DAT-29]]; the first three runs are quoted from the session that made them and were not kept. Not measured: whether the model ever declines a plan, on other seeds or with a learned elasticity; 28 of 28 accepted says nothing about that.
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_recorded_live_run_replays_without_a_key_and_gives_28818
- Links: [[MOD-09]], [[MOD-22]], [[DAT-29]], [[DEC-36]], [[DEC-44]], [[FRK-04]]
### UNK-02 [C] Whether the enum schema behaves as expected against the live API
- Was unknown: the per-request schema ([[DEC-34]]) had been tested with a fake client only.
- Measured: in the recorded live run of seed 7 ([[DAT-29]]), 7 calls to claude-opus-5-5 with the structured-output schema that lists the request's own entry ids and options as enums, every answer parsed as JSON, named the entry's id and chose the plan or hold, so the check of the answer never raised; every call ended with the stop reason end_turn, none was refused and none fell back to another model. The three earlier runs of the same seed, not kept, did the same over 21 calls. The figures here come from one recorded run of seed 7.
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_schema_limits_ids_and_choices_to_the_requests_options, test_claude_client_sends_the_request_and_handles_a_refusal
- Links: [[DEC-34]], [[MOD-09]], [[MOD-22]], [[DAT-29]]
### UNK-03 [U] Whether the container image builds and its tests pass
- Unknown: the Dockerfile has not been built; the machine the code was written on has no container daemon.
- Best guess: it builds and the tests pass; the same non-editable install from the same files was exercised in a virtual environment, and the suite passed from another directory.
- Resolves when: make image and make docker-test run on a machine with a daemon.
- Links: [[DEC-28]]

### UNK-04 [U] Whether the suite passes on Python 3.12 and 3.13
- Unknown: only Python 3.11 has run the suite; the hosted runs that would have covered the others never started ([[DEC-29]]).
- Best guess: it passes; the code uses nothing beyond Python 3.11, and the dependencies publish wheels for both versions.
- Resolves when: the suite is run on either version.
- Links: [[DEC-30]]

### UNK-05 [U] How a change in arriving seats turns into hotel demand in a real market
- Unknown: the simulator makes demand rise by the hotel's air share times the fractional seat change, which is a modelling choice.
- Best guess: the real link is weaker than one for one and lagged, and it differs by hotel more than the air shares alone say.
- Resolves when: never within this repository; it holds no real data ([[DEC-35]]).
- Links: [[MOD-04]], [[SHK-02]]

### UNK-06 [U] The real cost to service an occupied room
- Unknown: one third of the start rate ([[RUL-61]]) is a scenario choice made so that the start rates are best on ordinary nights.
- Best guess: lower as a share at the airport hotel and higher at the lifestyle hotel; any other value makes every starting rate wrong and turns the agent into a corrector of starting rates.
- Resolves when: never within this repository.
- Links: [[DEC-12]], [[FRK-01]], [[DEC-41]]

### UNK-07 [U] The real price elasticity, and what the learned estimate does and does not settle
- Unknown: the real elasticity of any hotel. 1.5 is assumed in the simulator ([[RUL-21]]) and, in the default mode, handed to the agent as an oracle ([[RUL-56]]).
- Settled: inside this simulator the agent can recover a value it is not told ([[DEC-38]], [[MOD-16]]). From a prior of 1.0 or 2.0 its day-59 estimates land at 1.36 to 1.68 by hotel across 20 seeds, within three standard errors of the truth in every check at true values of 1.0, 1.5 and 2.0, and the standard error says how little the data pin it down: 0.12 to 0.31 on day 59 when the agent has been changing rates, 0.4 to 0.5 (the prior's own width) when it has not. What a wrong value costs, and what learning wins back, is measured: about three quarters of the gain lost, about a quarter of the loss recovered by learning alone, and with the cautious rule ([[DEC-39]]) 76% of the gain kept from a prior of 1.0 and 54% from 2.0.
- Not settled: whether a real market's bookings obey one elasticity at all, let alone the same one across stay dates, days out and guest segments. The estimator takes the simulator's own demand formula as its baseline; a real baseline error lands in the intercept only if it is a constant factor. And the cost of learning is measured against a simulator whose truth is 1.5.
- Best guess: between 1 and 2 at a real hotel, different by hotel and by distance to arrival, and not recoverable from a run in which the hotel's own rate barely moves, since the estimate needs the rate to move to learn anything.
- Resolves when: never within this repository.
- Links: [[DEC-38]], [[FRK-02]], [[MOD-16]]

### UNK-08 [U] Whether the measured gains say anything about a real hotel
- Unknown: the agent shares the simulator's demand formula, booking curve and elasticity, so it knows exactly how guests respond.
- Best guess: no; the numbers show that the loop detects, scores, decides and records correctly, and nothing more. They are a test of the machinery.
- Resolves when: never within this repository.
- Links: [[DEC-36]], [[UNK-05]], [[UNK-07]]

### UNK-09 [C] What a live run costs and how long it takes
- Was unknown: no live call had been made from this repository; the guess was about seven calls, a few cents to under a dollar, and under a minute.
- Measured: seed 7 in the default mode makes 7 calls (days 10, 20, 27 and 34, one entry each). The recorded run ([[DAT-29]]), with display strings alone in the request and each range as one phrase, used 21,148 input tokens (1,744 to 3,923 a call) and 1,713 output tokens (124 to 524), spent 32 s in the model (2.9 to 7.4 s a call, median 3.5 s) in a run of 37 s with both simulations, and cost $0.12 at list prices of $4 and $20 per million tokens; no prompt cache was read or written. The figures here come from that one recorded run of seed 7. Three earlier runs of the same seed, not kept, measured 20,329 input tokens and $0.12 with bare numbers in the request, 37,107 input tokens and $0.18 with a raw value next to every display string, and 24,219 input tokens and $0.14 with display strings alone and each range as a named pair. A declined plan would change later flags and so the number of calls; a learn-mode run adds nothing to the calls, only to the estimates.
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_claude_client_sends_the_request_and_handles_a_refusal
- Links: [[UNK-01]], [[RUL-46]], [[MOD-22]], [[DAT-29]], [[DEC-44]]
### UNK-10 [U] Whether sql/schema.sql runs on a cloud warehouse as written
- Unknown: the schema ([[DAT-28]]) was written for DuckDB and read against the documentation of BigQuery, Snowflake and Redshift; it has not been run on any of them.
- Best guess: the changes its head lists are the only ones, the type names and the PRIMARY KEY clauses first among them, and the row writers in [[MOD-21]] would need each warehouse's own client.
- Resolves when: someone runs the file on one of them.
- Links: [[DAT-28]], [[MOD-21]], [[DEC-42]]
