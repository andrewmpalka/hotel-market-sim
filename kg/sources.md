# Sources

The four data feeds a real revenue system would read, and what stands in for
each one here. Each feed has an interface in [[MOD-17]] ([[DAT-25]]), and the
agent reads nothing else ([[DEC-40]]). The simulator implements the four in
[[MOD-19]], and [[MOD-21]] implements them over stored tables ([[DAT-28]]),
which is where a real feed would be loaded. Every statement about a real
feed is an assumption: this repository holds no real data ([[DEC-35]]) and
was written without access to any feed.

### SRC-01 [C] Bookings
- Stands in: SimulatedBookings in [[MOD-19]], over the Books' daily log ([[DAT-07]]). It gives rooms on the books, rates in force and the booking record ([[DAT-26]]), each as of the day asked.
- Shape: the simulator draws every booking from the seed around its own expected demand. There are no reservations, only rooms and revenue per hotel and stay date, once a day.
- Real feed (assumption): a property management system or central reservation system would supply individual reservations. Each would carry booking date, arrival and departure dates, rate, room type, channel, cancellations and no-shows.
- Stored: StoredBookings in [[MOD-21]] answers the same three methods from the daily_bookings table ([[DAT-28]]). It has one row per hotel and night in each day's window, and day -1 for the opening position.
- To read one: a real feed would be loaded into that table one day at a time. Each day's rows would be counted from the reservations as of that day. The opening rooms ([[DEC-03]]) would be the bookings already on hand.
- Limit: nothing on the agent's side would change. The fixed-rate comparison run ([[MOD-12]]) would have no counterpart, since one market cannot be run twice.
- Evidence: test_the_simulated_sources_answer_as_of_the_day, test_the_stored_sources_answer_as_the_simulated_ones_do, test_decisions_see_the_books_after_that_days_bookings

### SRC-02 [C] Competitor rate shops
- Stands in: SimulatedRateShops in [[MOD-19]]. It gives each competitor's rate for a stay date as shopped on a day ([[MOD-05]], [[DAT-06]]). Each rate is seeded noise, fresh each shop day, with the shocks applied ([[DEC-62]]).
- Medians: it also keeps the log of the medians the simulator used.
- Real feed (assumption): a rate-shopping service would supply each competitor's lowest public rate per shop date, hotel, stay date and length of stay. There would be gaps where a competitor was sold out or not shopped.
- Stored: StoredRateShops in [[MOD-21]] reads the rate_shops table and computes the medians as the interface does. The table has one row per shop day, hotel, competitor and night, from the shop day to the schedule's end.
- Reach: the stored shop reaches every night the schedule covers. shock_known ([[MOD-07]]) compares a night's median with its starting level, the comp set's base-rate median, beyond the median threshold ([[RUL-65]]).
- To read one: a real shop would be loaded into that table one shop day at a time. The comp median ([[CON-04]]) and the median-change flag ([[RUL-65]]) would need a rule for missing competitors. The stand-in never has any.
- Horizon: a shop with a shorter horizon than the schedule would need a rule for the nights beyond it, because the detect numbers read every night's median each day.
- Evidence: test_the_simulated_sources_answer_as_of_the_day, test_the_stored_sources_answer_as_the_simulated_ones_do, test_comp_median_moves_every_day_and_beyond_the_threshold_only_on_a_shock

### SRC-03 [C] Air schedules
- Stands in: SimulatedSchedules in [[MOD-19]]. It gives the seats as filed by a day and the passengers at each flight's load factor ([[DEC-63]]), from the schedule [[MOD-01]] builds for that day ([[DAT-01]], [[SHK-02]], [[SHK-04]]).
- Real feed (assumption): a schedule service would supply periodic snapshots of filed schedules, one row per flight and date. Each row would carry seats by cabin, codeshare markings and service type. Revisions would arrive on no fixed day.
- Stored: StoredSchedules in [[MOD-21]] reads schedule_snapshots, the seats and passengers arriving each day as filed by a day. The interface computes the passenger change and revision from them ([[DAT-25]]).
- To read one: a real snapshot would be counted into that table the way seats_by_day and passengers_by_day do. That means dropping codeshares and type U rows and grouping by city, the traps a real file holds.
- Warehouse: a warehouse would keep the flight-level snapshot as well and make the table a view over it. The seat-to-demand link ([[UNK-05]]) is the part a real market would not confirm.
- Evidence: test_the_simulated_sources_answer_as_of_the_day, test_the_stored_sources_answer_as_the_simulated_ones_do, test_known_passenger_revision_matches_the_schedule

### SRC-04 [C] Events
- Stands in: SimulatedEvents in [[MOD-19]]: the events [[MOD-03]] holds, as announced by a day ([[DAT-05]]). The competitor rate cut is not an event; the agent sees it only through the rate shop.
- Real feed (assumption): a convention bureau or an events data service would supply event names, dates, venues and expected attendance. Events are announced months ahead and sometimes revised, and the uplift would have to be estimated.
- Stored: StoredEvents in [[MOD-21]] reads the events table. An event has a row for every day from its announcement on. A day's rows are therefore the calendar as of that day.
- To read one: a real calendar would be loaded into that table as of each day. The uplift of each Event ([[DAT-05]]) would come from a model of attendance. The peak night would still be computed ([[DEC-09]]).
- Evidence: test_the_simulated_sources_answer_as_of_the_day, test_the_stored_sources_answer_as_the_simulated_ones_do, test_convention_is_not_known_before_day_10
