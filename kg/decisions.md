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
- Decided: the simulator loads each stay date in the window with a seeded Poisson draw before day 0's bookings. The mean is normal_demand x curve(days out + 1), capped at the rooms, at the start rate.
- Replaces: nothing built. Empty books would have flagged every early stay date as behind pace and left tonight's hotel empty.
- Reason: the first 90 stay dates are already part way up the booking curve when the run starts.
- Measured: tonight is 1 - 0.3 / 7 of the way up the curve. The convention hotel therefore starts with about 273 of its 285 expected rooms on the books.
- Commit: 054edd6
- Evidence: test_preload_mean_is_normal_demand_x_curve_of_days_out_plus_1, test_day_0_starts_with_the_bookings_made_before_the_run
- Links: [[MOD-06]], [[DAT-07]], [[RUL-68]], [[CON-01]]

### DEC-04 [C] seat_revision is the seat trigger; seat_change is carried for the text
- Decided: the detector flags a stay date when its arriving seats move 5% or more since the day before ([[RUL-64]]). The change against the no-shock baseline is shown but never flags.
- Replaces: nothing built; flagging on seat_change was the first idea.
- Reason: seat_change stays at +17% from day 20 on. Flagging on it would re-flag stay dates 50 to 149 every day. seat_revision is zero except on the two filing days.
- Measured: after the day-40 cut, seats on days 70 to 90 stay 240 a day above the baseline. They are 480 a day (about 10%) below the day before.
- Commit: abef71f
- Evidence: test_shock_causes_appear_only_on_the_days_shocks_become_known, test_known_seat_revision_matches_the_schedule
- Links: [[SHK-02]], [[SHK-04]], [[DAT-02]], [[MOD-07]]

### DEC-05 [C] The booking loop plays out to day 149 with rates frozen from day 60
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

### DEC-07 [C] A pace flag needs a gap beyond both 10% of rooms and 3 standard deviations
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

### DEC-09 [C] The peak night is computed from expected demand as of the day the event becomes known
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

### DEC-12 [C] Contribution with a room cost is the target, and the start rate is best on ordinary nights
- Decided: each occupied room costs one third of the hotel's start rate to service ([[RUL-61]]). Contribution is room revenue minus that cost for every room sold, and the agent scores candidates on it.
- Replaces: [[DEC-11]], and revenue as the implicit target
- Reason: revenue rewards selling every room at any price. With ELASTICITY 1.5 the contribution-best rate on a night that will not sell out is 3 x cost. That is the start rate, so only a night that may sell out can pay for a raise.
- Measured: with fixed rates, seed 7 holds occupancy at 75.7% to 83.7% by hotel over stay dates 0 to 59 ([[RES-02]]).
- Commit: 9d74c0d
- Evidence: test_each_occupied_room_costs_a_third_of_the_start_rate, test_contribution_is_revenue_minus_the_cost_of_every_room_sold, test_on_nights_that_will_not_sell_out_the_start_rate_is_already_best
- Links: [[RUL-61]], [[RUL-21]], [[FRK-01]], [[CON-07]]

### DEC-13 [C] Every flag gets scored candidates, with hold as the default
- Decided: every flag gets hold, raise 5%, raise 10% and lower 5% ([[RUL-43]]), each clamped to the floor and ceiling. A comp median drop adds lower halfway to the new median ([[RUL-42]]). Code scores each on the rooms still unsold.
- Detail: when nothing beats hold the entry is recorded as a hold and stays out of the queue. The model may decline the best candidate, which also records a hold.
- Replaces: [[DEC-11]]
- Reason: the same candidates for every cause keep the agent from reacting to a label, because the estimate decides. Hold wins a tie, so the agent never changes a rate for nothing.
- Commit: abef71f
- Evidence: test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits, test_a_comp_median_drop_adds_lower_halfway_to_the_new_median, test_a_model_that_declines_changes_no_rate
- Links: [[MOD-08]], [[DAT-11]], [[DAT-12]], [[CON-08]]

### DEC-14 [C] The airport hotel's base occupancy is 0.85; the other three are 0.75
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

