# Concepts

The ideas the code is built on, each with a plain definition and links to the
modules, constants and decisions that implement it.

### CON-01 [C] Booking curve
- Definition: the share of a stay date's final bookings that is normally on the books a given number of days before arrival: 0% at 90 days out, 20% at 60, 40% at 30, 70% at 7 and 100% on the day, linear in between. A day's expected new bookings are the demand times the curve's rise from yesterday to today.
- Implemented by: Customer.curve() in [[MOD-20]] from the customer file's [[RUL-68]] and [[RUL-69]] ([[DAT-27]]), read by both sides; [[MOD-06]] draws with it and the day-0 preload ([[DEC-03]]) loads each stay date to it; pace ([[CON-02]]), the agent's remaining demand in [[MOD-08]] and the estimator's baseline in [[MOD-16]] read it.
- Evidence: test_curve_matches_the_points_and_is_linear_in_between, test_expected_new_bookings_follow_the_formula

### CON-02 [C] Pace
- Definition: how a stay date's rooms on the books compare with normal. The pace gap is rooms on the books minus normal demand x curve, and a stay date is ahead of or behind pace when the gap is beyond both 10% of the hotel's rooms and three standard deviations of booking noise ([[DEC-07]]).
- Implemented by: detect_numbers() in [[MOD-07]] with [[RUL-62]] and [[RUL-63]], and the causes [[RUL-31]] and [[RUL-32]]; the hold period ([[CON-10]]) silences a pace-only flag.
- Evidence: test_numbers_follow_the_definitions, test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd

### CON-03 [C] Competitor set
- Definition: the four competitors each hotel is compared with, priced 8% and 3% below and 3% and 8% above its start rate ([[DAT-04]]), so the set's median starts level with the hotel. Competitors never react to the hotel; their rates move only with the scripted shocks ([[SHK-01]], [[SHK-03]]).
- Implemented by: Competitor and Hotel.competitors in [[MOD-02]] ([[DAT-04]]), built by [[MOD-20]] from the offsets in the customer file; the rate shop in [[MOD-05]].
- Evidence: test_each_hotel_has_four_competitors_within_10_percent_of_its_rate, test_comp_set_median_starts_at_the_hotels_own_rate

### CON-04 [C] Competitor median
- Definition: the median of the four competitors' rates for a stay date as shopped on a day; with four rates it is the mean of the middle two. Every rate ratio ([[CON-05]]) is measured against it, and a move of 5% or more since yesterday raises a flag ([[RUL-65]]).
- Implemented by: comp_median() in [[MOD-05]] ([[DAT-06]]); the noise behind it is drawn once per competitor and stay date ([[DEC-37]]).
- Evidence: test_comp_median_moves_only_when_a_shock_becomes_known, test_hotel_starts_level_with_its_comp_median

### CON-05 [C] Rate ratio
- Definition: the hotel's rate divided by its competitor median for the same stay date. Bookings scale with the ratio to the power of minus the elasticity ([[CON-06]]); the detect table carries it as rate_vs_median ([[DAT-08]]).
- Implemented by: Books.expected_new_bookings() in [[MOD-06]]; the agent's estimate in [[MOD-08]] applies a candidate's ratio the same way.
- Evidence: test_expected_new_bookings_follow_the_formula, test_numbers_follow_the_definitions

### CON-06 [C] Elasticity
- Definition: how strongly bookings respond to the rate ratio: expected bookings are multiplied by ratio ** -elasticity, so at 1.5 a rate 10% above the median loses about 13% of bookings. The simulator's value ([[RUL-21]]) and the agent's ([[RUL-56]], the oracle) are separate constants on purpose ([[DEC-40]]). In the default mode both are 1.5; the agent can also price with a fixed value, or learn one from the bookings it has seen by a Poisson regression on the rate ratio with a prior of width [[RUL-50]] ([[MOD-16]], [[DEC-38]]), which closed the fork [[FRK-02]]. The cautious rule ([[CON-11]]) makes the agent respect the estimate's standard error.
- Implemented by: [[MOD-06]] books with it; [[MOD-08]] estimates with the Pricing it is given ([[DAT-21]]); [[MOD-16]] estimates it; with it and the room cost, the start rate is best on an ordinary night ([[DEC-12]]).
- Evidence: test_expected_new_bookings_follow_the_formula, test_the_agent_reads_only_through_the_interfaces, test_on_nights_that_will_not_sell_out_the_start_rate_is_already_best, test_the_day_59_estimate_recovers_the_simulators_elasticity

