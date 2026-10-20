# Modules

One MOD node per source file. A node says what the file owns, which modules
it reads, which data it writes, and which test file covers it. The package
is `src/hotel_market/`. The modules are listed in the order they were built,
which is also the order in which they depend on each other.

### MOD-01 [C] schedule.py
- File: src/hotel_market/schedule.py
- Owns: the synthetic air schedule as known on a day (build_schedule), the seats arriving each day (seats_by_day) and the passengers they carry at each flight's load factor (passengers_by_day, [[DEC-63]]), with the change in each.
- Holds: both air shocks ([[SHK-02]], [[SHK-04]]), the scenarios and the churn ([[DEC-53]]), and the load factors ([[RUL-125]] to [[RUL-127]]). It also holds the three counting traps: codeshare rows, the type U bus and the second airport.
- Carriers: where the operating carrier differs from the marketing carrier, a regional flies the route under capacity purchase. IS_WETLEASE is False on every row, because a wet lease is a separate arrangement ([[DEC-35]]).
- Reads: nothing in the package
- Writes: [[DAT-01]], [[DAT-02]], [[DAT-03]]
- Tests: tests/test_schedule.py
- Evidence: test_normal_day_has_4244_seats, test_seat_change_as_of_day_21_is_plus_17_percent_for_day_55, test_summing_with_type_u_rows_counts_the_bus

### MOD-02 [C] world.py
- File: src/hotel_market/world.py
- Owns: the types a market is described with: Hotel, Competitor ([[DAT-04]]) and RateCut ([[DAT-05]]). A Hotel carries its rooms, rate, air share, base occupancy, weekday factors, curve ([[CON-01]]), comp set, limits, room cost and row.
- Level: Hotel.starting_median() is the comp set's base-rate median, the level the market term and the forecast measure a shopped median against ([[DEC-52]], [[DEC-62]]).
- Holds: the calendar: SIM_DAYS ([[RUL-12]]), the window ([[RUL-13]]), TICKS_PER_DAY ([[RUL-128]]), weekday, and the landings: arrival_tick for a slot, news_tick for a known_tick ([[DAT-05]]), shop_landings for the shops ([[DAT-06]]).
- Reads: [[MOD-01]] for SIM_START and HORIZON_DAYS
- Writes: [[DAT-04]]
- Tests: tests/test_world.py
- Evidence: test_hotels_match_the_table, test_clamp_keeps_a_rate_between_floor_and_ceiling, test_simulation_runs_days_0_to_59_and_each_day_sees_90_stay_dates

### MOD-03 [C] shocks.py
- File: src/hotel_market/shocks.py
- Owns: the lookups over a market's events and competitor rate cuts ([[DAT-05]]), which its customer file holds ([[DEC-69]]). The demo market's are the convention ([[SHK-01]]) and the rate cut ([[SHK-03]]).
- Lookups: events_as_of, event_uplift, comp_rate_raise, rate_cuts_as_of and rate_cut, each as of a day and for a customer, the demo market by default. The Event type lives at the boundary ([[MOD-17]]).
- Reads: [[MOD-17]] for the Event type, [[MOD-20]] for the customer and its calendar, [[MOD-02]] for RateCut
- Writes: nothing; it reads [[DAT-05]] out of [[DAT-27]]
- Tests: tests/test_shocks.py
- Evidence: test_convention_is_not_known_before_day_10, test_two_full_service_competitors_cut_20_percent_on_days_37_to_39_from_day_30

### MOD-04 [C] demand.py
- File: src/hotel_market/demand.py
- Owns: the simulator's demand per hotel and stay date as known on a day: rooms x base occupancy x weekday factor x passengers x events. Normal demand leaves both out. rush_profile() is what a rush moves on a day ([[DEC-71]]).
- Holds: the per-filing cache of passenger changes (last_filing, known_passenger_change), keyed by the run's scenario ([[DEC-53]]). The agent never reads this module. Its own demand model is [[MOD-18]], which matches it by construction.
- Bias: DEMAND_BIAS multiplies both demands for the simulator alone ([[RUL-82]], [[DEC-50]]). MARKET_ELASTICITY scales expected demand by the median's level, and the agent is told it ([[RUL-87]], [[DEC-52]]).
- Reads: [[MOD-01]], [[MOD-02]], [[MOD-03]], [[MOD-20]]
- Writes: nothing stored; the functions are pure functions of what is known on a day
- Tests: tests/test_demand.py
- Evidence: test_expected_demand_follows_the_formula, test_the_forecast_is_the_simulators_demand_for_the_demo_market