### DEC-16 [C] Flat rates: starting and competitor rates do not follow the day of the week
- Decided: every hotel's starting rate is its table start rate on every stay date. Competitor rates are base rate x noise with the shocks applied. Demand still follows the day of the week ([[DAT-04]]).
- Replaces: [[DEC-15]]
- Reason: with a fixed room cost the best rate on an ordinary night is the same every day. Flat starting rates are therefore right on those nights, and the agent's gain comes from reacting to the market.
- Measured: on seed 7 the gain fell from +$26,420 to +$22,894 with this change, the per-weekday plan and the minimum ([[RES-11]]). The smaller number is the true one.
- Commit: bd556fb
- Evidence: test_competitor_rates_are_base_rate_x_noise_with_no_weekly_pattern, test_hotel_starts_level_with_its_comp_median
- Links: [[MOD-05]], [[DEC-12]], [[RES-11]]

### DEC-17 [C] A plan must be worth at least $250 over holding to enter the queue
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

### DEC-19 [C] The best candidate is chosen separately for each day of the week within a flag
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

### DEC-21 [C] Estimated bookings are the exact expectation E[min(N, unsold)] for a Poisson N
- Decided: expected_bookings(mean, unsold) sums the Poisson probabilities below the unsold count and gives the rest to a sell-out. That is the booking noise the simulator draws.
- Replaces: [[DEC-20]]
- Reason: a night expected 97% full still sells out fairly often, so a small raise there pays.
- Measured: the 20-seed mean went from +$27,350 to +$32,899 ([[RES-12]], [[RES-01]]). The agent was ahead in 20 of 20 seeds both before and after.
- Commit: abef71f
- Evidence: test_expected_bookings_is_the_mean_of_a_poisson_count_that_stops_at_the_unsold_rooms, test_expected_bookings_matches_the_simulators_daily_draws, test_a_night_expected_97_percent_full_raises_where_a_cap_on_demand_would_hold
- Links: [[MOD-08]], [[DAT-10]], [[CON-09]]

### DEC-22 [C] One random number per booking draw, fixed by the seed before the run
- Decided: every draw of the run has its own uniform random number, drawn in one go from the seed. The function poisson_draw turns it into a count by the Poisson quantile. A bigger mean never gives a smaller count on the same number.
- Replaces: nothing built; a shared random stream was the alternative.
- Reason: a rate change on one stay date leaves every other draw as it was. The fixed-rate and agent runs therefore differ only where the agent acted, and the changed-pairs comparison is exact.
- Measured: on seed 7 the 93 hotel-nights the agent changed carry the whole +$28,818 ([[RES-02]]). The other 507 book identically in both runs.
- Commit: 054edd6
- Evidence: test_a_rate_change_applies_from_the_next_day_and_touches_no_other_stay_date, test_every_other_pair_books_the_same_in_both_runs, test_a_bigger_mean_never_draws_fewer_rooms_on_the_same_luck
- Links: [[MOD-06]], [[DAT-07]], [[RUL-02]], [[RUL-22]]

### DEC-26 [H] AGENT_ELASTICITY is the agent's own constant and never imports the simulator's
- Decided: plan.py defined AGENT_ELASTICITY = 1.5 ([[RUL-39]]). A test read the module's imports to make sure ELASTICITY ([[RUL-21]]) was not among them.
- Replaced by: [[DEC-40]], which draws the line around the whole agent and names the value an oracle ([[RUL-56]]).
- Reason it went: one constant kept apart was the right idea on too small a scale. The agent still read the simulator's demand, draws and shocks directly.
- Commit: abef71f
- Links: [[RUL-39]], [[RUL-21]], [[FRK-02]], [[DEC-38]]

### DEC-35 [C] Every number is synthetic, and the schedule's columns follow a published data dictionary
- Decided: the city, airports, airlines, flights, hotels, competitors and bookings are invented. The schedule table's column names follow Cirium's published schedule data dictionary. The code therefore reads data shaped like a real feed.
- Policy: the repository holds no Cirium data and has no affiliation with Cirium. It names no real hotel brand or employer anywhere.
- Replaces: a schedule whose IS_WETLEASE was set wherever the carriers differed. A differing operating carrier is capacity purchase, so the flag is now False on every row. The carrier pair expresses the arrangement ([[MOD-01]]).
- Reason: the project tests whether the loop works and not a market. Data shaped like a real feed makes the counting traps real traps without any real rows.
- Commit: e134523
- Kind: policy
- Evidence: review
- Links: [[DAT-01]], [[MOD-01]], [[RUL-06]]

