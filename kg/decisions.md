# Decisions

One DEC node per design decision, in two groups: the market and the agent's
design, then engineering. Within a group the nodes are in the order the
decisions were made. A node says what was decided, what it replaced and why,
and names the commit it landed in. The commit is information, not evidence:
the evidence is the tests the node cites. A node keeps at most one headline
figure and links to its RES node in `results.md` for the rest. A replaced
design keeps its node, marked [H], and names the decision that replaced it.

## Market and agent design

### DEC-01 [C] Code computes every number; the model only chooses and writes
- Decided: every number in a flag, a candidate, an estimate, a reason and a report comes from code. The model sees the request ([[DAT-16]]), picks the plan or hold for each entry, and writes two or three sentences.
- Replaces: nothing; it is the first rule of the project.
- Reason: a number the model made up could not be traced or tested. The comparison of the two runs would then measure the model's arithmetic and not the policy.
- Commit: 15e0215
- Evidence: test_a_choice_that_is_not_the_plan_or_hold_is_rejected, test_every_figure_in_the_request_is_a_display_string
- Links: [[RUL-01]], [[MOD-09]], [[DAT-16]]

### DEC-02 [C] Nothing is used before the day it becomes known
- Decided: every lookup takes the day it is made on: build_schedule(as_of_day), events_as_of, rate_cuts_as_of, comp_rates(shop_day, ...) and expected_demand(hotel, stay_day, as_of_day).
- Replaces: nothing; it is the third rule of the project.
- Reason: an agent that sees a flight before the airline files it is not tested on the schedule data at all.
- Measured: the seat change for day 55 is 0% as of day 19 and +17% as of day 21.
- Commit: 53a7081
- Evidence: test_nothing_changes_demand_before_day_10, test_shock_known_follows_what_is_known_on_the_day
- Links: [[RUL-03]], [[MOD-01]], [[MOD-03]], [[MOD-04]]

### DEC-03 [C] The day-0 preload: bookings made before the run starts
- Decided: the simulator loads every stay date of the horizon with a seeded Poisson draw before day 0's bookings. The mean is normal_demand x the hotel's curve(days out + 1), capped at the rooms, at the start rate.
- Replaces: nothing built. Empty books would have flagged every early stay date as behind pace and left tonight's hotel empty.
- Reason: the first 90 stay dates are already part way up the booking curve when the run starts. A curve that holds a share 90 or more days out gives the later stay dates that share too.
- Measured: tonight is 1 - 0.15 / 7 of the way up the convention hotel's curve. It therefore starts with about 279 of its 285 expected rooms on the books.
- Commit: 054edd6
- Evidence: test_preload_mean_is_normal_demand_x_curve_of_days_out_plus_1, test_day_0_starts_with_the_bookings_made_before_the_run
- Links: [[MOD-06]], [[DAT-07]], [[RUL-68]], [[CON-01]]

### DEC-04 [C] The passenger revision is the trigger; the change is carried for the text
- Decided: the detector flags a stay date when its arriving passengers move 5% or more since the day before ([[RUL-64]], [[DEC-63]]). The change against the no-shock baseline is shown but never flags.
- Replaces: nothing built; flagging on the change against the baseline was the first idea.
- Reason: the change stays up from day 20 on. Flagging on it would re-flag stay dates 50 to 149 every day. The revision is zero except on the two filing days.
- Measured: after the day-40 cut, seats on days 70 to 90 stay 240 a day above the baseline. They are 480 a day (about 10%) below the day before.
- Commit: abef71f
- Evidence: test_shock_causes_appear_only_on_the_days_shocks_become_known, test_known_passenger_revision_matches_the_schedule
- Links: [[SHK-02]], [[SHK-04]], [[DAT-02]], [[MOD-07]]

### DEC-63 [C] Arriving passengers, not seats, drive demand
- Decided: the demand rule and the agent's forecast read arriving passengers: each flight's seats at its load factor ([[RUL-125]]). A route the airline adds opens emptier and fills over a quarter ([[RUL-126]], [[RUL-127]]).
- Replaces: the seat link, where every seat filed counted as a seat flown from the first day.
- Reason: half of the headline gain rode on an immediate seat link. A new route's passengers arrive more slowly than its seats, and a suspended route loses only the passengers it carried.
- Agent: the detect numbers and FlagNumbers are passenger_change and passenger_revision ([[DAT-08]], [[DAT-13]]). The request keeps the keys seat_change and seat_revision, and its display strings say passengers.
- Evidence: test_passengers_are_seats_at_the_load_factor_and_a_new_route_ramps, test_known_passenger_revision_matches_the_schedule
- Links: [[DEC-04]], [[DAT-02]], [[SRC-03]], [[SHK-02]], [[SHK-04]]


### DEC-64 [C] Each hotel's luck and shop noise come from its own stream
- Decided: the booking luck comes from a stream keyed by the seed and the hotel's key ([[RUL-22]]), and the shop noise from one keyed by the seed, the hotel's key and the competitor's name ([[RUL-20]]).
- Replaces: one stream per run, where every hotel's draws sat in one array by row.
- Reason: a hotel added to the customer file took a row in that array and moved every other hotel's draws. With its own stream, the other hotels' fixed-rate bookings stay as they were.
- Evidence: test_a_fifth_hotel_leaves_the_other_hotels_fixed_rate_bookings_unchanged, test_rates_depend_only_on_the_seed
- Links: [[DEC-22]], [[DEC-62]], [[MOD-05]], [[MOD-06]], [[DAT-07]]

### DEC-65 [C] The market's price response is on by default, at 1.0
- Decided: the simulator's and the agent's defaults are 1.0 ([[RUL-87]], [[RUL-88]]), and the customer file records market.elasticity = 1.0 ([[RUL-124]]). --market-elasticity overrides it for a run; the agent is told the value.
- Replaces: a default of 0.0, where a matched raise cost no rooms ([[DEC-52]]).
- Reason: a market-wide rate rise should lose demand in proportion. The value is chosen on that reason and not on any result; the review found the convention's gain rode mostly on the competitors' raise through the rate ratio.
- Measured: the default mode earns +$16,164 a seed on world v2 against +$32,899 on world v1 ([[RES-01]]).
- Evidence: test_the_market_elasticity_scales_demand_with_the_medians_level, test_the_demo_file_describes_the_market_in_claude_md
- Links: [[DEC-52]], [[RUL-87]], [[RUL-88]], [[RUL-124]], [[UNK-15]], [[RES-01]]

### DEC-66 [C] Each hotel carries its own booking curve
- Decided: each hotel entry in the customer file holds a booking_curve ([[RUL-68]], [[RUL-69]]), read by Hotel.curve() ([[CON-01]]). The preload, pace baseline, planner and estimator read it; the preload covers the whole horizon.
- Replaces: one transient curve for all four hotels ([[FRK-12]]).
- Reason: a convention hotel holds group blocks months out and an airport hotel books late. Each curve suits its kind of hotel: a quarter of the convention hotel's rooms 90 days out, a tenth at the full-service, none at the airport.
- Measured: on seed 7 the two downtown hotels change no rate on the convention nights, because most of their business is in before the announcement ([[RES-02]], [[RES-41]]).
- Evidence: test_curve_matches_the_points_and_is_linear_in_between, test_preload_mean_is_normal_demand_x_curve_of_days_out_plus_1, test_the_demo_file_describes_the_market_in_claude_md
- Links: [[CON-01]], [[DAT-04]], [[DEC-03]], [[FRK-12]], [[RES-02]], [[RES-41]]
### DEC-67 [C] A day's bookings are drawn once and split over its ticks
- Decided: with N ticks a day, tick 1 draws the day's count as before and assigns each booking to a tick from the hotel's own stream ([[RUL-132]]). Each tick then books its share.
- Replaces: nothing built; with one tick a day the loop is the daily one, and its log is byte for byte what it was.
- Reason: a fixed-rate run must book the same rooms per hotel and stay date at every N, not the same in expectation, so a finer clock changes only what the agent sees and when it acts.
- Change: a rate changed at tick t applies from tick t+1. The bookings still to come that day are thinned by a binomial, or topped up by a Poisson, at (new / old) ** -ELASTICITY ([[RUL-21]]).
- Feeds: the shop lands at [[RUL-129]], the filing at [[RUL-130]], an event at the day's last tick, and bookings at every tick; a customer file may name other ticks ([[DAT-27]]). Before a feed lands, a tick reads the previous value.
- Evidence: test_the_fixed_rate_run_books_the_same_rooms_at_one_tick_a_day_and_at_four, test_a_rate_changed_at_a_tick_thins_or_tops_up_the_ticks_after_it, test_the_default_clock_books_byte_for_byte_what_it_booked_before_the_split
- Links: [[MOD-06]], [[MOD-19]], [[DAT-07]], [[RUL-128]], [[DEC-22]], [[DEC-64]]