### MOD-05 [C] shops.py
- File: src/hotel_market/shops.py
- Owns: the rate shop: each competitor's rate for a stay date as seen on a shop day, and their median ([[DAT-06]]). The median's starting level is Hotel.starting_median() in [[MOD-02]] ([[DEC-52]]).
- Holds: NOISE ([[RUL-19]]) and NOISE_STREAM ([[RUL-20]]). Rates are flat across the week ([[DEC-16]]). The noise is drawn afresh every shop day, per competitor from a stream keyed by its hotel and name ([[DEC-62]], [[DEC-64]]).
- Reaction: comp_rates() takes the hotel's lagged change in dollars and moves each competitor REACTION_SHARE of it ([[RUL-83]], [[RUL-84]], [[DEC-51]]). The Books pass it ([[DAT-07]]).
- Reads: [[MOD-01]], [[MOD-02]], [[MOD-03]], [[MOD-20]]
- Writes: [[DAT-06]]
- Tests: tests/test_shops.py
- Evidence: test_comp_median_moves_every_day_and_beyond_the_threshold_only_on_a_shock, test_rates_depend_only_on_the_seed

### MOD-06 [C] bookings.py
- File: src/hotel_market/bookings.py
- Owns: the day-0 preload ([[DEC-03]]) and the Poisson quantile draw with one random number per draw ([[DEC-22]]). It also owns the Books ([[DAT-07]]) and simulate(), the loop over days 0 to 149.
- Holds: the five measures [[MEA-01]] to [[MEA-05]] as Books methods. The daily log records what each draw took, at what rate and against which median. ELASTICITY ([[RUL-21]]) and BOOKING_STREAM ([[RUL-22]]) live here.
- Calls: the agent after each of days 0 to 59 ([[DEC-05]]), or after each tick with --ticks ([[DEC-67]]); the estimator learns from the log ([[MOD-16]]). Books._rushed() applies the rushes to a day's draw ([[DEC-71]]).
- Reads: [[MOD-01]], [[MOD-02]], [[MOD-03]], [[MOD-04]], [[MOD-05]], [[MOD-20]]
- Writes: [[DAT-07]]
- Tests: tests/test_bookings.py
- Evidence: test_same_seed_gives_the_same_books_and_another_seed_does_not, test_expected_new_bookings_follow_the_formula, test_a_rate_change_applies_from_the_next_day_and_touches_no_other_stay_date

### MOD-07 [C] detect.py
- File: src/hotel_market/detect.py
- Ticks: with several ticks a day the numbers are read as of (day, tick), "since yesterday" means since the previous tick, the pace baseline is the curve at the fractional day, and the hold is hold_days of ticks ([[RUL-128]]).
- Owns: the detect numbers for every hotel and stay date after a day's bookings ([[DAT-08]]). It assigns each stay date its causes and merges consecutive stay dates with the same causes into flags ([[DAT-09]]).
- Holds: the hold on pace flags ([[DEC-06]]) and the cause labels ([[RUL-31]] to [[RUL-38]]). The thresholds and the hold period come from the customer ([[RUL-62]] to [[RUL-66]]).
- Reads: [[MOD-02]], [[MOD-17]] (the sources), [[MOD-18]] (the forecast), [[MOD-20]]; never the simulator ([[DEC-40]])
- Writes: [[DAT-08]], [[DAT-09]]
- Tests: tests/test_detect.py
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known, test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags, test_pace_causes_follow_the_gap_against_the_threshold