### DEC-36 [C] The summary reports what the run produces; the rules are not tuned to force a gain
- Decided: the summary reports the comparison of the two runs as it comes out. It shows every rate-changing decision and the plans that lost money. The README states that the agent shares the simulator's demand formula.
- Replaces: nothing.
- Reason: a tuned gain would say nothing about the loop.
- Measured: reported this way, the 20-seed mean is +$32,899 ([[RES-01]]). The agent is ahead in every seed, and revenue is down in every seed.
- Commit: 12e000b
- Kind: policy
- Evidence: review
- Links: [[MOD-12]], [[DAT-20]], [[RES-01]], [[RES-02]]

### DEC-37 [C] Competitor noise is drawn once per competitor and stay date, so a comp median moves only on a shock
- Decided: the rate-shop noise is one array per seed with shape (hotels, competitors, stay dates). It is drawn before the run on its own stream ([[RUL-20]]). The shop day only applies the shocks known by then.
- Replaces: nothing built; fresh noise on every shop day was the alternative.
- Reason: fresh noise would move every comp median every day and raise comp-median flags from nothing. Drawn once, only the convention nights move on day 10 and the cut nights on day 30.
- Commit: bd556fb
- Evidence: test_comp_median_moves_only_when_a_shock_becomes_known
- Links: [[MOD-05]], [[DAT-06]], [[CON-04]]

### DEC-38 [C] The agent can learn its elasticity from the bookings; the default stays the simulator's value
- Decided: --elasticity picks where the agent's elasticity comes from ([[RUL-49]], [[DAT-22]]). The default, true, is the oracle value ([[RUL-56]]).
- Modes: a fixed:X mode uses X for the whole run. A learn:X mode starts from the prior X and re-estimates every hotel every day ([[MOD-16]]). Every entry, request and log line records the elasticity, its error and its mode ([[DAT-21]]).
- Estimator: a Poisson regression of the bookings on log(rate / median). The offset is the forecast's log baseline with the market term ([[DEC-52]]). An intercept absorbs the level, and [[RUL-50]] to [[RUL-52]] hold and clamp the slope.
- Observations: a stay date's observations stop on the day it sells out. The day-0 preload is never an observation, because the simulator draws it with no price response.
- Reason: with the agent's elasticity equal to the simulator's, the agent was never wrong about price response. The question was what being wrong costs and how much learning wins back ([[FRK-02]], [[UNK-07]]).
- Measured: a wrong value costs about three quarters of the gain ([[RES-03]]). Learning wins back about a quarter of the loss ([[RES-04]], [[RES-10]]).
- Commit: abef71f
- Evidence: test_the_day_59_estimate_recovers_the_simulators_elasticity, test_the_default_mode_still_gives_28818_on_seed_7, test_each_mode_records_the_elasticity_its_plans_assume

### DEC-39 [C] The cautious rule: a learning agent changes a rate only where the change beats holding across its band
- Decided: in learn mode, --cautious scores every candidate at three elasticities. They are the estimate and the estimate [[RUL-54]] standard error lower and higher, clamped to [[RUL-51]] and [[RUL-52]].
- Rule: a candidate replaces hold only if it is ahead of hold at all three. The best such candidate wins; otherwise the day of the week holds ([[CON-11]], [[MOD-08]]).
- Records: each plan record, the request and the log line store all three values and the rejected candidates ([[DAT-11]], [[DAT-16]], [[DAT-18]]). Without the option nothing changes.
- Replaces: nothing built. It answers the question [[DEC-38]] left open, whether an agent that knows how little it knows keeps more.
- Reason: the plain learning agent acted on estimates it should not have trusted ([[RES-04]]). It made about twice the true arm's rate changes, and its estimates were many times what they realised.
- Measured: from a prior of 1.0 the rule keeps 76% of the true arm's gain, against 43% without it ([[RES-05]]). From 2.0 it keeps 54% against 49%. The first build is [[RES-13]] ([[DEC-43]]).
- Commit: abef71f
- Evidence: test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held, test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side, test_a_cautious_agent_records_the_band_and_what_it_rejected

