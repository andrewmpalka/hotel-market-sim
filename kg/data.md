# Data

The data structures that pass between modules, in the order the loop makes
them: the schedule, the world and the customer, the books, the detect table,
the plans, the model's request and answer, and what the command writes.

### DAT-01 [C] The schedule table
- File: src/hotel_market/schedule.py
- Made by: build_schedule(as_of_day), one row per flight per operating date, as the schedule was known on that simulation day
- Columns: EXPANDED_ID, OPERATING_DATE_LOCAL, FLIGHT_NUMBER, MARKETING_CARRIER_IATA, OPERATING_CARRIER_IATA, IS_CODESHARE, CODESHARE_INFO, IS_WETLEASE, SERVICE_TYPE_IATA, EFFECTIVE_DATE, DISCONTINUE_DATE, IS_OPERATING_MONDAY to IS_OPERATING_SUNDAY, DEPARTURE_STATION_CODE_IATA, DEPARTURE_COUNTRY_CODE_IATA, DEPARTURE_STATE_PROVINCE_CODE_IATA, DEPARTURE_CITY_CODE_IATA, PASSENGER_DEPARTURE_TIME_LOCAL, ARRIVAL_STATION_CODE_IATA, ARRIVAL_COUNTRY_CODE_IATA, ARRIVAL_STATE_PROVINCE_CODE_IATA, ARRIVAL_CITY_CODE_IATA, EQUIPMENT_SUBTYPE_CODE_IATA, FIRST_CLASS_SEATS, BUSINESS_CLASS_SEATS, ECONOMY_CLASS_SEATS, FLIGHT_DISTANCE
- Source: the column names follow Cirium's published schedule data dictionary. Every row is synthetic; the repository contains no Cirium data and has no affiliation with Cirium. The carrier codes are invented, and any match with a real airline's code is a coincidence.
- Traps: codeshare rows repeat an operating row's seats, the type U row is a bus sold under a flight number, and the SLC flights land at QMS, the city's second airport. seats_by_day drops the first two and groups arrivals by city.
- Read by: [[MOD-01]] only; the rest of the package reads [[DAT-02]]
- Evidence: test_summing_by_arrival_station_misses_the_second_airport, test_summing_with_type_u_rows_counts_the_bus

### DAT-02 [C] Seats by day, seat change and seat revision
- File: src/hotel_market/schedule.py
- Made by: seats_by_day(schedule), a Series of arriving seats per simulation day 0 to 149; seat_change(as_of_day), the fractional change against the schedule with no shocks; seat_revision(as_of_day), the fractional change against the schedule known one day earlier
- Values: 4,244 seats on a normal day and 3,326 on Tuesdays and Saturdays before any shock; seat_change(21) is +17% for day 55
- Read by: [[MOD-04]] (seat_change, cached once per filing day), [[MOD-07]] (seat_revision, zero except on filing days)
- Evidence: test_normal_day_has_4244_seats, test_tuesdays_and_saturdays_have_3326_seats, test_known_seat_revision_matches_the_schedule

### DAT-03 [C] Route and Shock
- File: src/hotel_market/schedule.py
- Fields: Route(origin, origin_city, origin_state, marketing, operating, flights, equipment, distance, first_flight_number, reduced_tue_sat, codeshare_partner, destination, service_type, periods); Shock(known_day, kind "add" or "suspend", start_day, end_day, routes, origin, marketing)
- Held in: BASE_ROUTES (13 routes, one of them the bus) and AIR_SHOCKS ([[SHK-02]], [[SHK-04]]); routes_as_of(as_of_day) applies the shocks known by a day
- Read by: [[MOD-01]]
- Evidence: test_seat_change_as_of_day_21_is_plus_17_percent_for_day_55

