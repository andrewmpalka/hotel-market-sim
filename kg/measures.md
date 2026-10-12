# Measures

The numbers a run is judged by, each with its exact formula and the function
that computes it. `kg_check.py` confirms that each function exists. All five
are per hotel over a range of stay dates. The summary reports room revenue
and contribution over stay dates 0 to 149, and again over only the stay dates
the agent changed.

### MEA-01 [C] Occupancy
- Formula: rooms sold over the stay dates / (the hotel's rooms x the number of stay dates)
- Function: hotel_market.bookings.Books.occupancy
- Used by: the check that a fixed-rate run ends between 60% and 90% full at every hotel ([[RES-02]]). It covers stay dates 0 to 59.
- Evidence: test_occupancy_is_rooms_sold_over_rooms_available, test_fixed_rate_occupancy_is_between_60_and_90_percent_for_stay_dates_0_to_59

### MEA-02 [C] Average rate
- Formula: room revenue / rooms sold, over the stay dates: the average daily rate. It is nan when no room was sold.
- Function: hotel_market.bookings.Books.average_rate
- Used by: nothing in the reports yet. It is the measure a raise moves up.
- Evidence: test_average_rate_is_room_revenue_over_rooms_sold

### MEA-03 [C] Revenue per available room
- Formula: room revenue / (the hotel's rooms x the number of stay dates), which equals occupancy x average rate
- Function: hotel_market.bookings.Books.revpar
- Used by: nothing in the reports yet.
- Evidence: test_revpar_is_room_revenue_over_rooms_available

### MEA-04 [C] Room revenue
- Formula: the sum over stay dates and booking days of rooms booked that day x the rate in force that day. A rate change counts only for the bookings made after it.
- Function: hotel_market.bookings.Books.room_revenue
- Used by: [[DAT-20]] and the summary. It falls in every seed when the agent scores on contribution ([[RES-01]]). It rises in every seed when the agent scores on revenue ([[RES-07]]).
- Target: under a revenue target it is what a sweep counts ([[DAT-24]], [[DEC-41]]).
- Evidence: test_fixed_rate_revenue_is_rooms_times_starting_rate, test_the_summary_reports_revenue_and_contribution_for_both_runs

### MEA-05 [C] Contribution
- Formula: room revenue - rooms sold x cost per occupied room. The cost is the customer's cost share x the start rate ([[RUL-61]]).
- Function: hotel_market.bookings.Books.contribution
- Used by: the agent's default target ([[CON-07]], [[DEC-12]], [[RUL-58]]), [[DAT-19]], [[DAT-20]] and the summary.
- Evidence: test_contribution_is_revenue_minus_the_cost_of_every_room_sold, test_the_summary_compares_both_runs_on_the_changed_pairs

### MEA-06 [C] Regret
- Formula: the realised change of the arm that followed the oracle - the realised change of the arm under test. Both arms share the seed and the mode, and a positive regret means the reviewer left money behind.
- Function: hotel_market.bench.regret
- Used by: the bench report ([[MOD-23]]), per arm and per seed, with the oracle reviewer's arm as the reference ([[DEC-47]]).
- Evidence: test_regret_is_the_oracle_arms_change_minus_the_arms_change

### MEA-07 [C] Accept rate
- Formula: queued entries whose plan the reviewer accepted / queued entries. A queued entry is one the reviewer saw; an entry under the minimum is never asked. nan with no queued entry.
- Function: hotel_market.bench.accept_rate
- Used by: the bench report ([[MOD-23]]). The template's rate is 1, and the oracle's in the default mode is 1 too.
- Evidence: test_accept_rate_counts_accepted_queued_plans

### MEA-08 [C] Decline precision
- Formula: the reviewer's declines that the oracle also declined / the reviewer's declines. nan when the reviewer declined nothing.
- Function: hotel_market.bench.decline_precision
- Used by: the bench report ([[MOD-23]]). A decline stands for a block in the fraud benchmark the measures follow.
- Evidence: test_decline_precision_recall_and_f1_against_the_oracle, test_the_measures_are_nan_when_nobody_declined

### MEA-09 [C] Decline recall
- Formula: the oracle's declines that the reviewer also declined / the oracle's declines. nan when the oracle declined nothing.
- Function: hotel_market.bench.decline_recall
- Used by: the bench report ([[MOD-23]]).
- Evidence: test_decline_precision_recall_and_f1_against_the_oracle, test_the_measures_are_nan_when_nobody_declined

### MEA-10 [C] Decline F1
- Formula: 2 x precision x recall / (precision + recall), from [[MEA-08]] and [[MEA-09]]. nan when either is nan, and 0 when both are 0.
- Function: hotel_market.bench.decline_f1
- Used by: the bench report ([[MOD-23]]).
- Evidence: test_decline_precision_recall_and_f1_against_the_oracle, test_the_measures_are_nan_when_nobody_declined

### MEA-11 [C] Dollar-weighted decline recall
- Formula: the oracle's loss from accepting a plan is hold minus plan at ORACLE_ELASTICITY. The recall is that loss summed over the plans both declined / the loss over every plan the oracle declined.
- Function: hotel_market.bench.dollar_weighted_recall
- Weight: a wrong elasticity overstates a plan's own value at stake ([[CON-08]]). The oracle's loss is therefore the weight.
- Used by: the bench report ([[MOD-23]]). It weighs a missed decline by what accepting it cost at the simulator's elasticity.
- Evidence: test_decline_precision_recall_and_f1_against_the_oracle

### MEA-12 [C] Recovered share
- Formula: (the arm's mean realised change - the template's) / (the oracle's - the template's), on the same seeds and mode. 1 is the oracle's, 0 is accept-all's, and below 0 the reviewer lost money against accept-all.
- Function: hotel_market.bench.recovered_share
- Tie: nan when the oracle and the template tie, as in the true mode, since there is nothing to recover ([[DEC-47]]).
- Used by: the bench report ([[MOD-23]]), per mode and pooled over the mismatched modes. It is the one figure that says how much of the value a reviewer could recover this one did.
- Evidence: test_the_recovered_share_is_the_gain_over_the_template_as_a_share_of_the_oracles