### MOD-08 [C] plan.py
- File: src/hotel_market/plan.py
- Owns: what the agent could do about a flag and what each option is worth. It builds each weekday's candidates ([[DAT-11]], [[DAT-12]]) and their estimates, the flag's numbers ([[DAT-13]]) and the Entry ([[DAT-14]]).
- Estimate: E[min(N, unsold)] bookings ([[DEC-21]]) on each StayDate ([[DAT-10]]) times the margin, summed over the flag. The elasticity is a Pricing's ([[DAT-21]]), and under a revenue target the rate replaces the margin ([[RUL-58]]).
- Cautious: under the cautious rule ([[CON-11]], [[DEC-39]]) each estimate is made again at both ends of the pricing's band. A change must beat hold at all three. rescored() re-scores for the grader ([[MOD-23]], [[DEC-52]]).
- Holds: ORACLE_ELASTICITY ([[RUL-56]]), MODES ([[RUL-49]]), BAND_STANDARD_ERRORS ([[RUL-54]]), the candidate names and factors ([[RUL-41]] to [[RUL-45]]). The minimum ([[RUL-67]]) and the target come from the customer.
- Reads: [[MOD-02]], [[MOD-07]], [[MOD-16]] (the estimator's bounds), [[MOD-20]]; never the simulator ([[DEC-40]])
- Tests: tests/test_plan.py
- Evidence: test_estimate_is_expected_contribution_on_the_unsold_rooms, test_a_plan_lists_its_changes_by_day_of_week, test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held

### MOD-09 [C] model.py
- File: src/hotel_market/model.py
- Owns: the model call: the request the model sees ([[DAT-16]]) and the system prompt ([[RUL-47]]). It builds the answer schema from the request's own options ([[DEC-34]]) and checks the answer against them.
- Holds: the cache ([[DAT-17]], [[DEC-23]], [[DEC-25]]), the Claude client with its refusal fallback and the template, which needs no key. Measured wraps any client, records each call ([[DAT-30]]) and retries it after an error.
- Names: MODEL and MODELS ([[RUL-46]], [[RUL-79]]), MODE_NAMES ([[RUL-75]]) and, for Measured, RETRIES, BACKOFF_SECONDS and SDK_ERRORS ([[RUL-76]] to [[RUL-78]]). Every request figure is a display string from [[MOD-11]] ([[DEC-44]]).
- Definition: The template is a stand-in that answers in the model's place when there is no key; it says yes to every plan and writes a reason from the entry's own figures.
- Reads and writes: reads [[MOD-02]], [[MOD-07]], [[MOD-08]] and [[MOD-11]]; writes [[DAT-16]], [[DAT-17]] and [[DAT-30]]
- Tests: tests/test_model.py
- Evidence: test_ask_calls_the_model_once_and_then_reads_the_cache, test_a_choice_that_is_not_the_plan_or_hold_is_rejected, test_every_figure_in_the_request_is_a_display_string, test_a_measured_client_records_one_call

### MOD-10 [C] agent.py
- File: src/hotel_market/agent.py
- Owns: the daily decision, decide(day, sources): detect numbers, flags, entries and the queue of plans worth the minimum. It makes one model or template call per hotel and records the accepted changes, their hold and the log ([[DAT-18]]).
- Also: the minimum-stay advice ([[DAT-15]], [[DEC-10]]), named by MIN_STAY ([[RUL-48]]). decide() keeps the day's entries in agent.today for the oracle ([[MOD-23]]) and each request with its answer in agent.asked for the tables.
- Modes: the elasticity modes ([[DAT-22]]): true, fixed:X or learn:X. In learn mode it re-estimates every hotel's elasticity every day ([[MOD-16]], [[DEC-38]]). It passes the cautious and level flags into each day's pricing ([[CON-11]]).
- Resume: plans_for() builds a day's entries, each with its stay dates' earlier changes ([[DEC-45]]), and advice_for() the advice. resume() picks up the hold, the advice and the changes that earlier days left ([[MOD-21]], [[DEC-42]]).
- Reads: [[MOD-02]], [[MOD-07]], [[MOD-08]], [[MOD-09]], [[MOD-16]], [[MOD-17]], [[MOD-18]], [[MOD-20]]; never the simulator, which wraps it with deciding() ([[MOD-19]])
- Tests: tests/test_agent.py
- Evidence: test_accepted_rates_apply_and_hold_those_stay_dates_for_7_days, test_a_model_that_declines_changes_no_rate, test_each_mode_records_the_elasticity_its_plans_assume, test_another_model_gets_its_own_cache_folder_and_record

### MOD-11 [C] text.py
- File: src/hotel_market/text.py
- Owns: the wording the template reasons and the printed reports share, so that a number reads the same wherever it appears. The shared helpers are stay_range, money_range, percent_range, pace_text and capitalize_first.
- Strings: the display strings of the request ([[DEC-44]]): dollars, tens_of_dollars, percent_change, against_median, versus_holding, rooms and number. The cautious band adds versus_holding_at_end and band_verdict ([[DEC-56]]).
- Ranges: span, money_range, percent_change_range and against_median_range write a range as one phrase. They write the single value when both ends read the same. A signed quantity reads with its direction in words.
- Reads: nothing in the package
- Writes: nothing
- Tests: tests/test_text.py; tests/test_model.py and tests/test_cli.py exercise it through the reasons and the reports
- Evidence: test_rates_read_to_the_dollar_and_estimates_to_the_nearest_ten, test_a_signed_quantity_reads_as_a_phrase_with_its_direction_in_words, test_a_range_is_one_phrase_and_the_single_value_when_both_ends_read_the_same

### MOD-12 [C] cli.py
- File: src/hotel_market/cli.py
- Owns: the hotel-market command: both runs, decisions.jsonl ([[DAT-18]]), the replay of a day and the bench ([[DEC-48]]). It prints the queues, the summary tables ([[DAT-20]]) and the plans' nights against their estimates ([[DEC-45]]).
- Sweep: sweep() runs one arm per seed, mode ([[DAT-24]]) and reviewer ([[DAT-32]]). bench runs the template, the oracle and each --model in every --elasticity mode. It prints a table per mode, a ranking and the groups of [[MEA-13]].
- Daily: run_days() plays the simulator to a day under the run's world options and writes the feeds, per tick with --ticks. A fresh agent runs on the tables ([[MOD-21]]). replay_day() rebuilds a moment's plans and checks them ([[DEC-42]]).
- Holds: REPORT_DAYS ([[RUL-53]]), SHOCK_PLAN_CAUSES ([[RUL-55]]), DAILY_COMMANDS ([[RUL-74]]), BENCH_MODES ([[RUL-81]]), NO_KEY_LINE ([[RUL-122]]) and DEFAULT_DB. --customer and --target name the market and its target ([[DEC-41]]).
- Reads: [[MOD-01]], [[MOD-02]], [[MOD-06]], [[MOD-08]], [[MOD-09]], [[MOD-10]], [[MOD-11]], [[MOD-16]], [[MOD-19]], [[MOD-20]], [[MOD-21]], [[MOD-23]], [[MOD-26]] (the hotel count's words)
- Tests: tests/test_cli.py
- Evidence: test_two_runs_with_the_same_seed_write_identical_decisions_files, test_the_summary_compares_both_runs_on_the_changed_pairs, test_the_daily_commands_run_a_day_and_replay_it, test_the_bench_command_prints_its_tables

### MOD-13 [C] __init__.py
- File: src/hotel_market/__init__.py
- Owns: the package docstring, which names no hotel count, and nothing else.
- Reads: nothing
- Writes: nothing
- Tests: tests/test_package.py
- Evidence: test_the_package_imports_and_describes_the_project

### MOD-14 [C] __main__.py
- File: src/hotel_market/__main__.py
- Owns: the entry point that lets python -m hotel_market run the command in [[MOD-12]].
- Reads: [[MOD-12]]
- Writes: nothing
- Tests: tests/test_package.py
- Evidence: test_python_m_hotel_market_runs_the_command

### MOD-15 [C] kg_check.py
- File: kg_check.py
- Owns: the checks that this graph agrees with the code. Links resolve, every source file has a MOD node, and every [H] node links to its replacement. Every [C] node cites tests that exist or is a reviewed policy node.
- Checks: every constant's value and kind match the code, and every customer setting has a node. Every measure's function exists, each demo-file shock or filing has an SHK node naming its day, and every RES node names its table.
- Limits: a field line has at most 240 characters and a node at most 8 fields. The index is the one it writes with --write-index. A commit named in a Commit field is looked up when the history is present, and a miss is a warning.
- Reads: the package modules, to read the constants' values. A module whose import fails, such as the demo page without its extra, is skipped and named in a warning.
- Writes: kg/index.md with --write-index; otherwise nothing. It prints the problems and exits 1 when there are any
- Tests: tests/test_kg.py
- Evidence: test_the_knowledge_graph_agrees_with_the_code, test_a_constant_whose_value_differs_from_the_code_is_reported, test_a_shock_in_the_code_without_a_node_is_reported, test_a_module_that_cannot_import_is_skipped_with_a_warning

### MOD-16 [C] estimate.py
- File: src/hotel_market/estimate.py
- Owns: the agent's own estimate of the elasticity ([[CON-06]], [[DEC-38]]). It gathers the observations it may use on a day. It fits a Poisson regression with the log baseline as an offset and a normal prior, and clamps the result.
- Observations: one per stay date and booking day, from the sources' booking and shop histories ([[DAT-26]]). They are bookings made before the day, inside the day's window and before the stay date sold out. The opening rooms never count.
- Holds: PRIOR_SD ([[RUL-50]]), ELASTICITY_MIN ([[RUL-51]]) and ELASTICITY_MAX ([[RUL-52]]). The baseline comes from the agent's own forecast ([[MOD-18]]), with the run's market term ([[DEC-52]]).
- Reads: [[MOD-02]] (the hotel and its booking curve), [[MOD-17]] (the sources), [[MOD-18]] (the forecast); never the simulator ([[DEC-40]])
- Writes: [[DAT-23]]; level_factor() turns an Estimate's intercept into the --level factor ([[DEC-54]])
- Tests: tests/test_estimate.py
- Evidence: test_the_day_59_estimate_recovers_the_simulators_elasticity, test_the_estimate_uses_no_booking_made_on_or_after_as_of_day, test_observations_stop_on_the_day_a_stay_date_sells_out

### MOD-17 [C] sources.py
- File: src/hotel_market/sources.py
- Owns: the boundary between the agent and its data: the four interfaces ([[DAT-25]]) for bookings, rate shops, schedules and events, the Event type ([[DAT-05]]), BookingHistory ([[DAT-26]]), the Sources bundle and the as-of guard Limited.
- Rule: every method takes the day it is asked on and returns only what was known then. The module holds no data and no truth ([[DEC-40]]).
- Seats: the schedule interface asks an implementation for the seats and passengers arriving each day as filed. It computes the passenger change and revision itself (seat_fraction), so every implementation counts alike ([[DEC-42]]).
- Reads: [[MOD-02]] for the Hotel type
- Writes: nothing
- Tests: tests/test_sources.py
- Evidence: test_the_agent_reads_only_through_the_interfaces, test_the_simulated_sources_answer_as_of_the_day, test_the_stored_sources_answer_as_the_simulated_ones_do

### MOD-18 [C] forecast.py
- File: src/hotel_market/forecast.py
- Owns: the agent's own demand model. Normal demand is rooms x base occupancy x weekday factor. Expected demand adds the schedule and event feeds as of a day. It also gives the event uplift and an event's peak night ([[DEC-09]]).
- Limit: it uses the same formula as the simulator's [[MOD-04]]. That is the known limit that the agent's demand model is right by construction. A test holds the two equal for the demo market.
- Market: expected_demand() takes the market elasticity and scales by the median's level over first_median ([[RUL-88]], [[DEC-52]]). ORACLE_MARKET_ELASTICITY is the run's value, handed to the agent.
- Reads: [[MOD-02]] (the hotels' settings, the calendar), [[MOD-17]] (the sources)
- Writes: nothing stored
- Tests: tests/test_forecast.py
- Evidence: test_the_forecast_is_the_simulators_demand_for_the_demo_market, test_convention_peak_night_is_its_busiest_night_as_of_day_10, test_peak_night_uses_what_is_known_on_the_day_the_event_becomes_known

### MOD-19 [C] simulated.py
- File: src/hotel_market/simulated.py
- Owns: the simulator as the agent's four sources ([[DEC-40]]). SimulatedBookings reads the Books' daily and tick logs ([[DAT-07]]), and SimulatedRateShops the seed and the logged medians. Each feed lands at its tick ([[DEC-67]]).
- Also: SimulatedSchedules holds the seats filed by the day under the run's scenario ([[DEC-53]]), and SimulatedEvents the events known. Each copies what it reads when made, holds no Books or Scenario and refuses a later day ([[DEC-61]]).
- Reaction: the rate-shop source passes the Books' lagged hotel change to each shop ([[DEC-51]]). first_median() is the shop of day -1 ([[DEC-52]]). The agent sees the shop the simulator used. deciding() also wraps a policy ([[MOD-25]]).
- Reads: [[MOD-01]], [[MOD-02]], [[MOD-03]], [[MOD-04]], [[MOD-05]], [[MOD-06]], [[MOD-07]], [[MOD-10]], [[MOD-17]], [[MOD-20]]
- Writes: [[DAT-25]], as their implementation
- Tests: tests/test_sources.py, tests/test_detect.py
- Evidence: test_the_simulated_sources_answer_as_of_the_day, test_the_simulated_sources_refuse_a_later_day_and_hand_out_copies, test_each_shock_flags_on_the_day_it_becomes_known

### MOD-20 [C] customer.py
- File: src/hotel_market/customer.py
- Owns: one market, read from its customer file ([[DEC-41]]). load(path) turns the TOML into a Customer ([[DAT-27]]): hotels ([[DAT-04]]), limits, thresholds, hold, minimum, price response, target and calendar ([[DEC-69]]).
- Default: demo() is the demo market, loaded once and the default wherever no customer is given. demo_path() finds it through CUSTOMER_VARIABLE ([[RUL-71]]) or under the package's repository, never the working directory.
- Checks: load() refuses a bad target ([[RUL-70]]), a repeated key or name, a share outside 0 to 1, a floor above the ceiling, a curve that rises, a hotel short of factors, rooms or rate, and a shock naming an unknown hotel or competitor.
- Reads: [[MOD-02]] for the Hotel and Competitor types
- Writes: [[DAT-27]], [[DAT-04]]; customers/harbour.toml is a second market it reads the same way ([[RES-44]])
- Tests: tests/test_customer.py
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_a_customer_file_with_a_bad_target_or_repeated_key_or_name_is_refused, test_a_hotel_needs_seven_weekday_factors, test_a_share_must_lie_between_0_and_1

### MOD-21 [C] stored.py
- File: src/hotel_market/stored.py
- Owns: the four sources read from stored tables ([[DAT-28]], [[DEC-42]]), the second implementation of [[DAT-25]]: StoredBookings, StoredRateShops, StoredSchedules and StoredEvents. Made for a day, each refuses a later one ([[DEC-61]]).
- Writers: write_snapshot() copies one moment of any Sources into the feed tables, a day or a tick. write_decisions() stores a moment's flags, plans and decisions with each request and answer; write_outcomes() a night's. Each deletes first.
- Readers: state_before() gives an agent its hold, advice and accepted changes, and rate_changes_before() gives the simulator its playback. decided_on(), records_on(), decisions_file() and plan_differences() read a run back.
- Holds: TABLES ([[RUL-72]]) and OPENING_DAY ([[RUL-73]]). connect() opens the DuckDB file and creates the tables from sql/schema.sql. It imports nothing from the simulator and is one of the modules the import test covers.
- Reads: [[MOD-02]], [[MOD-08]] (the Entry, for the plan and decision rows), [[MOD-17]] (the interfaces), [[MOD-20]]; never the simulator ([[DEC-40]])
- Tests: tests/test_stored.py
- Evidence: test_a_60_day_run_through_the_tables_gives_the_same_decisions_file, test_the_stored_sources_answer_as_the_simulated_ones_do, test_a_failed_day_write_rolls_the_earlier_tables_back

### MOD-22 [C] scripts/live_audit.py
- File: scripts/live_audit.py
- Owns: the measured live run and its audit, outside the package. A Measured client ([[MOD-09]]) records each call's tokens, time, stop reason and answering model ([[DAT-30]]).
- Run: live_run() is the command's run for a seed with that client ([[MOD-12]]), so the request stays the one in [[MOD-09]]. calls.jsonl lands beside cache/. The client sends the workspace header when ANTHROPIC_WORKSPACE_ID is set.
- Audit: audit() reads the cache ([[DAT-17]]) and prints each reason and declined plan. It lists each figure in a reason that its request does not hold, and each sentence with no request figure. It ends with the token, time and cost totals.
- Quoted: a figure is quoted when a display string holding it appears whole in the same sentence. It is also quoted as a whole number or inside a name the request holds. "More than holding" in a sentence vouches for a bare dollar gain.
- Ranges: a range such as "12–14%" counts as its two ends. Figures with different units stay apart, and one end of a request range on its own is not a quotation. The recorded run it audits is [[DAT-29]].
- Tests: tests/test_live_audit.py, on made-up reasons and on the recorded run
- Evidence: test_a_range_in_a_reason_is_read_as_its_two_ends, test_a_sentence_that_lists_several_gains_may_write_more_than_holding_once, test_the_recorded_live_run_of_seed_7_passes_the_audit

### MOD-23 [C] bench.py
- File: src/hotel_market/bench.py
- Owns: the benchmark of the model as a reviewer ([[DEC-47]], [[DEC-48]]). The oracle reviewer re-scores each queued plan and hold at ORACLE_ELASTICITY ([[RUL-56]]). It declines the plan when hold scores at least as well.
- Measures: regret ([[MEA-06]]), accept rate ([[MEA-07]]), decline precision, recall and F1 ([[MEA-08]] to [[MEA-10]]), dollar recall ([[MEA-11]]) and recovered share ([[MEA-12]]). Also [[MEA-13]] and [[MEA-14]] for the learn arms.
- Counts: DeclineCounts ([[DAT-31]]) pools the counts behind the measures. counted() keeps one call record per digest ([[DAT-30]]), and cost() prices each call at the model that answered it ([[RUL-80]]).
- Scripted: Reviewer ([[DAT-32]]) names an arm's reviewer: TEMPLATE, ORACLE, oracle(...) or live(model). ScriptedClient plays a model offline, cached as scripted. It answers from a digest dict or declines the keys it is given.
- Reads: [[MOD-08]] (the entries and rescored()), [[MOD-09]] (the clients and request_digest()), [[MOD-10]] (the day's entries in agent.today), [[MOD-11]], [[MOD-20]]; never the simulator, and nothing in the agent's path imports it
- Tests: tests/test_bench.py
- Evidence: test_the_oracle_reviewer_accepts_every_queued_plan_in_true_mode, test_the_oracle_declines_where_hold_scores_at_least_as_well, test_a_call_a_fallback_model_answered_is_priced_at_that_model

### MOD-24 [C] scripts/median_path.py
- File: scripts/median_path.py
- Owns: the comp median's path on one hotel's stay dates next to its rate, shop day by shop day. The run is a template run of one seed. median_path() returns the rows, the agent and the Books.
- Run: the run is the command's template run in the true mode, with --react, --demand-bias and --market-elasticity as given ([[MOD-12]]). It makes no model call and writes nothing. It also prints the rooms each stay date sold.
- Tests: tests/test_median_path.py
- Evidence: test_the_median_follows_the_hotels_change_after_the_lag

### MOD-25 [C] policy.py
- File: src/hotel_market/policy.py
- Owns: the rule-based controls ([[DEC-55]]): PacePolicy, RulesPolicy and NeverCutPolicy, deciders with no estimate and no model. Each maps flag causes to a direction, and decide() moves a flag's dates by POLICY_STEP ([[RUL-99]]).
- Rules: pace acts on the two pace causes. rules adds the event and seat-up causes as raises and the seat-cut cause as a cut ([[DEC-11]]). never-cut keeps those raises and never lowers. A conflict is left alone. POLICIES maps the names.
- Hold: it keeps the agent's hold, by the day each stay date last changed. The detector lifts it for a shock cause, as for the agent. It counts the flags it acted on and the pairs it changed.
- Reads: [[MOD-07]] (the detect numbers and the flags), [[MOD-17]] (the sources), [[MOD-20]]; never the simulator, which wraps it with deciding() ([[MOD-19]])
- Writes: nothing stored; the sweep reads its run as a SeedResult's control fields ([[DAT-19]])
- Tests: tests/test_policy.py
- Evidence: test_the_rule_raises_ahead_of_pace_and_lowers_behind_by_the_step, test_the_rules_policy_adds_the_event_and_seat_rules_and_skips_a_conflict, test_the_never_cut_policy_keeps_the_raises_and_never_lowers

### MOD-26 [C] demo_data.py
- File: src/hotel_market/demo_data.py
- Owns: the demo file ([[DAT-33]], [[DEC-57]], [[DEC-58]]) at --ticks N. build() runs days 0 to 59 through run_days ([[MOD-12]]) with the client of the run recorded at that clock, or the template with a warning; both book to day 149.
- Rows: _news_texts, _stay_rows and _queue_rows fill the tables per moment ([[MOD-07]], [[MOD-11]]); _add_outcomes closes a filing's or event's day. A queued plan's headline leads with the money. _strip_row counts the day so far.
- Scorecard: figures() gives the five measures over hotels and stay dates together ([[MEA-01]] to [[MEA-05]]). _stayed takes stay dates 0 to the day before, _outcome_rows every stay date, and _gain_rows the contribution by stay date.
- Dates: stay_label, stay_span and day_label write a date as "Thu 18 Feb" from SIM_START ([[RUL-01]]). day_index writes "day 10". At four ticks a day, a tick reads as its time of day, such as "11:00".
- Holds: DEMO_FILE, DEMO_SCHEMA_FILE and RECORDED_RUNS, the paths, and DEMO_TABLES, NOTHING_NEW, ALL, MEASURES, RATE_AXIS, GAIN_TICK_DAYS and NUMBER_WORDS ([[RUL-103]], [[RUL-104]], [[RUL-107]] to [[RUL-111]]).
- Tests: tests/test_demo_data.py
- Evidence: test_the_file_holds_the_stored_tables_for_every_day_and_the_pages_tables, test_the_reasons_come_from_the_recorded_live_run, test_the_outcome_is_the_result_once_every_stay_date_is_complete

### MOD-27 [C] demo_page.py
- File: src/hotel_market/demo_page.py
- Owns: the read-only demo page ([[DEC-57]], [[DEC-58]]) over [[DAT-33]]. On a finer clock, the sidebar picks a time of day ([[RUL-133]], [[RUL-134]]). The news opens the page, then a strip of three tiles. An engineers' expander closes it.
- Charts: both cover the next two weeks, or the first flagged night to the last, two weeks at least. Both shade the flagged nights. One shows our rate, the comp set median and each change as an arrow. The other shows rooms against pace.
- Queue: each recommendation is one line that leads with the money, and on a finer clock with its time. The panel lists the day's plans so far. Earlier changes follow with dates. Its reason sits closed under Why. The held flags sit closed.
- Scorecard: the nights already stayed for the hotel and for all together, as five large tiles each. With the checkbox on, the five months' tiles follow each, in a compact size, then the small line. A zero change has no chip.
- Holds: the file, parameter, plot, tile, colour and mark constants, FILE_VARIABLE to REASON_MARKS ([[RUL-105]], [[RUL-106]], [[RUL-112]] to [[RUL-123]], [[RUL-133]], [[RUL-134]]), and STYLE.
- Reads: nothing in the package; streamlit, altair and duckdb only, the optional extra demo. The page computes nothing, and a test parses it for an arithmetic operator or an aggregate call. Tests: tests/test_demo_page.py.
- Evidence: test_the_page_imports_nothing_from_the_package_or_the_simulator, test_the_page_does_no_arithmetic_on_a_figure, test_the_page_shows_the_airport_hotel_on_day_20, test_a_reason_with_two_dollar_amounts_shows_both_as_written

### MOD-28 [C] scripts/demo_screenshots.py
- File: scripts/demo_screenshots.py
- Owns: the check that the demo page fits one window ([[DEC-58]]). It starts the page's server on a free loopback port, opens each page in a headless Chromium-based browser at 1440 by 900, and measures it.
- Pages: pages() is every hotel on DAYS, 10, 18, 20, 23, 30, 34 and 40, in both states, or with --ticks N every hotel on INTRADAY_DAYS, 20, 25, 30 and 45, at every tick. PAGES names the six daily pages saved. A taller page fails it.
- Browser: find_browser() takes the path in HOTEL_MARKET_BROWSER, else the first of BROWSERS found: a Chromium under /Applications or in Playwright's cache, Google Chrome, or a chromium or chrome on the PATH.
- Driver: the Browser class drives it over the DevTools pipe, file descriptors 3 and 4, with no package beyond the standard library. The server's output goes to SERVER_LOG beside the screenshots, printed when a page does not render.
- Reads: [[MOD-27]] as the page it runs; nothing from the package
- Tests: tests/test_demo_screenshots.py
- Evidence: test_a_page_is_too_tall_when_its_content_passes_the_window_or_it_scrolls, test_every_checked_page_fits_the_window_and_six_are_saved, test_the_intraday_pages_fit_the_window_at_every_tick_and_nothing_is_saved

### MOD-29 [C] scripts/no_comp_raise.py
- File: scripts/no_comp_raise.py
- Owns: the template sweep with the convention's competitor raise at zero, next to the shipped run ([[RES-41]]). sweep() runs a copy of the demo market whose convention ([[SHK-01]]) carries the raise; the demo stays as it is ([[DEC-69]]).
- Run: each seed is the command's template run ([[MOD-12]]), with its decisions file in a temporary folder, and no model is called. table() prints the rows as markdown.
- Tests: tests/test_no_comp_raise.py
- Evidence: test_the_raise_at_zero_keeps_the_uplift_and_puts_the_event_back

### MOD-30 [C] scripts/measures.py
- File: scripts/measures.py
- Owns: the template sweep in a revenue manager's measures ([[RES-42]]): occupancy, average rate, RevPAR and the sold-out share per hotel for both runs ([[MEA-01]] to [[MEA-03]]), and what the agent run gave up a seed.
- Break-even: cost_table() gives the cost per occupied room, as a share of the start rate, at which a hotel's gain is zero ([[RUL-61]], [[UNK-06]]). A hotel whose room revenue rose prints a share below zero.
- Tests: tests/test_measures.py
- Evidence: test_the_measures_are_the_books_measures_over_the_seeds

### MOD-31 [C] scripts/tick_sweep.py
- File: scripts/tick_sweep.py
- Owns: the template sweep on the daily clock and on a finer one, side by side ([[RES-43]]). seed_result() runs one seed at one clock; sweep() sums the seeds; table() prints the rows and the paired difference.
- Lag: for the day-20 filing it counts the ticks from the filing's tick ([[RUL-130]], or the file's) to the first accepted raise with a seats cause on or after it, by moment_index in [[MOD-07]].
- Event: with --customer and --event the lag runs from the event's announcement, and two columns give the rooms its hotels booked on its stay dates before the first raise and what those dates earned.
- Run: each seed is the command's template run ([[MOD-12]]) at --ticks 1 and at the finer clock, with its decisions file in a temporary folder, and no model is called.
- Tests: tests/test_tick_sweep.py
- Evidence: test_the_sweep_runs_a_seed_at_each_clock_and_reads_the_lag_from_the_filing, test_the_sweep_takes_a_customer_and_an_event_and_reads_what_its_stay_dates_did

### MOD-32 [C] scripts/tick_lag.py
- File: scripts/tick_lag.py
- Owns: the day-20 filing, or with --event an announcement, at one tick a day and at a finer clock, five lines each: the tick it landed at, when the first flag rose and the first raise was accepted, its stay dates and what they earned.
- Page: the same five facts are the demo page's news line for a filing or an event on a finer clock ([[MOD-26]], [[DEC-46]]); the script is the walkthrough's one screen for the clock.
- Run: one seed and one hotel, the airport hotel or the event's first by default, each as the command's template run ([[MOD-12]]) on the market --customer names, in a temporary folder, with no model call.
- Tests: tests/test_tick_lag.py
- Evidence: test_the_five_lines_follow_the_filing_at_each_clock, test_the_five_lines_follow_the_concert_on_the_intraday_market
