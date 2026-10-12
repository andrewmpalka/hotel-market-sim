# Decisions

One DEC node per design decision, from the git history and CLAUDE.md, in two
groups: the market and the agent's design, then engineering. Within a group
the nodes are in the order the decisions were made. Each one says what was
decided, what it replaced, the reason with the numbers that were measured,
and the commit it landed in. The commit is information, not evidence: the
evidence is the tests the node cites, so it survives a new git history. A
replaced design keeps its node, marked [H], and names the decision that
replaced it.

Every measured number below is from this simulator, whose demand formula the
agent shares; the numbers show that the loop works and are not a forecast.

## Market and agent design

### DEC-01 [C] Code computes every number; the model only chooses and writes
- Decided: every number in a flag, candidate, estimate, reason and report comes from code. The model sees the request ([[DAT-16]]), picks the plan or hold for each entry, and writes two or three sentences. Its answer is checked against the options it was given.
- Replaces: nothing; the first rule of the project
- Reason: a number the model made up could not be traced or tested, and the comparison between the fixed-rate run and the agent run would measure the model's arithmetic instead of the policy.
- Commit: 15e0215
- Evidence: test_a_choice_that_is_not_the_plan_or_hold_is_rejected
- Links: [[RUL-01]], [[MOD-09]]

### DEC-02 [C] Nothing is used before the day it becomes known
- Decided: every lookup takes the day it is made on: build_schedule(as_of_day), events_as_of, rate_cuts_as_of, comp_rates(shop_day, ...), expected_demand(hotel, stay_day, as_of_day).
- Replaces: nothing; the third rule of the project
- Reason: an agent that sees a flight before the airline files it is not being tested on the schedule data at all. The seat change for day 55 is 0% as of day 19 and +17% as of day 21.
- Commit: 53a7081
- Evidence: test_nothing_changes_demand_before_day_10, test_shock_known_follows_what_is_known_on_the_day
- Links: [[RUL-03]], [[MOD-01]], [[MOD-03]], [[MOD-04]]

### DEC-03 [C] The day-0 preload: bookings made before the run starts
- Decided: before day 0's bookings, each stay date in the window is loaded with a seeded Poisson draw around normal_demand x curve(days out + 1), capped at the rooms, at the hotel's starting rate.
- Replaces: nothing built; the alternative was starting with empty books, which would have flagged every early stay date as behind pace and left tonight's hotel empty.
- Reason: the first 90 stay dates are already part way up the booking curve when the run starts; tonight is 1 - 0.3 / 7 of the way, so the convention hotel starts with about 273 of 285 expected rooms on the books for day 0.
- Commit: 054edd6
- Evidence: test_preload_mean_is_normal_demand_x_curve_of_days_out_plus_1, test_day_0_starts_with_the_bookings_made_before_the_run
- Links: [[MOD-06]], [[DAT-07]], [[RUL-68]]

### DEC-04 [C] seat_revision is the seat trigger; seat_change is carried for the text
- Decided: a flag is raised when the change in arriving seats against the schedule known the day before is 5% or more either way ([[RUL-64]]). The change against the no-shock baseline is computed and shown but never flags.
- Replaces: nothing built; flagging on seat_change was the first idea.
- Reason: seat_change stays at +17% from day 20 on, so flagging on it would re-flag stay dates 50 to 149 every day. seat_revision is zero except on the two filing days, 20 and 40, and it is the only number that shows the day-40 cut as a cut: after it, seats on days 70 to 90 are still 240 a day above the baseline, but 480 a day (about 10%) below the day before.
- Commit: abef71f
- Evidence: test_shock_causes_appear_only_on_the_days_shocks_become_known, test_known_seat_revision_matches_the_schedule
- Links: [[SHK-02]], [[SHK-04]], [[DAT-02]], [[MOD-07]]

### DEC-05 [C] The booking loop plays out to day 149 with rates frozen from day 60
- Decided: the agent decides on days 0 to 59; the loop keeps booking to day 149 with no new decisions, and the window stops at stay date 149, so every stay date from 0 to 149 ends complete.
- Replaces: nothing built; the first plan stopped the loop at day 59.
- Reason: the agent's last decisions change stay dates up to 148, which would be mostly empty on day 59; revenue and contribution are counted over all 150 stay dates. On seed 7 with fixed rates, stay dates 140 to 149 end 78% to 91% full on average by hotel (the emptiest single night is 57% full at the lifestyle hotel); stopping at day 59 would have left them nearly empty, since they were still 81 to 90 days out.
- Commit: 054edd6
- Evidence: test_every_stay_date_to_149_is_complete, test_rates_can_only_change_on_days_0_to_59
- Links: [[RUL-12]], [[RUL-05]], [[MOD-06]]

