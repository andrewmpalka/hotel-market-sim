# Rules and constants

The three project rules, then every named constant with its value, file and
kind, grouped by module, then the settings of the customer file. A constant
is a parameter when its value changes the results, or a label when it is a
name or a string. The index lists the parameters one per line and the labels
together. `kg_check.py` compares each `Value:` with the code and fails when
they differ, when a constant has no kind, or when a constant in the code has
no node here. The cited test confirms what the constant means; the checker
confirms its value. A constant that moved to another file keeps its node,
marked [H], with one line that names the node it moved to.

## The three rules

### RUL-01 [C] Code computes every number
- Statement: every number in a flag, a candidate, an estimate, a reason and a report comes from code. The model only chooses between a plan and hold and writes the reason.
- Check: the model's answer is checked against the options it was given, and a choice outside them is rejected.
- Where: [[MOD-08]] computes, [[MOD-09]] asks and checks ([[DAT-16]])
- Decision: [[DEC-01]]
- Evidence: test_a_choice_that_is_not_the_plan_or_hold_is_rejected, test_the_schema_limits_ids_and_choices_to_the_requests_options

### RUL-02 [C] Every run takes a seed
- Statement: two runs with the same seed and settings produce the same bookings and the same decisions.jsonl.
- Draws: every random number comes from the seed before the run starts, one number per draw ([[DEC-22]]). Competitor noise uses stream [[RUL-20]] and bookings stream [[RUL-22]].
- Where: [[MOD-05]], [[MOD-06]]
- Evidence: test_same_seed_gives_the_same_books_and_another_seed_does_not, test_two_runs_with_the_same_seed_write_identical_decisions_files, test_rates_depend_only_on_the_seed

### RUL-03 [C] Nothing is used before the day it becomes known
- Statement: every lookup takes the day it is made on. A flight counts from the day the airline files it, and an event from the day it is announced. A competitor's rate counts from the day it is shopped.
- Peak: the convention's peak night is computed from what is known on the day it is announced ([[DEC-02]], [[DEC-09]]).
- Where: [[MOD-01]] (build_schedule(as_of_day)), [[MOD-03]] (events_as_of, rate_cuts_as_of), [[MOD-04]], [[MOD-05]], [[MOD-07]]
- Evidence: test_nothing_changes_demand_before_day_10, test_shock_known_follows_what_is_known_on_the_day, test_peak_night_uses_what_is_known_on_the_day_the_event_becomes_known

## schedule.py

### RUL-04 [C] SIM_START
- Value: date(2027, 1, 4)
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: simulation day 0, a Monday.
- Evidence: test_weekday_agrees_with_the_schedule

### RUL-05 [C] HORIZON_DAYS
- Value: 150
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: the last stay date is 149: 60 decided days plus the 90-day look-ahead.
- Evidence: test_every_stay_date_seen_is_inside_the_schedule, test_after_day_59_the_window_stops_at_stay_date_149

### RUL-06 [C] MARKET_STATION
- Value: "QMC"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the made-up main airport.
- Evidence: test_summing_by_arrival_station_misses_the_second_airport

### RUL-07 [C] SECOND_STATION
- Value: "QMS"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the made-up second airport in the same city, where the SLC flights land.
- Evidence: test_summing_by_arrival_station_misses_the_second_airport

### RUL-08 [C] MARKET_CITY
- Value: "QMC"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the made-up city code that covers both airports. seats_by_day groups the seats by it.
- Evidence: test_summing_by_arrival_station_misses_the_second_airport

### RUL-09 [C] MARKET_COUNTRY
- Value: "US"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the arrival country code written into every row.
- Evidence: test_every_row_arrives_in_the_market_country_and_state

### RUL-10 [C] MARKET_STATE
- Value: "CO"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the arrival state code written into every row.
- Evidence: test_every_row_arrives_in_the_market_country_and_state

### RUL-11 [C] EQUIPMENT
- Value: {"738": (0, 16, 150), "321": (0, 20, 170), "320": (0, 12, 148), "E75": (0, 12, 64), "32N": (0, 0, 180), "BUS": (0, 0, 50)}
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: equipment code to (first, business, economy) seats. BUS is the coach sold under a flight number.
- Evidence: test_normal_day_has_4244_seats, test_summing_with_type_u_rows_counts_the_bus

