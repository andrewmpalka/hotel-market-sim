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