### DEC-06 [C] The 7-day hold after an accepted rate change
- Decided: after an accepted change on day d, a pace gap alone raises no new flag on that stay date on days d+1 to d+7 ([[RUL-66]]). A shock cause lifts the hold.
- Replaces: nothing built.
- Reason: a new rate needs days of bookings before its pace reads differently; re-deciding the same stay date every day would chase booking noise. In the first full agent run, one stay date (the full-service hotel's stay date 46) was still changed five times across days 10 to 44, each time after its hold had expired, which is what led to the $250 minimum ([[DEC-17]]).
- Commit: abef71f
- Evidence: test_the_hold_silences_pace_flags_for_7_days_but_not_shock_flags, test_accepted_rates_apply_and_hold_those_stay_dates_for_7_days
- Links: [[MOD-07]], [[MOD-10]], [[DAT-09]]

### DEC-07 [C] A pace flag needs a gap beyond both 10% of rooms and 3 standard deviations
- Decided: the pace threshold is max(0.10 x rooms, 3 x sqrt(normal demand x curve)) ([[RUL-62]], [[RUL-63]]).
- Replaces: nothing built; a single percentage floor was the first idea.
- Reason: a percentage of rooms alone flags far-out stay dates where few rooms are on the books and noise dominates; 3 x sqrt(mean) is three Poisson standard deviations. At the convention hotel tonight is 285 rooms on pace, where 3 x sqrt(285) = 50.6 beats 40; sixty days out only 54 rooms are on pace, where 3 x sqrt(54) = 22 and the 40-room floor wins.
- Commit: abef71f
- Evidence: test_pace_threshold_is_the_larger_of_10_percent_of_rooms_and_3_sd
- Links: [[MOD-07]], [[DAT-08]]

### DEC-08 [H] The convention's peak night was fixed at stay date 46
- Decided: the second review set the peak night at 46 as a given.
- Replaced by: [[DEC-09]]
- Reason it went: with the downtown day-of-week factors, Thursday 45 (1.05) draws more demand than Friday 46 (0.90), so the fixed night was the wrong one.
- Commit: 53a7081
- Links: [[SHK-01]]

### DEC-09 [C] The peak night is computed from expected demand as of the day the event becomes known
- Decided: peak_night(hotel, event, sources), now in [[MOD-18]], is the event night with the highest expected demand as of event.known_day, earliest night on a tie.
- Replaces: [[DEC-08]]
- Reason: the peak must follow the data and the as-of rule. For the convention it is Thursday 45 at both downtown hotels. A test with a made-up event over nights 49 to 55 shows the answer moving from Monday 49 to Thursday 52 once the day-20 flights are known.
- Commit: abef71f
- Evidence: test_convention_peak_night_is_its_busiest_night_as_of_day_10, test_peak_night_uses_what_is_known_on_the_day_the_event_becomes_known
- Links: [[MOD-04]], [[SHK-01]], [[RUL-03]]

### DEC-10 [C] A minimum stay is advice only, never simulated
- Decided: when an event's peak night is ahead of pace, the agent recommends a two-night minimum once per hotel and event. The advice goes into decisions.jsonl marked "simulated": false and is left out of every estimate and result.
- Replaces: nothing built.
- Reason: the simulator has no length of stay, so a minimum-stay rule cannot be booked or scored; recording it as advice keeps the estimates honest and still shows the recommendation a revenue manager would want.
- Commit: abef71f
- Evidence: test_minimum_stay_advice_is_given_once_per_hotel_and_event_and_not_simulated, test_minimum_stay_advice_is_not_repeated_on_later_days
- Links: [[DAT-15]], [[MOD-10]], [[FRK-03]]

### DEC-11 [H] The rule "seats up, so raise the rate"
- Decided: the first plan for the agent raised rates when seats rose and lowered them when seats fell.
- Replaced by: [[DEC-12]] and [[DEC-13]], before it was built
- Reason it went: it ignored that each room sold costs money to service and that a raise on a night that will not sell out loses bookings for nothing. A rule that always raises on more seats is not a decision; scoring is.
- Commit: abef71f
- Links: [[SHK-02]]

### DEC-12 [C] Contribution with a room cost is the target, and the start rate is best on ordinary nights
- Decided: each occupied room costs one third of the hotel's start rate to service ([[RUL-61]]); contribution is room revenue minus that cost for every room sold, and the agent scores candidates on it.
- Replaces: [[DEC-11]], and revenue as the implicit target
- Reason: revenue rewards selling every room at any price. With ELASTICITY 1.5 the contribution-best rate on a night that will not sell out is 3 x cost, which is the start rate, so the agent has nothing to gain on ordinary nights and only a night that may sell out can pay for a raise. The fixed-rate seed-7 run holds occupancy at 75.7%, 76.0%, 76.6% and 83.7% over stay dates 0 to 59.
- Commit: 9d74c0d
- Evidence: test_each_occupied_room_costs_a_third_of_the_start_rate, test_contribution_is_revenue_minus_the_cost_of_every_room_sold, test_on_nights_that_will_not_sell_out_the_start_rate_is_already_best
- Links: [[RUL-61]], [[RUL-21]], [[FRK-01]]

### DEC-13 [C] Every flag gets scored candidates, with hold as the default
- Decided: every flag, whatever its cause, gets hold, raise 5%, raise 10% and lower 5% ([[RUL-43]]), clamped to the floor and ceiling, plus lower halfway to the new median when the comp median dropped ([[RUL-42]]). Each is scored on the rooms still unsold; value at stake is the best estimate minus the hold estimate; when nothing beats hold the entry is recorded as a hold and stays out of the queue. The model may decline the best candidate, which records a hold.
- Replaces: [[DEC-11]]
- Reason: the same candidates for every cause keeps the agent from reacting to a label; the estimate decides. Hold wins a tie, so the agent never changes a rate for nothing.
- Commit: abef71f
- Evidence: test_each_day_of_the_week_gets_hold_raise_5_raise_10_and_lower_5_clamped_to_the_limits, test_a_comp_median_drop_adds_lower_halfway_to_the_new_median, test_a_model_that_declines_changes_no_rate
- Links: [[MOD-08]], [[DAT-11]], [[DAT-12]]

### DEC-14 [C] The airport hotel's base occupancy is 0.85; the other three are 0.75
- Decided: base occupancy is stored per hotel ([[DAT-04]]) and the airport hotel's is 0.85.
- Replaces: one base occupancy of 0.75 for every hotel.
- Reason: a choice about the scenario. At 0.75 the new flights never fill the airport hotel, so the schedule data would never matter there; at 0.85 Mondays, Thursdays and Sundays after day 50 are expected 101% full. The fixed-rate occupancy check is 60% to 90% over stay dates 0 to 59, and the airport hotel ends at 83.7%.
- Commit: 9d74c0d
- Evidence: test_hotels_match_the_table, test_fixed_rate_occupancy_is_between_60_and_90_percent_for_stay_dates_0_to_59
- Links: [[DAT-04]], [[SHK-02]]

### DEC-15 [H] Rates followed the day of the week
- Decided: each hotel's starting rate and each competitor's rate carried a rate factor of 1 + 0.5 x (demand factor - 1), so a Saturday at the lifestyle hotel started 12.5% dearer than its table rate.
- Replaced by: [[DEC-16]]
- Reason it went: with a fixed room cost the best rate on a night that will not fill is the same every day, so the weekday factor made the starting rates wrong, and most of the agent's gain was correcting them rather than reacting to the market: the lifestyle hotel gained +$12,514 on seed 7, mostly on Fridays and Saturdays.
- Commit: bd556fb
- Links: [[MOD-05]], [[DAT-04]]

### DEC-16 [C] Flat rates: starting and competitor rates do not follow the day of the week
- Decided: every hotel's starting rate is its table start rate on every stay date, and competitor rates are base rate x noise, with the shocks applied. Demand still follows the day of the week ([[DAT-04]]).
- Replaces: [[DEC-15]]
- Reason: see [[DEC-15]]. Measured on seed 7 together with [[DEC-17]] and [[DEC-19]]: the agent's gain fell from +$26,420 to +$22,894 of contribution and the lifestyle hotel's from +$12,514 to +$5,832; the smaller number is the true one, since the starting rates are now right on ordinary nights.
- Commit: bd556fb
- Evidence: test_competitor_rates_are_base_rate_x_noise_with_no_weekly_pattern, test_hotel_starts_level_with_its_comp_median
- Links: [[MOD-05]], [[DEC-12]]

### DEC-17 [C] A plan must be worth at least $250 over holding to enter the queue
- Decided: a minimum value at stake of $250 ([[RUL-67]], a setting of the customer file since [[DEC-41]]); an entry below it is recorded as a hold with the reason "under the $250 minimum".
- Replaces: a queue of every entry whose best candidate beat hold by any amount.
- Reason: the first full agent run made 23 rate changes, several worth under $10, and 8 of them lost money; a revenue manager should not be shown an $8 recommendation. With the minimum, seed 7 made 10 changes and held 22 flags as under the minimum (7 changes and 57 held once [[DEC-21]] landed). The day-40 take-back at the airport hotel, worth $132, is held by it on purpose.
- Commit: abef71f
- Evidence: test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue, test_entries_below_the_minimum_are_held_and_stay_out_of_the_queue
- Links: [[RUL-67]], [[SHK-04]]

### DEC-18 [H] One candidate moved all of a flag's stay dates together
- Decided: the first agent applied one candidate to every stay date in a flag.
- Replaced by: [[DEC-19]]
- Reason it went: the day-20 airport flag covers stay dates 50 to 109, and one move raised all sixty, including the Tuesdays and Saturdays that would never fill.
- Commit: abef71f
- Links: [[SHK-02]]

### DEC-19 [C] The best candidate is chosen separately for each day of the week within a flag
- Decided: a flag's stay dates are grouped by weekday ([[DAT-12]]); each group gets its own best candidate, hold winning a tie; the plan names the days that change ("raise 10% on Thu; raise 5% on Sat"), and value at stake is summed over them.
- Replaces: [[DEC-18]]
- Reason: on day 20 the airport hotel then raised Mondays, Thursdays and Sundays and held Tuesdays and Saturdays, worth $3,849 with the capped estimate of the time; with the exact estimate ([[DEC-21]]) it raises every night but Saturday, worth $10,627.
- Commit: abef71f
- Evidence: test_a_plan_lists_its_changes_by_day_of_week, test_after_the_new_flights_the_airport_raises_every_night_close_to_full
- Links: [[MOD-08]], [[DAT-14]]

### DEC-20 [H] Expected bookings were capped at the unsold rooms
- Decided: estimated bookings = min(remaining demand x (rate / median) ** -AGENT_ELASTICITY, unsold rooms).
- Replaced by: [[DEC-21]]
- Reason it went: the cap treats a night expected to come close to full as if it could not sell out. Measured on seed 7, it understated the day-20 airport plan by about half ($3,849 against $8,012 with booking noise counted), overstated the three biggest convention plans by $356 to $575 each, and held the 97%-full Wednesdays and Fridays that the exact estimate raises. It had first been kept as a known limit because the error looked like $200 on a $2,000 estimate.
- Commit: abef71f
- Links: [[MOD-08]]

### DEC-21 [C] Estimated bookings are the exact expectation E[min(N, unsold)] for a Poisson N
- Decided: expected_bookings(mean, unsold) sums the Poisson probabilities below the unsold count and gives the rest to a sell-out, the same booking noise the simulator draws.
- Replaces: [[DEC-20]]
- Reason: a night expected 97% full still sells out fairly often, so a small raise there pays. Seed 7 went from +$22,894 to +$28,818 of contribution and the 20-seed mean from +$27,350 to +$32,899, with the agent ahead in 20 of 20 seeds both before and after; room revenue falls in every seed, by $22,861 on average, because fewer rooms are sold dearer.
- Commit: abef71f
- Evidence: test_expected_bookings_is_the_mean_of_a_poisson_count_that_stops_at_the_unsold_rooms, test_expected_bookings_matches_the_simulators_daily_draws, test_a_night_expected_97_percent_full_raises_where_a_cap_on_demand_would_hold
- Links: [[MOD-08]], [[DAT-10]]

### DEC-22 [C] One random number per booking draw, fixed by the seed before the run
- Decided: every draw of the run has its own uniform random number, drawn in one go from the seed, and poisson_draw turns it into a count by the Poisson quantile. A bigger mean never gives a smaller count on the same number.
- Replaces: nothing built; a shared random stream was the alternative.
- Reason: a rate change on one stay date leaves every other draw as it was, so the fixed-rate and agent runs differ only where the agent acted. That makes the changed-pairs comparison exact: on seed 7 the 93 hotel-nights the agent changed carry the whole +$28,818, and the other 507 book identically in both runs.
- Commit: 054edd6
- Evidence: test_a_rate_change_applies_from_the_next_day_and_touches_no_other_stay_date, test_every_other_pair_books_the_same_in_both_runs, test_a_bigger_mean_never_draws_fewer_rooms_on_the_same_luck
- Links: [[MOD-06]], [[DAT-07]], [[RUL-02]]

### DEC-26 [H] AGENT_ELASTICITY is the agent's own constant and never imports the simulator's
- Decided: plan.py defined AGENT_ELASTICITY = 1.5 ([[RUL-39]]) and a test read the module's imports to make sure ELASTICITY ([[RUL-21]]) was not among them.
- Replaced by: [[DEC-40]], which draws the line around the whole agent and names the value an oracle ([[RUL-56]]).
- Reason it went: one constant kept apart was the right idea on too small a scale; the agent still read the simulator's demand, draws and shocks directly.
- Commit: abef71f
- Links: [[RUL-39]], [[RUL-21]], [[FRK-02]], [[DEC-38]]

### DEC-35 [C] Every number is synthetic, and the schedule's columns follow a published data dictionary
- Decided: the city, airports, airlines, flights, hotels, competitors and bookings are invented. The schedule table's column names follow Cirium's published schedule data dictionary so that the code reads data shaped like a real feed; the repository contains no Cirium data and has no affiliation with Cirium. No real hotel brand or employer is named anywhere in the repository.
- Replaces: nothing.
- Reason: the project tests whether the loop works, not a market; shaped-like-real data lets the counting traps (codeshares, a bus under a flight number, a second airport) be real traps without any real rows.
- Commit: e134523
- Evidence: test_summing_by_arrival_station_misses_the_second_airport
- Links: [[DAT-01]], [[MOD-01]]

### DEC-36 [C] The summary reports what the run produces; the rules are not tuned to force a gain
- Decided: the comparison between the fixed-rate run and the agent run is reported as it comes out, with every rate-changing decision and the plans that lost money, and the README states that the agent shares the simulator's demand formula.
- Replaces: nothing.
- Reason: a tuned gain would say nothing about the loop. Reported this way, seed 7 is +$28,818 and the 20-seed mean +$32,899, with the agent ahead in every seed and revenue down in every seed.
- Commit: 12e000b
- Evidence: test_the_summary_compares_both_runs_on_the_changed_pairs
- Links: [[MOD-12]], [[DAT-20]]

### DEC-37 [C] Competitor noise is drawn once per competitor and stay date, so a comp median moves only on a shock
- Decided: the rate-shop noise is one array per seed, shape (hotels, competitors, stay dates), drawn before the run on its own stream ([[RUL-20]]); the shop day only applies the shocks known by then.
- Replaces: nothing built; fresh noise on every shop day was the alternative.
- Reason: fresh noise would move every comp median every day and raise comp-median flags from nothing; drawn once, the only medians that move are the convention nights on day 10 and the cut nights on day 30.
- Commit: bd556fb
- Evidence: test_comp_median_moves_only_when_a_shock_becomes_known
- Links: [[MOD-05]], [[DAT-06]]

### DEC-38 [C] The agent can learn its elasticity from the bookings; the default stays the simulator's value
- Decided: --elasticity picks where the agent's elasticity comes from ([[RUL-49]], [[DAT-22]]): true, the default, is the oracle value ([[RUL-56]]), the simulator's own 1.5, so nothing in the published results changes; fixed:X is X for the whole run; learn:X starts from the prior X and re-estimates every hotel every day by a Poisson regression of the bookings made before that day on log(rate / competitor median), with the log of the agent's own baseline (expected demand as known on the booking day times the booking curve's rise) as an offset, an intercept for the demand level, a normal prior of width [[RUL-50]] on the elasticity, and a clamp to [[RUL-51]] to [[RUL-52]] ([[MOD-16]]). A stay date's observations stop on the day it sells out, and the day-0 preload is never one, because the simulator draws it with no price response. Every entry, request and log line records the elasticity used, its standard error and the mode ([[DAT-21]]), so a change of mode changes the cache key.
- Replaces: nothing built; it closes the fork [[FRK-02]].
- Commit: abef71f
- Reason: with the agent's elasticity equal to the simulator's, the agent was never wrong about price response, and the question was what being wrong costs and how much of it learning wins back. Measured on seeds 1 to 20 with the template, each arm against the same fixed-rate runs: true +$32,899 a seed, ahead in 20 of 20, 179 rate changes in all, the accepted plans' estimates summing to 1.04 times the realised gain; fixed:1.0 +$8,438, 14 of 20, 515 changes, estimates 39 times the gain; fixed:2.0 +$9,551, 18 of 20, 486 changes, 13 times; learn:1.0 +$14,141, 16 of 20, 373 changes, 18 times; learn:2.0 +$16,258, 20 of 20, 418 changes, 5 times. A wrong value costs about three quarters of the gain and learning wins back about a quarter of the loss. The estimates move toward 1.5 from both sides, with day-59 means of 1.36 to 1.45 by hotel from a prior of 1.0 and 1.55 to 1.68 from 2.0, but on days 10 and 20, when the convention and the new flights are decided, they still sit near the prior. The rate ratio barely moves on its own: in a fixed-rate run the standard deviation of its log is 0.011 to 0.027 by hotel, from competitor noise and the two competitor shocks, and the bookings alone would pin the elasticity to about 0.2 at the downtown hotels and 0.9 to 1.2 at the lifestyle and airport hotels; the agent's own rate changes supply most of the usable variation, 12% of the lifestyle and 37% of the airport observations on seed 7. With the true value at 1.0, 1.5 or 2.0 and a prior of 1.5, every day-59 estimate on seeds 7 and 3 landed within 1.6 standard errors of the truth.
- Evidence: test_the_day_59_estimate_recovers_the_simulators_elasticity, test_the_default_mode_still_gives_28818_on_seed_7, test_the_default_mode_still_gives_a_20_seed_mean_of_32899, test_each_mode_records_the_elasticity_its_plans_assume
- Links: [[MOD-16]], [[MOD-10]], [[CON-06]], [[FRK-02]], [[UNK-07]], [[DEC-26]]

