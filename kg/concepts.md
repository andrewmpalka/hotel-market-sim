# Concepts

The ideas the code is built on, each with a plain definition and links to
the modules, constants and decisions that implement it.

### CON-01 [C] Booking curve
- Definition: the share of a stay date's final bookings normally on the books a given number of days out. Each hotel has its own curve, flat beyond its last pinned point.
- Points: every curve is pinned at 90, 60, 30, 7 and 0 days out ([[RUL-68]]) and reaches 100% on the night. The shares are the hotel's ([[RUL-69]]): the convention hotel holds 25% at 90 days out, the airport hotel 0%.
- Daily: a day's expected new bookings are the demand times the curve's rise from yesterday to today.
- Implemented by: Hotel.curve() in [[MOD-02]] from the hotel's entry in the customer file ([[DAT-04]], [[MOD-20]]), read by both sides. [[MOD-06]] draws with it, and the day-0 preload ([[DEC-03]]) loads each stay date to it.
- Read by: pace ([[CON-02]]), the agent's remaining demand in [[MOD-08]] and the estimator's baseline in [[MOD-16]]
- Evidence: test_curve_matches_the_points_and_is_linear_in_between, test_expected_new_bookings_follow_the_formula

### CON-02 [C] Pace
- Definition: how a stay date's rooms on the books compare with normal. The pace gap is rooms on the books minus normal demand x curve.
- Flag: a stay date is ahead of or behind pace when the gap passes the threshold ([[DEC-07]]). The threshold is the larger of 10% of the hotel's rooms and three standard deviations of booking noise.
- Implemented by: detect_numbers() in [[MOD-07]] with [[RUL-62]] and [[RUL-63]], and the causes [[RUL-31]] and [[RUL-32]]. The hold period ([[CON-10]]) silences a pace-only flag.
- Evidence: test_numbers_follow_the_definitions, test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd, test_pace_causes_follow_the_gap_against_the_threshold

### CON-03 [C] Competitor set
- Definition: the four competitors each hotel is compared with. They are priced 8% and 3% below and 3% and 8% above its start rate ([[DAT-04]]). The set's median therefore starts level with the hotel.
- Reaction: competitors never react by default. Their rates move a little with the shop noise ([[DEC-62]]) and a lot only with the shocks ([[SHK-01]], [[SHK-03]]). With --react each moves half of the hotel's change after a lag ([[DEC-51]]).
- Implemented by: Competitor and Hotel.competitors in [[MOD-02]] ([[DAT-04]]), which [[MOD-20]] builds from the offsets in the customer file. The rate shop is in [[MOD-05]].
- Evidence: test_each_hotel_has_four_competitors_within_10_percent_of_its_rate, test_comp_set_median_starts_at_the_hotels_own_rate, test_comp_median_moves_every_day_and_beyond_the_threshold_only_on_a_shock

### CON-04 [C] Competitor median
- Definition: the median of the four competitors' rates for a stay date as shopped on a day. With four rates it is the mean of the middle two.
- Use: every rate ratio ([[CON-05]]) is measured against it. A move of 5% or more since yesterday raises a flag ([[RUL-65]]).
- Implemented by: comp_median() in [[MOD-05]] ([[DAT-06]]). The noise behind it is drawn afresh every shop day ([[DEC-62]]); the noise alone never moves it 5% from its starting level.
- Evidence: test_comp_median_moves_every_day_and_beyond_the_threshold_only_on_a_shock, test_hotel_starts_level_with_its_comp_median

### CON-05 [C] Rate ratio
- Definition: the hotel's rate divided by its competitor median for the same stay date. Bookings scale with the ratio to the power of minus the elasticity ([[CON-06]]). The detect table carries it as rate_vs_median ([[DAT-08]]).
- Implemented by: Books.expected_new_bookings() in [[MOD-06]]. The agent's estimate in [[MOD-08]] applies a candidate's ratio the same way.
- Evidence: test_expected_new_bookings_follow_the_formula, test_numbers_follow_the_definitions

### CON-06 [C] Elasticity
- Definition: how strongly bookings respond to the rate ratio. Expected bookings are multiplied by ratio ** -elasticity. At 1.5 a rate 10% above the median loses about 13% of bookings.
- Two values: the simulator's value ([[RUL-21]]) and the agent's ([[RUL-56]], the oracle) are separate constants on purpose ([[DEC-40]]). In the default mode both are 1.5.
- Modes: the agent can also price with a fixed value, or learn one from the bookings ([[MOD-16]], [[DEC-38]]). The estimator is a Poisson regression on the rate ratio with a prior of width [[RUL-50]]; it closed [[FRK-02]].
- Cautious: the cautious rule ([[CON-11]]) makes the agent respect the estimate's standard error.
- Implemented by: [[MOD-06]] books with it, [[MOD-08]] estimates with the Pricing it is given ([[DAT-21]]), and [[MOD-16]] estimates it. With it and the room cost, the start rate is best on an ordinary night ([[DEC-12]]).
- Evidence: test_expected_new_bookings_follow_the_formula, test_on_nights_that_will_not_sell_out_the_start_rate_is_already_best, test_the_day_59_estimate_recovers_the_simulators_elasticity