### RUL-89 [C] KINDS
- Value: ("add", "suspend", "equipment", "frequency", "time")
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: what a filing can do ([[DEC-53]]). add and suspend are the default's kinds. equipment swaps a route's code for a date range, frequency sets its daily flights and time shifts its departures.
- Evidence: test_the_default_scenario_is_the_air_shocks_and_the_kinds_are_named

### RUL-90 [C] CHURN_STREAM
- Value: 3
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: the random stream for the churn ([[SHK-07]]), kept apart from the rate-shop and booking streams ([[RUL-20]], [[RUL-22]]).
- Evidence: test_the_churn_files_weekly_revisions_below_the_threshold

### RUL-91 [C] CHURN_WEEKS
- Value: 8
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: the churn files on days 7, 14 and every seventh day through 56 ([[SHK-07]]). Each filing holds one swap and one time change.
- Evidence: test_the_churn_files_weekly_revisions_below_the_threshold

### RUL-92 [C] CHURN_SHIFTS
- Value: (-30, -15, 15, 30)
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: the departure-time changes the churn draws from, in minutes ([[SHK-07]]). A time change moves no seat.
- Evidence: test_the_churn_files_weekly_revisions_below_the_threshold, test_a_time_change_moves_departures_and_no_seat

### RUL-95 [C] CHURN_BLOCK
- Value: (14, 21)
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: the days a churn swap lasts, drawn per filing: two to three weeks, starting one to six weeks out ([[SHK-07]]).
- Evidence: test_the_churn_files_weekly_revisions_below_the_threshold

### RUL-93 [C] SWAPS
- Value: {"738": "321", "321": "738", "320": "32N", "32N": "320"}
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the equipment swaps the churn draws, between codes within 24 seats a flight of each other ([[RUL-11]], [[SHK-07]]). A day moves at most 96 seats, against a threshold of 212.
- Evidence: test_the_churn_files_weekly_revisions_below_the_threshold

## world.py

### RUL-12 [C] SIM_DAYS
- Value: 60
- File: src/hotel_market/world.py
- Kind: parameter
- Meaning: the agent decides on days 0 to 59. Bookings run on to day 149.
- Evidence: test_simulation_runs_days_0_to_59_and_each_day_sees_90_stay_dates, test_rates_can_only_change_on_days_0_to_59

### RUL-13 [C] LOOKAHEAD_DAYS
- Value: 90
- File: src/hotel_market/world.py
- Kind: parameter
- Meaning: the stay dates each hotel looks at on a simulation day, starting with that night.
- Evidence: test_simulation_runs_days_0_to_59_and_each_day_sees_90_stay_dates

### RUL-14 [H] FLOOR_SHARE
- Moved to: [[RUL-59]]

### RUL-15 [H] CEILING_SHARE
- Moved to: [[RUL-60]]

### RUL-16 [H] COST_SHARE
- Moved to: [[RUL-61]]

### RUL-17 [H] COMP_RATE_OFFSETS
- Moved to: [[DAT-04]], as each competitor's offset in its hotel's entry

### RUL-18 [H] DOW_FACTORS
- Moved to: [[DAT-04]], as each hotel's weekday_factors

### RUL-23 [H] CURVE_DAYS_OUT
- Moved to: [[RUL-68]]

### RUL-24 [H] CURVE_SHARE
- Moved to: [[RUL-69]]

### RUL-25 [H] HOTEL_ROW
- Moved to: [[DAT-04]], as each hotel's row, its position in the file

## demand.py

### RUL-82 [C] DEMAND_BIAS
- Value: 1.0
- File: src/hotel_market/demand.py
- Kind: parameter
- Meaning: a factor on the simulator's demand, the day-0 preload included, that the agent never sees ([[DEC-50]]). --demand-bias sets it for a run. At 1.0 the agent's forecast equals the simulator's demand ([[MOD-18]]).
- Evidence: test_the_forecast_is_the_simulators_demand_for_the_demo_market, test_the_demand_bias_multiplies_both_demands_and_is_1_by_default

### RUL-87 [C] MARKET_ELASTICITY
- Value: 0.0
- File: src/hotel_market/demand.py
- Kind: parameter
- Meaning: the market's price response. Expected demand scales with (the comp median as shopped / its starting level) ** -this ([[DEC-52]]). At 0.0 only the rate against the median moves bookings, so a matched raise is free.
- Evidence: test_the_market_elasticity_scales_demand_with_the_medians_level, test_the_market_elasticity_scales_each_days_draw_by_the_medians_level

