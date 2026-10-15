# Data

The data structures that pass between modules, in the order the loop makes
them: the schedule, the world and the customer, the books, the detect table,
the plans, the model's request and answer, and what the command writes.

### DAT-01 [C] The schedule table
- File: src/hotel_market/schedule.py
- Made by: build_schedule(as_of_day), one row per flight per operating date, as the schedule was known on that simulation day.
- Columns: EXPANDED_ID, OPERATING_DATE_LOCAL, FLIGHT_NUMBER, the marketing and operating carriers, IS_CODESHARE, CODESHARE_INFO, IS_WETLEASE, SERVICE_TYPE_IATA, EFFECTIVE_DATE, DISCONTINUE_DATE and the seven IS_OPERATING_ day flags.
- More columns: the departure and arrival station, country, state and city codes, PASSENGER_DEPARTURE_TIME_LOCAL, EQUIPMENT_SUBTYPE_CODE_IATA, the seats in three classes and FLIGHT_DISTANCE.
- Source: the column names follow Cirium's published schedule data dictionary ([[DEC-35]]). Every row is synthetic, and the carrier codes are invented.
- Traps: codeshare rows repeat an operating row's seats, and the type U row is a bus sold under a flight number. The SLC flights land at QMS, the city's second airport. seats_by_day drops the first two and groups arrivals by city.
- Read by: [[MOD-01]] only; the rest of the package reads [[DAT-02]]
- Evidence: test_summing_by_arrival_station_misses_the_second_airport, test_summing_with_type_u_rows_counts_the_bus

### DAT-02 [C] Seats by day, seat change and seat revision
- File: src/hotel_market/schedule.py
- Made by: seats_by_day(schedule), a Series of arriving seats per simulation day 0 to 149.
- Changes: seat_change(as_of_day) is the fractional change against the schedule with no shocks. seat_revision(as_of_day) is the change against the schedule known one day earlier. Both take the run's scenario ([[DEC-53]]).
- Values: 4,244 seats on a normal day and 3,326 on Tuesdays and Saturdays before any shock. seat_change(21) is +17% for day 55.
- Read by: [[MOD-04]] (seat_change, cached once per filing day), [[MOD-07]] (seat_revision, zero except on filing days)
- Evidence: test_normal_day_has_4244_seats, test_tuesdays_and_saturdays_have_3326_seats, test_known_seat_revision_matches_the_schedule

### DAT-03 [C] Route and Shock
- File: src/hotel_market/schedule.py
- Fields: Route(origin, origin_city, origin_state, marketing, operating, flights, equipment, distance, first_flight_number, reduced_tue_sat, codeshare_partner, destination, service_type, periods, time_shift).
- Shock: Shock(known_day, kind of [[RUL-89]], start_day, end_day, routes, origin, marketing, equipment, operating, flights, minutes). The last four serve the equipment, frequency and time kinds.
- Scenario: Scenario(name, shocks), frozen, with filing_days(). DEFAULT_SCENARIO holds AIR_SHOCKS, and SCENARIOS maps each name to its scenario ([[DEC-53]]). with_churn(scenario, seed) adds the seed's churn ([[SHK-07]]).
- Held in: BASE_ROUTES (13 routes, one of them the bus) and AIR_SHOCKS ([[SHK-02]], [[SHK-04]]). routes_as_of(as_of_day, scenario) applies the shocks known by a day.
- Read by: [[MOD-01]]
- Evidence: test_normal_day_has_4244_seats, test_seat_change_as_of_day_21_is_plus_17_percent_for_day_55

### DAT-04 [C] Hotel, Competitor and the customer's hotels
- File: src/hotel_market/world.py
- Fields: Hotel(key, name, rooms, start_rate, air_share, base_occupancy, weekday_factors, competitors, floor, ceiling, room_cost, row) with clamp(), and Competitor(name, base_rate).
- Built by: [[MOD-20]] from the customer file ([[DAT-27]]). Floor, ceiling and room_cost are the file's shares of the start rate ([[RUL-59]] to [[RUL-61]]).
- Offsets: each competitor's base rate is the start rate at its offset. row is the hotel's place in the file and in every array indexed by hotel.
- Values: convention: 400 rooms, $220, air share 0.60, base occupancy 0.75. Full-service: 250, $190, 0.45, 0.75. Lifestyle: 120, $240, 0.50, 0.75. Airport: 150, $140, 0.80, 0.85 ([[DEC-14]]).
- Comp sets: each hotel has four competitors at -8%, -3%, +3% and +8% of its start rate ([[CON-03]]). Its comp median therefore starts level with its own rate, and the weekday factors are the demo file's day-of-week table.
- Read by: every module after [[MOD-02]]; Customer.hotels lists the hotels and Customer.hotel(key) finds one
- Evidence: test_hotels_match_the_table, test_each_hotel_has_four_competitors_within_10_percent_of_its_rate, test_day_of_week_factors_match_the_table