### CON-07 [C] Contribution
- Definition: room revenue minus the cost of servicing every room sold. The cost is one third of the hotel's start rate ([[RUL-61]]), and as a measure it is [[MEA-05]].
- Target: the agent scores on it and the summary compares the runs on it ([[DEC-12]]). A customer file may name revenue instead ([[RUL-58]], [[DEC-41]]). The agent then counts each room at its rate, and the summary still reports both.
- Implemented by: Hotel.room_cost in [[MOD-02]], Books.contribution() in [[MOD-06]], and the estimate in [[MOD-08]], which multiplies expected bookings by rate minus cost.
- Evidence: test_contribution_is_revenue_minus_the_cost_of_every_room_sold, test_estimate_is_expected_contribution_on_the_unsold_rooms, test_the_revenue_target_scores_candidates_on_the_rate_alone

### CON-08 [C] Value at stake
- Definition: what a flag's plan is expected to earn over holding. It is the best candidate's estimate minus the hold estimate, summed over the days of the week that change ([[DEC-19]]).
- Queue: a plan enters the queue only at the customer's minimum ([[RUL-67]]) or more ([[DEC-17]]). The queue is printed highest value first.
- Implemented by: Entry.value_at_stake and WeekdayGroup.gain in [[MOD-08]] ([[DAT-14]], [[DAT-12]]), and queue() in [[MOD-12]].
- Evidence: test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue, test_the_queue_holds_plans_worth_the_minimum_highest_value_first

### CON-09 [C] Sell-out
- Definition: a stay date whose rooms on the books reach the hotel's rooms.
- Both sides: the simulator caps each day's draw at the rooms still unsold. The agent's estimate counts the chance of a sell-out through E[min(N, unsold)] ([[DEC-21]]). A night expected to come close to full is therefore where a raise pays.
- Implemented by: Books.book() in [[MOD-06]], and expected_bookings() in [[MOD-08]].
- Evidence: test_rooms_never_exceed_the_hotel, test_expected_bookings_is_the_mean_of_a_poisson_count_that_stops_at_the_unsold_rooms, test_a_raise_wins_only_where_the_night_has_a_real_chance_of_selling_out

### CON-10 [C] Hold period
- Definition: an accepted rate change on day d holds the changed stay dates on days d+1 to d+7 ([[RUL-66]]), or for 7 days of ticks with several ticks a day. A new shock lifts the hold ([[DEC-06]]); a pace gap alone raises no flag under it.
- Implemented by: Agent.held in [[MOD-10]], and flags() in [[MOD-07]], which drops pace-only causes on held stay dates.
- Evidence: test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags, test_accepted_rates_apply_and_hold_those_stay_dates_for_7_days

### CON-11 [C] The cautious rule
- Definition: a learned elasticity ([[CON-06]]) comes with a standard error, and the cautious rule makes the agent respect it. Every candidate is scored at the estimate and at the estimate one standard error lower and higher ([[RUL-54]]).
- Band: the band is clamped to the estimator's bounds [[RUL-51]] and [[RUL-52]]. A candidate replaces hold only if it is ahead of hold at all three. The best such candidate wins, or the day of the week holds.
- Minimum: the minimum value at stake ([[RUL-67]]) applies to the whole plan, as in every mode ([[DEC-43]]). Without the rule the highest estimate wins as before.
- Effect: early in a run the band is wide, so the rule holds on ordinary nights. It still acts where the gain comes from a sell-out ([[CON-09]]) rather than from the elasticity.
- Implemented by: Pricing.band and WeekdayGroup.best, replaces_hold and rejected_at_an_end in [[MOD-08]]. --cautious in [[MOD-12]] sets it on every learn mode ([[DAT-22]]). The request and the template in [[MOD-09]] carry the three values.
- Decision: [[DEC-39]], with [[DEC-43]] for the one minimum rule.
- Evidence: test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held, test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side, test_the_three_values_reach_the_model_request

### CON-12 [C] The customer's real counterparts
- Definition: each piece here stands for one thing a hotel company has. The customer file is the market ([[DAT-27]]). The four interfaces ([[DAT-25]]) are the reservation system, the rate shop, the schedule feed and the events calendar.
- Tables: the stored tables ([[DAT-28]]) are the day's snapshot the customer's systems write, and run-day ([[MOD-12]]) is the daily job over them ([[DEC-42]]).
- Clock: the clock ([[RUL-128]]) is the cadence of their feeds. A feed that lands once a day gives the daily loop, and one that lands through the day gives the ticks ([[DEC-46]]).
- Audit: the cache ([[DAT-17]]) and the replay are the audit trail. Each decision keeps its request, answer and digests ([[DEC-45]]).
- Market: a second market runs with --customer and no change to the agent ([[DEC-69]], [[RES-44]]).
- Where: the README section "What this is when a customer stands behind it", under "Data as it comes in".
- Kind: policy
- Evidence: review
