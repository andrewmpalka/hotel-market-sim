# Rules and constants

The three project rules, then every named constant with its value, file and
kind, grouped by module, and the settings of the customer file, which hold
everything specific to the demo market ([[DEC-41]]). A constant is a parameter when its value changes the
results, or a label when it is a name or a string; the index lists the
parameters one per line and the labels together. `kg_check.py` compares each
`Value:` with the code and fails when they differ, when a constant has no
kind, or when a constant in the code has no node here.

## The three rules

### RUL-01 [C] Code computes every number
- Statement: every number in a flag, a candidate, an estimate, a reason and a report comes from code. The model only chooses between a plan and hold, and writes the reason; its answer is checked against the options it was given, and a choice outside them is rejected.
- Where: [[MOD-08]] computes, [[MOD-09]] asks and checks ([[DAT-16]])
- Decision: [[DEC-01]]
- Evidence: test_a_choice_that_is_not_the_plan_or_hold_is_rejected, test_the_schema_limits_ids_and_choices_to_the_requests_options

### RUL-02 [C] Every run takes a seed
- Statement: two runs with the same seed and settings produce the same bookings and the same decisions.jsonl. Every random number is drawn from the seed before the run starts: competitor noise on stream [[RUL-20]], bookings on stream [[RUL-22]], one number per draw ([[DEC-22]]).
- Where: [[MOD-05]], [[MOD-06]]
- Evidence: test_same_seed_gives_the_same_books_and_another_seed_does_not, test_two_runs_with_the_same_seed_write_identical_decisions_files, test_rates_depend_only_on_the_seed

### RUL-03 [C] Nothing is used before the day it becomes known
- Statement: every lookup takes the day it is made on. A flight counts from the day the airline files it, an event from the day it is announced, a competitor's rate from the day it is shopped, and the convention's peak night is computed from what is known on the day it is announced ([[DEC-02]], [[DEC-09]]).
- Where: [[MOD-01]] (build_schedule(as_of_day)), [[MOD-03]] (events_as_of, rate_cuts_as_of), [[MOD-04]], [[MOD-05]], [[MOD-07]]
- Evidence: test_nothing_changes_demand_before_day_10, test_shock_known_follows_what_is_known_on_the_day, test_peak_night_uses_what_is_known_on_the_day_the_event_becomes_known

## schedule.py

### RUL-04 [C] SIM_START
- Value: date(2027, 1, 4)
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: simulation day 0, a Monday
- Evidence: test_weekday_agrees_with_the_schedule

### RUL-05 [C] HORIZON_DAYS
- Value: 150
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: the last stay date is 149: 60 decided days plus the 90-day look-ahead
- Evidence: test_every_stay_date_seen_is_inside_the_schedule, test_after_day_59_the_window_stops_at_stay_date_149

### RUL-06 [C] MARKET_STATION
- Value: "QMC"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the made-up main airport
- Evidence: test_summing_by_arrival_station_misses_the_second_airport

### RUL-07 [C] SECOND_STATION
- Value: "QMS"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the made-up second airport in the same city, where the SLC flights land
- Evidence: test_summing_by_arrival_station_misses_the_second_airport

### RUL-08 [C] MARKET_CITY
- Value: "QMC"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the made-up city code that covers both airports; seats are grouped by it
- Evidence: test_summing_by_arrival_station_misses_the_second_airport

### RUL-09 [C] MARKET_COUNTRY
- Value: "US"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the arrival country code written into every row
- Evidence: test_every_row_arrives_in_the_market_country_and_state

### RUL-10 [C] MARKET_STATE
- Value: "CO"
- File: src/hotel_market/schedule.py
- Kind: label
- Meaning: the arrival state code written into every row
- Evidence: test_every_row_arrives_in_the_market_country_and_state

### RUL-11 [C] EQUIPMENT
- Value: {"738": (0, 16, 150), "321": (0, 20, 170), "320": (0, 12, 148), "E75": (0, 12, 64), "32N": (0, 0, 180), "BUS": (0, 0, 50)}
- File: src/hotel_market/schedule.py
- Kind: parameter
- Meaning: equipment code to (first, business, economy) seats; BUS is the coach sold under a flight number
- Evidence: test_normal_day_has_4244_seats, test_summing_with_type_u_rows_counts_the_bus