### DEC-39 [C] The cautious rule: a learning agent changes a rate only where the change beats holding across its band
- Decided: --cautious, in learn mode, scores every candidate at three elasticities: the estimate, and the estimate [[RUL-54]] standard error lower and higher, clamped to [[RUL-51]] and [[RUL-52]]. A candidate replaces hold only if it is ahead of hold at the estimate and at both ends of the band; the best such candidate wins, else the day of the week holds ([[CON-11]], [[MOD-08]]). As first built, the rule also asked each day of the week on its own to be worth [[RUL-67]]; [[DEC-43]] took that away, so the minimum applies to the whole plan as in every mode. Each plan record, the request and the log line store all three values and the candidates the band rejected ([[DAT-11]], [[DAT-16]], [[DAT-18]]). Without the option nothing changes: the default and plain learn runs are what they were.
- Replaces: nothing built; it answers the question [[DEC-38]] left open, whether an agent that knows how little it knows keeps more of the gain.
- Commit: abef71f
- Reason: the plain learning agent acted on estimates it should not have trusted: 373 and 418 rate changes against the true arm's 179, with estimates 18 and 5 times what they realised. Measured on seeds 1 to 20 with the template, each arm against the same fixed-rate runs: learn:1.0 cautious +$25,084 a seed, ahead in 20 of 20, 299 changes, estimates 7.7 times the gain, 1,205 candidates rejected at an end of the band; learn:2.0 cautious +$17,618, 20 of 20, 229 changes, 2.4 times, 766 rejected. Against the plain learn arms (+$14,141 and +$16,258) the rule won back most of what a prior of 1.0 lost, 76% of the true arm's +$32,899 instead of 43%, and little of what a prior of 2.0 lost, 54% instead of 49%. The gain sits in the shock plans: in the learn:1.0 cautious arm $487,235 of the $501,683 came from the 103 plans the convention and the new flights raised (the true arm: $632,532 from 97), against $259,736 from 123 such plans without the rule; from a prior of 2.0 the shock plans earned $290,380 with the rule and $294,785 without, and the rule's gain came from cutting the other plans from 291 to 158 while their take rose from $30,370 to $61,983. The band's rejections on seeds 1, 2 and 7 were 151 of 159 at the high end from a prior of 1.0 (raises that lose at the true value) and 65 of 108 at the low end from 2.0 (cuts), where from 2.0 the low end sits near 1.5, at which a 5% cut is close to break-even, so most cuts pass. The minimum applied to each day of the week on its own, which the rule adds to the other modes' plan-level minimum, makes almost no difference: a diagnostic run of the band alone with the plan-level minimum kept gave +$25,076 and +$17,634 a seed on the same seeds, so the band does the work. On seeds 1, 2 and 7 the rule held 294 days of the week that plain mode would have changed from a prior of 1.0 and 393 from 2.0, and switched 5 to a smaller move. It did not stop the agent acting more often than the true arm.
- Evidence: test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held, test_the_cautious_rule_scores_each_candidate_one_standard_error_either_side, test_the_three_values_reach_the_model_request, test_plain_learn_mode_gives_the_same_results_as_before, test_a_cautious_agent_records_the_band_and_what_it_rejected
- Links: [[CON-11]], [[DEC-38]], [[MOD-08]], [[MOD-12]], [[UNK-07]], [[DEC-43]]