## shops.py

### RUL-19 [C] NOISE
- Value: 0.03
- File: src/hotel_market/shops.py
- Kind: parameter
- Meaning: each competitor's rate is off its base by up to 3% either way. The noise is drawn once per competitor and stay date ([[DEC-37]]).
- Evidence: test_competitor_rates_are_base_rate_x_noise_with_no_weekly_pattern

### RUL-20 [C] NOISE_STREAM
- Value: 1
- File: src/hotel_market/shops.py
- Kind: parameter
- Meaning: the random stream for the rate-shop noise, kept apart from the booking stream [[RUL-22]]. Another stream draws other noise and other results.
- Evidence: test_rates_depend_only_on_the_seed, test_the_default_mode_still_gives_28818_on_seed_7

### RUL-83 [C] REACTION_SHARE
- Value: 0.5
- File: src/hotel_market/shops.py
- Kind: parameter
- Meaning: with --react, the share of a hotel's change from its start rate that each competitor moves ([[DEC-51]]). The move is in dollars, on top of the noise and the shocks.
- Evidence: test_competitors_move_half_of_the_hotels_change_when_they_are_told_it

### RUL-84 [C] REACTION_LAG
- Value: 3
- File: src/hotel_market/shops.py
- Kind: parameter
- Meaning: the days between a hotel's rate taking effect and the competitors' move. A shop day reads the hotel's rate in force that many days earlier from the Books' log ([[DEC-51]]).
- Evidence: test_the_reaction_reads_the_hotels_rate_three_days_back_from_the_log

## bookings.py

### RUL-21 [C] ELASTICITY
- Value: 1.5
- File: src/hotel_market/bookings.py
- Kind: parameter
- Meaning: the simulator's price sensitivity. Bookings scale with (rate / comp median) ** -ELASTICITY. The default mode hands the same value to the agent as an oracle ([[RUL-56]]).
- Evidence: test_expected_new_bookings_follow_the_formula

### RUL-22 [C] BOOKING_STREAM
- Value: 2
- File: src/hotel_market/bookings.py
- Kind: parameter
- Meaning: the random stream for every booking draw of a run. Another stream draws other bookings and other results.
- Evidence: test_same_seed_gives_the_same_books_and_another_seed_does_not, test_the_default_mode_still_gives_28818_on_seed_7

## forecast.py

### RUL-88 [C] ORACLE_MARKET_ELASTICITY
- Value: 0.0
- File: src/hotel_market/forecast.py
- Kind: parameter
- Meaning: the market elasticity the agent prices with ([[DEC-52]]). It is the simulator's value handed to it, as [[RUL-56]] hands it the share elasticity. The command sets the run's value, and every plan record carries it.
- Evidence: test_the_agents_market_elasticity_starts_at_0_and_lowers_demand_where_the_median_rose, test_the_plan_record_carries_the_market_elasticity_and_only_a_set_value_reaches_the_request

## detect.py

### RUL-26 [H] PACE_SHARE
- Moved to: [[RUL-62]]

### RUL-27 [H] PACE_NOISE_SD
- Moved to: [[RUL-63]]

### RUL-28 [H] SEAT_THRESHOLD
- Moved to: [[RUL-64]]

### RUL-29 [H] MEDIAN_THRESHOLD
- Moved to: [[RUL-65]]

### RUL-30 [H] HOLD_DAYS
- Moved to: [[RUL-66]]

### RUL-31 [C] AHEAD
- Value: "ahead of pace"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the pace gap is above the threshold. The label reaches the model request, so the recorded live run replays only with this text.
- Evidence: test_pace_causes_follow_the_gap_against_the_threshold, test_the_recorded_live_run_replays_without_a_key_and_gives_28818

### RUL-32 [C] BEHIND
- Value: "behind pace"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the pace gap is below minus the threshold.
- Evidence: test_pace_causes_follow_the_gap_against_the_threshold

### RUL-33 [C] SEATS_UP
- Value: "seats up"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the seat revision is at least [[RUL-64]]. The label reaches the model request.
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known, test_the_recorded_live_run_replays_without_a_key_and_gives_28818

### RUL-34 [C] SEATS_CUT
- Value: "seats cut"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the seat revision is at most minus [[RUL-64]].
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known