### DEC-05 [C] The booking loop runs to day 149 with rates frozen from day 60
- Decided: the agent decides on days 0 to 59. The loop keeps booking to day 149 with no new decisions. The window stops at stay date 149, so every stay date from 0 to 149 ends complete.
- Replaces: nothing built; the first plan stopped the loop at day 59.
- Reason: the last decisions change stay dates up to 148, which would be mostly empty on day 59. The summary counts all 150 stay dates.
- Measured: on seed 7 with fixed rates, stay dates 140 to 149 end 78% to 91% full by hotel ([[RES-02]]).
- Commit: 054edd6
- Evidence: test_every_stay_date_to_149_is_complete, test_rates_can_only_change_on_days_0_to_59
- Links: [[RUL-12]], [[RUL-05]], [[MOD-06]]

### DEC-06 [C] The 7-day hold after an accepted rate change
- Decided: an accepted change on day d holds its stay date on days d+1 to d+7 ([[RUL-66]]). Under the hold a pace gap alone raises no new flag, and a shock cause lifts the hold.
- Replaces: nothing built.
- Reason: a new rate needs days of bookings before its pace reads differently. Deciding the same stay date every day would chase booking noise.
- Measured: in the first full agent run one stay date was changed five times across days 10 to 44 ([[RES-11]]). That led to the minimum ([[DEC-17]]).
- Commit: abef71f
- Evidence: test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags, test_accepted_rates_apply_and_hold_those_stay_dates_for_7_days
- Links: [[MOD-07]], [[MOD-10]], [[DAT-09]], [[CON-10]]

### DEC-07 [C] A pace flag needs a gap beyond 10% of rooms and 3 standard deviations
- Decided: the pace threshold is max(0.10 x rooms, 3 x sqrt(normal demand x curve)) ([[RUL-62]], [[RUL-63]]).
- Replaces: nothing built; a single percentage floor was the first idea.
- Reason: a percentage of rooms alone flags far-out stay dates, where few rooms are on the books and noise dominates. 3 x sqrt(mean) is three Poisson standard deviations.
- Measured: tonight at the convention hotel 3 x sqrt(285) = 50.6 beats the 40-room floor; sixty days out the floor wins.
- Commit: abef71f
- Evidence: test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd
- Links: [[MOD-07]], [[DAT-08]], [[CON-02]]

### DEC-08 [H] The convention's peak night was fixed at stay date 46
- Decided: the second review set the peak night at 46 as a given.
- Replaced by: [[DEC-09]]
- Reason it went: with the downtown weekday factors, Thursday 45 (1.05) draws more demand than Friday 46 (0.90). The fixed night was the wrong one.
- Commit: 53a7081
- Links: [[SHK-01]]

### DEC-09 [C] The peak night is the expected-demand peak on the event's known day
- Decided: peak_night(hotel, event, sources) in [[MOD-18]] is the event night with the highest expected demand as of event.known_day. The earliest night wins a tie.
- Replaces: [[DEC-08]]
- Reason: the peak must follow the data and the as-of rule. For the convention it is Thursday 45 at both downtown hotels.
- Measured: a test event over nights 49 to 55 has its peak on Monday 49. Once the day-20 flights are known, the peak moves to Thursday 52.
- Commit: abef71f
- Evidence: test_convention_peak_night_is_its_busiest_night_as_of_day_10, test_peak_night_uses_what_is_known_on_the_day_the_event_becomes_known
- Links: [[MOD-18]], [[SHK-01]], [[RUL-03]]

### DEC-10 [C] A minimum stay is advice only, never simulated
- Decided: when an event's peak night is ahead of pace, the agent recommends a two-night minimum once per hotel and event. The advice goes into decisions.jsonl marked "simulated": false and stays out of every estimate and result.
- Replaces: nothing built.
- Reason: the simulator has no length of stay, so a minimum-stay rule cannot be booked or scored. Recorded as advice, it keeps the estimates honest and still shows the recommendation.
- Commit: abef71f
- Evidence: test_minimum_stay_advice_is_given_once_per_hotel_and_event_and_not_simulated, test_minimum_stay_advice_is_not_repeated_on_later_days
- Links: [[DAT-15]], [[MOD-10]], [[FRK-03]]

### DEC-11 [H] The rule "seats up, so raise the rate"
- Decided: the first plan for the agent raised rates when seats rose and lowered them when seats fell.
- Replaced by: [[DEC-12]] and [[DEC-13]], before it was built
- Reason it went: it ignored the cost of servicing each room sold. A raise on a night that will not sell out loses bookings for nothing. A rule that always raises on more seats decides nothing, so the agent scores candidates instead.
- Commit: abef71f
- Links: [[SHK-02]]

### DEC-12 [C] Contribution with a room cost is the target
- Decided: each occupied room costs one third of the hotel's start rate to service ([[RUL-61]]). Contribution is room revenue minus that cost for every room sold, and the agent scores candidates on it.
- Replaces: [[DEC-11]], and revenue as the implicit target
- Reason: revenue rewards selling every room at any price. With ELASTICITY 1.5 the contribution-best rate on a night that will not sell out is 3 x cost. That is the start rate, so only a night that may sell out can pay for a raise.
- Measured: with fixed rates, seed 7 holds occupancy at 75.7% to 83.7% by hotel over stay dates 0 to 59 ([[RES-02]]).
- Commit: 9d74c0d
- Evidence: test_each_occupied_room_costs_a_third_of_the_start_rate, test_contribution_is_revenue_minus_the_cost_of_every_room_sold, test_on_nights_that_will_not_sell_out_the_start_rate_is_already_best
- Links: [[RUL-61]], [[RUL-21]], [[FRK-01]], [[CON-07]]

### DEC-13 [C] Every flag gets scored candidates; hold is the default
- Decided: every flag gets hold, raise 5%, raise 10% and lower 5% ([[RUL-43]]), each clamped to the floor and ceiling. A comp median drop adds lower halfway to the new median ([[RUL-42]]). Code scores each on the rooms still unsold.
- Detail: when nothing beats hold the entry is recorded as a hold and stays out of the queue. The model may decline the best candidate, which also records a hold.
- Replaces: [[DEC-11]]
- Reason: the same candidates for every cause keep the agent from reacting to a label, because the estimate decides. Hold wins a tie, so the agent never changes a rate for nothing.
- Commit: abef71f
- Evidence: test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits, test_a_comp_median_drop_adds_lower_halfway_to_the_new_median, test_a_model_that_declines_changes_no_rate
- Links: [[MOD-08]], [[DAT-11]], [[DAT-12]], [[CON-08]]

### DEC-14 [C] Base occupancy is 0.85 at the airport hotel
- Decided: the customer file stores base occupancy per hotel ([[DAT-04]]), and the airport hotel's is 0.85.
- Replaces: one base occupancy of 0.75 for every hotel.
- Reason: the value is a choice about the scenario. At 0.75 the new flights never fill the airport hotel, so the schedule data would never matter there. At 0.85 Mondays, Thursdays and Sundays after day 50 are expected 101% full.
- Measured: with fixed rates the airport hotel ends at 83.7% over stay dates 0 to 59 ([[RES-02]]). That is inside the 60% to 90% check.
- Commit: 9d74c0d
- Evidence: test_hotels_match_the_table, test_fixed_rate_occupancy_is_between_60_and_90_percent_for_stay_dates_0_to_59
- Links: [[DAT-04]], [[SHK-02]]

### DEC-15 [H] Rates followed the day of the week
- Decided: each hotel's starting rate and each competitor's rate carried a factor of 1 + 0.5 x (demand factor - 1). A Saturday at the lifestyle hotel started 12.5% dearer than its table rate.
- Replaced by: [[DEC-16]]
- Reason it went: with a fixed room cost the best rate on a night that will not fill is the same every day. The weekday factor therefore made the starting rates wrong, and most of the agent's gain came from correcting them ([[RES-11]]).
- Commit: bd556fb
- Links: [[MOD-05]], [[DAT-04]], [[RES-11]]

### DEC-16 [C] Flat rates ignore the day of the week
- Decided: every hotel's starting rate is its table start rate on every stay date. Competitor rates are base rate x noise with the shocks applied. Demand still follows the day of the week ([[DAT-04]]).
- Replaces: [[DEC-15]]
- Reason: with a fixed room cost the best rate on an ordinary night is the same every day. Flat starting rates are therefore right on those nights, and the agent's gain comes from reacting to the market.
- Measured: on seed 7 the gain fell from +$26,420 to +$22,894 with this change, the per-weekday plan and the minimum ([[RES-11]]). The smaller number is the true one.
- Commit: bd556fb
- Evidence: test_competitor_rates_are_base_rate_x_noise_with_no_weekly_pattern, test_hotel_starts_level_with_its_comp_median
- Links: [[MOD-05]], [[DEC-12]], [[RES-11]]