### DAT-05 [C] Event and RateCut
- File: src/hotel_market/shocks.py
- Fields: Event(name, known_day, start_day, end_day, hotels, uplift, comp_rate_raise) with covers(hotel_key, stay_day). It is defined at the boundary in [[MOD-17]], so the agent and the simulator share it.
- Cut: RateCut(known_day, start_day, end_day, hotel, competitors, cut) with covers(hotel_key, competitor, stay_day), the simulator's alone.
- Held in: EVENTS ([[SHK-01]]) and RATE_CUTS ([[SHK-03]])
- Read by: [[MOD-04]], [[MOD-05]], [[MOD-19]], which hands the events to the agent through [[DAT-25]]
- Evidence: test_shocks_name_hotels_and_competitors_that_exist, test_convention_raises_downtown_demand_35_percent_on_days_45_to_48_from_day_10

### DAT-06 [C] The rate shop
- File: src/hotel_market/shops.py
- Made by: comp_rates(shop_day, hotel, stay_day, seed, hotel_change), a dict of competitor name to rate on the shop day. comp_median(...) is their median. hotel_change is the lagged change the competitors follow ([[DEC-51]]).
- Noise: one read-only array per seed, shape (hotels, competitors, stay dates), drawn on the seed's noise stream [[RUL-20]].
- Read by: [[MOD-06]] (bookings scale with rate over comp median), [[MOD-07]] (rate against median, median change since yesterday), [[MOD-08]] (estimates)
- Evidence: test_comp_median_moves_only_when_a_shock_becomes_known, test_hotel_starts_level_with_its_comp_median

### DAT-07 [C] Books
- File: src/hotel_market/bookings.py
- Fields: rooms (int, hotels x stay dates), revenue and rates (float, same shape). demand_bias ([[RUL-82]]), react ([[DEC-51]]), market_elasticity ([[RUL-87]]), scenario and churn ([[DEC-53]]) are the run's settings.
- Draws: the random numbers for every draw of the run ([[DEC-22]]). The preload has one per hotel and stay date, and the loop one per day, hotel and stay date.
- Log: daily_rooms, daily_rates and daily_medians, shape (days, hotels, stay dates), zero outside the day's window. preload holds the rooms loaded before day 0, and [[MOD-19]] serves the agent from the log as of any day.
- Methods: book(day) and set_rates(changes). hotel_change() and comp_median() serve the reaction ([[DEC-51]]), and starting_median() the market term ([[DEC-52]]). The five measures are [[MEA-01]] to [[MEA-05]].
- Written by: [[MOD-06]]; the agent's rate changes arrive through set_rates after each day's bookings
- Read by: [[MOD-19]], [[MOD-12]]
- Evidence: test_day_0_starts_with_the_bookings_made_before_the_run, test_contribution_is_revenue_minus_the_cost_of_every_room_sold, test_the_simulated_sources_answer_as_of_the_day