### RUL-35 [C] MEDIAN_UP
- Value: "comp median up"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the comp median rose by at least [[RUL-65]] since yesterday. The label reaches the model request.
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known, test_the_recorded_live_run_replays_without_a_key_and_gives_28818

### RUL-36 [C] MEDIAN_DOWN
- Value: "comp median down"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the comp median fell by at least [[RUL-65]]. It adds the candidate [[RUL-42]].
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known, test_a_comp_median_drop_adds_lower_halfway_to_the_new_median

### RUL-37 [C] NEW_EVENT
- Value: "event announced"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause on the day an event becomes known, on the stay dates it covers. The label reaches the model request.
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known, test_the_recorded_live_run_replays_without_a_key_and_gives_28818

### RUL-38 [C] PACE
- Value: {"ahead of pace", "behind pace"}
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the two pace causes. A flag with only these is silenced under the hold.
- Evidence: test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags

## plan.py

### RUL-39 [H] AGENT_ELASTICITY
- Moved to: [[RUL-56]], the same value named for what it is

### RUL-56 [C] ORACLE_ELASTICITY
- Value: 1.5
- File: src/hotel_market/plan.py
- Kind: parameter
- Meaning: the elasticity the default mode prices with. It is the simulator's own value ([[RUL-21]]), handed to the agent as an oracle ([[DEC-40]]). A real hotel does not have one.
- Modes: the other modes replace it with a fixed value or a learned one ([[DEC-38]], [[RUL-49]]).
- Evidence: test_elasticity_modes_parse_and_print, test_the_default_mode_still_gives_28818_on_seed_7

### RUL-40 [H] MIN_VALUE_AT_STAKE
- Moved to: [[RUL-67]]

### RUL-41 [C] HOLD
- Value: "hold"
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: the name of the candidate that keeps the current rate, and of the action when nothing changes. It is one of the two options in every request.
- Evidence: test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits, test_the_recorded_live_run_replays_without_a_key_and_gives_28818

### RUL-42 [C] HALFWAY
- Value: "lower halfway to the new median"
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: the extra candidate when the comp median dropped.
- Evidence: test_a_comp_median_drop_adds_lower_halfway_to_the_new_median

### RUL-43 [C] CANDIDATES
- Value: (("hold", 1.00), ("raise 5%", 1.05), ("raise 10%", 1.10), ("lower 5%", 0.95))
- File: src/hotel_market/plan.py
- Kind: parameter
- Meaning: every flag's candidates and the factor each applies to the current rate ([[DEC-13]]).
- Evidence: test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits

### RUL-44 [C] PLAN_ORDER
- Value: ("raise 5%", "raise 10%", "lower 5%", "lower halfway to the new median")
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: the order in which a plan names its actions, such as "raise 5% on Mon; raise 10% on Thu".
- Evidence: test_a_plan_lists_its_changes_by_day_of_week

### RUL-45 [C] DAY_NAMES
- Value: ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: the day names used in plans, requests and reports. Monday is 0.
- Evidence: test_a_plan_lists_its_changes_by_day_of_week

### RUL-49 [C] MODES
- Value: ("true", "fixed", "learn")
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: where the agent's elasticity comes from: the simulator's own value, a fixed value, or a learned one ([[DAT-22]], [[DEC-38]]). The model sees the first as "assumed" ([[RUL-75]]).
- Evidence: test_elasticity_modes_parse_and_print, test_a_mode_that_is_not_true_fixed_or_learn_is_rejected

### RUL-54 [C] BAND_STANDARD_ERRORS
- Value: 1
- File: src/hotel_market/plan.py
- Kind: parameter
- Meaning: under the cautious rule ([[CON-11]], [[DEC-39]]) every candidate is also scored this many standard errors below and above the estimate. The band is clamped to [[RUL-51]] and [[RUL-52]].
- Evidence: test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side

## model.py

### RUL-46 [C] MODEL
- Value: "claude-opus-5-5"
- File: src/hotel_market/model.py
- Kind: label
- Meaning: the model the live client asks, with the server-side refusal fallback on. It is a label because a template run does not depend on it.
- Evidence: test_claude_client_sends_the_request_and_handles_a_refusal