### DEC-17 [C] A plan needs $250 over holding to enter the queue
- Decided: a plan needs a value at stake of at least $250 ([[RUL-67]], a setting of the customer file since [[DEC-41]]). An entry below it is recorded as a hold with the reason "under the $250 minimum".
- Replaces: a queue of every entry whose best candidate beat hold by any amount.
- Reason: the first full agent run made rate changes worth under $10, and some of them lost money ([[RES-11]]). A revenue manager should not be shown an $8 recommendation.
- Measured: on seed 7 the minimum holds 57 of the 113 flags ([[RES-02]]).
- Commit: abef71f
- Evidence: test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue, test_entries_below_the_minimum_are_held_and_stay_out_of_the_queue
- Links: [[RUL-67]], [[SHK-04]], [[CON-08]]

### DEC-18 [H] One candidate moved all of a flag's stay dates together
- Decided: the first agent applied one candidate to every stay date in a flag.
- Replaced by: [[DEC-19]]
- Reason it went: the day-20 airport flag covers stay dates 50 to 109. One move raised all sixty, the Tuesdays and Saturdays that would never fill included.
- Commit: abef71f
- Links: [[SHK-02]], [[RES-11]]

### DEC-19 [C] The best candidate is chosen per day of the week within a flag
- Decided: the planner groups a flag's stay dates by weekday ([[DAT-12]]). Each group gets its own best candidate, and hold wins a tie. The plan names the days that change, and value at stake is summed over them.
- Replaces: [[DEC-18]]
- Reason: the quiet days of the week in a long flag should hold while the busy ones move.
- Measured: on day 20 the airport hotel raises every night but Saturday, worth $10,627 with the exact estimate ([[RES-12]], [[RES-02]]).
- Commit: abef71f
- Evidence: test_a_plan_lists_its_changes_by_day_of_week, test_after_the_new_flights_the_airport_raises_every_night_close_to_full
- Links: [[MOD-08]], [[DAT-14]], [[CON-08]]

### DEC-20 [H] Expected bookings were capped at the unsold rooms
- Decided: estimated bookings = min(remaining demand x (rate / median) ** -AGENT_ELASTICITY, unsold rooms).
- Replaced by: [[DEC-21]]
- Reason it went: the cap treats a night expected to come close to full as if it could not sell out. It understated the day-20 airport plan by about half and held nights the exact estimate raises ([[RES-12]]).
- Note: the cap was first kept as a known limit because the error looked like $200 on a $2,000 estimate.
- Commit: abef71f
- Links: [[MOD-08]], [[RES-12]]

### DEC-21 [C] Estimated bookings are E[min(N, unsold)] for a Poisson N
- Decided: expected_bookings(mean, unsold) sums the Poisson probabilities below the unsold count and gives the rest to a sell-out. That is the booking noise the simulator draws.
- Replaces: [[DEC-20]]
- Reason: a night expected 97% full still sells out fairly often, so a small raise there pays.
- Measured: the 20-seed mean went from +$27,350 to +$32,899 ([[RES-12]], [[RES-01]]). The agent was ahead in 20 of 20 seeds both before and after.
- Commit: abef71f
- Evidence: test_expected_bookings_is_the_mean_of_a_poisson_count_that_stops_at_the_unsold_rooms, test_expected_bookings_matches_the_simulators_daily_draws, test_a_night_close_to_full_raises_where_a_cap_on_demand_would_hold
- Links: [[MOD-08]], [[DAT-10]], [[CON-09]]

### DEC-22 [C] One random number per booking draw, fixed by the seed
- Decided: every draw of the run has its own uniform random number, drawn in one go from the seed. The function poisson_draw turns it into a count by the Poisson quantile. A bigger mean never gives a smaller count on the same number.
- Replaces: nothing built; a shared random stream was the alternative.
- Reason: a rate change on one stay date leaves every other draw as it was. The fixed-rate and agent runs therefore differ only where the agent acted, and the changed-pairs comparison is exact.
- Streams: since world v2 each hotel draws from its own stream, keyed by its key ([[DEC-64]]).
- Measured: on seed 7 of world v2 the 70 hotel-nights the agent changed carry the whole +$19,796 ([[RES-02]]). The other 530 book identically in both runs.
- Commit: 054edd6
- Evidence: test_a_rate_change_applies_from_the_next_day_and_touches_no_other_stay_date, test_every_other_pair_books_the_same_in_both_runs, test_a_bigger_mean_never_draws_fewer_rooms_on_the_same_luck
- Links: [[MOD-06]], [[DAT-07]], [[RUL-02]], [[RUL-22]]

### DEC-26 [H] AGENT_ELASTICITY is the agent's own constant
- Decided: plan.py defined AGENT_ELASTICITY = 1.5 ([[RUL-39]]). A test read the module's imports to make sure ELASTICITY ([[RUL-21]]) was not among them.
- Replaced by: [[DEC-40]], which draws the line around the whole agent and names the value an oracle ([[RUL-56]]).
- Reason it went: one constant kept apart was the right idea on too small a scale. The agent still read the simulator's demand, draws and shocks directly.
- Commit: abef71f
- Links: [[RUL-39]], [[RUL-21]], [[FRK-02]], [[DEC-38]]

### DEC-35 [C] Every number is synthetic; the schedule's columns follow a published dictionary
- Decided: the city, airports, airlines, flights, hotels, competitors and bookings are invented. The schedule table's column names follow Cirium's published schedule data dictionary. The code therefore reads data shaped like a real feed.
- Policy: the repository holds no Cirium data and has no affiliation with Cirium. It names no real hotel brand or employer anywhere.
- Replaces: a schedule whose IS_WETLEASE was set wherever the carriers differed. A differing operating carrier is capacity purchase, so the flag is now False on every row. The carrier pair expresses the arrangement ([[MOD-01]]).
- Reason: the project tests whether the loop works and not a market. Data shaped like a real feed makes the counting traps real traps without any real rows.
- Commit: e134523
- Kind: policy
- Evidence: review
- Links: [[DAT-01]], [[MOD-01]], [[RUL-06]]

### DEC-36 [C] The summary reports what the run produces; nothing is tuned
- Decided: the summary reports the comparison of the two runs as it comes out. It shows every rate-changing decision and the plans that lost money. The README states that the agent shares the simulator's demand formula.
- Replaces: nothing.
- Reason: a tuned gain would say nothing about the loop.
- Measured: reported this way, the 20-seed mean is +$32,899 ([[RES-01]]). The agent is ahead in every seed, and revenue is down in every seed.
- Commit: 12e000b
- Kind: policy
- Evidence: review
- Links: [[MOD-12]], [[DAT-20]], [[RES-01]], [[RES-02]]

### DEC-37 [H] Competitor noise drawn once per competitor and stay date
- Decided: the rate-shop noise was one array per seed with shape (hotels, competitors, stay dates), drawn before the run on its own stream ([[RUL-20]]). The shop day only applied the shocks known by then.
- Replaces: nothing built; fresh noise on every shop day was the alternative.
- Reason: fresh noise would have moved every comp median every day and raised comp-median flags from nothing. Drawn once, only the convention nights moved on day 10 and the cut nights on day 30.
- Commit: bd556fb
- Replaced by: [[DEC-62]]
- Links: [[MOD-05]], [[DAT-06]], [[CON-04]]

### DEC-62 [C] The shop noise is fresh every shop day
- Decided: each competitor's noise is drawn per shop day and stay date from a stream keyed by the seed and its name ([[RUL-20]]). The median's starting level is the comp set's base-rate median, with no noise, on both routes.
- Replaces: [[DEC-37]], one draw per competitor and stay date, so a median moved only on a shock.
- Reason: a rate shop that never moved between shocks made every comp-median flag a shock. The estimator saw a ratio that moved only when the hotel did. The name in the key keeps every other competitor's shops as they were.
- Measured: docs/results.md counts the comp-median flags on the days no shock moved a median, over seeds 1 to 20.
- Evidence: test_comp_median_moves_every_day_and_beyond_the_threshold_only_on_a_shock, test_rates_depend_only_on_the_seed
- Links: [[MOD-05]], [[DAT-06]], [[CON-04]], [[RUL-19]], [[RUL-65]]

