# Modules

One MOD node per source file: what it owns, which modules it reads, which
data it writes, and its test file. The package is `src/hotel_market/`; the
modules are listed in the order they were built, which is also the order in
which they depend on each other.

### MOD-01 [C] schedule.py
- File: src/hotel_market/schedule.py
- Owns: the synthetic air schedule as known on a given day (build_schedule), the seats arriving each day (seats_by_day), the seat change against the no-shock schedule (seat_change) and against the day before (seat_revision), both air shocks ([[SHK-02]], [[SHK-04]]) and the three counting traps (codeshare rows, the type U bus, the second airport). Finished before the rest of the package; its column names and function signatures do not change.
- Reads: nothing in the package
- Writes: [[DAT-01]], [[DAT-02]], [[DAT-03]]
- Tests: tests/test_schedule.py
- Evidence: test_normal_day_has_4244_seats, test_seat_change_as_of_day_21_is_plus_17_percent_for_day_55, test_summing_with_type_u_rows_counts_the_bus

### MOD-02 [C] world.py
- File: src/hotel_market/world.py
- Owns: the types a market is described with, read by both sides: Hotel, which carries its rooms, starting rate, air share, base occupancy, weekday demand factors, comp set, rate floor and ceiling, cost per occupied room and its row in every array, and Competitor ([[DAT-04]]); and the calendar, SIM_DAYS ([[RUL-12]]), the 90-day window ([[RUL-13]]) and weekday. The hotels themselves, the booking curve and the rest of a market's settings come from the customer file ([[MOD-20]], [[DEC-41]]). Nothing here is random, and nothing here is the simulator's secret.
- Reads: [[MOD-01]] for SIM_START and HORIZON_DAYS
- Writes: [[DAT-04]]
- Tests: tests/test_world.py
- Evidence: test_hotels_match_the_table, test_clamp_keeps_a_rate_between_floor_and_ceiling, test_simulation_runs_days_0_to_59_and_each_day_sees_90_stay_dates, test_weekday_agrees_with_the_schedule

### MOD-03 [C] shocks.py
- File: src/hotel_market/shocks.py
- Owns: the two shocks that are not in the schedule, the convention ([[SHK-01]]) and the competitor rate cut ([[SHK-03]]), as Event and RateCut records ([[DAT-05]]), and the as-of-day lookups on them (events_as_of, event_uplift, comp_rate_raise, rate_cut). The Event type itself is defined at the boundary ([[MOD-17]]) so that both sides share it.
- Reads: [[MOD-17]] for the Event type
- Writes: [[DAT-05]]
- Tests: tests/test_shocks.py
- Evidence: test_convention_is_not_known_before_day_10, test_two_full_service_competitors_cut_20_percent_on_days_37_to_39_from_day_30

### MOD-04 [C] demand.py
- File: src/hotel_market/demand.py
- Owns: the simulator's demand per hotel and stay date as known on a day (rooms x base occupancy x weekday factor x seats x events), normal demand without seats or events, and the per-filing cache of seat changes (last_filing, known_seat_change). The agent never reads it: its own demand model is [[MOD-18]], which matches it by construction for the demo market.
- Reads: [[MOD-01]], [[MOD-03]], [[MOD-02]], [[MOD-20]] (the demo hotels, for its printout)
- Writes: nothing stored; pure functions of what is known on a day
- Tests: tests/test_demand.py
- Evidence: test_expected_demand_follows_the_formula, test_the_forecast_is_the_simulators_demand_for_the_demo_market