### RUL-47 [C] SYSTEM
- File: src/hotel_market/model.py
- Kind: label
- Meaning: the system prompt. It tells the model what an entry is. Code picked the best candidate for each day of the week. The model chooses the plan or "hold" for each entry.
- Writing: the model writes as "we" and states only what the entry shows. It makes no claim about price sensitivity or risk that the entry does not contain ([[DEC-44]]).
- Figures: every figure is written as a report writes it, with its direction in words. The model copies the phrases whole, with no sign, direction word or rounding of its own. It quotes no end of a range alone.
- Allowed: "more than holding" may be written once in a sentence that lists several gains. An event's name is written in lower case inside a sentence. The prompt also explains the modes "assumed", "fixed" and "learn".
- Band: under the cautious rule each candidate's band_verdict states the rule's result ([[DEC-56]]). The prompt tells the model to copy it as written.
- Evidence: test_the_system_prompt_tells_the_model_how_to_choose_and_write

### RUL-75 [C] MODE_NAMES
- Value: {"true": "assumed"}
- File: src/hotel_market/model.py
- Kind: label
- Meaning: how the request names an elasticity mode to the model. The command line's "true" reads "assumed", a value the agent was given; fixed and learn keep their names ([[DEC-44]], [[RUL-49]]).
- Evidence: test_the_request_carries_the_elasticity_and_its_digest_changes_with_it

### RUL-76 [C] RETRIES
- Value: 2
- File: src/hotel_market/model.py
- Kind: parameter
- Meaning: how many times a Measured client asks again after an SDK error or an invalid answer. A refusal is not asked again. The last failure raises, and the call record still lands ([[DAT-30]]).
- Evidence: test_a_measured_client_retries_a_bad_answer_and_counts_it

### RUL-77 [C] BACKOFF_SECONDS
- Value: 2.0
- File: src/hotel_market/model.py
- Kind: parameter
- Meaning: the wait before a Measured client asks again after an SDK error. It doubles on each retry: 2 s, then 4 s. The SDK has already retried the call itself. An invalid answer is asked again at once ([[DAT-30]]).
- Evidence: test_a_request_that_fails_past_retries_still_leaves_a_record

### RUL-78 [C] SDK_ERRORS
- Value: ("APIStatusError", "APIConnectionError")
- File: src/hotel_market/model.py
- Kind: label
- Meaning: the anthropic error classes a Measured client asks again, matched by class name so that model.py imports without the SDK. A status error is a rate limit or an overload; a connection error is a request that never arrived.
- Evidence: test_a_measured_client_retries_an_sdk_error_after_a_backoff

### RUL-79 [C] MODELS
- Value: ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5")
- File: src/hotel_market/model.py
- Kind: label
- Meaning: the current model at each tier, the bench's default reviewers, with MODEL ([[RUL-46]]) first. A label: no run depends on it until a model is asked. PRICES ([[RUL-80]]) prices each.
- Evidence: test_a_models_cost_comes_from_the_price_table

## agent.py

### RUL-48 [C] MIN_STAY
- Value: "two-night minimum stay"
- File: src/hotel_market/agent.py
- Kind: label
- Meaning: the action name of the advice in [[DAT-15]].
- Evidence: test_minimum_stay_advice_is_given_once_per_hotel_and_event_and_not_simulated

## estimate.py

### RUL-50 [C] PRIOR_SD
- Value: 0.5
- File: src/hotel_market/estimate.py
- Kind: parameter
- Meaning: the standard deviation of the normal prior on the learned elasticity, centred on the prior the agent is given. It is the whole standard error until the rate ratio has moved ([[DEC-38]]).
- Evidence: test_with_no_observations_the_estimate_is_the_prior, test_the_prior_holds_the_estimate_when_the_ratio_never_moves, test_plain_learn_mode_gives_the_same_results_as_before

### RUL-51 [C] ELASTICITY_MIN
- Value: 0.5
- File: src/hotel_market/estimate.py
- Kind: parameter
- Meaning: the learned elasticity is clamped to at least this.
- Evidence: test_the_estimate_is_clamped_to_the_range

### RUL-52 [C] ELASTICITY_MAX
- Value: 3.0
- File: src/hotel_market/estimate.py
- Kind: parameter
- Meaning: the learned elasticity is clamped to at most this.
- Evidence: test_the_estimate_is_clamped_to_the_range

### RUL-96 [C] LEVEL_OBSERVATIONS
- Value: 500
- File: src/hotel_market/estimate.py
- Kind: parameter
- Meaning: the observations a --level agent's fit needs before it scales its forecast by the fitted level ([[DEC-54]]). Until then the factor is 1, as the prior holds the elasticity.
- Evidence: test_the_level_factor_is_the_fitted_level_once_the_fit_has_enough_observations

