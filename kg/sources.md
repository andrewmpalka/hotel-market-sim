# Sources

The four data feeds a real revenue system would read, and what stands in for
each one here. Each feed has an interface in [[MOD-17]] ([[DAT-25]]), the
agent reads nothing else ([[DEC-40]]), the simulator implements the four in
[[MOD-19]], and [[MOD-21]] implements them over stored tables ([[DAT-28]]),
which is where a real feed would be loaded. Every statement about a real feed
is an assumption: this
repository holds no real data ([[DEC-35]]) and was written without access to
any feed.

### SRC-01 [C] Bookings
- Stand-in: SimulatedBookings in [[MOD-19]], over the Books' daily log ([[DAT-07]]): rooms on the books, rates in force and the record of bookings ([[DAT-26]]), each as of the day asked. The simulator draws every booking from the seed around its own expected demand; there are no reservations, only rooms and revenue per hotel and stay date, once a day.
- Real feed (assumption): a property management system or central reservation system would supply individual reservations with booking date, arrival and departure dates, rate, room type, channel, cancellations and no-shows.
- Stored: StoredBookings in [[MOD-21]] answers the same three methods from the daily_bookings table ([[DAT-28]]): one row per hotel and night in each day's window with the rooms taken that day, the rooms on the books and the rate in force, and day -1 for the opening position.
- To read one: a real feed would be loaded into that table one day at a time, each day's rows counted from the reservations as of that day, and the opening rooms ([[DEC-03]]) would be the bookings already on hand. Nothing on the agent's side would change. The fixed-rate comparison run ([[MOD-12]]) would have no counterpart, since one market cannot be run twice.
- Evidence: test_day_0_starts_with_the_bookings_made_before_the_run, test_decisions_see_the_books_after_that_days_bookings

### SRC-02 [C] Competitor rate shops
- Stand-in: SimulatedRateShops in [[MOD-19]]: each competitor's rate for a stay date as shopped on a day, from one seeded noise array with the scripted shocks applied ([[MOD-05]], [[DAT-06]]), and the log of the medians the simulator used.
- Real feed (assumption): a rate-shopping service would supply, per shop date, hotel, stay date and length of stay, the lowest public rate of each competitor, with gaps where a competitor was sold out or not shopped.
- Stored: StoredRateShops in [[MOD-21]] reads the rate_shops table, one row per shop day, hotel, competitor and night from the shop day to the end of the schedule, and computes the medians as the interface does. The stored shop reaches every night the schedule covers because shock_known ([[MOD-07]]) compares a night's median with the day-0 shop.
- To read one: a real shop would be loaded into that table one shop day at a time. The comp median ([[CON-04]]) and the median-change flag ([[RUL-65]]) would need a rule for missing competitors, which the stand-in never has, and a shop with a shorter horizon than the schedule would need shock_known to compare with the first shop that covered the night rather than the day-0 shop.
- Evidence: test_rates_depend_only_on_the_seed, test_comp_median_moves_only_when_a_shock_becomes_known

### SRC-03 [C] Air schedules
- Stand-in: SimulatedSchedules in [[MOD-19]]: the seat change and the seat revision as filed by a day, from the synthetic schedule [[MOD-01]] builds as known on that day, with the column names of a published schedule data dictionary ([[DAT-01]]) and the two air shocks filed on days 20 and 40.
- Real feed (assumption): a schedule data service would supply periodic snapshots of filed schedules, one row per flight per operating date, with seats by cabin, codeshare markings and service type; revisions would arrive between snapshots on no fixed day.
- Stored: StoredSchedules in [[MOD-21]] reads schedule_snapshots, the seats arriving each day as filed by a day, and the interface computes the seat change and the seat revision from them ([[DAT-25]]).
- To read one: a real snapshot would be counted into that table the way seats_by_day does, dropping codeshares and type U rows and grouping by city, which are the traps a real file holds; a warehouse would keep the flight-level snapshot as well and make the table a view over it. The seat-to-demand link ([[UNK-05]]) is the part a real market would not confirm.
- Evidence: test_normal_day_has_4244_seats, test_summing_by_arrival_station_misses_the_second_airport

### SRC-04 [C] Events
- Stand-in: SimulatedEvents in [[MOD-19]]: the events [[MOD-03]] holds, as announced by a day ([[DAT-05]]). The competitor rate cut is not an event; the agent sees it only through the rate shop.
- Real feed (assumption): a convention bureau calendar or an events data service would supply event names, dates, venues and expected attendance, announced months ahead and sometimes revised. The demand uplift would not be given and would have to be estimated.
- Stored: StoredEvents in [[MOD-21]] reads the events table, where an event has a row for every day from its announcement on, so that a day's rows are the calendar as of that day.
- To read one: a real calendar would be loaded into that table as of each day. The uplift of each Event ([[DAT-05]]) would come from a model of attendance, and the peak night would still be computed ([[DEC-09]]).
- Evidence: test_convention_is_not_known_before_day_10, test_shocks_name_hotels_and_competitors_that_exist