### MOD-05 [C] shops.py
- File: src/hotel_market/shops.py
- Owns: the rate shop: each competitor's rate for a stay date as seen on a shop day, and the comp median ([[DAT-06]]). Rates are flat across the week ([[DEC-16]]); the noise is drawn once per competitor and stay date from the seed ([[DEC-37]]).
- Reads: [[MOD-01]], [[MOD-03]], [[MOD-20]] (the customer's hotels), [[MOD-02]]
- Writes: [[DAT-06]]
- Tests: tests/test_shops.py
- Evidence: test_comp_median_moves_only_when_a_shock_becomes_known, test_rates_depend_only_on_the_seed

### MOD-06 [C] bookings.py
- File: src/hotel_market/bookings.py
- Owns: the day-0 preload ([[DEC-03]]), the Poisson quantile draw with one random number per draw ([[DEC-22]]), the Books ([[DAT-07]]) and simulate(), the loop over days 0 to 149 that calls the agent after each of days 0 to 59 ([[DEC-05]]), the five measures [[MEA-01]] to [[MEA-05]] as Books methods, and the daily log of what each draw took, at what rate and against which competitor median, which the agent learns from ([[MOD-16]]). ELASTICITY ([[RUL-21]]) lives here.
- Reads: [[MOD-04]], [[MOD-01]], [[MOD-05]], [[MOD-20]] (the hotels and the booking curve), [[MOD-02]]
- Writes: [[DAT-07]]
- Tests: tests/test_bookings.py
- Evidence: test_same_seed_gives_the_same_books_and_another_seed_does_not, test_expected_new_bookings_follow_the_formula, test_a_rate_change_applies_from_the_next_day_and_touches_no_other_stay_date

### MOD-07 [C] detect.py
- File: src/hotel_market/detect.py
- Owns: the detect numbers for every hotel and stay date after a day's bookings ([[DAT-08]]), read through the four sources and carrying the forecast's expected demand, the causes each stay date is flagged for, the flags that merge consecutive stay dates with the same causes ([[DAT-09]]), the hold on pace flags ([[DEC-06]]), with the thresholds and the hold period read from the customer ([[RUL-62]] to [[RUL-66]]).
- Reads: [[MOD-17]] (the sources), [[MOD-18]] (the forecast), [[MOD-20]] (the thresholds, the hold period and the booking curve), [[MOD-02]]; never the simulator ([[DEC-40]])
- Writes: [[DAT-08]], [[DAT-09]]
- Tests: tests/test_detect.py
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known, test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags

### MOD-08 [C] plan.py
- File: src/hotel_market/plan.py
- Owns: what the agent could do about a flag and what each option is worth: the candidates ([[DAT-11]]) for each day of the week ([[DAT-12]]), the exact expected bookings E[min(N, unsold)] ([[DEC-21]]), the estimate of contribution, or of room revenue under a revenue target ([[RUL-58]]), on the rooms still unsold, the flag's numbers ([[DAT-13]], every range a Range that writes itself as a named pair) and the Entry ([[DAT-14]]) whose plan is the best candidate per weekday ([[DEC-19]]). Every estimate takes the elasticity from a Pricing record ([[DAT-21]]), which says where it came from ([[DEC-38]]), and under the cautious rule ([[CON-11]], [[DEC-39]]) is made again at both ends of the pricing's band, so that a change must beat hold at all three. ORACLE_ELASTICITY ([[RUL-56]]), MODES ([[RUL-49]]) and BAND_STANDARD_ERRORS ([[RUL-54]]) live here; the minimum value at stake ([[RUL-67]]) and the target come from the customer.
- Reads: [[MOD-07]] (the table, with each stay date's expected demand), [[MOD-16]] (the estimator's bounds, for the band), [[MOD-20]] (the minimum, the target and the booking curve), [[MOD-02]]; never the simulator ([[DEC-40]])
- Writes: [[DAT-10]], [[DAT-11]], [[DAT-12]], [[DAT-13]], [[DAT-14]]
- Tests: tests/test_plan.py
- Evidence: test_estimate_is_expected_contribution_on_the_unsold_rooms, test_a_plan_lists_its_changes_by_day_of_week, test_the_agent_reads_only_through_the_interfaces, test_each_mode_records_the_elasticity_its_plans_assume, test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held

### MOD-09 [C] model.py
- File: src/hotel_market/model.py
- Owns: the model call: the request the model sees ([[DAT-16]]), in which every figure is a display string the model copies and every range one phrase, written by [[MOD-11]], the pricing named for the model (MODE_NAMES, [[RUL-75]]), the target when it is revenue and, under the cautious rule, every candidate's estimate at both ends of the band; the system prompt ([[RUL-47]]); the answer schema built from the request's own options ([[DEC-34]]); the check of the answer against those options; the cache of the model's answers ([[DAT-17]], [[DEC-23]], [[DEC-25]]); the template that answers without an API key from the request's display strings and cites a fixed or learned elasticity; and the Claude client with its refusal fallback ([[DEC-44]]).
- Reads: [[MOD-07]], [[MOD-08]], [[MOD-11]], [[MOD-02]]
- Writes: [[DAT-16]], [[DAT-17]]
- Tests: tests/test_model.py
- Evidence: test_ask_calls_the_model_once_and_then_reads_the_cache, test_a_choice_that_is_not_the_plan_or_hold_is_rejected, test_the_template_never_reads_the_models_cache, test_the_request_carries_the_elasticity_and_its_digest_changes_with_it, test_the_three_values_reach_the_model_request, test_every_figure_in_the_request_is_a_display_string

### MOD-10 [C] agent.py
- File: src/hotel_market/agent.py
- Owns: the daily decision, decide(day, sources): detect numbers to flags to entries, the queue of plans worth the minimum, one model (or template) call per hotel per day, the accepted rate changes and the 7-day hold on them, the decisions log, and the minimum-stay advice ([[DAT-15]], [[DEC-10]]). It reads the day through the four sources ([[DAT-25]]) and never the simulator; simulated.deciding() wraps it for a run ([[MOD-19]]). plans_for() builds the day's entries before anything is asked, advice_for() the advice, and resume() picks up the hold and the advice that earlier days left, which is how a table-backed run gives each day's agent its state ([[MOD-21]], [[DEC-42]]). Also the elasticity modes ([[DAT-22]]): true, fixed:X or learn:X, which in learn mode re-estimates every hotel's elasticity every day from the bookings made before it ([[MOD-16]], [[DEC-38]]) and keeps every estimate, with the cautious flag passed into each day's pricing ([[CON-11]]).
- Reads: [[MOD-07]], [[MOD-09]], [[MOD-08]], [[MOD-16]], [[MOD-18]], [[MOD-17]], [[MOD-20]], [[MOD-02]]
- Writes: [[DAT-15]], [[DAT-18]]
- Tests: tests/test_agent.py
- Evidence: test_accepted_rates_apply_and_hold_those_stay_dates_for_7_days, test_a_model_that_declines_changes_no_rate, test_the_log_lists_every_entry_and_advice_in_order, test_each_mode_records_the_elasticity_its_plans_assume, test_a_cautious_agent_records_the_band_and_what_it_rejected, test_the_stored_state_is_what_the_earlier_decisions_left

### MOD-11 [C] text.py
- File: src/hotel_market/text.py
- Owns: the wording shared by the template reasons and the printed reports (stay_range, money_range, percent_range, pace_text, capitalize_first), so that a number reads the same wherever it appears, and the display strings the model request carries in place of every figure ([[DEC-44]]): dollars (to the dollar), tens_of_dollars (an estimate, to the nearest $10), percent_change ("up 15.0%"), against_median ("14.6% below the median"), versus_holding ("$340 more than holding"), pace_text ("44 rooms ahead of pace", shared with the reports), rooms and number (an elasticity, up to two decimals), and the range phrases, span (each end as a formatter writes it, "45 to 48", the single value when both ends read the same), money_range ("$220 to $242", shared with the reports), percent_change_range ("up 17.0% to 21.6%", "down 2.0% to up 3.0%") and against_median_range ("10.7% to 14.6% below the median", "2.5% below to 2.5% above the median"): a signed quantity reads as a phrase with its direction in words and no sign, and a range as one phrase.
- Reads: nothing in the package
- Writes: nothing
- Tests: tests/test_text.py; tests/test_model.py and tests/test_cli.py exercise it through the reasons and the reports
- Evidence: test_rates_read_to_the_dollar_and_estimates_to_the_nearest_ten, test_a_signed_quantity_reads_as_a_phrase_with_its_direction_in_words, test_a_range_is_one_phrase_and_the_single_value_when_both_ends_read_the_same, test_without_a_client_the_template_accepts_the_plan_and_quotes_the_numbers, test_the_replay_command_prints_day_20s_queue

### MOD-12 [C] cli.py
- File: src/hotel_market/cli.py
- Owns: the hotel-market command: the fixed-rate and agent runs, decisions.jsonl ([[DAT-18]]), the replay of a day, the sweep over seeds ([[DAT-19]]) with one arm per --elasticity mode ([[DAT-24]]) and --cautious on the learn arms, the printed queues and the summary tables ([[DAT-20]]), the arm, source and estimate tables, and the argument checks; --customer names the market's file and --target overrides its target ([[MOD-20]], [[DEC-41]]), and a sweep counts its wins and the realised gain in the target. Also the two daily commands ([[DEC-42]]): run_days() plays the simulator to a day with the rate changes the tables hold, writes the day's feeds, runs a fresh agent on the tables ([[MOD-21]]) and writes its flags, plans and decisions; replay_day() rebuilds a day's plans from the tables alone, with the actions the stored decisions record, and checks them against the stored plans. REPORT_DAYS ([[RUL-53]]), SHOCK_PLAN_CAUSES ([[RUL-55]]) and DAILY_COMMANDS ([[RUL-74]]) live here, with DEFAULT_DB, the file the daily commands keep the tables in.
- Reads: [[MOD-10]], [[MOD-19]], [[MOD-21]], [[MOD-06]], [[MOD-09]], [[MOD-08]], [[MOD-16]], [[MOD-20]], [[MOD-01]], [[MOD-11]], [[MOD-02]]
- Writes: [[DAT-18]], [[DAT-19]], [[DAT-20]]
- Tests: tests/test_cli.py
- Evidence: test_two_runs_with_the_same_seed_write_identical_decisions_files, test_the_summary_compares_both_runs_on_the_changed_pairs, test_the_command_rejects_bad_arguments, test_the_seeds_command_prints_one_row_per_arm_and_a_learn_arms_estimates, test_a_cautious_run_says_so_and_shows_the_band_on_each_change, test_the_daily_commands_run_a_day_and_replay_it

### MOD-13 [C] __init__.py
- File: src/hotel_market/__init__.py
- Owns: the package docstring. Nothing else.
- Reads: nothing
- Writes: nothing
- Tests: tests/test_package.py
- Evidence: test_the_package_imports_and_describes_the_project

### MOD-14 [C] __main__.py
- File: src/hotel_market/__main__.py
- Owns: the entry point that lets `python -m hotel_market` run the command in [[MOD-12]].
- Reads: [[MOD-12]]
- Writes: nothing
- Tests: tests/test_package.py
- Evidence: test_python_m_hotel_market_runs_the_command

### MOD-15 [C] kg_check.py
- File: kg_check.py
- Owns: the checks that this graph agrees with the code: links resolve, every source file has a MOD node, every [C] node cites tests that exist, every [H] node names its replacement, every constant's value and kind here match the code, every setting of the customer file outside the hotels has a node whose value matches the file, every measure's function exists, and the index is the one it writes with --write-index. A commit named in a Commit field is looked up when the history is present and reported as a warning, never a failure. Lives at the repository root, outside the package.
- Reads: the package modules, to read the constants' values
- Writes: kg/index.md with --write-index; otherwise nothing. It prints problems and exits 1 when there are any
- Tests: tests/test_kg.py
- Evidence: test_the_knowledge_graph_agrees_with_the_code, test_a_constant_whose_value_differs_from_the_code_is_reported, test_a_customer_setting_missing_from_the_graph_is_reported

### MOD-16 [C] estimate.py
- File: src/hotel_market/estimate.py
- Owns: the agent's own estimate of the elasticity ([[CON-06]], [[DEC-38]]): the observations it may use on a day (one per stay date and booking day, from the booking history and the shop history of the sources ([[DAT-26]]); bookings made before the day, inside the day's window and before the stay date sold out; never the opening rooms), the baseline from the agent's own forecast ([[MOD-18]]), the Poisson regression with the log baseline as an offset and the normal prior on the elasticity, and the clamp. PRIOR_SD ([[RUL-50]]), ELASTICITY_MIN ([[RUL-51]]) and ELASTICITY_MAX ([[RUL-52]]) live here.
- Reads: [[MOD-17]] (the sources), [[MOD-18]] (the forecast, for the baseline), [[MOD-20]] (the booking curve), [[MOD-02]]; never the simulator ([[DEC-40]])
- Writes: [[DAT-23]]
- Tests: tests/test_estimate.py
- Evidence: test_the_day_59_estimate_recovers_the_simulators_elasticity, test_the_estimate_uses_no_booking_made_on_or_after_as_of_day, test_observations_stop_on_the_day_a_stay_date_sells_out, test_the_preload_is_not_an_observation