### DEC-38 [C] The agent can learn its elasticity from the bookings
- Decided: --elasticity picks where the agent's elasticity comes from ([[RUL-49]], [[DAT-22]]). The default, true, is the oracle value ([[RUL-56]]).
- Modes: a fixed:X mode uses X for the whole run. A learn:X mode starts from the prior X and re-estimates every hotel every day ([[MOD-16]]). Every entry, request and log line records the elasticity, its error and its mode ([[DAT-21]]).
- Estimator: a Poisson regression of the bookings on log(rate / median). The offset is the forecast's log baseline with the market term ([[DEC-52]]). An intercept absorbs the level, and [[RUL-50]] to [[RUL-52]] hold and clamp the slope.
- Observations: a stay date's observations stop on the day it sells out. The day-0 preload is never an observation, because the simulator draws it with no price response.
- Reason: with the agent's elasticity equal to the simulator's, the agent was never wrong about price response. The question was what being wrong costs and how much learning wins back ([[FRK-02]], [[UNK-07]]).
- Measured: a wrong value costs about three quarters of the gain ([[RES-03]]). Learning wins back about a quarter of the loss ([[RES-04]], [[RES-10]]).
- Commit: abef71f
- Evidence: test_the_day_59_estimate_recovers_the_simulators_elasticity, test_the_default_mode_gives_the_pinned_seed_7_figure, test_each_mode_records_the_elasticity_its_plans_assume

### DEC-39 [C] The cautious rule changes a rate only where it beats hold across the band
- Decided: in learn mode, --cautious scores every candidate at three elasticities. They are the estimate and the estimate [[RUL-54]] standard error lower and higher, clamped to [[RUL-51]] and [[RUL-52]].
- Rule: a candidate replaces hold only if it is ahead of hold at all three. The best such candidate wins; otherwise the day of the week holds ([[CON-11]], [[MOD-08]]).
- Records: each plan record, the request and the log line store all three values and the rejected candidates ([[DAT-11]], [[DAT-16]], [[DAT-18]]). Without the option nothing changes.
- Replaces: nothing built. It answers the question [[DEC-38]] left open, whether an agent that knows how little it knows keeps more.
- Reason: the plain learning agent acted on estimates it should not have trusted ([[RES-04]]). It made about twice the true arm's rate changes, and its estimates were many times what they realised.
- Measured: from a prior of 1.0 the rule keeps 76% of the true arm's gain, against 43% without it ([[RES-05]]). From 2.0 it keeps 54% against 49%. The first build is [[RES-13]] ([[DEC-43]]).
- Commit: abef71f
- Evidence: test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held, test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side, test_a_cautious_agent_records_the_band_and_what_it_rejected

### DEC-43 [C] The cautious rule tests the band alone; one minimum applies to the plan
- Decided: a cautious candidate replaces hold when it beats hold at the estimate and at both band ends ([[CON-11]]). The minimum value at stake ([[RUL-67]]) applies to the whole plan through Entry.queued, as in every mode.
- Detail: the rejected count now includes every candidate ahead of hold at the estimate, not only those worth $250. The default run and the plain learn runs are unchanged.
- Replaces: the minimum per day of the week that [[DEC-39]] first added. Under it a day of the week worth less than $250 on its own held.
- Reason: two minimum rules were one too many, and the second did almost nothing.
- Measured: the band alone and the first rule differ by $8 and $16 a seed ([[RES-05]], [[RES-13]]). The shares of the true arm's gain stay 76% and 54%.
- Commit: abef71f
- Evidence: test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held, test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue, test_a_cautious_agent_records_the_band_and_what_it_rejected
- Links: [[DEC-39]], [[CON-11]], [[RUL-67]], [[MOD-08]], [[FRK-05]], [[RES-05]], [[RES-13]]

### DEC-44 [C] Every request figure is a display string the prompt says to copy whole
- Decided: every figure in the request ([[DAT-16]], built by [[MOD-09]]) is a display string written by code ([[MOD-11]]). The raw number stays in the log line and the stored tables ([[DAT-13]], [[DAT-18]]).
- Phrases: a signed quantity reads as a phrase with its direction in words and no sign. A range reads as one phrase, and as the single value when both ends read the same.
- Format: a rate, a median, a floor, a ceiling or a cost reads to the dollar. An estimate reads to the nearest $10, rooms to the room, and an elasticity with up to two decimals. A band-end gain under $10 reads to the dollar ([[DEC-56]]).
- Prompt: the system prompt ([[RUL-47]]) tells the model to write as "we" and to copy the phrases whole. It states only what the entry shows and writes event names in lower case. It may write "more than holding" once for several gains.
- Replaces: bare numbers, which the model rounded and reformatted as it pleased, and three later formats ([[RES-08]]). It also replaced the mode name "true" ([[RUL-75]]) and the prompt line "use only numbers that appear in the entry".
- Reason: the model copied figures only when the request held them as finished phrases. Each format was tried in a live run of seed 7 ([[RES-08]], [[UNK-01]]).
- Measured: the fourth run copied every phrase and every range whole in 21,148 input tokens ([[RES-08]], [[DAT-29]]). No figure fell outside its request, and no sentence lacked a request figure.
- Evidence: test_every_figure_in_the_request_is_a_display_string, test_a_range_is_one_phrase_and_the_single_value_when_both_ends_read_the_same, test_the_recorded_live_run_of_seed_7_passes_the_audit

### DEC-45 [C] The tables keep each decision's request, answer and outcome
- Decided: a decision's row holds the request its hotel's queue was asked with, the answer, the request's digest and, from a cache record, the prompt's digest and the model ([[DAT-28]]). An outcomes row holds what a plan earned on a night.
- Outcome: the row holds the rooms sold and the room revenue over every booking day, the plan's estimate for the night ([[DAT-11]]), and what the rooms sold after the decision earned. The sweep prints the same per arm ([[MOD-12]]).
- Replaces: a record with the as-of numbers and every alternative and no request, no digest and no outcome. An operator could rebuild the plan and not show what it earned or what the model was shown.
- Reason: from the tables alone an operator can now show what the agent knew, what the model saw, that the stored answer was the answer to that request, and what the plan earned.
- Request: since world v2 each entry lists the hotel's earlier changes on its stay dates, with the rooms booked since each against the rooms expected ([[DAT-16]]). The template cites the latest; the prompt lets the model cite them.
- Measured: a 60-day run through the tables still writes the in-memory run's decisions file byte for byte ([[RES-14]]), and the seed-7 checksum is unchanged ([[RES-02]]).
- Evidence: test_each_decision_carries_its_request_its_answer_and_their_digests, test_an_entry_lists_the_earlier_changes_on_its_dates_with_the_rooms_booked_since, test_the_stored_state_is_what_the_earlier_decisions_left
- Links: [[DAT-28]], [[DAT-16]], [[DAT-17]], [[MOD-10]], [[MOD-21]], [[DEC-42]], [[FRK-09]], [[RES-37]]

### DEC-46 [C] The agent reprices when data arrives during the day
- Decided: with --ticks N each day is cut into N ticks, the feeds land at fixed ticks of it, and the agent runs after each tick reading the sources as of that tick ([[DEC-68]], [[RUL-128]]).
- Replaces: the daily loop as the only clock; it stays the default, and a run on it is unchanged.
- Reason: a real feed arrives through the day, and a rate decided in the morning is stale by the afternoon. The option shows what the loop earns when it can act within the day.
- Measured: on this world a finer clock earns nothing, +$40 a seed with a standard error of $108, because the demand moves once a day except at the shocks ([[RES-43]]).
- Evidence: test_at_four_ticks_a_day_the_agent_runs_after_each_tick_and_each_feed_flags_at_its_tick, test_a_60_day_run_through_the_tables_at_four_ticks_gives_the_same_decisions_file
- Links: [[MOD-10]], [[DAT-25]], [[DAT-28]], [[DEC-42]], [[DEC-67]], [[DEC-68]], [[RES-43]]

### DEC-68 [C] The clock is an option; a tick is a slice of a day
- Decided: TICKS_PER_DAY is 1 and --ticks N sets a run's clock ([[RUL-128]]). A moment is (day, tick). Every source takes as_of_tick, the day's last by default, and a source made for a tick refuses a later one.
- Replaces: nothing built; the daily loop stays the default and every pinned figure is measured on it.
- Reason: an event-driven agent must read a feed when it lands and act before the day ends. A configurable clock gives that without a wall clock, and N of 1 keeps the daily loop byte for byte.
- Feeds: the shop lands at [[RUL-129]], the filing at [[RUL-130]], an event at the day's last tick and bookings at every tick, or where the customer file puts them ([[DAT-27]]). Real time is this loop with a wall clock behind the sources.
- Record: with more than one tick a day, flags, plans and decisions carry as_of_tick, and each line data_arrived and decided ([[DAT-18]], [[DAT-28]]). The cache names the tick ([[DEC-23]]). The outcomes table credits later days only.
- Evidence: test_a_source_made_for_a_tick_refuses_a_later_tick_of_its_day_on_both_routes, test_the_default_clock_books_byte_for_byte_what_it_booked_before_the_split
- Links: [[RUL-128]], [[DEC-46]], [[DEC-67]], [[MOD-02]], [[MOD-06]], [[MOD-10]], [[MOD-19]], [[MOD-21]], [[RES-43]]

