# The air schedule feed as this repository models it

The simulator reads one air schedule feed, and every number in it is made up. The feed is a
table with one row per flight per operating date. A row names the operating date, the flight
number, the marketing carrier that sells the flight and the operating carrier that flies it.
With them go a codeshare flag with the partner's flight in a text field, a wet-lease flag, the
service type, the effective and discontinue dates of the filing and seven day-of-week flags. The
departure and arrival stations with their country, state and city codes, the local departure
time, the equipment subtype code, the seats in three cabins and the distance complete the row.
The column names follow Cirium's published schedule data dictionary, so the code reads data
shaped like a real feed. The repository holds no Cirium data and has no affiliation with Cirium.
The row carries a departure time and no arrival time, which is a limit of this model and not of
a feed, because an airport hotel's demand turns on the arrival hour; FRK-10 in the graph holds
that column.

The simulator uses a small part of the table. It groups rows by arrival city, because the city
code covers both of the city's airports. Of those rows it keeps the ones whose service type is
scheduled passenger service and drops the ones flagged as codeshares. It adds the three cabins
into one seat count and sums that count by operating date. Those daily totals are the arriving
seats. The seats become arriving passengers at a load factor: a flight that flew before the run
fills 80% of its seats, and a flight the airline adds opens at 60% on its first operating day
and fills to 85% over 90 days, linear between, so a filing's passengers arrive more slowly than
its seats. A suspended flight keeps its load factor when it resumes. The daily passengers are
what the demand rule and the agent's detector read, and the stored snapshot keeps the seats
beside them. The marketing and operating carriers tell
the reader who sells and who flies, and on an operating row a differing pair is a regional
airline flying under capacity purchase. The wet-lease flag is false on every row, because a wet
lease is a separate arrangement that no route here uses.

A filed flight has an "as of" day. The airline files a change on a simulation day, and from that
day the schedule includes it. A hotel knows nothing of a flight before the filing, so every
schedule lookup takes the day it is made on and returns the table as it was known then. The
function build_schedule takes that day, and seats_by_day and passengers_by_day count the table
it returns. The detector reads two numbers from the passengers. The passenger change compares
the known schedule with the schedule before any filing. The passenger revision is the same
comparison against the schedule known the day before, and that is the number that flags,
because a filing moves it once on the day it arrives and then leaves it at zero. The passenger
change stays raised for as long as the flights stay, and a detector that flagged on it would
flag the same dates every day.

There are several ways to miscount the seats in a feed like this one, and each has a test that
fails when the code makes the mistake. A codeshare row repeats the seats of the operating
carrier's flight under the partner's flight number, so counting both rows doubles those seats.
The test test_normal_day_has_4244_seats pins the daily total with the codeshare rows dropped. A
bus sold under a flight number appears with service type U, and counting it adds fifty seats
that arrive by road. The test test_summing_with_type_u_rows_counts_the_bus shows the count with
those rows in. The city's second airport takes some arrivals, and summing by arrival station
instead of by city loses them, as test_summing_by_arrival_station_misses_the_second_airport
shows. An equipment change moves the seats on a route while the flight count stays the same, so
a reader that counts flights misses it. The test
test_an_equipment_change_moves_the_seats_and_not_the_flight_count holds the upgauge to three
flights and 270 more seats a day. A frequency change does the opposite and changes the number of
flights, which the test test_a_frequency_change_sets_the_daily_flights covers. A time change
moves departures and no seat, which test_a_time_change_moves_departures_and_no_seat holds. The
regional operating carrier is not a wet lease, and
test_a_regional_operating_carrier_is_not_a_wet_lease pins that.

A real feed also revises every week, and most revisions change nothing a hotel should act on,
which is what the churn stands for. With it on, the airline files an equipment swap of two to
three weeks and a departure-time change for a fortnight each week, drawn from the seed, and each
stays under the five per cent threshold the detector uses, because a day moves at most 96 seats,
77 passengers at the mature load factor, against a threshold of 212 seats. The churn stays
under the threshold by construction, so the absence of seat flags proves nothing. The finding
is that a filing as such never reaches the detector, which keys on the day-over-day passenger
revision. The test
test_the_churn_files_weekly_revisions_below_the_threshold holds the revisions under the
threshold, and test_a_detector_that_fires_on_any_revision_is_caught_by_the_churn pins the
finding by holding the flags with a seat cause to the same two days with the churn as without
it. On seeds 1 to 20 the churn added 160 filing days and raised no seat flag, which the table
under "The air schedule's filings" in docs/results.md records.