### DEC-43 [C] One minimum rule: the cautious rule tests the band alone, and the minimum applies to the plan as in every mode
- Decided: a cautious candidate replaces hold when it beats hold at the estimate and at both band ends ([[CON-11]]). The minimum value at stake ([[RUL-67]]) applies to the whole plan through Entry.queued, as in every mode.
- Detail: the rejected count now includes every candidate ahead of hold at the estimate, not only those worth $250. The default run and the plain learn runs are unchanged.
- Replaces: the minimum per day of the week that [[DEC-39]] first added. Under it a day of the week worth less than $250 on its own held.
- Reason: two minimum rules were one too many, and the second did almost nothing.
- Measured: the band alone and the first rule differ by $8 and $16 a seed ([[RES-05]], [[RES-13]]). The shares of the true arm's gain stay 76% and 54%.
- Commit: abef71f
- Evidence: test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held, test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue, test_a_cautious_agent_records_the_band_and_what_it_rejected
- Links: [[DEC-39]], [[CON-11]], [[RUL-67]], [[MOD-08]], [[FRK-05]], [[RES-05]], [[RES-13]]

### DEC-44 [C] The request carries a display string in place of every figure, with its direction in words and each range as one phrase, and the prompt tells the model to copy the phrases whole and state only what the entry shows
- Decided: every figure in the request ([[DAT-16]], built by [[MOD-09]]) is a display string written by code ([[MOD-11]]). The raw number stays in the log line and the stored tables ([[DAT-13]], [[DAT-18]]).
- Phrases: a signed quantity reads as a phrase with its direction in words and no sign. A range reads as one phrase, and as the single value when both ends read the same.
- Format: a rate, a median, a floor, a ceiling or a cost reads to the dollar. An estimate reads to the nearest $10, rooms to the room, and an elasticity with up to two decimals.
- Prompt: the system prompt ([[RUL-47]]) tells the model to write as "we" and to copy the phrases whole. It states only what the entry shows and writes event names in lower case. It may write "more than holding" once for several gains.
- Replaces: bare numbers, which the model rounded and reformatted as it pleased, and three later formats ([[RES-08]]). It also replaced the mode name "true" ([[RUL-75]]) and the prompt line "use only numbers that appear in the entry".
- Reason: the model copied figures only when the request held them as finished phrases. Each format was tried in a live run of seed 7 ([[RES-08]], [[UNK-01]]).
- Measured: the fourth run copied every phrase and every range whole in 21,148 input tokens ([[RES-08]], [[DAT-29]]). No figure fell outside its request, and no sentence lacked a request figure.
- Evidence: test_every_figure_in_the_request_is_a_display_string, test_a_range_is_one_phrase_and_the_single_value_when_both_ends_read_the_same, test_the_recorded_live_run_of_seed_7_passes_the_audit

### DEC-45 [T] Each model request carries the hotel's past decisions and their outcomes
- Decided: the request for a hotel's queue will carry the hotel's earlier decisions and what each earned. The model can then weigh a plan against what the last ones did.
- Replaces: nothing built; today the model sees only the day's entries ([[DAT-16]]).
- Reason: a revenue manager judges a recommendation against the last ones, and the model cannot.
- Needs: a record of each accepted plan's realised gain on its stay dates. The changed-pairs comparison already computes that per run ([[RES-02]]). The request and the cache digest need a place for it ([[DEC-23]]).
- Measured: before this change, Opus recovers 0.28 of the oracle's gain over accept-all at fixed:1.0 ([[RES-16]]). It earns +$14,584 a seed against +$8,438 and +$30,588. Its reasons cite the fixed elasticity and no past outcome.
- Links: [[DAT-16]], [[MOD-09]], [[MOD-10]], [[DEC-44]], [[RES-16]]