### DAT-08 [C] The detect table
- File: src/hotel_market/detect.py
- Made by: detect_numbers(day, sources), one row per hotel and stay date in the day's window, from the four sources ([[DAT-25]]).
- Columns: day, hotel, stay_day, days_out, rooms, pace_gap, pace_threshold, expected_demand, seat_change, seat_revision, rate, comp_median, rate_vs_median, median_change, new_event, shock_known and causes.
- Forecast: expected_demand is the forecast as of the day, which is all the planner needs.
- Read by: [[MOD-07]] (flags), [[MOD-08]] (the flag's rows feed the candidates and the numbers)
- Evidence: test_numbers_follow_the_definitions, test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd

### DAT-09 [C] Flag
- File: src/hotel_market/detect.py
- Fields: Flag(day, hotel, first_stay, last_stay, causes), frozen. Consecutive stay dates of a hotel with the same causes make one flag. A pace cause alone is dropped on a stay date under the hold.
- Written by: [[MOD-07]]
- Read by: [[MOD-08]], [[MOD-10]]
- Evidence: test_consecutive_stay_dates_with_the_same_causes_merge_into_one_flag

### DAT-10 [C] StayDate
- File: src/hotel_market/plan.py
- Fields: StayDate(stay_day, rate, comp_median, unsold, remaining_demand), frozen: what the estimate needs to know about one stay date of a flag. remaining_demand is expected demand x (1 - curve today).
- Written by: [[MOD-08]]
- Read by: [[MOD-08]]
- Evidence: test_estimate_is_expected_contribution_on_the_unsold_rooms

### DAT-11 [C] Candidate
- File: src/hotel_market/plan.py
- Fields: Candidate(name, rates by stay day clamped to the floor and ceiling, estimate, band). The names are the entries of [[RUL-43]], plus [[RUL-42]] when the comp median dropped.
- Band: None unless the cautious rule is on ([[CON-11]]); then it holds the estimate at the band's low and high elasticity.
- Written by: [[MOD-08]]
- Read by: [[MOD-08]], [[MOD-09]], [[MOD-12]]
- Evidence: test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits

### DAT-12 [C] WeekdayGroup
- File: src/hotel_market/plan.py
- Fields: WeekdayGroup(weekday, candidates with hold first, cautious, stay_dates), with stays, hold, best, gain (best over hold), gains(candidate), replaces_hold(candidate) and rejected_at_an_end.
- Best: the highest estimate, hold winning a tie. Under the cautious rule it is the highest of the candidates that replace hold, else hold.
- Cautious: gains(candidate) gives the gain over hold at the band's low elasticity, at the estimate and at the high one. replaces_hold() asks for a gain at all three, and rejected_at_an_end lists the candidates the band rejected.
- Minimum: the minimum [[RUL-67]] applies to the whole plan through Entry.queued ([[DEC-43]]).
- Stay dates: stay_dates keeps the StayDate records the estimates were made from, so a grader can score the candidates again ([[MOD-23]]). They are not in the log line.
- Used by: written by [[MOD-08]]; read by [[MOD-08]], [[MOD-09]] and [[MOD-12]]
- Evidence: test_after_the_new_flights_the_airport_raises_every_night_close_to_full, test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue, test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held

### DAT-13 [C] FlagNumbers and Range
- File: src/hotel_market/plan.py
- Fields: FlagNumbers holds the detect numbers over a flag's stay dates, rounded.
- Names: days_out, rooms_on_books, unsold_rooms, remaining_demand, pace_gap, seat_change, seat_revision, rate, comp_median, rate_vs_median, median_change and new_event.
- Range: the six numbers that vary across the stay dates, and days_out, are each a Range(lowest, highest), frozen. It iterates as its two ends for the wording helpers, and lowest_highest() makes one.
- Written as: the named pair {"lowest": x, "highest": y} in the log line and the stored tables. The model request carries it as one phrase ([[DAT-16]], [[DEC-44]]).
- Band: band_json() writes a candidate's two band estimates as {"at_low_elasticity", "at_high_elasticity"}, named by the end of the band. The low elasticity can give the higher estimate.
- Used by: written by [[MOD-08]]; read by [[MOD-09]] (the request and the template reason) and [[MOD-12]] (the printed entry)
- Evidence: test_the_request_holds_each_entrys_plan_and_hold_as_its_only_options, test_every_figure_in_the_request_is_a_display_string, test_without_a_client_the_template_accepts_the_plan_and_quotes_the_numbers

### DAT-14 [C] Entry
- File: src/hotel_market/plan.py
- Fields: Entry(day, hotel, first_stay, last_stay, causes, numbers, weekdays, action, reason, reason_source, pricing, minimum, target), one per flag.
- Derived: id "first-last", changed_weekdays, plan (the changes in words) and value_at_stake, summed over the days that change. queued means value at stake >= the minimum [[RUL-67]]; new_rates, current_rates and rejected_at_an_end follow.
- JSON: to_json() adds target only when it is not contribution, so that a line for the demo market reads as before. pricing ([[DAT-21]]) is the elasticity every estimate assumed, and target ([[RUL-58]]) is what the estimates counted.
- Written by: [[MOD-08]]; [[MOD-10]] sets action, reason and reason_source and gives the pricing
- Read by: [[MOD-09]], [[MOD-10]], [[MOD-12]]
- Evidence: test_a_plan_lists_its_changes_by_day_of_week, test_entries_below_the_minimum_are_held_and_stay_out_of_the_queue

### DAT-15 [C] Advice
- File: src/hotel_market/agent.py
- Fields: Advice(day, hotel, stay_day, event, reason), and to_json() marks it "simulated": false. It is a two-night minimum stay on an event's peak night, once per hotel and event ([[DEC-10]]).
- Written by: [[MOD-10]]
- Read by: [[MOD-12]]
- Evidence: test_minimum_stay_advice_is_given_once_per_hotel_and_event_and_not_simulated

### DAT-16 [C] The model request
- File: src/hotel_market/model.py
- Made by: request_for(day, hotel, entries) writes day, hotel (name, rooms, floor, ceiling, cost_per_occupied_room) and elasticity, the shared pricing ([[DAT-21]]). It adds target only when it is revenue ([[RUL-58]]), then the entries.
- Entry: id, stay_dates, what_changed, numbers ([[DAT-13]]), by_day_of_week, plan, value_at_stake and options [plan, "hold"].
- Weekday: day, stay_dates, best and the candidates with rates, estimated_contribution and versus_hold. Under the cautious rule each candidate also carries its band values, and all but hold the band_verdict ([[DEC-56]]).
- Figures: every figure is a display string from [[MOD-11]] in place of the raw number ([[DEC-44]]). Every number in it comes from code ([[RUL-01]]), and the mode reads "assumed" for the default pricing ([[RUL-75]]).
- Digest: a change of elasticity or target changes the request, and the sorted-keys JSON is digested for the cache key ([[DEC-23]]).
- Used by: written by [[MOD-09]], and read by the model, the template and [[MOD-09]]'s check of the answer
- Evidence: test_the_request_holds_each_entrys_plan_and_hold_as_its_only_options, test_every_figure_in_the_request_is_a_display_string, test_the_request_carries_the_elasticity_and_its_digest_changes_with_it

### DAT-17 [C] The cache record
- File: src/hotel_market/model.py
- Where: cache/seed<seed>/day<DDD>_<hotel key>.json, one file per model call, in the default mode and model. Another mode adds -<mode>, such as seed7-learn-1, a revenue target adds -revenue and another model adds -<model>.
- Fields: request_digest (sha256 of the request's sorted-keys JSON), request, source "model" and decisions (id, choice, reason per entry). The model field names the model asked, [[RUL-46]] by default.
- Template: template answers are not cached ([[DEC-25]]). A file from an older version that holds one is ignored and overwritten. A record from before the model field has none and still reads back ([[DAT-29]]).
- Written by: [[MOD-09]]
- Read by: [[MOD-09]] on a rerun or a replay; a digest that does not match the request raises StaleCache
- Evidence: test_ask_calls_the_model_once_and_then_reads_the_cache, test_a_learn_run_keeps_its_own_cache_and_says_where_its_estimates_ended, test_another_model_gets_its_own_cache_folder_and_record

### DAT-18 [C] A decisions.jsonl line
- File: src/hotel_market/plan.py
- Made by: Entry.to_json() in [[MOD-08]] and Advice.to_json() in [[MOD-10]]. [[MOD-12]] writes one line per entry and advice, by day, entries before advice.
- Entry line: day, hotel, stays [first, last], causes and numbers ([[DAT-13]], its ranges as named pairs). elasticity is the pricing, with the mode as the command line names it, market_elasticity ([[RUL-88]]) and level ([[DEC-54]]).
- More: by_weekday, plan, value_at_stake, queued, action, new_rates (null when held), reason and simulated true. reason_source is "code", "template", "model" or a client's name. The line holds raw numbers, not the request's display strings.
- By weekday: weekday, stays and the candidates with name, rates as a named pair, estimate, best and gain. Under the cautious rule a candidate's band is named by its ends, and the line adds rejected_at_an_end. A revenue target adds target.
- Advice line: day, hotel, stays, causes, event, action, value_at_stake null, reason and simulated false.
- Read by: nothing in the package; it is the record a person reads
- Evidence: test_decisions_jsonl_has_one_line_per_flag_and_advice, test_the_log_lists_every_entry_and_advice_in_order

### DAT-19 [C] SeedResult
- File: src/hotel_market/cli.py
- Fields: SeedResult(seed, contribution_change, revenue_change, rate_changes, estimated, estimates, rejected_at_an_end, shock_changes, shock_gain, other_changes, other_gain, entries, calls, counts, and five counts), frozen.
- Meaning: estimated is what the accepted plans were estimated to earn over holding. estimates maps (day, hotel key) to the learned Estimate ([[DAT-23]]) in learn mode. rejected_at_an_end counts the candidates the cautious band rejected.
- Shocks: the shock fields count the plans whose causes include one of [[RUL-55]] and the target's change on their stay dates. The other fields do the same for every other plan, on the stay dates only those changed.
- Bench: entries are the run's entries, calls its call records ([[DAT-30]]) and counts the oracle's labels on it ([[DAT-31]]). The bench tables sum them over an arm's seeds.
- Counts: flags, pace_flags and median_flags count the entries by cause ([[RUL-86]]). own_median_flags and repeat_changes are the reaction's, seat_flags and filings the schedule's, and the control_ fields the rule's ([[DEC-55]]).
- Written by: [[MOD-12]] (sweep). [[MOD-12]] reads it through [[DAT-24]] for the seeds, arm, estimate, bench and reaction tables.
- Evidence: test_the_sweep_gives_each_seeds_change_over_the_fixed_run, test_a_sweep_counts_the_shock_plans_apart_from_the_other_plans, test_a_sweep_with_reviewers_keeps_each_arms_entries_calls_and_counts

### DAT-20 [C] Comparison
- File: src/hotel_market/cli.py
- Fields: Comparison(name, fixed_revenue, agent_revenue, fixed_contribution, agent_contribution), frozen, with revenue_change and contribution_change. One row of a summary table: a hotel, or all four.
- Tables: the summary prints one table over every stay date and one over only the stay dates the agent changed.
- Written by: [[MOD-12]]
- Read by: [[MOD-12]]
- Evidence: test_the_summary_reports_revenue_and_contribution_for_both_runs, test_the_summary_compares_both_runs_on_the_changed_pairs

### DAT-21 [C] Pricing
- File: src/hotel_market/plan.py
- Fields: Pricing(elasticity, mode, standard_error, prior, observations, cautious, market_elasticity, level), frozen. It holds the elasticity a day's estimates assume and its source ([[RUL-49]]). level is the --level factor ([[DEC-54]]).
- Learn: standard_error, prior and observations are set in learn mode only. cautious turns on the rule in [[CON-11]]. band is then the elasticities [[RUL-54]] standard errors around the estimate, clamped to [[RUL-51]] and [[RUL-52]].
- Default: TRUE_PRICING is ORACLE_ELASTICITY ([[RUL-56]]) in mode "true". to_json() is the log line's elasticity field, with the band as a named pair. cautious and band appear only when the rule is on.
- Request: [[MOD-09]] builds the request's elasticity field from the same record. Every number is a display string, and the mode is named for the model ([[RUL-75]]). market_elasticity reaches the request only when set ([[DEC-52]]).
- Written by: [[MOD-10]], once per hotel and day
- Read by: [[MOD-08]] (the estimate), [[MOD-09]] (the request and the template's sentence), [[MOD-12]] (the printed entry)
- Evidence: test_each_mode_records_the_elasticity_its_plans_assume, test_the_template_cites_a_fixed_or_learned_elasticity, test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side

### DAT-22 [C] ElasticityMode
- File: src/hotel_market/agent.py
- Fields: ElasticityMode(kind, value, cautious, level), frozen, parsed from "true", "fixed:X" or "learn:X" and printed back the same way. A learn mode prints " cautious" and " level" after it for its flags.
- Meaning: kind is one of [[RUL-49]]. value is ORACLE_ELASTICITY ([[RUL-56]]) for true, the fixed value, or the prior for learn. --cautious and --level set their flags on every learn mode ([[DEC-54]]). TRUE_MODE is the default.
- Written by: [[MOD-12]] from the --elasticity and --cautious options
- Read by: [[MOD-10]] (which pricing to give each day, and which cache folder to use), [[MOD-12]] (the arms of a sweep)
- Evidence: test_elasticity_modes_parse_and_print, test_a_mode_that_is_not_true_fixed_or_learn_is_rejected, test_a_cautious_agent_records_the_band_and_what_it_rejected

### DAT-23 [C] Observations and Estimate
- File: src/hotel_market/estimate.py
- Fields: Observations(stay_days, booking_days, bookings, log_ratio, log_baseline), frozen arrays with one row per (stay date, booking day) the estimate may use.
- Estimate: Estimate(elasticity, standard_error, observations, prior, intercept), frozen, what the fit says as of a day. The elasticity is clamped to [[RUL-51]] to [[RUL-52]].
- Error: the standard error comes from the curvature of the fit with the prior included. With no observations it is PRIOR_SD ([[RUL-50]]).
- Written by: [[MOD-16]]
- Read by: [[MOD-10]] (the day's Pricing, and the record of every estimate), [[MOD-12]] (the estimate table of a sweep)
- Evidence: test_with_no_observations_the_estimate_is_the_prior, test_the_fit_recovers_a_known_elasticity_from_made_up_bookings, test_the_estimate_is_clamped_to_the_range

### DAT-24 [C] ArmResult
- File: src/hotel_market/cli.py
- Fields: ArmResult(mode, seeds, target, reviewer), frozen: one elasticity mode and one reviewer ([[DAT-32]]) over the seeds of a sweep.
- Derived: changes (contribution), revenue_changes, target_changes and wins, the seeds where the agent run earned more of the target. counts ([[DAT-31]]) and calls pool the seeds' counts and call records.
- Sums: rate_changes, estimated and realised (summed over the seeds), rejected_at_an_end, the shock and other changes and gains ([[RUL-55]]), and estimates_on(day).
- Printed: a sweep with one mode prints the seeds table, with several one row per arm. Both print where the gain came from and an estimate table per learn arm ([[RUL-53]]). The bench prints a table per mode and a ranking.
- Written by: [[MOD-12]] (sweep)
- Read by: [[MOD-12]]
- Evidence: test_the_sweep_gives_each_seeds_change_over_the_fixed_run, test_the_seeds_command_prints_one_row_per_arm_and_a_learn_arms_estimates, test_the_bench_command_prints_its_tables

### DAT-25 [C] The four sources
- File: src/hotel_market/sources.py
- Bookings: on_books(as_of_day) by [hotel row, stay day] after that day's bookings, and rates(as_of_day), each hotel's rate in force that day. history(as_of_day) is a [[DAT-26]].
- RateShops: competitor_rates(shop_day, hotel, stay_day), median(...), the median of those rates, and median_history(as_of_day) by [shop day, hotel row, stay day]. first_median(hotel, stay_day) is the median's starting level ([[DEC-52]]).
- Schedules: seats(as_of_day), the arriving seats by stay day as filed by the day. From them the interface computes seat_change(as_of_day) against the first schedule known and seat_revision(as_of_day) against the day before.
- Events: known(as_of_day). Sources(bookings, shops, schedules, events) bundles one of each. Every method returns only what was known on the day it is asked on ([[RUL-03]]).
- Written by: [[MOD-19]], the simulator's implementation, and [[MOD-21]], the one over the stored tables ([[DAT-28]])
- Read by: [[MOD-07]], [[MOD-18]], [[MOD-16]], [[MOD-10]]; nothing on the agent's side reads anything else ([[DEC-40]])
- Evidence: test_the_agent_reads_only_through_the_interfaces, test_the_simulated_sources_answer_as_of_the_day, test_the_stored_sources_answer_as_the_simulated_ones_do

### DAT-26 [C] BookingHistory
- File: src/hotel_market/sources.py
- Fields: BookingHistory(taken, rates, opening), frozen. taken holds the rooms each day's bookings took, and rates the rate in force each day. Both are by [day, hotel row, stay day] for the days before the one asked about.
- Values: zero outside each day's window; opening is the rooms on the books before day 0 by [hotel row, stay day]. With the shop history it is what the estimator learns from.
- Written by: [[MOD-19]] from the Books' daily log ([[DAT-07]])
- Read by: [[MOD-16]]
- Evidence: test_the_simulated_sources_answer_as_of_the_day, test_the_estimate_uses_no_booking_made_on_or_after_as_of_day

### DAT-27 [C] Customer
- File: src/hotel_market/customer.py
- Fields: Customer(name, target, hotels, floor_share, ceiling_share, cost_share, pace_share, pace_noise_sd, seat_threshold, median_threshold, hold_days, min_value_at_stake, curve_days_out, curve_share), frozen.
- Methods: hotel(key) finds a hotel ([[DAT-04]]), and curve(days_out) is the booking curve ([[CON-01]]), linear between the pinned points. scores_contribution() says whether the target is contribution ([[RUL-58]]).
- Settings: one market's description and settings, read from its TOML file by load(path) ([[MOD-20]]). The demo market's settings are the nodes [[RUL-57]] to [[RUL-69]].
- Written by: [[MOD-20]]; demo() holds the demo market, the default wherever no customer is given
- Read by: [[MOD-05]], [[MOD-06]], [[MOD-07]], [[MOD-08]], [[MOD-10]], [[MOD-12]], [[MOD-16]], [[MOD-19]]
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_the_command_takes_a_customer_file_and_a_target, test_without_a_customer_the_demo_market_is_the_default

### DAT-28 [C] The stored tables
- File: sql/schema.sql
- Tables: seven, each keyed by as_of_day, the day a row was known on. Day -1 ([[RUL-73]]) holds the position before the first day.
- Feeds: daily_bookings (as_of_day, hotel, stay_day, rooms_taken, rooms_on_books, rate) has a row per hotel and night in the window. rate_shops (as_of_day, hotel, stay_day, competitor, rate) runs from the shop day to the schedule's end.
- More feeds: schedule_snapshots (as_of_day, stay_day, seats) is counted the way seats_by_day counts. events (as_of_day, name, known_day, start_day, end_day, hotels, uplift, comp_rate_raise) has one row per known event per day.
- Output: flags (as_of_day, hotel, first_stay, last_stay, causes). plans has one row per candidate with its exact rates, estimate, versus_hold, band and is_best. decisions has one row per entry and advice, with the log line in record.
- Warehouse: the file's head lists the statements a cloud warehouse would change. They are the type names, PRIMARY KEY enforcement, the JSON text columns and the transaction.
- Used by: [[MOD-21]] writes them with write_snapshot and write_decisions, driven by run-day in [[MOD-12]], deleting a day's rows first ([[DEC-42]]). Its four sources and run readers read them back for run-day's playback and replay.
- Evidence: test_the_schema_is_seven_tables_each_keyed_by_as_of_day, test_a_60_day_run_through_the_tables_gives_the_same_decisions_file, test_running_a_day_twice_leaves_the_tables_unchanged

### DAT-29 [C] The recorded live run
- File: tests/fixtures/live_seed7/
- Fields: the seven cache records ([[DAT-17]]) of one live run of seed 7 in the default mode with claude-opus-5-5. The files day010_convention.json to day034_convention.json each hold the request, its digest and the model's decisions.
- Calls: calls.jsonl, one line per call, as [[MOD-22]] wrote it before [[DAT-30]]. A line holds the tokens, seconds, stop reason, answering model and request id. It lacks the fields [[DAT-30]] added later.
- Origin: copied from the run's cache/seed7/ and calls.jsonl on the day of the run. It was the fourth live run of the seed, made after each range became one phrase ([[DEC-44]], [[RES-08]]).
- Stale: a change to the request makes the fixture stale, and the replay test then says to record a run again.
- Written by: scripts/live_audit.py's live run, then copied by hand
- Read by: tests/test_live_audit.py. The audit on it finds no declined plan, no figure outside its request and no sentence without a request figure. With it as the cache, seed 7 replays without a key and ends at +$28,818 ([[RES-09]]).
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_recorded_live_run_replays_without_a_key_and_gives_28818

### DAT-30 [C] The call record
- File: src/hotel_market/model.py
- Where: calls.jsonl, one line per call to a Measured client, at the path its maker gives. live_audit.py replaces its file each run ([[MOD-22]]); the bench appends to its own. counted() merges a digest's records into one ([[DAT-17]]).
- Fields: day, hotel (the request's hotel name) and request_digest. asked is the model asked and model the one that answered. Then input_tokens, output_tokens, both cache token counts, seconds, stop_reason, fallback and request_id.
- Flags: retries counts the attempts after the first. bad_attempt is true when any attempt ended without a valid answer. failed is true when the request ended without one. error names the last error's class, or is null.
- Retries: an SDK error ([[RUL-78]]) is asked again after a backoff ([[RUL-77]]) and an invalid answer at once. RETRIES bounds them ([[RUL-76]]). A refusal is not asked again: the API ran the fallback. The record lands before the raise.
- Written by: [[MOD-09]], Measured.complete(), which also keeps the records in memory as calls. The tokens and seconds sum over the attempts.
- Read by: [[MOD-22]] for the token, time and cost totals; [[MOD-23]] for invalid_answers(), failed_requests() and retries()
- Evidence: test_a_measured_client_records_one_call, test_a_call_record_names_its_day_hotel_and_request_digest, test_a_measured_client_retries_an_sdk_error_after_a_backoff, test_a_request_that_fails_past_retries_still_leaves_a_record

### DAT-31 [C] DeclineCounts
- File: src/hotel_market/bench.py
- Fields: DeclineCounts(queued, accepted, declined, oracle, agreed, loss, caught), frozen. Adding two sums the counts, so an arm's rates are pooled over its seeds and not averaged.
- Rates: accept_rate, precision, recall, f1 and dollar_recall follow [[MEA-07]] to [[MEA-11]], with the same nan rules. of(entries) labels a run with the oracle after the fact.
- Written by: [[MOD-12]] (sweep), one per seed and arm
- Read by: [[MOD-12]] for the bench tables, summed over an arm's seeds
- Evidence: test_decline_counts_pool_the_step_1_measures, test_a_sweep_with_reviewers_keeps_each_arms_entries_calls_and_counts

### DAT-32 [C] Reviewer
- File: src/hotel_market/bench.py
- Fields: Reviewer(name, model, make), frozen: an arm's reviewer. name labels the row, model is the model it asks (None when none) and make builds its client. TEMPLATE, ORACLE, oracle(bias, market, share) and live(model) are the kinds.
- Client: client_for(agent) builds the client once the agent exists. The template has none. The oracle reads agent.today ([[DEC-47]]) and takes the demand bias ([[DEC-50]]). A model gets a measured Claude client ([[DAT-30]]).
- Model: the agent takes the reviewer's model, so the arm's cache folder names it ([[DEC-23]]). live is true when the arm asks a model, and the bench then prints its calls, tokens, latency and cost.
- Written by: [[MOD-12]] (the bench command, from --model) and tests
- Read by: [[MOD-12]] (sweep)
- Evidence: test_the_three_kinds_of_reviewer_make_their_clients, test_a_sweep_with_reviewers_keeps_each_arms_entries_calls_and_counts

### DAT-33 [C] The demo file
- File: sql/demo.sql
- Tables: eight from sql/demo.sql beside the seven stored tables ([[DAT-28]]), and run (seed, reason_source), which demo_data.py creates for the sidebar. Every date reads as "Thu 18 Feb [45]" ([[DEC-58]]).
- Hotels and days: hotels (position, key, name, rooms, start_rate, rate_axis_low, rate_axis_high). days (as_of_day, label, stay_window). news (as_of_day, hotel, position, kind, text) holds what became known, and one row says nothing did.
- Chart: stay_dates (as_of_day, hotel, stay_day, label, tick, rate, comp_median, rooms_on_books, pace, flagged, causes, flag, planned_rate), one row per stay date in the window. planned_rate is NULL without an accepted plan.
- Queue: queue (as_of_day, hotel, position, stays, causes, plan, value, value_text, reason, reason_source, queued, outcome, alternative, alternative_text). The outcome is accepted, declined or held. A held flag names its best alternative.
- Scorecard: scorecard (as_of_day, hotel, title, nights, position, measure, agent, fixed, delta, value_text, delta_text) for the nights already stayed, none on day 0. outcome holds the same tiles once every stay date is complete.
- Gains: gains (hotel, title, stay_day, label, tick, agent, fixed, difference), the contribution by stay date once complete. The scorecard tables hold each hotel and all together, under the key all ([[RUL-107]]).
- Evidence: test_the_file_holds_the_stored_tables_for_every_day_and_the_pages_tables, test_the_chart_rows_mark_the_flagged_stay_dates_and_carry_the_planned_rate, test_the_scorecard_counts_the_nights_already_stayed