### DEC-43 [C] One minimum rule: the cautious rule tests the band alone, and the minimum applies to the plan as in every mode
- Decided: under the cautious rule a candidate replaces hold when it is ahead of hold at the estimate and at both ends of the band ([[CON-11]], [[MOD-08]]); the minimum value at stake ([[RUL-67]]) applies to the whole plan through Entry.queued, as in every mode, so the repository has one minimum rule. The candidates the band rejected are those ahead of hold at the estimate that fell behind it at an end.
- Replaces: the minimum per day of the week that [[DEC-39]] added to the rule, under which a day of the week worth less than $250 on its own held.
- Reason: two minimum rules were one too many, and the second did almost nothing: the diagnostic in [[DEC-39]] had already measured the band alone at +$25,076 and +$17,634 a seed. Measured again as the rule, on seeds 1 to 20 with the template, each arm against the same fixed-rate runs: learn:1.0 cautious +$25,076 a seed, range +$8,406 to +$53,535, ahead in 20 of 20, 299 rate changes, estimates 7.7 times the gain; learn:2.0 cautious +$17,634, range +$5,839 to +$27,585, 20 of 20, 240 changes, 2.5 times. Against the rule as first built (+$25,084 and +$17,618, 299 and 229 changes) the means moved by $8 and $16 a seed and the prior-2.0 arm made 11 more changes, so the band is the rule and the shares of the true arm's gain stay 76% and 54%. The count of candidates rejected at an end rose from 1,205 and 766 to 3,294 and 2,681, because it now counts every candidate ahead of hold at the estimate rather than only those worth $250. The shock plans earned $487,196 from 103 changes from a prior of 1.0 and $292,857 from 72 from a prior of 2.0; the other plans $14,322 from 196 and $59,831 from 168. The default run and the plain learn runs are unchanged.
- Evidence: test_under_the_cautious_rule_a_candidate_that_loses_at_one_end_is_held, test_a_plan_needs_at_least_the_minimum_value_to_enter_the_queue, test_a_cautious_agent_records_the_band_and_what_it_rejected
- Commit: abef71f
- Links: [[DEC-39]], [[CON-11]], [[RUL-67]], [[MOD-08]], [[FRK-05]]