### RUL-97 [C] LEVEL_MIN
- Value: 0.5
- File: src/hotel_market/estimate.py
- Kind: parameter
- Meaning: the fitted level factor is clamped to at least this, as [[RUL-51]] clamps the elasticity ([[DEC-54]]).
- Evidence: test_the_level_factor_is_the_fitted_level_once_the_fit_has_enough_observations

### RUL-98 [C] LEVEL_MAX
- Value: 2.0
- File: src/hotel_market/estimate.py
- Kind: parameter
- Meaning: the fitted level factor is clamped to at most this, as [[RUL-52]] clamps the elasticity ([[DEC-54]]).
- Evidence: test_the_level_factor_is_the_fitted_level_once_the_fit_has_enough_observations

## cli.py

### RUL-53 [C] REPORT_DAYS
- Value: (10, 20, 30, 40, 59)
- File: src/hotel_market/cli.py
- Kind: parameter
- Meaning: the days a sweep reports a learn arm's estimates for. It changes the report and not the runs.
- Evidence: test_the_seeds_command_prints_one_row_per_arm_and_a_learn_arms_estimates

### RUL-55 [C] SHOCK_PLAN_CAUSES
- Value: {"event announced", "seats up"}
- File: src/hotel_market/cli.py
- Kind: label
- Meaning: the causes that mark a plan as raised by the convention or the new flights. A sweep reports the gain on those plans apart from every other plan ([[DAT-24]], [[RES-06]]).
- Evidence: test_a_sweep_counts_the_shock_plans_apart_from_the_other_plans

### RUL-74 [C] DAILY_COMMANDS
- Value: ("run-day", "replay")
- File: src/hotel_market/cli.py
- Kind: label
- Meaning: the two commands that run the agent against the stored tables ([[DEC-42]]). main() hands an argument list that starts with one of them to their own parser.
- Evidence: test_the_daily_commands_run_a_day_and_replay_it

### RUL-81 [C] BENCH_MODES
- Value: ("fixed:1.0", "fixed:2.0", "true")
- File: src/hotel_market/cli.py
- Kind: parameter
- Meaning: the bench's default modes: two where the code's elasticity is wrong, and the true one as the check. The ranking pools the mismatched modes ([[DEC-48]]).
- Evidence: test_the_bench_needs_a_key_unless_it_runs_the_template_alone

### RUL-85 [C] REPEAT_WINDOW
- Value: 14
- File: src/hotel_market/cli.py
- Kind: parameter
- Meaning: a reacting run reports the stay dates changed twice or more within this many days. The hold ([[RUL-66]]) lasts seven, so a second change inside the window follows soon after it lifts ([[DEC-51]]).
- Evidence: test_a_reacting_sweep_counts_its_own_median_flags_and_the_repeat_changes

### RUL-86 [C] MEDIAN_CAUSES
- Value: {"comp median down", "comp median up"}
- File: src/hotel_market/cli.py
- Kind: label
- Meaning: the two comp-median causes. A sweep counts the flags that carry one, and with --react those the hotels' own changes caused ([[DEC-51]]).
- Evidence: test_a_reacting_sweep_counts_its_own_median_flags_and_the_repeat_changes

### RUL-94 [C] SEAT_CAUSES
- Value: {"seats up", "seats cut"}
- File: src/hotel_market/cli.py
- Kind: label
- Meaning: the two seat causes, the flags a filing raises. A sweep counts them in its filings table ([[DEC-53]]).
- Evidence: test_a_scenario_and_the_churn_go_to_both_runs

## bench.py

### RUL-80 [C] PRICES
- Value: {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.1, 0.5)}
- File: src/hotel_market/bench.py
- Kind: parameter
- Meaning: list prices in dollars per million input and output tokens, from Anthropic's pricing page on 2026-10-12. cost() prices every attempt's tokens with them. Haiku 5.5's price is for prompts under 100,000 tokens.
- Evidence: test_a_models_cost_comes_from_the_price_table

## policy.py

### RUL-99 [C] POLICY_STEP
- Value: 0.05
- File: src/hotel_market/policy.py
- Kind: parameter
- Meaning: the raise a policy applies on a raising cause, and the cut on a lowering cause ([[DEC-55]]). Both are clamped to the floor and ceiling.
- Evidence: test_the_rule_raises_ahead_of_pace_and_lowers_behind_by_the_step