### DEC-46 [T] The agent reprices when data arrives during the day
- Decided: the agent will run again within a day when a feed delivers new data.
- Replaces: nothing built; today decide(day, sources) runs once per day ([[MOD-10]]).
- Reason: a real feed arrives through the day, and a rate decided in the morning is stale by the afternoon.
- Needs: a clock finer than as_of_day in the sources ([[DAT-25]]) and the stored tables ([[DAT-28]]). The hold needs a rule within a day ([[CON-10]]).
- Links: [[MOD-10]], [[DAT-25]], [[DAT-28]], [[DEC-42]]

### DEC-49 [C] The benchmark measures the reviewer in the mismatched modes
- Decided: the bench measures every reviewer at fixed:1.0 and fixed:2.0 and keeps the true mode as a check. The ranking pools the two mismatched modes ([[DEC-48]]).
- Replaces: nothing built; the live model had been measured in the true mode only ([[UNK-01]]).
- Reason: in the true mode every plan is scored at the simulator's elasticity, so accepting every plan is right. The oracle accepts all ([[DEC-47]]). Only where the code's elasticity is wrong can a decline be right ([[DEC-38]]).
- Measured: at fixed:1.0 Opus recovers 0.28 of the oracle's gain over accept-all, and Sonnet and Haiku recover none ([[RES-16]], [[RES-19]]).
- Commit: 5935444
- Evidence: test_the_oracle_reviewer_accepts_every_queued_plan_in_true_mode, test_the_offline_bench_on_20_seeds_pins_the_benchmarks_headline
- Links: [[UNK-01]], [[DEC-38]], [[DEC-47]], [[DEC-48]], [[MEA-12]], [[RES-16]], [[RES-17]], [[RES-18]], [[RES-19]]

### DEC-50 [C] A demand bias the agent never sees is the demand-level twin of a fixed elasticity
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

### DEC-52 [C] The share elasticity alone made a matched raise free, so the market can answer the comp median's level
- Decided: expected demand scales with (the comp median as shopped / its starting level) ** -MARKET_ELASTICITY ([[RUL-87]]). The default is 0.0, so every pinned result stands. --market-elasticity sets it on both commands.
- Why: bookings follow the hotel's rate against the comp median alone ([[RUL-21]]). A raise the competitors follow therefore costs no rooms, and the reaction run measured the ratchet that makes ([[DEC-51]], [[RES-24]]).
- Agent: forecast.py mirrors the term and the equality test covers it ([[RUL-88]]). The agent is told the run's value, and every plan record carries it as market_elasticity. A set value changes the request digest.
- Oracle: the command tells the oracle the value and the reaction's share. It then scores a candidate against the median the reaction moves, with the market's answer. It is the ceiling again.
- Cache: a run with a market elasticity other than 0 keeps its cache under cache/market-E/ ([[DEC-50]]). That folder nests under the bias and react folders where those apply.
- Measured: with the reaction on, a market elasticity of 1.0 cuts the default mode's gain to +$43,584 a seed ([[RES-26]], [[RES-27]]).
- Evidence: test_the_market_elasticity_scales_each_days_draw_by_the_medians_level, test_the_grader_scores_a_raise_against_the_median_the_reaction_moves, test_the_oracle_reviewer_is_told_the_market_elasticity_and_the_reaction
- Links: [[DEC-51]], [[DEC-50]], [[RUL-87]], [[RUL-88]], [[RES-26]], [[RES-27]], [[UNK-11]], [[UNK-15]], [[FRK-08]], [[FRK-09]]

### DEC-53 [C] The air schedule's filings are a named scenario, and the churn files what a feed files
- Decided: a Scenario is a named list of filings ([[DAT-03]]). The default is AIR_SHOCKS as it was. --scenario picks another from SCENARIOS, and the upgauge scenario holds an upgauge and a frequency cut ([[SHK-05]], [[SHK-06]]).
- Kinds: a filing adds routes, suspends one, swaps a route's equipment, sets its daily flights or shifts its departures ([[RUL-89]]). An equipment change moves the seats while the flight count stays. A time change moves no seat.
- Churn: --churn files the seed's weekly revisions on top, each under the detect threshold ([[SHK-07]]). A detector that fires on any revision fires on them. The threshold detector does not.
- Reason: a real feed revises every week, and most revisions change no seat count a hotel should act on. The default's two shocks never tested that. The scenario option keeps the default pinned while another story runs.
- Measured: with the churn, seeds 1 to 20 raise the same 173 seat flags as without it ([[RES-28]]).
- Evidence: test_the_churn_files_weekly_revisions_below_the_threshold, test_a_detector_that_fires_on_any_revision_is_caught_by_the_churn, test_a_scenario_and_the_churn_go_to_both_runs
- Links: [[DAT-03]], [[SHK-05]], [[SHK-06]], [[SHK-07]], [[RUL-89]], [[RES-28]], [[DEC-04]], [[UNK-05]]