### DAT-04 [C] Hotel, Competitor and the customer's hotels
- File: src/hotel_market/world.py
- Fields: Hotel(key, name, rooms, start_rate, air_share, base_occupancy, weekday_factors, competitors, floor, ceiling, room_cost, row) with clamp(); Competitor(name, base_rate). [[MOD-20]] builds the hotels from the customer file ([[DAT-27]]): floor, ceiling and room_cost are the file's shares of the start rate ([[RUL-59]], [[RUL-60]], [[RUL-61]]), each competitor's base rate is the start rate at the file's offset, and row is the hotel's place in the file and in every array indexed by hotel. Customer.hotels lists them and Customer.hotel(key) finds one.
- Values: convention 400 rooms at $220, air share 0.60, base occupancy 0.75; full-service 250 at $190, 0.45, 0.75; lifestyle 120 at $240, 0.50, 0.75; airport 150 at $140, 0.80, 0.85 ([[DEC-14]]). Each hotel has four competitors at -8%, -3%, +3% and +8% of its start rate, so its comp median starts level with its own rate ([[CON-03]]), and the weekday factors of CLAUDE.md's day-of-week table.
- Read by: every module after [[MOD-02]]
- Evidence: test_hotels_match_the_table, test_each_hotel_has_four_competitors_within_10_percent_of_its_rate, test_day_of_week_factors_match_the_table, test_the_demo_file_describes_the_market_in_claude_md

### DAT-05 [C] Event and RateCut
- File: src/hotel_market/shocks.py
- Fields: Event(name, known_day, start_day, end_day, hotels, uplift, comp_rate_raise) with covers(hotel_key, stay_day), defined at the boundary in [[MOD-17]] so that the agent and the simulator share it; RateCut(known_day, start_day, end_day, hotel, competitors, cut) with covers(hotel_key, competitor, stay_day), the simulator's alone
- Held in: EVENTS ([[SHK-01]]) and RATE_CUTS ([[SHK-03]])
- Read by: [[MOD-04]], [[MOD-05]], [[MOD-19]] (which hands the events to the agent through [[DAT-25]])
- Evidence: test_shocks_name_hotels_and_competitors_that_exist, test_convention_raises_downtown_demand_35_percent_on_days_45_to_48_from_day_10

### DAT-06 [C] The rate shop
- File: src/hotel_market/shops.py
- Made by: comp_rates(shop_day, hotel, stay_day, seed), a dict of competitor name to rate as seen on the shop day; comp_median(...), the median of those four. The noise behind them is one read-only array per seed, shape (hotels, competitors, stay dates), drawn on the seed's noise stream [[RUL-20]].
- Read by: [[MOD-06]] (bookings scale with rate over comp median), [[MOD-07]] (rate against median, median change since yesterday), [[MOD-08]] (estimates)
- Evidence: test_comp_median_moves_only_when_a_shock_becomes_known, test_hotel_starts_level_with_its_comp_median

### DAT-07 [C] Books
- File: src/hotel_market/bookings.py
- Fields: rooms (int, hotels x stay dates), revenue (float, same shape), rates (float, same shape, starting at each hotel's start rate), and the random numbers for every draw of the run: one per hotel and stay date for the preload, one per day, hotel and stay date for the loop ([[DEC-22]]). The daily log, shape (days, hotels, stay dates): daily_rooms (what each day's draw took), daily_rates (the rate in force that day) and daily_medians (the competitor median shopped that day), zero outside the day's window, plus preload (the rooms loaded before day 0). The log is what [[MOD-19]] serves the agent from, as of any day. Methods: book(day), set_rates(changes), and the measures occupancy, average_rate, revpar, room_revenue and contribution over a range of stay dates ([[MEA-01]] to [[MEA-05]]).
- Written by: [[MOD-06]]; the agent's rate changes arrive through set_rates after each day's bookings
- Read by: [[MOD-19]], [[MOD-12]]
- Evidence: test_day_0_starts_with_the_bookings_made_before_the_run, test_contribution_is_revenue_minus_the_cost_of_every_room_sold, test_the_simulated_sources_answer_as_of_the_day