## world.py

### RUL-12 [C] SIM_DAYS
- Value: 60
- File: src/hotel_market/world.py
- Kind: parameter
- Meaning: the agent decides on days 0 to 59; bookings run on to day 149
- Evidence: test_simulation_runs_days_0_to_59_and_each_day_sees_90_stay_dates, test_rates_can_only_change_on_days_0_to_59

### RUL-13 [C] LOOKAHEAD_DAYS
- Value: 90
- File: src/hotel_market/world.py
- Kind: parameter
- Meaning: stay dates each hotel looks at on a simulation day, starting with that night
- Evidence: test_simulation_runs_days_0_to_59_and_each_day_sees_90_stay_dates

### RUL-14 [H] FLOOR_SHARE
- Was: 0.70 in src/hotel_market/world.py: the rate floor as a share of the start rate
- Replaced by: [[RUL-59]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-15 [H] CEILING_SHARE
- Was: 1.40 in src/hotel_market/world.py: the rate ceiling as a share of the start rate
- Replaced by: [[RUL-60]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-16 [H] COST_SHARE
- Was: 1 / 3 in src/hotel_market/world.py: the cost to service an occupied room, as a share of the start rate ([[DEC-12]])
- Replaced by: [[RUL-61]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-17 [H] COMP_RATE_OFFSETS
- Was: (-0.08, -0.03, 0.03, 0.08) in src/hotel_market/world.py: each hotel's four competitors price at these offsets from its start rate, so the comp median starts level with the hotel
- Replaced by: each competitor's offset in the hotel's entry ([[DAT-04]]) ([[DEC-41]])

### RUL-18 [H] DOW_FACTORS
- Was: {"convention": (0.95, 1.10, 1.10, 1.05, 0.90, 0.95, 0.80), "full-service": (0.95, 1.10, 1.10, 1.05, 0.90, 0.95, 0.80), "lifestyle": (0.85, 0.85, 0.90, 1.00, 1.20, 1.25, 0.90), "airport": (1.05, 0.90, 1.00, 1.05, 1.00, 0.85, 1.05)} in src/hotel_market/world.py: the day-of-week demand factors, Monday to Sunday, given to each hotel as its weekday_factors; rates do not follow them ([[DEC-16]]). Both the simulator's demand and the agent's forecast read them from the hotel
- Replaced by: each hotel's weekday_factors in its entry ([[DAT-04]]) ([[DEC-41]])

### RUL-23 [H] CURVE_DAYS_OUT
- Was: (0, 7, 30, 60, 90) in src/hotel_market/world.py: the days out at which the booking curve is pinned, paired with [[RUL-24]]
- Replaced by: [[RUL-68]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-24 [H] CURVE_SHARE
- Was: (1.00, 0.70, 0.40, 0.20, 0.00) in src/hotel_market/world.py: the share of final bookings on the books at each pinned days-out, linear in between
- Replaced by: [[RUL-69]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-25 [H] HOTEL_ROW
- Was: {"convention": 0, "full-service": 1, "lifestyle": 2, "airport": 3} in src/hotel_market/world.py: the row of each hotel in every array: the Books ([[DAT-07]]) and what the sources return ([[DAT-25]])
- Replaced by: each hotel's row, its position in the file ([[DAT-04]]) ([[DEC-41]])

## shops.py

### RUL-19 [C] NOISE
- Value: 0.03
- File: src/hotel_market/shops.py
- Kind: parameter
- Meaning: each competitor's rate is off its base by up to 3% either way, drawn once per competitor and stay date ([[DEC-37]])
- Evidence: test_competitor_rates_are_base_rate_x_noise_with_no_weekly_pattern

### RUL-20 [C] NOISE_STREAM
- Value: 1
- File: src/hotel_market/shops.py
- Kind: parameter
- Meaning: the random stream for the rate-shop noise, kept apart from the booking stream [[RUL-22]]; a parameter because another stream draws other noise and other results
- Evidence: test_rates_depend_only_on_the_seed

## bookings.py

### RUL-21 [C] ELASTICITY
- Value: 1.5
- File: src/hotel_market/bookings.py
- Kind: parameter
- Meaning: the simulator's price sensitivity; bookings scale with (rate / comp median) ** -ELASTICITY. The agent's default mode prices with the same value, handed to it as an oracle ([[RUL-56]]).
- Evidence: test_expected_new_bookings_follow_the_formula

### RUL-22 [C] BOOKING_STREAM
- Value: 2
- File: src/hotel_market/bookings.py
- Kind: parameter
- Meaning: the random stream for every booking draw of a run; a parameter because another stream draws other bookings
- Evidence: test_same_seed_gives_the_same_books_and_another_seed_does_not

## detect.py

### RUL-26 [H] PACE_SHARE
- Was: 0.10 in src/hotel_market/detect.py: a pace gap counts only beyond 10% of the hotel's rooms ([[DEC-07]])
- Replaced by: [[RUL-62]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-27 [H] PACE_NOISE_SD
- Was: 3 in src/hotel_market/detect.py: and beyond 3 standard deviations of booking noise, 3 x sqrt(normal demand x curve) ([[DEC-07]])
- Replaced by: [[RUL-63]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-28 [H] SEAT_THRESHOLD
- Was: 0.05 in src/hotel_market/detect.py: a seat revision of 5% or more either way raises a flag ([[DEC-04]])
- Replaced by: [[RUL-64]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-29 [H] MEDIAN_THRESHOLD
- Was: 0.05 in src/hotel_market/detect.py: a comp median that moved 5% or more since yesterday raises a flag
- Replaced by: [[RUL-65]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-30 [H] HOLD_DAYS
- Was: 7 in src/hotel_market/detect.py: an action accepted on day d holds its stay dates on days d+1 to d+7 ([[DEC-06]])
- Replaced by: [[RUL-66]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-31 [C] AHEAD
- Value: "ahead of pace"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the pace gap is above the threshold
- Evidence: test_consecutive_stay_dates_with_the_same_causes_merge_into_one_flag

### RUL-32 [C] BEHIND
- Value: "behind pace"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the pace gap is below minus the threshold
- Evidence: test_consecutive_stay_dates_with_the_same_causes_merge_into_one_flag

### RUL-33 [C] SEATS_UP
- Value: "seats up"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the seat revision is at least [[RUL-64]]
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known

### RUL-34 [C] SEATS_CUT
- Value: "seats cut"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the seat revision is at most minus [[RUL-64]]
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known

### RUL-35 [C] MEDIAN_UP
- Value: "comp median up"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the comp median rose by at least [[RUL-65]] since yesterday
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known

### RUL-36 [C] MEDIAN_DOWN
- Value: "comp median down"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause when the comp median fell by at least [[RUL-65]]; it adds the candidate [[RUL-42]]
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known, test_a_comp_median_drop_adds_lower_halfway_to_the_new_median

### RUL-37 [C] NEW_EVENT
- Value: "event announced"
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the cause on the day an event becomes known, on the stay dates it covers
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known

### RUL-38 [C] PACE
- Value: {"ahead of pace", "behind pace"}
- File: src/hotel_market/detect.py
- Kind: label
- Meaning: the two pace causes; a flag with only these is silenced under the hold
- Evidence: test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags

## plan.py

### RUL-39 [H] AGENT_ELASTICITY
- Was: 1.5 in src/hotel_market/plan.py, the agent's elasticity in the default mode, kept apart from the simulator's by not importing it ([[DEC-26]])
- Replaced by: [[RUL-56]], the same value named for what it is

### RUL-56 [C] ORACLE_ELASTICITY
- Value: 1.5
- File: src/hotel_market/plan.py
- Kind: parameter
- Meaning: the elasticity the default mode prices with: the simulator's own value ([[RUL-21]]) handed to the agent as an oracle, which a real hotel does not have ([[DEC-40]]). The other modes replace it with a fixed value or a learned one ([[DEC-38]], [[RUL-49]])
- Evidence: test_elasticity_modes_parse_and_print, test_the_default_mode_still_gives_28818_on_seed_7

### RUL-40 [H] MIN_VALUE_AT_STAKE
- Was: 250 in src/hotel_market/plan.py: a plan worth less than this over holding is held rather than queued ([[DEC-17]])
- Replaced by: [[RUL-67]], the same value as a setting of the customer file ([[DEC-41]])

### RUL-41 [C] HOLD
- Value: "hold"
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: the name of the candidate that keeps the current rate, and of the action when nothing changes
- Evidence: test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits

### RUL-42 [C] HALFWAY
- Value: "lower halfway to the new median"
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: the extra candidate when the comp median dropped
- Evidence: test_a_comp_median_drop_adds_lower_halfway_to_the_new_median

### RUL-43 [C] CANDIDATES
- Value: (("hold", 1.00), ("raise 5%", 1.05), ("raise 10%", 1.10), ("lower 5%", 0.95))
- File: src/hotel_market/plan.py
- Kind: parameter
- Meaning: every flag's candidates and the factor each applies to the current rate ([[DEC-13]])
- Evidence: test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits

### RUL-44 [C] PLAN_ORDER
- Value: ("raise 5%", "raise 10%", "lower 5%", "lower halfway to the new median")
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: the order in which a plan names its actions, such as "raise 5% on Mon; raise 10% on Thu"
- Evidence: test_a_plan_lists_its_changes_by_day_of_week

### RUL-45 [C] DAY_NAMES
- Value: ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: the day names used in plans, requests and reports; Monday is 0
- Evidence: test_a_plan_lists_its_changes_by_day_of_week

### RUL-49 [C] MODES
- Value: ("true", "fixed", "learn")
- File: src/hotel_market/plan.py
- Kind: label
- Meaning: where the agent's elasticity comes from: the simulator's own value, a fixed value, or one learned from the bookings ([[DAT-22]], [[DEC-38]]); the model sees the first as "assumed" ([[RUL-75]])
- Evidence: test_elasticity_modes_parse_and_print, test_a_mode_that_is_not_true_fixed_or_learn_is_rejected

### RUL-54 [C] BAND_STANDARD_ERRORS
- Value: 1
- File: src/hotel_market/plan.py
- Kind: parameter
- Meaning: under the cautious rule ([[CON-11]], [[DEC-39]]) every candidate is also scored at the estimate this many standard errors lower and higher, clamped to [[RUL-51]] and [[RUL-52]]
- Evidence: test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side

## model.py

### RUL-46 [C] MODEL
- Value: "claude-opus-5-5"
- File: src/hotel_market/model.py
- Kind: label
- Meaning: the model the live client asks, with the server-side refusal fallback on. A label: a live run's answers depend on it, a template run's do not
- Evidence: test_claude_client_sends_the_request_and_handles_a_refusal

### RUL-47 [C] SYSTEM
- File: src/hotel_market/model.py
- Kind: label
- Meaning: the system prompt: it tells the model what an entry is, that code picked the best candidate for each day of the week, that it chooses the plan or "hold" for each entry, that it writes as "we", that it states only what the entry shows and makes no claim about price sensitivity or risk the entry does not contain, that every figure in the request is written as a report writes it, its direction in words, and must be copied whole with no sign, direction word or rounding of the model's own, that a range is one phrase and no end of it is quoted alone, that "more than holding" may be written once in a sentence that lists several gains, that an event's name is written in lower case inside a sentence, and what the elasticity modes "assumed", "fixed" and "learn" mean ([[DEC-44]]). Its text is in the file; it is not a value this file repeats. A label for the same reason as [[RUL-46]].
- Evidence: test_claude_client_sends_the_request_and_handles_a_refusal, test_every_figure_in_the_request_is_a_display_string

### RUL-75 [C] MODE_NAMES
- Value: {"true": "assumed"}
- File: src/hotel_market/model.py
- Kind: label
- Meaning: how the request names an elasticity mode to the model: the command line's "true", the simulator's own value handed to the agent, reads "assumed", a value the agent was given; fixed and learn keep their names ([[DEC-44]], [[RUL-49]])
- Evidence: test_the_request_carries_the_elasticity_and_its_digest_changes_with_it

## agent.py

### RUL-48 [C] MIN_STAY
- Value: "two-night minimum stay"
- File: src/hotel_market/agent.py
- Kind: label
- Meaning: the action name of the advice in [[DAT-15]]
- Evidence: test_minimum_stay_advice_is_given_once_per_hotel_and_event_and_not_simulated

## estimate.py

### RUL-50 [C] PRIOR_SD
- Value: 0.5
- File: src/hotel_market/estimate.py
- Kind: parameter
- Meaning: the standard deviation of the normal prior on the learned elasticity, centred on the prior the agent is given; it is the whole standard error until the rate ratio has moved ([[DEC-38]])
- Evidence: test_with_no_observations_the_estimate_is_the_prior, test_the_prior_holds_the_estimate_when_the_ratio_never_moves

### RUL-51 [C] ELASTICITY_MIN
- Value: 0.5
- File: src/hotel_market/estimate.py
- Kind: parameter
- Meaning: the learned elasticity is clamped to at least this
- Evidence: test_the_estimate_is_clamped_to_the_range

### RUL-52 [C] ELASTICITY_MAX
- Value: 3.0
- File: src/hotel_market/estimate.py
- Kind: parameter
- Meaning: the learned elasticity is clamped to at most this
- Evidence: test_the_estimate_is_clamped_to_the_range

## cli.py

### RUL-53 [C] REPORT_DAYS
- Value: (10, 20, 30, 40, 59)
- File: src/hotel_market/cli.py
- Kind: parameter
- Meaning: the days a sweep reports a learn arm's estimates for; it changes the report, not the runs
- Evidence: test_the_seeds_command_prints_one_row_per_arm_and_a_learn_arms_estimates

### RUL-55 [C] SHOCK_PLAN_CAUSES
- Value: {"event announced", "seats up"}
- File: src/hotel_market/cli.py
- Kind: label
- Meaning: the causes that mark a plan as raised by the convention or the new flights; a sweep reports the gain on those plans apart from every other plan ([[DAT-24]])
- Evidence: test_the_seeds_command_prints_each_seed_and_the_mean_and_range

### RUL-74 [C] DAILY_COMMANDS
- Value: ("run-day", "replay")
- File: src/hotel_market/cli.py
- Kind: label
- Meaning: the two commands that run the agent against the stored tables ([[DEC-42]]); main() hands an argument list starting with one of them to their own parser
- Evidence: test_the_daily_commands_run_a_day_and_replay_it

## stored.py

### RUL-72 [C] TABLES
- Value: ("daily_bookings", "rate_shops", "schedule_snapshots", "events", "flags", "plans", "decisions")
- File: src/hotel_market/stored.py
- Kind: label
- Meaning: the seven tables sql/schema.sql defines ([[DAT-28]]), the four feeds first
- Evidence: test_the_schema_is_seven_tables_each_keyed_by_as_of_day

### RUL-73 [C] OPENING_DAY
- Value: -1
- File: src/hotel_market/stored.py
- Kind: label
- Meaning: the as_of_day of the position before the first day: the rooms already on the books, the first rate shop and the first schedule. A key for those rows, not a quantity: run-day writes them with day 0
- Evidence: test_the_stored_sources_answer_as_the_simulated_ones_do

## customer.py

### RUL-70 [C] TARGETS
- Value: ("contribution", "revenue")
- File: src/hotel_market/customer.py
- Kind: label
- Meaning: what a customer file may name as its target ([[RUL-58]]); load() refuses any other value, and --target offers the same two
- Evidence: test_a_customer_file_with_a_bad_target_or_repeated_key_is_refused, test_the_command_takes_a_customer_file_and_a_target

### RUL-71 [C] CUSTOMER_VARIABLE
- Value: "HOTEL_MARKET_CUSTOMER"
- File: src/hotel_market/customer.py
- Kind: label
- Meaning: the environment variable that names the default customer file when it is set; otherwise demo_path() looks for customers/demo.toml under the working directory, then under the repository root
- Evidence: test_without_a_customer_the_demo_market_is_the_default

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
- Meaning: the market's name, used in the summary's target sentence
- Evidence: test_the_demo_file_describes_the_market_in_claude_md

### RUL-58 [C] target
- Value: "contribution"
- File: customers/demo.toml
- Key: target
- Kind: parameter
- Meaning: what the agent scores candidates on, "contribution" or "revenue"; a string, but it changes every estimate, so it is a parameter ([[DEC-41]], [[CON-07]])
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_the_revenue_target_scores_candidates_on_the_rate_alone

### RUL-59 [C] floor_share
- Value: 0.70
- File: customers/demo.toml
- Key: limits.floor_share
- Kind: parameter
- Meaning: the rate floor as a share of the start rate
- Evidence: test_floor_is_70_percent_and_ceiling_is_140_percent_of_start_rate

### RUL-60 [C] ceiling_share
- Value: 1.40
- File: customers/demo.toml
- Key: limits.ceiling_share
- Kind: parameter
- Meaning: the rate ceiling as a share of the start rate
- Evidence: test_floor_is_70_percent_and_ceiling_is_140_percent_of_start_rate

### RUL-61 [C] cost_share
- Value: 1 / 3
- File: customers/demo.toml
- Key: limits.cost_share
- Kind: parameter
- Meaning: the cost to service an occupied room, as a share of the start rate ([[DEC-12]]); written in the file as 0.3333333333333333, which reads back as exactly one third
- Evidence: test_each_occupied_room_costs_a_third_of_the_start_rate

### RUL-62 [C] pace_share
- Value: 0.10
- File: customers/demo.toml
- Key: detect.pace_share
- Kind: parameter
- Meaning: a pace gap counts only beyond this share of the hotel's rooms ([[DEC-07]])
- Evidence: test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd

### RUL-63 [C] pace_noise_sd
- Value: 3
- File: customers/demo.toml
- Key: detect.pace_noise_sd
- Kind: parameter
- Meaning: and beyond this many standard deviations of booking noise, sqrt(normal demand x curve) ([[DEC-07]])
- Evidence: test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd

### RUL-64 [C] seat_threshold
- Value: 0.05
- File: customers/demo.toml
- Key: detect.seat_threshold
- Kind: parameter
- Meaning: a seat revision of this much either way raises a flag ([[DEC-04]])
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known

### RUL-65 [C] median_threshold
- Value: 0.05
- File: customers/demo.toml
- Key: detect.median_threshold
- Kind: parameter
- Meaning: a comp median that moved this much since yesterday raises a flag
- Evidence: test_each_shock_flags_on_the_day_it_becomes_known

### RUL-66 [C] hold_days
- Value: 7
- File: customers/demo.toml
- Key: detect.hold_days
- Kind: parameter
- Meaning: an action accepted on day d holds its stay dates on days d+1 to d+hold_days ([[DEC-06]], [[CON-10]])
- Evidence: test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags

### RUL-67 [C] min_value_at_stake
- Value: 250
- File: customers/demo.toml
- Key: agent.min_value_at_stake
- Kind: parameter
- Meaning: a plan worth less than this over holding is held rather than queued ([[DEC-17]], [[CON-08]]), in every mode, the cautious rule included ([[CON-11]], [[DEC-43]]); the one minimum rule in the repository
- Evidence: test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue

### RUL-68 [C] days_out
- Value: (0, 7, 30, 60, 90)
- File: customers/demo.toml
- Key: booking_curve.days_out
- Kind: parameter
- Meaning: the days out at which the booking curve is pinned, paired with [[RUL-69]] ([[CON-01]])
- Evidence: test_curve_matches_the_points_and_is_linear_in_between

### RUL-69 [C] share
- Value: (1.00, 0.70, 0.40, 0.20, 0.00)
- File: customers/demo.toml
- Key: booking_curve.share
- Kind: parameter
- Meaning: the share of final bookings on the books at each pinned days-out, linear in between
- Evidence: test_curve_matches_the_points_and_is_linear_in_between