### RUL-100 [C] RAISE
- Value: 1
- File: src/hotel_market/policy.py
- Kind: label
- Meaning: the direction a policy's rules map a raising cause to ([[DEC-55]]). Ahead of pace raises for both policies. An event or seats up raises for rules.
- Evidence: test_the_rules_policy_adds_the_event_and_seat_rules_and_skips_a_conflict

### RUL-101 [C] LOWER
- Value: -1
- File: src/hotel_market/policy.py
- Kind: label
- Meaning: the direction a policy's rules map a lowering cause to: behind pace for both policies, seats cut for rules ([[DEC-55]]).
- Evidence: test_the_rules_policy_adds_the_event_and_seat_rules_and_skips_a_conflict

### RUL-102 [C] STANDARD_ERROR_EDGES
- Value: (0.15, 0.25, 0.35)
- File: src/hotel_market/bench.py
- Kind: parameter
- Meaning: the standard errors that bound the groups of by_standard_error. A learn arm's queued plans are grouped by how little their elasticity was pinned down when the reviewer saw them.
- Evidence: test_the_decline_rate_by_standard_error_groups_a_learn_arms_queue

## stored.py

### RUL-72 [C] TABLES
- Value: ("daily_bookings", "rate_shops", "schedule_snapshots", "events", "flags", "plans", "decisions")
- File: src/hotel_market/stored.py
- Kind: label
- Meaning: the seven tables sql/schema.sql defines ([[DAT-28]]), the four feeds first.
- Evidence: test_the_schema_is_seven_tables_each_keyed_by_as_of_day

### RUL-73 [C] OPENING_DAY
- Value: -1
- File: src/hotel_market/stored.py
- Kind: label
- Meaning: the as_of_day of the position before the first day. That is the rooms already on the books, the first rate shop and the first schedule. It is a key for those rows, which run-day writes with day 0.
- Evidence: test_the_daily_commands_run_a_day_and_replay_it, test_the_stored_sources_answer_as_the_simulated_ones_do

## customer.py

### RUL-70 [C] TARGETS
- Value: ("contribution", "revenue")
- File: src/hotel_market/customer.py
- Kind: label
- Meaning: what a customer file may name as its target ([[RUL-58]]). load() refuses any other value, and --target offers the same two.
- Evidence: test_a_customer_file_with_a_bad_target_or_repeated_key_or_name_is_refused, test_a_revenue_target_arm_counts_wins_and_earnings_in_revenue

### RUL-71 [C] CUSTOMER_VARIABLE
- Value: "HOTEL_MARKET_CUSTOMER"
- File: src/hotel_market/customer.py
- Kind: label
- Meaning: the environment variable that names the default customer file when it is set. Otherwise demo_path() looks for customers/demo.toml under the working directory, then under the repository root.
- Evidence: test_the_customer_variable_names_the_default_file

## customers/demo.toml

Everything specific to the demo market, read by [[MOD-20]] into a Customer
([[DAT-27]]). `kg_check.py` compares each `Value:` with the file through its
`Key:`, and fails when a setting outside the hotels has no node here. The
hotels themselves are data ([[DAT-04]]).

### RUL-57 [C] name
- Value: "demo"
- File: customers/demo.toml
- Key: name
- Kind: label
- Meaning: the market's name, used in the summary's target sentence.
- Evidence: test_the_demo_file_describes_the_market_in_claude_md

### RUL-58 [C] target
- Value: "contribution"
- File: customers/demo.toml
- Key: target
- Kind: parameter
- Meaning: what the agent scores candidates on, "contribution" or "revenue". It is a string, but it changes every estimate, so it is a parameter ([[DEC-41]], [[CON-07]]).
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_the_revenue_target_scores_candidates_on_the_rate_alone

### RUL-59 [C] floor_share
- Value: 0.70
- File: customers/demo.toml
- Key: limits.floor_share
- Kind: parameter
- Meaning: the rate floor as a share of the start rate.
- Evidence: test_floor_is_70_percent_and_ceiling_is_140_percent_of_start_rate

### RUL-60 [C] ceiling_share
- Value: 1.40
- File: customers/demo.toml
- Key: limits.ceiling_share
- Kind: parameter
- Meaning: the rate ceiling as a share of the start rate.
- Evidence: test_floor_is_70_percent_and_ceiling_is_140_percent_of_start_rate