### DAT-08 [C] The detect table
- File: src/hotel_market/detect.py
- Made by: detect_numbers(day, sources), one row per hotel and stay date in the day's window, from the four sources ([[DAT-25]])
- Columns: day, hotel, stay_day, days_out, rooms, pace_gap, pace_threshold, expected_demand (the forecast as of the day, which is all the planner needs), seat_change, seat_revision, rate, comp_median, rate_vs_median, median_change, new_event, shock_known, causes
- Read by: [[MOD-07]] (flags), [[MOD-08]] (the flag's rows feed the candidates and the numbers)
- Evidence: test_numbers_follow_the_definitions, test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd

### DAT-09 [C] Flag
- File: src/hotel_market/detect.py
- Fields: Flag(day, hotel, first_stay, last_stay, causes), frozen. Consecutive stay dates of a hotel with the same causes make one flag; a pace cause alone is dropped on a stay date under the hold.
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
- Fields: Candidate(name, rates by stay day clamped to the floor and ceiling, estimate, band). The names are the entries of [[RUL-43]], plus [[RUL-42]] when the comp median dropped. band is None unless the cautious rule is on ([[CON-11]]); then it is the estimate at the band's low and high elasticity.
- Written by: [[MOD-08]]
- Read by: [[MOD-08]], [[MOD-09]], [[MOD-12]]
- Evidence: test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits

### DAT-12 [C] WeekdayGroup
- File: src/hotel_market/plan.py
- Fields: WeekdayGroup(weekday, candidates with hold first, cautious); stays, hold, best (max estimate, hold wins a tie; under the cautious rule the highest of the candidates that replace hold, else hold), gain (best over hold), gains(candidate) (over hold at the band's low elasticity, at the estimate, and at the high one), replaces_hold(candidate) (the cautious rule: ahead of hold at the estimate and at both ends of the band; the minimum [[RUL-67]] applies to the whole plan through Entry.queued, [[DEC-43]]) and rejected_at_an_end (the candidates ahead of hold at the estimate that the band rejected).
- Written by: [[MOD-08]]
- Read by: [[MOD-08]], [[MOD-09]], [[MOD-12]]
- Evidence: test_after_the_new_flights_the_airport_raises_every_night_close_to_full, test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue, test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held

### DAT-13 [C] FlagNumbers and Range
- File: src/hotel_market/plan.py
- Fields: FlagNumbers(days_out, rooms_on_books, unsold_rooms, remaining_demand, pace_gap, seat_change, seat_revision, rate, comp_median, rate_vs_median, median_change, new_event), the detect numbers over a flag's stay dates, rounded, for the model and the log. The six numbers that vary across the stay dates, and days_out, are each a Range(lowest, highest), frozen, which iterates as its two ends for the wording helpers and writes itself as the named pair {"lowest": x, "highest": y} in the log line and the stored tables, while the model request carries it as one phrase ([[DAT-16]], [[DEC-44]]); lowest_highest() makes one. band_json() writes a candidate's two band estimates as {"at_low_elasticity", "at_high_elasticity"}, named by the end of the band because the low elasticity can give the higher estimate.
- Written by: [[MOD-08]]
- Read by: [[MOD-09]] (in the request and the template reason), [[MOD-12]] (the printed entry)
- Evidence: test_the_request_holds_each_entrys_plan_and_hold_as_its_only_options, test_every_figure_in_the_request_is_a_display_string, test_without_a_client_the_template_accepts_the_plan_and_quotes_the_numbers

### DAT-14 [C] Entry
- File: src/hotel_market/plan.py
- Fields: Entry(day, hotel, first_stay, last_stay, causes, numbers, weekdays, action, reason, reason_source, pricing, minimum, target); id "first-last", changed_weekdays, plan (the changes in words), value_at_stake (summed over the days that change), queued (value at stake >= minimum, the customer's [[RUL-67]]), new_rates, current_rates, rejected_at_an_end (cautious only: the candidates the band rejected, over the days of the week), to_json(), which adds target only when it is not contribution, so that a line for the demo market reads as before. One per flag. pricing ([[DAT-21]]) is the elasticity every candidate's estimate assumed; target ([[RUL-58]]) is what the estimates counted.
- Written by: [[MOD-08]]; [[MOD-10]] sets action, reason and reason_source and gives the pricing
- Read by: [[MOD-09]], [[MOD-10]], [[MOD-12]]
- Evidence: test_a_plan_lists_its_changes_by_day_of_week, test_entries_below_the_minimum_are_held_and_stay_out_of_the_queue

### DAT-15 [C] Advice
- File: src/hotel_market/agent.py
- Fields: Advice(day, hotel, stay_day, event, reason); to_json() marks it "simulated": false. A two-night minimum stay on an event's peak night, once per hotel and event ([[DEC-10]]).
- Written by: [[MOD-10]]
- Read by: [[MOD-12]]
- Evidence: test_minimum_stay_advice_is_given_once_per_hotel_and_event_and_not_simulated

### DAT-16 [C] The model request
- File: src/hotel_market/model.py
- Made by: request_for(day, hotel, entries): day; hotel (name, rooms, floor, ceiling, cost_per_occupied_room); elasticity, the entries' shared pricing ([[DAT-21]]: elasticity, mode, standard_error, prior, observations, and under the cautious rule cautious and band), so that a change of elasticity changes the digest; target, only when it is revenue ([[RUL-58]]), so that a change of target does too; entries, each with id, stay_dates, what_changed, numbers ([[DAT-13]]), by_day_of_week (day, stay_dates, candidates with rates, estimated_contribution and versus_hold, plus estimated_contribution_band and versus_hold_band under the cautious rule, best), plan, value_at_stake and options [plan, "hold"]. Every figure in it is a display string written by the formatters in [[MOD-11]] in place of the raw number, which stays in the log line and the stored tables ([[DEC-44]]): dollars to the dollar for a rate, a median, a floor, a ceiling or a cost, to the nearest $10 for an estimate; a signed quantity as a phrase with its direction in words and no sign, "14.6% below the median", "up 15.0%", "44 rooms ahead of pace", "$120 less than holding"; rooms to the room; an elasticity with up to two decimals; a day as its number. A range is one phrase, "10.7% to 14.6% below the median", "up 17.0% to 21.6%", "2.5% below to 2.5% above the median", "$220 to $242", "45 to 48", the single value when both ends read the same; a candidate's band values are named by the end of the band. The mode reads "assumed" for the default pricing ([[RUL-75]]). Every number in it comes from code ([[RUL-01]]). Its sorted-keys JSON is digested for the cache key ([[DEC-23]]).
- Written by: [[MOD-09]]
- Read by: the model, the template, and [[MOD-09]]'s check of the answer
- Evidence: test_the_request_holds_each_entrys_plan_and_hold_as_its_only_options, test_every_figure_in_the_request_is_a_display_string, test_the_schema_limits_ids_and_choices_to_the_requests_options, test_the_request_carries_the_elasticity_and_its_digest_changes_with_it, test_the_three_values_reach_the_model_request

### DAT-17 [C] The cache record
- File: src/hotel_market/model.py
- Where: cache/seed<seed>/day<DDD>_<hotel key>.json, one file per model call, for the default mode; another elasticity mode asks other questions and keeps its answers in cache/seed<seed>-<mode>/, such as seed7-learn-1, and a revenue target adds -revenue to the folder, such as seed7-revenue
- Fields: request_digest (sha256 of the request's sorted-keys JSON), request, source "model", decisions (id, choice, reason per entry). Template answers are not cached ([[DEC-25]]); a file from an older version that holds one is ignored and overwritten.
- Written by: [[MOD-09]]
- Read by: [[MOD-09]] on a rerun or a replay; a digest that does not match the request raises StaleCache
- Evidence: test_ask_calls_the_model_once_and_then_reads_the_cache, test_a_cache_written_for_another_request_is_refused, test_a_template_answer_cached_by_an_older_version_is_ignored_and_replaced, test_a_learn_run_keeps_its_own_cache_and_says_where_its_estimates_ended

### DAT-18 [C] A decisions.jsonl line
- File: src/hotel_market/plan.py
- Made by: Entry.to_json() in [[MOD-08]] and Advice.to_json() in [[MOD-10]]; [[MOD-12]] writes one line per entry and advice, by day, entries before advice
- Fields of an entry line: day, hotel, stays [first, last], causes, numbers ([[DAT-13]], its ranges as named pairs), elasticity (the pricing: elasticity, mode as the command line names it, standard_error, prior, observations, and under the cautious rule cautious and band as a named pair), by_weekday (weekday, stays, candidates with name, rates as a named pair, estimate and under the cautious rule band named by its ends, best, gain), plan, value_at_stake, queued, action, new_rates (null when held), reason, reason_source ("code", "template" or "model"), simulated true, under the cautious rule rejected_at_an_end, and under a revenue target target. The line holds raw numbers, not the request's display strings. An advice line has day, hotel, stays, causes, event, action, value_at_stake null, reason, simulated false.
- Read by: nothing in the package; it is the record a person reads
- Evidence: test_decisions_jsonl_has_one_line_per_flag_and_advice, test_the_log_lists_every_entry_and_advice_in_order

### DAT-19 [C] SeedResult
- File: src/hotel_market/cli.py
- Fields: SeedResult(seed, contribution_change, revenue_change, rate_changes, estimated, estimates, rejected_at_an_end, shock_changes, shock_gain, other_changes, other_gain), frozen: one seed of a sweep, the agent run against the fixed-rate run over stay dates 0 to 149. estimated is what the accepted plans were estimated to earn over holding; estimates maps (day, hotel key) to the learned Estimate ([[DAT-23]]) in learn mode and is empty otherwise; rejected_at_an_end counts the candidates the cautious band rejected; the shock fields are the plans whose causes include one of [[RUL-55]] and the target's change (contribution, or room revenue under a revenue target) on the stay dates they changed, the other fields the same for every other plan, on the stay dates only those changed.
- Written by: [[MOD-12]] (sweep)
- Read by: [[MOD-12]] through [[DAT-24]] (the seeds table, the arm table and the estimate table)
- Evidence: test_the_sweep_gives_each_seeds_change_over_the_fixed_run, test_the_seeds_command_prints_each_seed_and_the_mean_and_range

### DAT-20 [C] Comparison
- File: src/hotel_market/cli.py
- Fields: Comparison(name, fixed_revenue, agent_revenue, fixed_contribution, agent_contribution), frozen, with revenue_change and contribution_change. One row of a summary table: a hotel, or all four. The summary prints one table over every stay date and one over only the stay dates the agent changed.
- Written by: [[MOD-12]]
- Read by: [[MOD-12]]
- Evidence: test_the_summary_reports_revenue_and_contribution_for_both_runs, test_the_summary_compares_both_runs_on_the_changed_pairs

### DAT-21 [C] Pricing
- File: src/hotel_market/plan.py
- Fields: Pricing(elasticity, mode, standard_error, prior, observations, cautious), frozen: the elasticity a day's estimates assume and where it came from. mode is one of [[RUL-49]]; standard_error, prior and observations are set in learn mode only; cautious turns on the rule in [[CON-11]], and band is then the elasticities [[RUL-54]] standard errors either side of the estimate, clamped to [[RUL-51]] and [[RUL-52]]. TRUE_PRICING is ORACLE_ELASTICITY ([[RUL-56]]) in mode "true". to_json() is the log line's elasticity field, with the band as a named pair; cautious and band appear in it only when the rule is on. The request's elasticity field is built from the same record by [[MOD-09]], every number a figure with its display string and the mode named for the model ([[RUL-75]]).
- Written by: [[MOD-10]], once per hotel and day
- Read by: [[MOD-08]] (the estimate), [[MOD-09]] (the request and the template's sentence), [[MOD-12]] (the printed entry)
- Evidence: test_each_mode_records_the_elasticity_its_plans_assume, test_the_template_cites_a_fixed_or_learned_elasticity, test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side

### DAT-22 [C] ElasticityMode
- File: src/hotel_market/agent.py
- Fields: ElasticityMode(kind, value, cautious), frozen, parsed from "true", "fixed:X" or "learn:X" and printed back the same way, with " cautious" after a learn mode under the cautious rule. kind is one of [[RUL-49]]; value is ORACLE_ELASTICITY ([[RUL-56]]) for true, the fixed value, or the prior for learn; cautious is set by --cautious on every learn mode of the command. TRUE_MODE is the default.
- Written by: [[MOD-12]] from the --elasticity and --cautious options
- Read by: [[MOD-10]] (which pricing to give each day, and which cache folder to use), [[MOD-12]] (the arms of a sweep)
- Evidence: test_elasticity_modes_parse_and_print, test_a_mode_that_is_not_true_fixed_or_learn_is_rejected, test_a_cautious_agent_records_the_band_and_what_it_rejected

### DAT-23 [C] Observations and Estimate
- File: src/hotel_market/estimate.py
- Fields: Observations(stay_days, booking_days, bookings, log_ratio, log_baseline), frozen arrays with one row per (stay date, booking day) the estimate may use; Estimate(elasticity, standard_error, observations, prior, intercept), frozen, what the fit says as of a day. The elasticity is clamped to [[RUL-51]] to [[RUL-52]]; the standard error comes from the curvature of the fit with the prior included, so it is PRIOR_SD ([[RUL-50]]) with no observations.
- Written by: [[MOD-16]]
- Read by: [[MOD-10]] (the day's Pricing, and the record of every estimate), [[MOD-12]] (the estimate table of a sweep)
- Evidence: test_with_no_observations_the_estimate_is_the_prior, test_the_fit_recovers_a_known_elasticity_from_made_up_bookings, test_the_estimate_is_clamped_to_the_range

### DAT-24 [C] ArmResult
- File: src/hotel_market/cli.py
- Fields: ArmResult(mode, seeds, target), frozen: one elasticity mode over the seeds of a sweep, with changes (contribution) and revenue_changes, target_changes (whichever the customer scores on), wins (seeds where the agent run earned more of the target), rate_changes, estimated and realised (the accepted plans' estimates and the target's change, summed over the seeds), rejected_at_an_end, the shock and other changes and gains ([[RUL-55]]), and estimates_on(day). A sweep with one mode prints the seeds table; with several it prints one row per arm; either way it prints where the gain came from, and an estimate table for each learn arm on REPORT_DAYS ([[RUL-53]]).
- Written by: [[MOD-12]] (sweep)
- Read by: [[MOD-12]]
- Evidence: test_the_sweep_gives_each_seeds_change_over_the_fixed_run, test_the_seeds_command_prints_one_row_per_arm_and_a_learn_arms_estimates, test_a_revenue_target_arm_counts_wins_and_earnings_in_revenue

### DAT-25 [C] The four sources
- File: src/hotel_market/sources.py
- Fields: Bookings (on_books(as_of_day) by [hotel row, stay day] after that day's bookings; rates(as_of_day), each hotel's rate in force that day; history(as_of_day), a [[DAT-26]]); RateShops (competitor_rates(shop_day, hotel, stay_day); median(...), the median of those rates; median_history(as_of_day) by [shop day, hotel row, stay day]); Schedules (seats(as_of_day), the arriving seats by stay day as filed by the day, from which the interface computes seat_change(as_of_day) against the first schedule known and seat_revision(as_of_day) against the day before); Events (known(as_of_day)). Sources(bookings, shops, schedules, events) bundles one of each. Every method takes the day it is asked on and returns only what was known then ([[RUL-03]]).
- Written by: [[MOD-19]], the simulator's implementation, and [[MOD-21]], the one over the stored tables ([[DAT-28]])
- Read by: [[MOD-07]], [[MOD-18]], [[MOD-16]], [[MOD-10]]; nothing on the agent's side reads anything else ([[DEC-40]])
- Evidence: test_the_agent_reads_only_through_the_interfaces, test_the_simulated_sources_answer_as_of_the_day, test_the_stored_sources_answer_as_the_simulated_ones_do

### DAT-26 [C] BookingHistory
- File: src/hotel_market/sources.py
- Fields: BookingHistory(taken, rates, opening), frozen: the rooms each day's bookings took and the rate in force each day, by [day, hotel row, stay day] for the days before the one asked about, zero outside each day's window, and the rooms on the books before day 0 by [hotel row, stay day]. With the shop history it is what the estimator learns from.
- Written by: [[MOD-19]] from the Books' daily log ([[DAT-07]])
- Read by: [[MOD-16]]
- Evidence: test_the_simulated_sources_answer_as_of_the_day, test_the_estimate_uses_no_booking_made_on_or_after_as_of_day

### DAT-27 [C] Customer
- File: src/hotel_market/customer.py
- Fields: Customer(name, target, hotels, floor_share, ceiling_share, cost_share, pace_share, pace_noise_sd, seat_threshold, median_threshold, hold_days, min_value_at_stake, curve_days_out, curve_share), frozen: one market's description and settings, read from its TOML file by load(path) ([[MOD-20]]). hotel(key) finds a hotel ([[DAT-04]]); curve(days_out) is the booking curve ([[CON-01]]), linear between the pinned points; scores_contribution() says whether the target is contribution ([[RUL-58]]). The demo market's settings are the nodes [[RUL-57]] to [[RUL-69]].
- Written by: [[MOD-20]]; demo() holds the demo market, the default wherever no customer is given
- Read by: [[MOD-05]], [[MOD-06]], [[MOD-07]], [[MOD-08]], [[MOD-10]], [[MOD-16]], [[MOD-19]], [[MOD-12]]
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_the_command_takes_a_customer_file_and_a_target, test_without_a_customer_the_demo_market_is_the_default

### DAT-28 [C] The stored tables
- File: sql/schema.sql
- Tables: seven, each keyed by as_of_day, the day a row was known on, with day -1 ([[RUL-73]]) for the position before the first day. The feeds: daily_bookings (as_of_day, hotel, stay_day, rooms_taken, rooms_on_books, rate), one row per hotel and night in the day's window; rate_shops (as_of_day, hotel, stay_day, competitor, rate), every night from the shop day to the end of the schedule; schedule_snapshots (as_of_day, stay_day, seats), the schedule counted the way seats_by_day counts it; events (as_of_day, name, known_day, start_day, end_day, hotels, uplift, comp_rate_raise), one row per known event per day. The agent's output: flags (as_of_day, hotel, first_stay, last_stay, causes); plans (as_of_day, hotel, first_stay, last_stay, weekday, candidate, rates as JSON, estimate, versus_hold, band_low, band_high, is_best), one row per candidate with the exact numbers; decisions (as_of_day, position, hotel, first_stay, last_stay, causes, plan, value_at_stake, queued, action, reason, reason_source, elasticity, elasticity_mode, new_rates, simulated, event, record), one row per entry and advice with the decisions.jsonl line in record. The file's head lists the statements a cloud warehouse would change: the type names, PRIMARY KEY enforcement, the JSON text columns and the transaction.
- Written by: [[MOD-21]]'s write_snapshot (from any sources) and write_decisions (from an agent's entries and advice), driven by run-day in [[MOD-12]]; a day's rows are deleted and written again, so a day written twice is unchanged ([[DEC-42]])
- Read by: [[MOD-21]]'s four sources and its readers of a run, for run-day's playback and replay in [[MOD-12]]
- Evidence: test_the_schema_is_seven_tables_each_keyed_by_as_of_day, test_a_60_day_run_through_the_tables_gives_the_same_decisions_file, test_running_a_day_twice_leaves_the_tables_unchanged

### DAT-29 [C] The recorded live run
- File: tests/fixtures/live_seed7/
- Fields: the seven cache records ([[DAT-17]]) of one live run of seed 7 in the default mode with claude-opus-5-5, day010_convention.json to day034_convention.json, each holding the request, its digest and the model's decisions with their reasons; and calls.jsonl, one line per call with its input and output tokens, cache tokens, seconds, stop reason, answering model and request id, as [[MOD-22]] writes it. Copied from the run's cache/seed7/ and calls.jsonl on the day of the run, the fourth live run of the seed, made after each range became one phrase ([[DEC-44]]).
- Written by: scripts/live_audit.py's live run, then copied by hand; a change to the request makes the fixture stale, and the replay test then says to record a run again
- Read by: tests/test_live_audit.py: the audit on it finds no declined plan, no figure outside its request and no sentence without a request figure, and with it as the cache the run of seed 7 reads every answer from it, never calls the model and ends at +$28,818. [[UNK-01]], [[UNK-02]] and [[UNK-09]] rest on it, and anyone can replay the live run from it without a key.
- Evidence: test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_recorded_live_run_replays_without_a_key_and_gives_28818