### DEC-49 [C] The benchmark measures the reviewer in the mismatched modes
- Decided: the bench measures every reviewer at fixed:1.0 and fixed:2.0 and keeps the true mode as a check. The ranking pools the two mismatched modes ([[DEC-48]]).
- Replaces: nothing built; the live model had been measured in the true mode only ([[UNK-01]]).
- Reason: in the true mode every plan is scored at the simulator's elasticity, so saying yes to every plan is right. The oracle accepts all ([[DEC-47]]). Only where the code's elasticity is wrong can a decline be right ([[DEC-38]]).
- Measured: at fixed:1.0 on world v2 Opus recovers 0.34 of the oracle's gain over say-yes-to-everything, and Sonnet and Haiku recover none ([[RES-16]], [[RES-19]]).
- Commit: 5935444
- Evidence: test_the_oracle_reviewer_accepts_every_queued_plan_in_true_mode, test_the_offline_bench_on_20_seeds_pins_the_benchmarks_headline
- Links: [[UNK-01]], [[DEC-38]], [[DEC-47]], [[DEC-48]], [[MEA-12]], [[RES-16]], [[RES-17]], [[RES-18]], [[RES-19]]

### DEC-50 [C] A demand bias the agent never sees
- Decided: --demand-bias multiplies the simulator's demand, the preload included ([[RUL-82]]). simulate() takes it. The agent's modules never receive it, and tests/test_sources.py keeps their imports as they are.
- Twin: fixed:X gives the agent a wrong price response and a right demand level ([[DEC-38]]). The bias gives it a wrong demand level and a right price response. Each is one wrong number the agent cannot see.
- Oracle: cli.py tells the oracle reviewer the bias when it builds it, as ORACLE_ELASTICITY names the elasticity for it ([[RUL-56]]). rescored() scales the remaining demand by it, so the oracle stays the simulator's truth ([[DEC-47]]).
- Reason: the estimator's intercept is meant to absorb a demand-level error ([[UNK-07]]). The bias is the first test of that, and of what a level error does to the pace flags ([[UNK-08]]).
- Measured: at a bias of 0.9 the default mode's gain falls to +$1,913 a seed ([[RES-21]]). The learn arms' day-59 estimates hold near 1.5 at both biases ([[RES-22]], [[RES-23]]).
- Commit: 416ea22
- Evidence: test_the_demand_bias_scales_the_preload_and_every_days_draw, test_the_oracle_reviewer_is_told_the_demand_bias, test_the_agent_reads_only_through_the_interfaces
- Links: [[RUL-82]], [[DEC-38]], [[DEC-47]], [[RES-21]], [[RES-22]], [[RES-23]], [[UNK-07]], [[UNK-08]]

### DEC-51 [C] Competitors can follow the hotel's rate changes, as an opt-in arm
- Decided: --react makes each competitor move REACTION_SHARE of a hotel's change from its start rate ([[RUL-83]]). It moves REACTION_LAG days after the change takes effect ([[RUL-84]]). The move is in dollars, on top of the shocks.
- Known: the shop on a day reads the hotel's rate in force REACTION_LAG days earlier from the Books' daily log. Nothing is therefore used before it is known ([[RUL-03]]). The agent's rate-shop source carries the same shop ([[MOD-19]]).
- Default: the reaction is off, so [[DEC-37]] stands for the default run. A fixed-rate run never changes a rate, so it is the same with the reaction on.
- Flags: a median move of 5% or more is a flag cause and lifts the hold ([[RUL-65]], [[RUL-66]]). A reaction can therefore raise a flag on the dates the hotel just changed. Nothing suppresses that.
- Oracle: at first the oracle scored a plan without the reaction and lost the ceiling with it on ([[RES-24]]). The command now tells it the reaction's share and the market elasticity, and it is the ceiling again ([[DEC-52]]).
- Measured: with the reaction on, the default mode earns +$111,272 a seed against +$32,899 without ([[RES-24]], [[RES-25]]).
- Evidence: test_the_reaction_reads_the_hotels_rate_three_days_back_from_the_log, test_the_simulated_rate_shops_carry_the_reaction_the_simulator_used, test_a_reacting_run_goes_to_both_runs_and_never_to_the_agent
- Links: [[DEC-37]], [[DEC-50]], [[RUL-83]], [[RUL-84]], [[RUL-85]], [[RES-24]], [[RES-25]], [[UNK-11]], [[CON-03]]

### DEC-52 [C] The market can answer the comp median's level
- Decided: expected demand scales with (the comp median as shopped / its starting level) ** -MARKET_ELASTICITY ([[RUL-87]]). The starting level is the comp set's base-rate median ([[DEC-62]]). --market-elasticity sets it on both commands.
- Why: bookings follow the hotel's rate against the comp median alone ([[RUL-21]]). A raise the competitors follow therefore costs no rooms, and the reaction run measured the ratchet that makes ([[DEC-51]], [[RES-24]]).
- Agent: forecast.py mirrors the term and the equality test covers it ([[RUL-88]]). The agent is told the run's value, and every plan record carries it as market_elasticity. A set value changes the request digest.
- Oracle: the command tells the oracle the value and the reaction's share. It then scores a candidate against the median the reaction moves, with the market's answer. It is the ceiling again.
- Cache: a run with a market elasticity other than 0 keeps its cache under cache/market-E/ ([[DEC-50]]). That folder nests under the bias and react folders where those apply.
- Measured: with the reaction on, a market elasticity of 1.0 cuts the default mode's gain to +$43,584 a seed ([[RES-26]], [[RES-27]]).
- Evidence: test_the_market_elasticity_scales_each_days_draw_by_the_medians_level, test_the_grader_scores_a_raise_against_the_median_the_reaction_moves, test_the_oracle_reviewer_is_told_the_market_elasticity_and_the_reaction
- Links: [[DEC-51]], [[DEC-50]], [[RUL-87]], [[RUL-88]], [[RES-26]], [[RES-27]], [[UNK-11]], [[UNK-15]], [[FRK-08]], [[FRK-09]]

### DEC-53 [C] The filings are a named scenario; the churn files what a feed files
- Decided: a Scenario is a named list of filings ([[DAT-03]]). The default is AIR_SHOCKS as it was. --scenario picks another from SCENARIOS, and the upgauge scenario holds an upgauge and a frequency cut ([[SHK-05]], [[SHK-06]]).
- Kinds: a filing adds routes, suspends one, swaps a route's equipment, sets its daily flights or shifts its departures ([[RUL-89]]). An equipment change moves the seats while the flight count stays. A time change moves no seat.
- Churn: --churn files the seed's weekly revisions on top, each under the detect threshold ([[SHK-07]]). A detector that fires on any revision fires on them. The threshold detector does not.
- Reason: a real feed revises every week, and most revisions change no seat count a hotel should act on. The default's two shocks never tested that. The scenario option keeps the default pinned while another story runs.
- Measured: with the churn, seeds 1 to 20 raise the same 173 seat flags as without it ([[RES-28]]).
- Evidence: test_the_churn_files_weekly_revisions_below_the_threshold, test_a_detector_that_fires_on_any_revision_is_caught_by_the_churn, test_a_scenario_and_the_churn_go_to_both_runs
- Links: [[DAT-03]], [[SHK-05]], [[SHK-06]], [[SHK-07]], [[RUL-89]], [[RES-28]], [[DEC-04]], [[UNK-05]]

### DEC-54 [C] A learning agent can feed the fitted demand level into its forecast
- Decided: learn:X --level scales the agent's forecast, the pace baseline included, by exp(intercept) ([[RUL-96]] to [[RUL-98]]). The factor is 1 until the fit has enough observations. Every plan record carries it ([[DAT-21]]).
- Baseline: the estimator's baseline stays unscaled, so the intercept keeps measuring the level against the raw forecast ([[MOD-16]]). The factor therefore does not compound.
- Reason: the intercept absorbed a demand-level error and the agent discarded it ([[DEC-38]]). At a bias of 0.9 the plain learner lost money ([[RES-21]]). The arm asks whether the level fed back recovers that, and what it costs at 1.0.
- Measured: the level is learned by day 10 in every world ([[RES-29]] to [[RES-32]]). The gain at 0.9 does not recover: say-yes-to-everything earns -$15,244 a seed with it.
- Evidence: test_a_level_agent_scales_its_forecast_by_the_fitted_demand_level, test_a_level_scales_one_hotels_pace_baseline_and_expected_demand, test_the_level_factor_is_the_fitted_level_once_the_fit_has_enough_observations
- Links: [[DEC-38]], [[DEC-50]], [[DEC-52]], [[RUL-96]], [[RUL-97]], [[RUL-98]], [[RES-29]], [[RES-30]], [[RES-31]], [[RES-32]], [[UNK-07]], [[UNK-08]]