### MOD-17 [C] sources.py
- File: src/hotel_market/sources.py
- Owns: the boundary between the agent and its data: the four interfaces ([[DAT-25]]) for bookings, competitor rate shops, air schedules and events, each method taking the day it is asked on and returning only what was known then; the Event type ([[DAT-05]]) and the BookingHistory record ([[DAT-26]]); and the Sources bundle the agent is handed. The schedule interface asks its implementations only for the seats arriving each day as filed by a day, and computes the seat change and the seat revision from them (seat_fraction), so that every implementation counts the same way ([[DEC-42]]). It holds no data and no truth ([[DEC-40]]).
- Reads: [[MOD-02]] for the Hotel type
- Writes: nothing
- Tests: tests/test_sources.py
- Evidence: test_the_agent_reads_only_through_the_interfaces, test_the_simulated_sources_answer_as_of_the_day, test_the_stored_sources_answer_as_the_simulated_ones_do

### MOD-18 [C] forecast.py
- File: src/hotel_market/forecast.py
- Owns: the agent's own demand model: normal demand (rooms x base occupancy x weekday factor), expected demand as of a day from the schedule and event feeds (seats and uplift), the event uplift, and an event's peak night ([[DEC-09]]). It uses the same formula as the simulator's [[MOD-04]], which is the known limit that the agent's demand model is right by construction; a test holds the two equal for the demo market.
- Reads: [[MOD-17]] (the sources), [[MOD-02]] (the hotels' settings, the calendar)
- Writes: nothing stored
- Tests: tests/test_forecast.py
- Evidence: test_the_forecast_is_the_simulators_demand_for_the_demo_market, test_convention_peak_night_is_its_busiest_night_as_of_day_10, test_peak_night_uses_what_is_known_on_the_day_the_event_becomes_known

### MOD-19 [C] simulated.py
- File: src/hotel_market/simulated.py
- Owns: the simulator as the agent's four sources ([[DEC-40]]): SimulatedBookings over the Books' daily log ([[DAT-07]]), answering rooms on the books, rates and history as of any day; SimulatedRateShops from the seed and the log of the medians the simulator used; SimulatedSchedules, counting the seats of the schedule as filed by a day, once per filing; SimulatedEvents over the events announced by a day. Also deciding(), which wraps an Agent as the simulator's decide hook, and watch(), the fixed-rate run that records every day's flags.
- Reads: [[MOD-06]], [[MOD-05]], [[MOD-04]], [[MOD-01]], [[MOD-03]], [[MOD-17]], [[MOD-07]], [[MOD-10]], [[MOD-20]], [[MOD-02]]
- Writes: [[DAT-25]] (as their implementation)
- Tests: tests/test_sources.py, tests/test_detect.py
- Evidence: test_the_simulated_sources_answer_as_of_the_day, test_known_seat_revision_matches_the_schedule, test_each_shock_flags_on_the_day_it_becomes_known

### MOD-20 [C] customer.py
- File: src/hotel_market/customer.py
- Owns: everything specific to one market, read from its customer file ([[DEC-41]]): load(path) turns the TOML into a Customer ([[DAT-27]]) with its hotels ([[DAT-04]], each competitor at an offset from the hotel's start rate), the cost share and rate limits, the detect thresholds, the hold period, the minimum value at stake, the booking curve ([[CON-01]]) and the target ([[RUL-58]]), and refuses a target outside TARGETS ([[RUL-70]]) or a repeated hotel key. demo() is the demo market, loaded once and the default wherever no customer is given; demo_path() finds it through the HOTEL_MARKET_CUSTOMER variable, the working directory or the repository root. Both sides read it: the simulator to make the market, the agent to know its hotels and settings.
- Reads: [[MOD-02]] for the Hotel and Competitor types
- Writes: [[DAT-27]], [[DAT-04]]
- Tests: tests/test_customer.py
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_a_customer_file_with_a_bad_target_or_repeated_key_is_refused, test_without_a_customer_the_demo_market_is_the_default

### MOD-21 [C] stored.py
- File: src/hotel_market/stored.py
- Owns: the four sources read from stored tables ([[DAT-28]], [[DEC-42]]): StoredBookings over daily_bookings, StoredRateShops over rate_shops (each shop day read once, the medians computed as statistics.median computes them), StoredSchedules over schedule_snapshots and StoredEvents over events, each answering as of the day asked; connect(), which opens the DuckDB file and creates the tables from sql/schema.sql (SCHEMA_FILE); write_snapshot(), which copies one day of any Sources into the feed tables, and write_decisions(), which stores a day's flags, plans (plan_rows, with the exact rates and estimates) and decisions, both deleting the day's rows first in one transaction; and the readers of a run, state_before() for an agent's hold and advice, rate_changes_before() for the simulator's playback, decided_on(), records_on(), decisions_file() and plan_differences(). TABLES ([[RUL-72]]) and OPENING_DAY ([[RUL-73]]) live here. It imports nothing from the simulator and is one of the modules the import test covers.
- Reads: [[MOD-17]] (the interfaces), [[MOD-08]] (the Entry, for the plan and decision rows), [[MOD-20]] (the hotels), [[MOD-02]]; never the simulator ([[DEC-40]])
- Writes: [[DAT-28]]; [[DAT-25]] as their second implementation
- Tests: tests/test_stored.py
- Evidence: test_a_60_day_run_through_the_tables_gives_the_same_decisions_file, test_the_stored_sources_answer_as_the_simulated_ones_do, test_running_a_day_twice_leaves_the_tables_unchanged, test_replaying_a_past_day_reproduces_its_plans_exactly

### MOD-22 [C] scripts/live_audit.py
- File: scripts/live_audit.py
- Owns: the measured live run and its audit, outside the package: a Recorder that stands in for the SDK and notes each call's tokens, time, stop reason and answering model, so that ClaudeClient's request stays the one in [[MOD-09]]; live_run(), the command's run for a seed with that client, which also writes calls.jsonl and sends the anthropic-workspace-id header when ANTHROPIC_WORKSPACE_ID is set; audit(), which reads the cache ([[DAT-17]]) and prints every reason, every declined plan, every figure in a reason that is not quoted from the request (quoted means, sentence by sentence, one of the figures of a display string that appears whole in the same sentence, a whole number the request holds as it is, a figure inside a name such as "raise 5%", or a bare dollar figure in a sentence that carries "more than holding" when the request holds that figure as a gain over holding, the one phrase the prompt lets a sentence write once for several gains; a range such as "12–14%" is read as its two ends, figures with different units are kept apart, and one end of a request range on its own is not a quotation), and every sentence that quotes nothing from the request; and the token, time and cost totals at the list prices written in the file. The recorded run it audits in the tests is [[DAT-29]]; it settled [[UNK-01]], [[UNK-02]] and [[UNK-09]].
- Reads: [[MOD-12]] (run, summary), [[MOD-09]] (ClaudeClient, HOLD)
- Writes: calls.jsonl beside the run's decisions.jsonl and cache/
- Tests: tests/test_live_audit.py, on made-up reasons and on the recorded run
- Evidence: test_a_range_in_a_reason_is_read_as_its_two_ends, test_the_requests_display_strings_and_whole_numbers_are_what_a_reason_may_quote, test_a_sentence_that_lists_several_gains_may_write_more_than_holding_once, test_the_audit_reads_a_cache_and_reports_what_is_not_in_the_request, test_the_recorded_live_run_of_seed_7_passes_the_audit