### DEC-44 [C] The request carries a display string in place of every figure, with its direction in words and each range as one phrase, and the prompt tells the model to copy the phrases whole and state only what the entry shows
- Decided: every figure in the model request ([[DAT-16]]) is a display string written by code ([[MOD-11]]) in place of the raw number, which stays in the log line and the stored tables: dollars to the dollar for a rate, a median, a floor, a ceiling or a cost; to the nearest $10 for an estimate; a signed quantity as a phrase with its direction in words and no sign, "14.6% below the median", "up 15.0%", "44 rooms ahead of pace", "$120 less than holding"; rooms to the room; an elasticity with up to two decimals. A range is one phrase in the request, "10.7% to 14.6% below the median", "up 17.0% to 21.6%", "2.5% below to 2.5% above the median", "$220 to $242", the single value when both ends read the same, and the named pair {"lowest", "highest"} in the log line and the stored tables ([[DAT-13]], [[DAT-18]]); a candidate's two band estimates are named by the end of the band they belong to. The default elasticity mode reads "assumed" to the model ([[RUL-75]]) while the command line keeps "true". The system prompt ([[RUL-47]]) tells the model to write as "we", to state only what the entry shows, to make no claim about price sensitivity or risk the entry does not contain, to copy the phrases whole with no sign, direction word or rounding of its own and no end of a range on its own, that "more than holding" may be written once in a sentence that lists several gains, and to write an event's name in lower case inside a sentence. The template writes its reasons from the same phrases, and the audit ([[MOD-22]]) matches them whole within a sentence, reads a range in a reason as its two ends, accepts a bare dollar gain in a sentence that carries "more than holding", and lists every sentence with no figure from the request.
- Replaces: bare numbers in the request, which the model rounded and reformatted as it pleased; a first version of the display strings that carried a sign and sat next to the raw value; two-item lists for ranges, then a named pair for each range in the request, whose ends the model quoted with joining words of its own; the mode name "true"; and a prompt that said "use only numbers that appear in the entry".
- Reason: four live runs of seed 7 with claude-opus-5-5, seven calls each, all seven plans accepted every time. The first, with bare numbers, traced every figure to its request but wrote them its own way ("14.65%", "$8,052.54", "217.09–220.40", "about 12–14%") and added claims the entry does not make, about which gains are most sensitive to the elasticity and about pace supporting a rate. The second, with a signed display string next to each raw value, copied the strings but put a direction word on top of the sign ("-14.6% below the median", "rose +15.0%", "ahead of pace by +44"), and the doubled figures took the input from 20,329 to 37,107 tokens. The third, with the strings alone and the direction in words, copied every phrase whole, no figure outside its request and no sentence without a request figure, event names in lower case, 24,219 input tokens; but it joined the ends of each range with words of its own ("between 14.6% below the median and 10.7% below the median", "up 17.0% to up 21.6%") and wrote "more than holding" after every gain it listed. The fourth, with each range as one phrase and the allowance for "more than holding", copied every range whole, listed a plan's gains by day with the phrase once ("$280 on Tuesday and $60 on Wednesday, $340 more than holding in all"), again with no figure outside its request and no sentence without a request figure, in 21,148 input tokens. The fourth is the recorded run, [[DAT-29]]; the first three were not kept. The default run is unchanged at +$28,818 on seed 7: the decisions do not depend on the reasons.
- Evidence: test_every_figure_in_the_request_is_a_display_string, test_a_signed_quantity_reads_as_a_phrase_with_its_direction_in_words, test_a_range_is_one_phrase_and_the_single_value_when_both_ends_read_the_same, test_the_request_carries_the_elasticity_and_its_digest_changes_with_it, test_a_range_in_a_reason_is_read_as_its_two_ends, test_a_sentence_that_lists_several_gains_may_write_more_than_holding_once, test_the_recorded_live_run_of_seed_7_passes_the_audit, test_the_default_mode_still_gives_28818_on_seed_7
- Links: [[DAT-16]], [[DAT-13]], [[DAT-18]], [[DAT-29]], [[RUL-47]], [[RUL-75]], [[MOD-09]], [[MOD-11]], [[MOD-22]], [[UNK-01]], [[DEC-01]]
## Engineering