### DEC-55 [C] A rule-based control is the fair comparison
- Decided: --policy runs a rule-based control beside each arm ([[MOD-25]]). pace raises POLICY_STEP where a stay date runs ahead of pace and lowers it where behind ([[RUL-99]]). Both keep the agent's hold, floor and ceiling.
- Rules: rules keeps the pace steps and adds the retired rules of [[DEC-11]]. It raises on an event or seat-up flag and lowers on a seat-cut flag. A flag whose causes point both ways is left alone.
- Why rules: pace skips every flag that is not a pace flag. It cannot act on the two shocks that carry most of the gain ([[RES-06]]). Against it the agent was beaten on the part of the problem the control was never given.
- Reason: a fixed-rate run never moves a rate, so every gain against it includes what a hotel's own rules earn anyway. The rule stands for what a hotel already does, and the agent's margin over it is the claim worth making.
- Measured: in the default world the never-cut policy earns +$24,780 a seed, and the agent's gain against it is +$8,119 ([[RES-40]]); the rules policy's figures are in [[RES-33]].
- Never-cut: never-cut keeps the raises and never lowers, because every cut loses in this market. The README quotes the lead over it first and the lead over the cutting rules policy after it. All three act only on a flag ([[FRK-11]]).
- Evidence: test_the_rule_raises_ahead_of_pace_and_lowers_behind_by_the_step, test_the_rules_policy_adds_the_event_and_seat_rules_and_skips_a_conflict, test_a_policy_runs_the_rule_based_control_beside_each_arm
- Links: [[MOD-25]], [[RUL-99]], [[RES-33]], [[RES-40]], [[RES-01]], [[RES-06]], [[DEC-11]], [[DEC-13]], [[FRK-11]], [[UNK-08]]

### DEC-59 [C] The README names the competitors' raise as the convention's source of gain
- Decided: the README's first finding says that the convention's share of the gain comes mostly from the competitors' 15% raise, which the rate ratio turns into 23% more of the remaining demand ([[RES-41]]).
- Replaces: a README that presented the convention as a demand shock and let the 96% share stand for the two shocks together ([[RES-06]]).
- Reason: with the raise at zero the mean falls to +$19,480 a seed and the convention plans earn +$538 a seed, so the demand uplift alone pays little. A reader was told the share and not its mechanism.
- Measured: at fixed rates the two downtown hotels sell out 79 of 160 convention nights with the raise and 10 without it ([[RES-41]]).
- Evidence: test_the_raise_at_zero_keeps_the_uplift_and_puts_the_event_back
- Links: [[RES-41]], [[RES-06]], [[SHK-01]], [[RUL-21]], [[MOD-29]], [[FRK-08]]

### DEC-69 [C] The market's events and rate cuts live in the customer file
- Decided: a customer file holds its events, each with the hotels it lifts and by how much, and its competitor rate cuts, each with the hotel it hits ([[DAT-05]], [[DAT-27]]). shocks.py keeps the lookups and takes the customer.
- Replaces: EVENTS and RATE_CUTS as constants in shocks.py, which named the demo market's hotel keys and competitors.
- Reason: a second market could not run while the simulator's shocks named the demo's hotels. The demo file carries the same values, so the seed-7 checksum holds, and the agent's modules do not change.
- Second market: customers/harbour.toml, three hotels of other shapes with its own regatta and cut, runs with --customer alone ([[RES-44]]). kg_check reads the demo file's calendar for the SHK nodes ([[MOD-15]]).
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_the_lookups_read_the_customers_own_calendar, test_the_second_market_runs_from_its_file_with_no_change_to_the_agent, test_the_agent_reads_only_through_the_interfaces
- Links: [[DEC-41]], [[DAT-05]], [[DAT-27]], [[MOD-03]], [[MOD-20]], [[SHK-01]], [[SHK-03]], [[RES-44]]

## Engineering

### DEC-23 [C] The cache key is seed, day and hotel, with the request's digest
- Decided: the answer to one hotel's queue on one day is saved at cache/seed<seed>/day<DDD>_<hotel key>.json. The file records the sha256 of the request's sorted-keys JSON ([[DAT-17]]), and a rerun reads the cache first.
- Detail: a file whose digest does not match the request, or whose prompt_digest differs from the running prompt, raises StaleCache. A record with no prompt_digest is current. A replay never calls the model.
- Model and market: another model ([[RUL-46]]) adds -<model> to the folder, and each record names it. Another market puts its folders under cache/<name>/, so the demo keeps cache/seed<seed>/ and [[DAT-29]] replays unchanged.
- Replaces: nothing built.
- Reason: each hotel's queue costs one model call a day, paid once per seed. A changed rule or constant changes the request, so it cannot reuse a stale answer silently.
- Commit: abef71f
- Evidence: test_ask_calls_the_model_once_and_then_reads_the_cache, test_a_cache_written_for_another_request_is_refused, test_a_cache_answered_under_another_prompt_is_refused, test_a_replay_never_calls_the_model
- Links: [[MOD-09]], [[DAT-17]], [[DEC-25]], [[FRK-04]]

### DEC-24 [H] Template answers were cached like the model's
- Decided: the template's answers were written to the same cache files as the model's, marked "source": "template". A client replaced a template-sourced file with the model's answer.
- Replaced by: [[DEC-25]]
- Reason it went: a live run after a template run stopped with StaleCache when a model decision changed a later day's request. --template and --seeds, which pass no client, reused the model's answers, so a sweep could mix two policies.
- Commit: abef71f
- Links: [[MOD-09]]

### DEC-25 [C] Only the model's answers are cached
- Decided: without a client the template answers and nothing is written. With a client the model's cached answer is read first. A cache file whose source is not "model" is ignored and overwritten.
- Detail: a replay reads the model's cache when a client is given and uses the template otherwise.
- Uncached: a client whose cached flag is false, such as the oracle grader ([[DEC-47]]), joins the template as an uncached answer. Nothing is written or read; its decisions record the client's name as their source.
- Replaces: [[DEC-24]]
- Reason: the template is a fixed function of the request, so it needs no cache. --template and --seeds always use it, and a live run can follow a template run. Template reasons now keep an event's name capitalised, the only output change.
- Commit: abef71f
- Evidence: test_the_template_never_reads_the_models_cache, test_replaying_day_20_makes_no_model_call_and_prints_the_same_entries, test_an_oracle_run_writes_nothing_to_the_cache
- Links: [[MOD-09]], [[DAT-17]], [[MOD-12]]

### DEC-27 [H] The modules lived flat at the repository root
- Decided: the eight modules and run.py sat next to each other at the root. A pytest.ini put the root on the path, and requirements.txt listed the dependencies.
- Replaced by: [[DEC-28]]
- Reason it went: it read like a folder of scripts. The tests ran against whatever was in the working directory rather than an installed package.
- Commit: 15e0215
- Links: [[MOD-12]]

### DEC-28 [C] The code is the package src/hotel_market, with pyproject.toml and a command
- Decided: the code is a src layout with absolute imports hotel_market.<module>. The old run.py became cli.py behind the hotel-market command and python -m hotel_market.
- Metadata: pyproject.toml holds the metadata, the dependencies with tested lower bounds, the dev extras and the pytest and ruff settings.
- Replaces: [[DEC-27]]
- Reason: a reader of production code expects this layout.
- Measured: the suite ran against the installed package on numpy 1.26 and pandas 2.2 ([[RES-15]]). The image built and passed the suite on Python 3.11, 3.12 and 3.14 ([[RES-20]]). A seed-7 run in it reproduced decisions.jsonl byte for byte.
- Commit: 15e0215
- Evidence: test_the_replay_command_prints_day_20s_queue, test_python_m_hotel_market_runs_the_command, test_the_image_takes_its_python_version_as_a_build_argument
- Links: [[MOD-12]], [[MOD-14]], [[RES-15]], [[RES-20]]

### DEC-29 [H] A hosted workflow ran the tests on every push
- Decided: a workflow file ran the tests on three Python versions and the linter on every push.
- Replaced by: [[DEC-30]]
- Reason it went: on the private repository the first run sat queued for 15 minutes without a runner and was cancelled. The owner then chose not to have hosted CI.
- Commit: 15e0215
- Links: [[MOD-15]]

### DEC-30 [H] No hosted CI; the checks run locally through make and pytest
- Decided: the workflow file was gone. The tests, ruff and the knowledge-graph check ran locally with python -m pytest and the two ruff commands. The Makefile wrapped them.
- Replaced by: [[DEC-70]]
- Reason it went: the repository is shown to other people, and a check that runs on every push says more than one that runs on one laptop. The local commands stay as they were.
- Commit: 5cef53e
- Links: [[MOD-15]], [[DEC-29]]

