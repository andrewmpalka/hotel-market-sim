# Shocks

The four shocks, with the day each becomes known. Two live in the schedule
([[MOD-01]]) and two in shocks.py ([[MOD-03]]). Each one produces a flag on
the day it becomes known, and every lookup on them takes the day it is made
on ([[RUL-03]]).

### SHK-01 [C] The convention
- Known on day: 10
- Stay dates: 45 to 48
- Effect: demand at the two downtown hotels rises 35%, and from shop day 10 their competitors charge 15% more on those nights. The peak night is computed, not fixed: Thursday 45 ([[DEC-09]]).
- File: src/hotel_market/shocks.py
- Flags: [[RUL-37]] and [[RUL-35]] on day 10 at both downtown hotels for stay dates 45 to 48
- Evidence: test_convention_raises_downtown_demand_35_percent_on_days_45_to_48_from_day_10, test_each_shock_flags_on_the_day_it_becomes_known

### SHK-02 [C] The new flights
- Known on day: 20, when the airline files them
- Stay dates: 50 to 149
- Effect: four new daily flights, two each from MCO and BNA on 180-seat equipment, add 720 seats a day: +17% on a normal day's 4,244. Demand rises by each hotel's air share times that ([[MOD-04]]).
- File: src/hotel_market/schedule.py
- Flags: [[RUL-33]] on day 20 at every hotel for stay dates 50 to 109, the end of that day's window
- Evidence: test_seat_change_as_of_day_21_is_plus_17_percent_for_day_55, test_new_flights_raise_demand_from_day_20, test_each_shock_flags_on_the_day_it_becomes_known

### SHK-03 [C] The competitor rate cut
- Known on day: 30, the first shop day that shows it
- Stay dates: 37 to 39
- Effect: the two cheapest competitors of the full-service hotel cut their rates 20%, which moves that comp median down by 5% or more
- File: src/hotel_market/shocks.py
- Flags: [[RUL-36]] on day 30 at the full-service hotel for stay dates 37 to 39; the candidate [[RUL-42]] joins the usual four, and in the seed-7 run nothing beat holding
- Evidence: test_two_full_service_competitors_cut_20_percent_on_days_37_to_39_from_day_30, test_the_cut_moves_the_full_service_comp_median_by_5_percent_or_more, test_each_shock_flags_on_the_day_it_becomes_known

### SHK-04 [C] The route suspension
- Known on day: 40, when the airline files it
- Stay dates: 70 to 90
- Effect: the DFW route, three daily flights of 160 seats, stops: 480 seats a day fewer, about 10% below the schedule known the day before. Seats stay above the original baseline (+240 a day), which is why the trigger is the revision against yesterday, not the change against the baseline ([[DEC-04]]).
- File: src/hotel_market/schedule.py
- Flags: [[RUL-34]] on day 40 at every hotel for stay dates 70 to 90; in the seed-7 run every take-back plan was worth less than [[RUL-67]] and was held
- Evidence: test_route_cut_lowers_demand_from_day_40, test_each_shock_flags_on_the_day_it_becomes_known