### DEC-23 [C] The cache is keyed by seed, day and hotel, and each file records a digest of its request
- Decided: the answer to one hotel's queue on one day is saved at cache/seed<seed>/day<DDD>_<hotel key>.json with the sha256 of the request's sorted-keys JSON ([[DAT-17]]). A rerun reads the cache first; a file whose digest does not match the request raises StaleCache instead of answering the wrong question; a replay reads the cache and never calls the model.
- Replaces: nothing built.
- Reason: one model call per hotel per day, paid once per seed; replaying day 20 makes no model call and prints the same entry; a changed rule or constant changes the request and so cannot reuse a stale answer silently.
- Commit: abef71f
- Evidence: test_ask_calls_the_model_once_and_then_reads_the_cache, test_a_cache_written_for_another_request_is_refused, test_a_replay_never_calls_the_model
- Links: [[MOD-09]], [[DAT-17]]

### DEC-24 [H] Template answers were cached like the model's
- Decided: the template's answers were written to the same cache files as the model's, marked "source": "template", and a client replaced a template-sourced file with the model's answer.
- Replaced by: [[DEC-25]]
- Reason it went: a review found two faults. A live run after a template run stopped with StaleCache as soon as a model decision changed a later day's request, because the template file for that day no longer matched. And --template and --seeds, which pass no client, reused the model's cached answers, so a sweep could mix two policies.
- Commit: abef71f
- Links: [[MOD-09]]

### DEC-25 [C] Only the model's answers are cached; the template is a function of the request
- Decided: without a client the template answers and nothing is written; with a client the model's cached answer is read first. A cache file whose source is not "model" is ignored and overwritten. A replay reads the model's cache when a client is given and uses the template otherwise.
- Replaces: [[DEC-24]]
- Reason: the template is deterministic given the request, so it needs no cache; --template and --seeds now always use it; a live run can follow a template run. The only output change was that template reasons keep an event's name capitalised.
- Commit: abef71f
- Evidence: test_the_template_never_reads_the_models_cache, test_a_template_answer_cached_by_an_older_version_is_ignored_and_replaced, test_replaying_day_20_makes_no_model_call_and_prints_the_same_entries
- Links: [[MOD-09]], [[DAT-17]], [[MOD-12]]

### DEC-27 [H] The modules lived flat at the repository root
- Decided: the eight modules and run.py sat next to each other at the root, with pytest.ini putting the root on the path and requirements.txt listing the dependencies.
- Replaced by: [[DEC-28]]
- Reason it went: it read like a folder of scripts, and the tests ran against whatever was in the working directory rather than an installed package.
- Commit: 15e0215
- Links: [[MOD-12]]

### DEC-28 [C] The code is the package src/hotel_market, with pyproject.toml and a console command
- Decided: a src layout, absolute imports hotel_market.<module>, run.py renamed to cli.py behind the hotel-market command and python -m hotel_market, and pyproject.toml holding the metadata, the dependencies with tested lower bounds, the dev extras and the pytest and ruff settings.
- Replaces: [[DEC-27]]
- Reason: the layout a reader of production code expects; the suite was run against the installed package on numpy 1.26 and pandas 2.2 as well as the current versions, and a seed-7 run from the package reproduced decisions.jsonl byte for byte.
- Commit: 15e0215
- Evidence: test_the_replay_command_prints_day_20s_queue, test_python_m_hotel_market_runs_the_command
- Links: [[MOD-12]], [[MOD-14]]