### DEC-54 [C] A learning agent can feed the fitted demand level back into its forecast
- Decided: learn:X --level scales the agent's forecast, the pace baseline included, by exp(intercept) ([[RUL-96]] to [[RUL-98]]). The factor is 1 until the fit has enough observations. Every plan record carries it ([[DAT-21]]).
- Baseline: the estimator's baseline stays unscaled, so the intercept keeps measuring the level against the raw forecast ([[MOD-16]]). The factor therefore does not compound.
- Reason: the intercept absorbed a demand-level error and the agent discarded it ([[DEC-38]]). At a bias of 0.9 the plain learner lost money ([[RES-21]]). The arm asks whether the level fed back recovers that, and what it costs at 1.0.
- Measured: the level is learned by day 10 in every world ([[RES-29]] to [[RES-32]]). The gain at 0.9 does not recover: accept-all earns -$15,244 a seed with it.
- Evidence: test_a_level_agent_scales_its_forecast_by_the_fitted_demand_level, test_a_level_scales_one_hotels_pace_baseline_and_expected_demand, test_the_level_factor_is_the_fitted_level_once_the_fit_has_enough_observations
- Links: [[DEC-38]], [[DEC-50]], [[DEC-52]], [[RUL-96]], [[RUL-97]], [[RUL-98]], [[RES-29]], [[RES-30]], [[RES-31]], [[RES-32]], [[UNK-07]], [[UNK-08]]

### DEC-55 [C] A rule-based control is the fair comparison, because frozen rates never move
- Decided: --policy runs a rule-based control beside each arm ([[MOD-25]]). pace raises POLICY_STEP where a stay date runs ahead of pace and lowers it where behind ([[RUL-99]]). Both keep the agent's hold, floor and ceiling.
- Rules: rules keeps the pace steps and adds the retired rules of [[DEC-11]]. It raises on an event or seat-up flag and lowers on a seat-cut flag. A flag whose causes point both ways is left alone. The README quotes it.
- Why rules: pace skips every flag that is not a pace flag. It cannot act on the two shocks that carry most of the gain ([[RES-06]]). Against it the agent was beaten on the part of the problem the control was never given.
- Reason: a fixed-rate run never moves a rate, so every gain against it includes what a hotel's own rules earn anyway. The rule stands for what a hotel already does, and the agent's margin over it is the claim worth making.
- Measured: in the default world the rules policy earns +$22,856 a seed, and the agent's gain against it is +$10,043 ([[RES-33]]). Both policies act only on a flag and share the blind spot of [[FRK-11]].
- Evidence: test_the_rule_raises_ahead_of_pace_and_lowers_behind_by_the_step, test_the_rules_policy_adds_the_event_and_seat_rules_and_skips_a_conflict, test_a_policy_runs_the_rule_based_control_beside_each_arm
- Links: [[MOD-25]], [[RUL-99]], [[RES-33]], [[RES-01]], [[RES-06]], [[DEC-11]], [[DEC-13]], [[FRK-11]], [[UNK-08]]

## Engineering