### DEC-70 [C] A hosted workflow runs the three checks on every push to main
- Decided: .github/workflows/test.yml runs on a push or a pull request to main, on Python 3.12 and ubuntu-latest. It installs the package with pip and runs make lint, make test and python kg_check.py.
- Detail: the workflow carries no API key and fetches nothing beyond pip, so the tests run offline as they do locally. It fetches the whole history, because kg_check.py looks each Commit line up in it.
- Slow tests: the ten slow tests stay out of the workflow, as plain pytest skips them. pytest --slow (make test-all) still runs them locally.
- Replaces: [[DEC-30]]; the first workflow, [[DEC-29]], was dropped after a queued run on a private repository.
- Reason: the three checks are the same on a runner and on a laptop, and a badge on the README shows that they pass.
- Evidence: test_the_workflow_runs_the_checks_on_push_to_main
- Links: [[MOD-15]], [[DEC-29]], [[DEC-30]], [[DEC-33]]

### DEC-31 [H] One agent.py held the planning, the model call and the daily loop
- Decided: candidates, estimates, the request, the cache, the template, the client and the loop were one module of 539 lines.
- Replaced by: [[DEC-32]]
- Reason it went: three jobs sat in one file, and the dense parts were hard to read. Four parallel dicts fed the estimate, a string-keyed dict held a flag's numbers, and request literals were nested.
- Commit: abef71f
- Links: [[MOD-10]]

### DEC-32 [C] The agent is plan.py, model.py and agent.py, with text.py for shared wording
- Decided: the module plan.py builds candidates, estimates and plans, and model.py holds the model call, its cache and the template. The module agent.py runs the daily loop and gives the advice, and text.py holds the shared wording.
- Replaces: [[DEC-31]]
- Reason: each module has one job. Named records (StayDate, FlagNumbers, Comparison, SeedResult) replace dicts and tuples, and the command line has one function per mode. The tests follow the split.
- Measured: the split preserved behaviour. Two seeds' decisions.jsonl, the printed summaries, both replays, the sweep and the diagnostics matched the previous output byte for byte.
- Commit: abef71f
- Evidence: test_the_agent_reads_only_through_the_interfaces, test_estimate_is_expected_contribution_on_the_unsold_rooms
- Links: [[MOD-08]], [[MOD-09]], [[MOD-10]], [[MOD-11]]

### DEC-33 [C] ruff formats the code at 100 columns, and lint checks the format
- Decided: ruff format owns the layout, and make lint runs ruff check . and ruff format --check .. The route table in schedule.py keeps one route per line under a bare fmt: off marker.
- Note: ruff ignores the marker when text follows it on the same line.
- Replaces: hand formatting at up to 120 columns.
- Reason: one layout leaves no arguments about style. The only hand work left was 14 lines the formatter could not shorten.
- Commit: 15e0215
- Evidence: test_the_formatter_runs_at_100_columns
- Links: [[MOD-15]], [[MOD-01]]

### DEC-34 [C] The answer schema lists the request's entry ids and options as enums
- Decided: schema_for(request) builds the answer schema as an object with one required decision per entry id. Each is limited to that entry's plan and "hold". An answer cannot leave an entry out or borrow a plan.
- Replaces: a fixed schema that typed id and choice as free strings.
- Reason: with free strings a schema-valid answer such as "Hold" failed the check, and the run aborted with nothing cached. With enums the API cannot return a choice the code would reject. The pairing check stays as the backstop.
- Commit: abef71f
- Evidence: test_the_schema_limits_ids_and_choices_to_the_requests_options
- Links: [[MOD-09]], [[DAT-16]], [[UNK-02]], [[RES-09]]

### DEC-40 [C] The agent reads only through four interfaces
- Decided: sources.py ([[MOD-17]]) defines Bookings, RateShops, Schedules and Events ([[DAT-25]]). Every method takes the day it is asked on and returns only what was known then.
- Boundary: the modules detect, forecast, estimate, plan, model and agent read data through them and import none of the simulator's modules. A test reads their imports and fails if one does.
- Detail: the agent's own demand model is forecast.py ([[MOD-18]]), held equal to demand.py by a test. The simulator implements the four in simulated.py ([[MOD-19]]). ORACLE_ELASTICITY ([[RUL-56]]) names the default elasticity an oracle.
- Replaces: [[DEC-26]], and the agent's direct reads of the simulator: detect_numbers(day, books), estimate_elasticity(books, ...) and the peak night in demand.py.
- Reason: a repository that can be pointed at a hotel's own data needs one place where the data comes in. With the line drawn, what the agent may know is the list of methods in sources.py.
- Measured: the default run is unchanged ([[RES-02]]). Seed 7's decisions file is byte for byte the one before the boundary, and the estimator's inputs are bitwise identical.
- Commit: 35967c8
- Evidence: test_the_agent_reads_only_through_the_interfaces, test_the_forecast_is_the_simulators_demand_for_the_demo_market, test_the_default_mode_gives_the_pinned_seed_7_figure

### DEC-41 [C] Everything specific to the market is a customer file
- Decided: customers/demo.toml holds the demo market, which [[MOD-20]] reads into a Customer ([[DAT-27]]).
- Holds: the hotels, their curves and comp sets ([[DAT-04]]), the cost share, rate limits, detect thresholds and hold period. It also holds the minimum, the market elasticity and the target ([[RUL-57]] to [[RUL-69]], [[RUL-124]]).
- Command: hotel-market --customer FILE names the file, and --target overrides its target. The demo file is the default wherever none is given. A revenue run keeps its own cache folder ([[DAT-17]]).
- Replaces: the market constants in world.py and the thresholds in detect.py and plan.py ([[RUL-14]] to [[RUL-18]], [[RUL-23]] to [[RUL-30]], [[RUL-40]]). It closes [[FRK-01]].
- Reason: with the boundary drawn ([[DEC-40]]), the market's numbers were the last demo facts written into code. In a file they are what a hotel would hand over, and the simulator reads it too. The simulator's constants stay in code.
- Measured: the revenue target earns +$211,445 of room revenue a seed and only +$461 of contribution ([[RES-07]]). The two targets pull the rates in opposite directions, and the default run is unchanged ([[RES-02]]).
- Commit: 9d74c0d
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_the_revenue_target_scores_candidates_on_the_rate_alone, test_the_command_takes_a_customer_file_and_a_target

### DEC-42 [C] Stored tables the agent can run against a day at a time
- Decided: sql/schema.sql defines eight tables ([[DAT-28]]): four feeds and three agent outputs keyed by as_of_day, and the outcomes keyed by the decision's day. Its head lists the statements a cloud warehouse would change.
- Stored: stored.py ([[MOD-21]]) implements the four interfaces over the tables and writes a day's rows. It deletes the day's rows first, so running a day twice leaves the tables unchanged. The simulated sources ([[MOD-19]]) are unchanged.
- Daily run: the run-day command plays the simulator to day N with the stored rate changes and writes the day's feeds. A fresh agent resumes the stored hold, advice and changes, decides the day from the tables alone and writes its output.
- Replay: hotel-market replay --as-of N rebuilds the day's plans from the tables alone and takes the actions the stored decisions record. It checks the rebuilt plans against the stored ones, and --from runs a range of days in one pass.
- Reason: a real hotel's data arrives a day at a time and lives in tables. This is therefore the shape a deployment would take, with the simulator standing in for the feeds. It also checks the boundary ([[DEC-40]]).
- Measured: a 60-day run through the tables writes the in-memory run's decisions file byte for byte, in about 6 seconds ([[RES-14]]).
- Commit: 6311cb6
- Evidence: test_a_60_day_run_through_the_tables_gives_the_same_decisions_file, test_running_a_day_twice_leaves_the_tables_unchanged, test_replaying_a_past_day_reproduces_its_plans_exactly

### DEC-47 [C] The oracle reviewer is a grader outside the agent's path
- Decided: bench.py ([[MOD-23]]) holds an oracle reviewer. It re-scores each queued plan and hold at ORACLE_ELASTICITY ([[RUL-56]]). It declines the plan when hold scores at least as well.
- Client: it stands in as the client the agent asks ([[MOD-09]]) and reads the day's entries from agent.today. Its decisions then drive a run of their own. It also labels the entries of any other run after the fact.
- Boundary: it imports from plan.py and agent.py, and nothing in the agent's path imports it. tests/test_sources.py checks its imports with the agent's modules. Its answers are never cached and record source oracle ([[DEC-25]]).
- Reason: the oracle uses the simulator's elasticity, which the agent may not see. A grader outside the agent's path cannot leak it. It is the ceiling for a reviewer: it cannot pick a better candidate, and a seed's draw can beat it.
- Measured: in the default mode the oracle says yes to every queued plan. That mode therefore cannot separate reviewers, and the mismatched modes can ([[RES-03]]).
- Commit: 03506d4
- Evidence: test_the_oracle_reviewer_accepts_every_queued_plan_in_true_mode, test_the_oracle_declines_where_hold_scores_at_least_as_well, test_the_agent_reads_only_through_the_interfaces
- Links: [[MOD-23]], [[DEC-01]], [[DEC-02]], [[DEC-40]], [[MEA-06]]