### DEC-29 [H] A hosted workflow ran the tests on every push
- Decided: a workflow file ran the tests on three Python versions and the linter on every push.
- Replaced by: [[DEC-30]]
- Reason it went: on the private repository the first run sat queued for 15 minutes without a runner and was cancelled; the owner chose not to have hosted CI.
- Commit: 15e0215
- Links: [[MOD-15]]

### DEC-30 [C] No hosted CI; the checks run locally through make and pytest
- Decided: the workflow file is gone; the tests, ruff and the knowledge-graph check run with python -m pytest, ruff check . and ruff format --check ., wrapped by the Makefile. A test marked slow runs 20 seeds and takes about a minute; plain pytest skips it, and pytest --slow, which make test-all runs, includes it.
- Replaces: [[DEC-29]]
- Reason: the owner's choice after the queued run; nothing in the repository depends on a hosted runner.
- Commit: 5cef53e
- Evidence: test_the_checks_run_locally_with_no_hosted_workflow
- Links: [[MOD-15]]

### DEC-31 [H] One agent.py held the planning, the model call and the daily loop
- Decided: candidates, estimates, the request, the cache, the template, the client and the loop were one module of 539 lines.
- Replaced by: [[DEC-32]]
- Reason it went: three jobs in one file, with the dense parts (four parallel dicts feeding the estimate, a string-keyed dict for a flag's numbers, nested request literals) hard to read.
- Commit: abef71f
- Links: [[MOD-10]]

### DEC-32 [C] The agent is three modules: plan.py, model.py and agent.py, with text.py for shared wording
- Decided: plan.py builds candidates, estimates and plans; model.py holds the model call, its cache and the template; agent.py runs the daily loop and gives the advice; text.py holds the wording the template and the reports share. The tests follow the split.
- Replaces: [[DEC-31]]
- Reason: one job per module, named records (StayDate, FlagNumbers, Comparison, SeedResult) instead of dicts and tuples, and the command line split into one function per mode. Verified behaviour-preserving: two seeds' decisions.jsonl, the printed summaries, both replays, the sweep and the diagnostics matched the previous output byte for byte.
- Commit: abef71f
- Evidence: test_estimate_is_expected_contribution_on_the_unsold_rooms
- Links: [[MOD-08]], [[MOD-09]], [[MOD-10]], [[MOD-11]]

### DEC-33 [C] ruff formats the code at 100 columns, and the format check is part of lint
- Decided: ruff format owns the layout; the route table in schedule.py keeps one route per line under a bare fmt: off marker (ruff ignores the marker when text follows it on the line); make lint runs ruff check . and ruff format --check ..
- Replaces: hand formatting at up to 120 columns.
- Reason: one layout with no arguments about style; the only hand work left was 14 lines the formatter could not shorten.
- Commit: 15e0215
- Evidence: test_the_formatter_runs_at_100_columns
- Links: [[MOD-15]]

### DEC-34 [C] The answer schema lists the request's own entry ids and options as enums
- Decided: schema_for(request) builds the structured-output schema with "id" limited to the entry ids and "choice" limited to the plans and "hold" in that request.
- Replaces: a fixed schema that typed id and choice as free strings.
- Reason: with free strings a schema-valid answer such as "Hold" or a reworded plan failed the check and aborted the run with nothing cached; with enums the API cannot return a choice the code would reject. The check of the pairing stays as the backstop.
- Commit: abef71f
- Evidence: test_the_schema_limits_ids_and_choices_to_the_requests_options
- Links: [[MOD-09]], [[DAT-16]], [[UNK-02]]

### DEC-40 [C] The agent reads data only through four interfaces; the simulator is one implementation
- Decided: sources.py ([[MOD-17]]) defines Bookings, RateShops, Schedules and Events ([[DAT-25]]), every method taking the day it is asked on and returning only what was known then. detect, forecast, estimate, plan, model and agent read data through them and import none of the simulator's modules (demand, bookings, shops, schedule, shocks, simulated); tests/test_sources.py reads their imports and fails if one does. The agent's demand model is its own module, forecast.py ([[MOD-18]]), with the same formula as the simulator's demand.py and a test that holds the two equal for the demo market. simulated.py ([[MOD-19]]) implements the four over the Books' daily log, the seeded shops, the schedule and the event records, and deciding() wraps an Agent as the simulator's decide hook. The default mode's elasticity is ORACLE_ELASTICITY ([[RUL-56]]), the simulator's value named for what it is.
- Replaces: [[DEC-26]], and the agent's direct reads of the simulator: detect_numbers(day, books), estimate_elasticity(books, ...), the peak night in demand.py.
- Reason: a repository that can be pointed at a hotel's own data needs one place where the data comes in. With the line drawn, what the agent is allowed to know is the list of methods in sources.py, and what it assumes about the market is world.py and forecast.py. The default run is unchanged: seed 7's decisions file is byte for byte the one before the boundary, and the estimator's inputs are bitwise identical.
- Commit: 35967c8
- Evidence: test_the_agent_reads_only_through_the_interfaces, test_the_forecast_is_the_simulators_demand_for_the_demo_market, test_the_simulated_sources_answer_as_of_the_day, test_the_default_mode_still_gives_28818_on_seed_7
- Links: [[MOD-17]], [[MOD-18]], [[MOD-19]], [[DAT-25]], [[SRC-01]], [[SRC-02]], [[SRC-03]], [[SRC-04]], [[RUL-56]]

### DEC-41 [C] Everything specific to the market is a customer file, and the target is one of its settings
- Decided: customers/demo.toml holds the demo market, read by [[MOD-20]] into a Customer ([[DAT-27]]): the hotels with their rooms, starting rates, air shares, base occupancies, weekday factors and comp sets, each competitor at an offset from the hotel's start rate ([[DAT-04]]); the cost share and the rate floor and ceiling ([[RUL-59]] to [[RUL-61]]); the detect thresholds and the hold period ([[RUL-62]] to [[RUL-66]]); the minimum value at stake ([[RUL-67]]); the booking curve ([[RUL-68]], [[RUL-69]]); and the target the agent scores candidates on, contribution or revenue ([[RUL-58]], [[RUL-70]]). The constants that describe the simulator stay in code: the calendar, ELASTICITY, the noise, the schedule and the shocks. hotel-market --customer FILE names the file and --target overrides its target; the demo file is the default wherever none is given. Every entry, request and log line carries the target when it is revenue, a revenue run keeps its own cache folder ([[DAT-14]], [[DAT-16]], [[DAT-17]], [[DAT-18]]), and a sweep counts its wins and the realised gain in the target ([[DAT-24]]).
- Replaces: the constants HOTELS, HOTEL_ROW, COMP_RATE_OFFSETS, DOW_FACTORS, FLOOR_SHARE, CEILING_SHARE, COST_SHARE, CURVE_DAYS_OUT and CURVE_SHARE in world.py ([[RUL-14]] to [[RUL-18]], [[RUL-23]] to [[RUL-25]]), the thresholds and HOLD_DAYS in detect.py ([[RUL-26]] to [[RUL-30]]) and MIN_VALUE_AT_STAKE in plan.py ([[RUL-40]]); it closes the fork [[FRK-01]].
- Reason: with the boundary drawn ([[DEC-40]]), the market's own numbers were the last thing the agent knew about the demo that was written into code. In a file they are what a hotel would hand over, and the simulator reads the same file to make the market. The default run is unchanged: the demo file reproduces every old constant exactly (the cost share is written as 0.3333333333333333, which reads back as one third), and seed 7's decisions file is byte for byte the one before. The target was the open fork, measured on seeds 1 to 20 with the simulator's own elasticity and the template, each target against the same fixed-rate runs. The contribution target earns +$32,899 of contribution a seed, ahead in 20 of 20, and loses $22,861 of room revenue, with 179 rate changes. The revenue target earns +$211,445 of room revenue a seed, ahead in 20 of 20 and about 1% of the fixed-rate run's revenue, and +$461 of contribution, ahead in 11 of 20, with 659 rate changes; on seed 7, 65 of its 85 changed days of the week are 5% cuts and the raises sit on nights that sell out. With an elasticity of 1.5 a cut sells more than enough rooms to raise revenue, and the rooms it adds cost about as much to service as they bring in, so the two targets pull the rates in opposite directions on this market: contribution gives up revenue for margin, revenue gives up margin for volume. The revenue target's estimates were close, the accepted plans' estimates summing to 0.99 of the realised revenue gain, against 1.04 for the contribution target. Most of the revenue gain sits on the stay dates the new-flights flag covered, 50 to 109 at every hotel, where the agent cut rates: $4,144,589 of the $4,228,903 over the 20 seeds came from the 130 plans whose causes mark them as shock plans, though the cut is the revenue target's answer to any flag, not a reading of the seats.
- Commit: 9d74c0d
- Evidence: test_the_demo_file_describes_the_market_in_claude_md, test_the_revenue_target_scores_candidates_on_the_rate_alone, test_the_command_takes_a_customer_file_and_a_target, test_a_revenue_target_arm_counts_wins_and_earnings_in_revenue, test_the_default_mode_still_gives_28818_on_seed_7
- Links: [[MOD-20]], [[DAT-27]], [[DAT-04]], [[RUL-58]], [[FRK-01]], [[DEC-12]], [[DEC-40]], [[CON-07]], [[MEA-04]]

### DEC-42 [C] The feeds and the agent's output are stored tables keyed by as_of_day, and the agent can run one day at a time against them
- Decided: sql/schema.sql defines seven tables ([[DAT-28]]), daily bookings, rate shops, schedule snapshots and events for the feeds and flags, plans and decisions for the agent, each keyed by as_of_day, in plain SQL with the statements a cloud warehouse would change listed at its head. stored.py ([[MOD-21]]) implements the four interfaces over them and writes a day's rows, deleting the day's rows first. hotel-market run-day --seed S --as-of N plays the simulator to day N with the rate changes the tables hold, writes day N's feeds (and day -1's position when N is 0), gives a fresh agent the hold and the advice the stored decisions left (Agent.resume, [[MOD-10]]), runs it on the tables alone and writes its flags, plans and decisions; running a day twice leaves the tables unchanged, and --from runs a range of days in one pass. hotel-market replay --as-of N rebuilds the day's plans from the tables alone, with the actions the stored decisions record, and checks them against the stored plans. The schedule interface gives the seats as filed by a day and computes the seat change and the seat revision from them ([[DAT-25]]), so that the stored snapshot is seats rather than fractions. DuckDB holds the file; it is an in-process database with no server to run.
- Replaces: nothing built; the simulated sources ([[MOD-19]]) stay as they were, and the default run is unchanged.
- Reason: a real hotel's data arrives a day at a time and lives in tables, not in a simulator's arrays, so this is the shape a deployment would take, with the simulator standing in for the feeds. It is also a check on the boundary ([[DEC-40]]): a 60-day run through the tables writes a decisions file byte for byte the same as the in-memory run's, every stored source answers as the simulated one does, and a past day's plans are rebuilt exactly from the tables. The plans table keeps the exact rates and estimates so that the simulator can be played back and a day checked; the decisions table keeps the decisions.jsonl line as well as its fields. Two measurements shaped the code: inserting rows one statement at a time took 2.5 seconds per 3,000 rows, so a day's rows go in as one frame, and reading the events table once per detect row made a day take 2 seconds, so each source reads a day once. The 60-day run through the tables takes about 6 seconds; one day on its own takes under a second, most of it the simulator's playback. The schema was tested on DuckDB 1.5 and 1.2 and read against the documentation of three warehouses, not run on one ([[UNK-10]]).
- Commit: 6311cb6
- Evidence: test_a_60_day_run_through_the_tables_gives_the_same_decisions_file, test_the_stored_sources_answer_as_the_simulated_ones_do, test_running_a_day_twice_leaves_the_tables_unchanged, test_replaying_a_past_day_reproduces_its_plans_exactly, test_the_schema_is_seven_tables_each_keyed_by_as_of_day
- Links: [[MOD-21]], [[DAT-28]], [[DAT-25]], [[MOD-12]], [[MOD-10]], [[DEC-40]], [[SRC-01]], [[SRC-02]], [[SRC-03]], [[SRC-04]], [[UNK-10]]