### DEC-23 [C] The cache is keyed by seed, day and hotel, and each file records a digest of its request
- Decided: the answer to one hotel's queue on one day is saved at cache/seed<seed>/day<DDD>_<hotel key>.json. The file records the sha256 of the request's sorted-keys JSON ([[DAT-17]]), and a rerun reads the cache first.
- Detail: a file whose digest does not match the request raises StaleCache instead of answering the wrong question. A replay reads the cache and never calls the model.
- Model: a model other than MODEL ([[RUL-46]]) adds -<model> to the folder, as a mode does. Each new record names its model. The default model in the default mode keeps cache/seed<seed>/, so [[DAT-29]] replays unchanged.
- Replaces: nothing built.
- Reason: each hotel's queue costs one model call a day, paid once per seed. A changed rule or constant changes the request, so it cannot reuse a stale answer silently.
- Commit: abef71f
- Evidence: test_ask_calls_the_model_once_and_then_reads_the_cache, test_a_cache_written_for_another_request_is_refused, test_a_replay_never_calls_the_model, test_the_cache_record_names_the_model_asked
- Links: [[MOD-09]], [[DAT-17]], [[DEC-25]], [[FRK-04]]

### DEC-24 [H] Template answers were cached like the model's
- Decided: the template's answers were written to the same cache files as the model's, marked "source": "template". A client replaced a template-sourced file with the model's answer.
- Replaced by: [[DEC-25]]
- Reason it went: a live run after a template run stopped with StaleCache when a model decision changed a later day's request. --template and --seeds, which pass no client, reused the model's answers, so a sweep could mix two policies.
- Commit: abef71f
- Links: [[MOD-09]]

### DEC-25 [C] Only the model's answers are cached; the template is a function of the request
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

### DEC-28 [C] The code is the package src/hotel_market, with pyproject.toml and a console command
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

### DEC-30 [C] No hosted CI; the checks run locally through make and pytest
- Decided: the workflow file is gone. The tests, ruff and the knowledge-graph check run locally with python -m pytest and the two ruff commands. The Makefile wraps them.
- Detail: a test marked slow runs 20 seeds and takes about a minute. Plain pytest skips it, and pytest --slow (make test-all) includes it.
- Replaces: [[DEC-29]]
- Reason: the owner chose it after the queued run, and nothing in the repository depends on a hosted runner.
- Commit: 5cef53e
- Evidence: test_the_checks_run_locally_with_no_hosted_workflow
- Links: [[MOD-15]]

### DEC-31 [H] One agent.py held the planning, the model call and the daily loop
- Decided: candidates, estimates, the request, the cache, the template, the client and the loop were one module of 539 lines.
- Replaced by: [[DEC-32]]
- Reason it went: three jobs sat in one file, and the dense parts were hard to read. Four parallel dicts fed the estimate, a string-keyed dict held a flag's numbers, and request literals were nested.
- Commit: abef71f
- Links: [[MOD-10]]

### DEC-32 [C] The agent is three modules: plan.py, model.py and agent.py, with text.py for shared wording
- Decided: the module plan.py builds candidates, estimates and plans, and model.py holds the model call, its cache and the template. The module agent.py runs the daily loop and gives the advice, and text.py holds the shared wording.
- Replaces: [[DEC-31]]
- Reason: each module has one job. Named records (StayDate, FlagNumbers, Comparison, SeedResult) replace dicts and tuples, and the command line has one function per mode. The tests follow the split.
- Measured: the split preserved behaviour. Two seeds' decisions.jsonl, the printed summaries, both replays, the sweep and the diagnostics matched the previous output byte for byte.
- Commit: abef71f
- Evidence: test_the_agent_reads_only_through_the_interfaces, test_estimate_is_expected_contribution_on_the_unsold_rooms
- Links: [[MOD-08]], [[MOD-09]], [[MOD-10]], [[MOD-11]]

### DEC-33 [C] ruff formats the code at 100 columns, and the format check is part of lint
- Decided: ruff format owns the layout, and make lint runs ruff check . and ruff format --check .. The route table in schedule.py keeps one route per line under a bare fmt: off marker.
- Note: ruff ignores the marker when text follows it on the same line.
- Replaces: hand formatting at up to 120 columns.
- Reason: one layout leaves no arguments about style. The only hand work left was 14 lines the formatter could not shorten.
- Commit: 15e0215
- Evidence: test_the_formatter_runs_at_100_columns
- Links: [[MOD-15]], [[MOD-01]]