### CON-07 [C] Contribution
- Definition: room revenue minus the cost of servicing every room sold, where the cost is one third of the hotel's start rate ([[RUL-61]]). It is the target the agent scores candidates on and the summary compares the runs on ([[DEC-12]]); as a measure it is [[MEA-05]]. It is the default target: a customer file may name revenue instead ([[RUL-58]], [[DEC-41]]), and the agent then counts each room at its rate, while the summary reports both measures either way.
- Implemented by: Hotel.room_cost in [[MOD-02]]; Books.contribution() in [[MOD-06]]; the estimate in [[MOD-08]] multiplies expected bookings by rate minus cost.
- Evidence: test_contribution_is_revenue_minus_the_cost_of_every_room_sold, test_estimate_is_expected_contribution_on_the_unsold_rooms, test_the_revenue_target_scores_candidates_on_the_rate_alone

### CON-08 [C] Value at stake
- Definition: what a flag's plan is expected to earn over holding: the best candidate's estimate minus the hold estimate, summed over the days of the week that change ([[DEC-19]]). A plan enters the queue only at the customer's minimum ([[RUL-67]]) or more ([[DEC-17]]); the queue is printed highest value first.
- Implemented by: Entry.value_at_stake and WeekdayGroup.gain in [[MOD-08]] ([[DAT-14]], [[DAT-12]]); queue() in [[MOD-12]].
- Evidence: test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue, test_the_queue_holds_plans_worth_the_minimum_highest_value_first

### CON-09 [C] Sell-out
- Definition: a stay date whose rooms on the books reach the hotel's rooms. The simulator caps each day's draw at the rooms still unsold, and the agent's estimate counts the chance of a sell-out through E[min(N, unsold)] ([[DEC-21]]), so a night expected to come close to full is where a raise pays.
- Implemented by: Books.book() in [[MOD-06]]; expected_bookings() in [[MOD-08]].
- Evidence: test_rooms_never_exceed_the_hotel, test_expected_bookings_is_the_mean_of_a_poisson_count_that_stops_at_the_unsold_rooms, test_when_demand_would_overfill_the_hotel_a_raise_wins

### CON-10 [C] Hold period
- Definition: after an accepted rate change on day d, the changed stay dates take no new action on days d+1 to d+7 ([[RUL-66]]) unless a new shock covers them ([[DEC-06]]). A pace gap alone raises no flag under the hold.
- Implemented by: Agent.held in [[MOD-10]]; flags() in [[MOD-07]] drops pace-only causes on held stay dates.
- Evidence: test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags, test_accepted_rates_apply_and_hold_those_stay_dates_for_7_days

### CON-11 [C] The cautious rule
- Definition: a learned elasticity ([[CON-06]]) comes with a standard error, and the cautious rule makes the agent respect it. Every candidate is scored three times: at the estimate, and at the estimate one standard error lower and one higher ([[RUL-54]], the band, clamped to the estimator's bounds [[RUL-51]] and [[RUL-52]]). A candidate replaces hold only if it is ahead of hold at the estimate and at both ends of the band; the best such candidate wins, else the day of the week holds. The minimum value at stake ([[RUL-67]]) applies to the whole plan, as in every mode ([[DEC-43]]). Early in a run the band is wide, so the rule holds on ordinary nights and still acts where the gain comes from a sell-out ([[CON-09]]) rather than from the elasticity. Without the rule the highest estimate wins as before.
- Implemented by: Pricing.band and WeekdayGroup.best, replaces_hold and rejected_at_an_end in [[MOD-08]] ([[DAT-21]], [[DAT-12]]); --cautious in [[MOD-12]] sets it on every learn mode ([[DAT-22]]); the request and the template in [[MOD-09]] carry the three values; the decision is [[DEC-39]].
- Evidence: test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held, test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side, test_the_three_values_reach_the_model_request