### DEC-48 [C] The bench is one sweep with a reviewer per arm
- Decided: sweep() takes reviewers ([[DAT-32]]) as well as modes. An arm is one mode and one reviewer over the seeds; the fixed-rate run is made once per seed. The bench command runs the template, the oracle and each model in every mode.
- Detail: each arm keeps its own cache folder ([[DEC-23]]), so a rerun reads the cache. The report merges a digest's call records into one, with the outcome from the last. It counts one only when its cache file is present or it failed.
- Replaces: nothing built.
- Reason: one sweep keeps one definition of the change against the fixed-rate run. The bench's template row is then the --seeds sweep's figure. A second loop would drift from it.
- Modes: the default modes are BENCH_MODES ([[RUL-81]]), two mismatched and the true one. The ranking pools the mismatched modes, since the true mode cannot separate reviewers ([[DEC-47]]).
- Commit: e15c32d
- Evidence: test_a_sweep_with_reviewers_keeps_each_arms_entries_calls_and_counts, test_the_bench_command_prints_its_tables, test_a_duplicate_call_record_is_counted_once
- Links: [[MOD-12]], [[MOD-23]], [[DAT-19]], [[DAT-24]], [[DAT-32]], [[DEC-47]]

### DEC-56 [C] The band verdict is a display field; small band-end gains read to the dollar
- Decided: each candidate but hold in a cautious request carries band_verdict ([[DAT-16]], [[MOD-11]]). An example is "beats holding at both ends of the band". A gain over hold at an end of the band under $10 reads to the dollar.
- Replaces: the ends read to the nearest $10 as every estimate does ([[DEC-44]]). A gain of $3 the rule had passed therefore read "the same as holding". The model inferred the rule's result from the rounded gains.
- Reason: on seed 7, day 29, Opus, Sonnet and Haiku each declined the same airport raise ([[RES-35]]). Each read "the same as holding" at the high end as a failed rule. That was the natural reading of what code wrote.
- Digest: the cautious requests change, so their digests and caches change ([[DEC-23]]). The recorded seed-7 run ([[DAT-29]]) is the default mode, which has no band, and is unaffected.
- Prompt: the system prompt ([[RUL-47]]) tells the model to copy the verdict as written.
- Measured: the three learn:1.0 cautious arms reran on seeds 1 to 20 and declined nothing. Each ties with the template at +$25,076 a seed ([[RES-35]]). The 852 calls cost $10.48.
- Evidence: test_a_band_end_gain_under_ten_dollars_reads_to_the_dollar, test_the_band_verdict_states_the_cautious_rules_result, test_the_three_values_reach_the_model_request, test_the_recorded_live_run_replays_without_a_key_and_gives_19796
- Links: [[DEC-44]], [[DEC-39]], [[DEC-23]], [[DAT-16]], [[DAT-29]], [[MOD-09]], [[MOD-11]], [[RUL-47]], [[RES-35]], [[UNK-01]]

### DEC-57 [C] A read-only demo page over a file code writes
- Decided: the demo page ([[MOD-27]]) is a Streamlit app, the optional extra demo. It reads one DuckDB file ([[DAT-33]]) that hotel-market demo-data writes ([[MOD-26]]) and computes nothing.
- Reasons: the file's reasons come from the recorded live run of seed 7 ([[DAT-29]]) where it covers the request. Elsewhere the template answers and the command warns, so any market or seed builds with no API key. The run table says which.
- Scorecard: the file holds the nights already stayed as of each day, stay dates 0 to the day before, and the outcome once every stay date is complete, which is the seed-7 table in docs/results.md ([[RES-02]], [[DEC-58]]).
- Guard: a test parses the page and fails on an import from the package, an arithmetic operator or an aggregate call. Every figure the page shows is a row code wrote ([[RUL-01]]).
- Replaces: CLAUDE.md's rule 5 allowed no web UI. It now allows this page, and nothing else.
- Evidence: test_the_page_imports_nothing_from_the_package_or_the_simulator, test_the_page_does_no_arithmetic_on_a_figure, test_the_reasons_come_from_the_recorded_live_run
- Links: [[MOD-26]], [[MOD-27]], [[DAT-33]], [[DAT-28]], [[DAT-29]], [[DEC-42]], [[DEC-58]], [[RUL-01]], [[RES-02]]

### DEC-58 [C] The demo page fits one window, and every date is a calendar date
- Decided: the page fits 1440 by 900 pixels with nothing cut off: the title, the news, both charts, the queue and the scorecard. scripts/demo_screenshots.py ([[MOD-28]]) measures every hotel on seven days and fails when a page is taller.
- Dates: every stay date reads as a calendar date with its day of the week and the day number in brackets, on the axes and in the text ([[DAT-33]]). The model's recorded reasons keep their day numbers, so the brackets tie the two together.
- Plan: on the day a plan is accepted, the rate chart draws the new rate as a dashed line beside the current one. A held day of the week keeps the current rate on that line.
- Held: the held flags are open by default. Each shows its stay dates, its cause, the best alternative and how far it fell short of holding, or of the minimum when its plan beats holding ([[RUL-67]]).
- Text: the page escapes the markdown marks in every reason and plan, so a pair of dollar amounts is not a formula and a model's text cannot draw a link. A tile writes a change that rounds to nothing as "0", with no arrow.
- Layout: the charts sit side by side, the queue beside the scorecard, and the toolbar is hidden. The end-of-run result is behind a checkbox, off by default. The queue's text is a size smaller, so a day with three plans fits.
- Evidence: test_every_checked_page_fits_the_window_and_six_are_saved, test_every_date_reads_as_a_calendar_date_with_its_day_number_in_brackets, test_a_held_flag_names_the_best_alternative_and_how_far_it_fell_short
- Links: [[DEC-57]], [[MOD-26]], [[MOD-27]], [[MOD-28]], [[DAT-33]], [[RUL-67]], [[RUL-109]]

### DEC-60 [C] Every printed mean carries its spread
- Decided: the sweep, arm, bench and control tables print the standard deviation and the standard error beside every mean ([[MOD-12]]). They print a two-sided sign test's p beside every count of seeds ahead. docs/results.md carries them.
- Replaces: means and counts with no spread. Under them +$1,913 a seed at a demand bias of 0.9, ahead in 12 of 20, read as a gain.
- Reason: a reader has to tell a result from a coin flip. 12 of 20 has p 0.50 ([[RES-21]]), 13 of 20 has p 0.26, and 17 of 20 has p 0.0026 ([[RES-40]]).
- Measured: the default lead over the never-cut control, +$8,119 a seed, has a standard deviation of $6,620 and a standard error of $1,480 ([[RES-40]]).
- Evidence: test_the_seeds_command_prints_each_seed_and_the_mean_and_range, test_the_bench_command_prints_its_tables
- Links: [[MOD-12]], [[DAT-24]], [[RES-01]], [[RES-21]], [[RES-40]]

### DEC-61 [C] The sources hold only what the day knows, on both routes
- Decided: each simulated source copies the log through its day, the seats filed and the events known by then, and holds no Books or Scenario ([[MOD-19]]). The stored sources take the day and refuse a later one ([[MOD-21]]).
- Routes: run-day and replay make both kinds for the day they decide ([[MOD-12]]). Limited, the guard, lives at the boundary ([[MOD-17]]) and both mix it in.
- Replaces: simulated sources that held the Books and the Scenario, through which a decider could read every future draw, the live rooms and the filings still to come, and stored sources with no guard at all.
- Reason: [[RUL-03]] was kept on the agent side by discipline alone. Now the objects a decider is handed cannot reach tomorrow on either route, which the live-feed version will build on.
- Measured: the seed-7 checksum and the 20-seed mean of +$32,899 are unchanged ([[RES-01]], [[RES-02]]).
- Evidence: test_a_decider_cannot_reach_a_future_draw_the_live_rooms_or_the_scenarios_shocks, test_the_stored_sources_refuse_a_later_day_and_the_daily_commands_make_them_for_the_day
- Links: [[MOD-17]], [[MOD-19]], [[MOD-21]], [[DAT-25]], [[DEC-40]], [[DEC-42]], [[FRK-13]], [[RUL-03]]