### RUL-61 [C] cost_share
- Value: 1 / 3
- File: customers/demo.toml
- Key: limits.cost_share
- Kind: parameter
- Meaning: the cost to service an occupied room, as a share of the start rate ([[DEC-12]]). The file writes it as 0.3333333333333333, which reads back as exactly one third.
- Evidence: test_each_occupied_room_costs_a_third_of_the_start_rate

### RUL-62 [C] pace_share
- Value: 0.10
- File: customers/demo.toml
- Key: detect.pace_share
- Kind: parameter
- Meaning: a pace gap counts only beyond this share of the hotel's rooms ([[DEC-07]]).
- Evidence: test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd

### RUL-63 [C] pace_noise_sd
- Value: 3
- File: customers/demo.toml
- Key: detect.pace_noise_sd
- Kind: parameter
- Meaning: a pace gap also counts only beyond this many standard deviations of booking noise, sqrt(normal demand x curve) ([[DEC-07]]).
- Evidence: test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd

### RUL-64 [C] seat_threshold
- Value: 0.05
- File: customers/demo.toml
- Key: detect.seat_threshold
- Kind: parameter
- Meaning: a seat revision of this much either way raises a flag ([[DEC-04]]).
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known

### RUL-65 [C] median_threshold
- Value: 0.05
- File: customers/demo.toml
- Key: detect.median_threshold
- Kind: parameter
- Meaning: a comp median that moved this much since yesterday raises a flag.
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known

### RUL-66 [C] hold_days
- Value: 7
- File: customers/demo.toml
- Key: detect.hold_days
- Kind: parameter
- Meaning: an action accepted on day d holds its stay dates on days d+1 to d+hold_days ([[DEC-06]], [[CON-10]]).
- Evidence: test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags

### RUL-67 [C] min_value_at_stake
- Value: 250
- File: customers/demo.toml
- Key: agent.min_value_at_stake
- Kind: parameter
- Meaning: a plan worth less than this over holding is held rather than queued ([[DEC-17]], [[CON-08]]). It applies in every mode, the cautious rule included ([[CON-11]], [[DEC-43]]).
- Evidence: test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue

### RUL-68 [C] days_out
- Value: (0, 7, 30, 60, 90)
- File: customers/demo.toml
- Key: booking_curve.days_out
- Kind: parameter
- Meaning: the days out at which the booking curve is pinned, paired with [[RUL-69]] ([[CON-01]]).
- Evidence: test_curve_matches_the_points_and_is_linear_in_between

### RUL-69 [C] share
- Value: (1.00, 0.70, 0.40, 0.20, 0.00)
- File: customers/demo.toml
- Key: booking_curve.share
- Kind: parameter
- Meaning: the share of final bookings on the books at each pinned days-out, linear in between.
- Evidence: test_curve_matches_the_points_and_is_linear_in_between

### RUL-103 [C] DEMO_TABLES
- Value: ("hotels", "news", "stay_dates", "queue", "scorecard")
- File: src/hotel_market/demo_data.py
- Kind: label
- Meaning: the five tables sql/demo.sql defines for the demo page ([[DAT-33]]), in the order build() fills them.
- Evidence: test_the_file_holds_the_stored_tables_for_every_day_and_the_pages_five

### RUL-104 [C] NOTHING_NEW
- Value: "Nothing new became known today."
- File: src/hotel_market/demo_data.py
- Kind: label
- Meaning: the one news row of a day with no event, filing or comp set move for the hotel ([[DAT-33]]).
- Evidence: test_the_news_names_the_convention_the_filings_and_the_comp_set_cut

### RUL-105 [C] FILE_VARIABLE
- Value: "HOTEL_MARKET_DEMO_FILE"
- File: src/hotel_market/demo_page.py
- Kind: label
- Meaning: the environment variable that names the demo file the page reads ([[DAT-33]]). make demo sets it, and the page test sets it to the file it built.
- Evidence: test_the_page_shows_the_convention_hotel_on_day_10

### RUL-106 [C] DEFAULT_FILE
- Value: "demo.duckdb"
- File: src/hotel_market/demo_page.py
- Kind: label
- Meaning: the file the page reads when the variable is not set, the one hotel-market demo-data writes by default ([[MOD-26]]).
- Evidence: test_the_page_shows_the_convention_hotel_on_day_10