### DEC-34 [C] The answer schema lists the request's own entry ids and options as enums
- Decided: schema_for(request) builds the structured-output schema. It limits "id" to the entry ids and "choice" to the plans and "hold" in that request. It sets the array's minimum length to the entries' count; the API rejects a maximum.
- Replaces: a fixed schema that typed id and choice as free strings.
- Reason: with free strings a schema-valid answer such as "Hold" failed the check, and the run aborted with nothing cached. With enums the API cannot return a choice the code would reject. The pairing check stays as the backstop.
- Commit: abef71f
- Evidence: test_the_schema_limits_ids_and_choices_to_the_requests_options
- Links: [[MOD-09]], [[DAT-16]], [[UNK-02]], [[RES-09]]

### DEC-40 [C] The agent reads data only through four interfaces; the simulator is one implementation
- Decided: sources.py ([[MOD-17]]) defines Bookings, RateShops, Schedules and Events ([[DAT-25]]). Every method takes the day it is asked on and returns only what was known then.
- Boundary: the modules detect, forecast, estimate, plan, model and agent read data through them and import none of the simulator's modules. A test reads their imports and fails if one does.
- Detail: the agent's own demand model is forecast.py ([[MOD-18]]), held equal to demand.py by a test. The simulator implements the four in simulated.py ([[MOD-19]]). ORACLE_ELASTICITY ([[RUL-56]]) names the default elasticity an oracle.
- Replaces: [[DEC-26]], and the agent's direct reads of the simulator: detect_numbers(day, books), estimate_elasticity(books, ...) and the peak night in demand.py.
- Reason: a repository that can be pointed at a hotel's own data needs one place where the data comes in. With the line drawn, what the agent may know is the list of methods in sources.py.
- Measured: the default run is unchanged ([[RES-02]]). Seed 7's decisions file is byte for byte the one before the boundary, and the estimator's inputs are bitwise identical.
- Commit: 35967c8
- Evidence: test_the_agent_reads_only_through_the_interfaces, test_the_forecast_is_the_simulators_demand_for_the_demo_market, test_the_default_mode_still_gives_28818_on_seed_7

### DEC-41 [C] Everything specific to the market is a customer file, and the target is one of its settings
- Decided: customers/demo.toml holds the demo market, which [[MOD-20]] reads into a Customer ([[DAT-27]]).
- Holds: the hotels and comp sets ([[DAT-04]]), the cost share and the rate limits, and the detect thresholds and hold period. It also holds the minimum, the booking curve and the target ([[RUL-57]] to [[RUL-69]]).
- Command: hotel-market --customer FILE names the file, and --target overrides its target. The demo file is the default wherever none is given. A revenue run keeps its own cache folder ([[DAT-17]]).
- Replaces: the market constants in world.py and the thresholds in detect.py and plan.py ([[RUL-14]] to [[RUL-18]], [[RUL-23]] to [[RUL-30]], [[RUL-40]]). It closes [[FRK-01]].
- Reason: with the boundary drawn ([[DEC-40]]), the market's numbers were the last demo facts written into code. In a file they are what a hotel would hand over, and the simulator reads it too. The simulator's constants stay in code.
- Measured: the revenue target earns +$211,445 of room revenue a seed and only +$461 of contribution ([[RES-07]]). The two targets pull the rates in opposite directions, and the default run is unchanged ([[RES-02]]).
- Commit: 9d74c0d
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_the_revenue_target_scores_candidates_on_the_rate_alone, test_the_command_takes_a_customer_file_and_a_target

### DEC-42 [C] The feeds and the agent's output are stored tables keyed by as_of_day, and the agent can run one day at a time against them
- Decided: sql/schema.sql defines seven tables ([[DAT-28]]), four feeds and three agent outputs, each keyed by as_of_day. The file is plain SQL, and its head lists the statements a cloud warehouse would change.
- Stored: stored.py ([[MOD-21]]) implements the four interfaces over the tables and writes a day's rows. It deletes the day's rows first, so running a day twice leaves the tables unchanged. The simulated sources ([[MOD-19]]) are unchanged.
- Daily run: the run-day command plays the simulator to day N with the stored rate changes and writes the day's feeds. A fresh agent resumes the stored hold and advice, decides the day from the tables alone and writes its output.
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
- Measured: in the default mode the oracle accepts every queued plan. That mode therefore cannot separate reviewers, and the mismatched modes can ([[RES-03]]).
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
