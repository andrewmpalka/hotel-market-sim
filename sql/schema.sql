-- The tables the daily command writes and the stored sources read.
--
-- Every table but the last is keyed by as_of_day, the simulation day a row was
-- known on, and as_of_tick, the tick of that day, so that a query as of a
-- moment sees only what was known then. On the daily clock every tick is 1.
-- The first four tables are the feeds: a day's bookings, rate shops, schedule
-- and known events, one snapshot per tick. The next three are what the agent made of them: its flags,
-- the plans it scored and the decisions it recorded, each decision with the
-- request the model saw and its answer. The last, outcomes, holds what each
-- accepted plan earned on each night once that night has passed, keyed by the
-- day the plan was accepted. Day -1 holds the position before the first day:
-- the rooms already on the books, the first rate shop and the first schedule.
--
-- Plain SQL, written so that a cloud warehouse would accept it with few
-- changes. What would need to change:
--   * The type names. DOUBLE is FLOAT64 in BigQuery and DOUBLE PRECISION in
--     Redshift, and BigQuery spells INTEGER, VARCHAR and BOOLEAN as INT64,
--     STRING and BOOL.
--   * PRIMARY KEY. DuckDB enforces it. BigQuery accepts it only with NOT
--     ENFORCED after it, and Snowflake and Redshift accept it without
--     enforcing it, so the daily command's delete-then-insert is what keeps a
--     day's rows unique there.
--   * The columns holding JSON text (rates, estimates, new_rates, record,
--     request and answer) are VARCHAR.
--     A warehouse with a JSON type (BigQuery JSON, Snowflake VARIANT,
--     Redshift SUPER) could type them.
--   * The transaction around a day's writes. DuckDB, Snowflake and Redshift
--     take BEGIN and COMMIT. BigQuery takes them only inside a script.
-- Nothing else: CREATE TABLE IF NOT EXISTS is accepted by all four, and there
-- are no sequences, no engine-specific types and no procedures.

-- One row per hotel and night in the day's window, read after that day's
-- bookings. On day -1 the rows are the opening position on every night of
-- the horizon, and rooms_taken is everything booked before the run.
CREATE TABLE IF NOT EXISTS daily_bookings (
    as_of_day INTEGER NOT NULL,
    as_of_tick INTEGER NOT NULL,       -- the tick of the day; 1 with one tick a day
    hotel VARCHAR NOT NULL,            -- the hotel's key in the customer file
    stay_day INTEGER NOT NULL,         -- the night
    rooms_taken INTEGER NOT NULL,      -- rooms booked at that tick (that day, with one tick)
    rooms_on_books INTEGER NOT NULL,   -- rooms on the books after that tick's bookings
    rate DOUBLE NOT NULL,              -- the hotel's rate in force at that tick
    PRIMARY KEY (as_of_day, as_of_tick, hotel, stay_day)
);

-- One row per hotel, competitor and night shopped on the day. A shop covers
-- every night from the shop day to the end of the schedule.
CREATE TABLE IF NOT EXISTS rate_shops (
    as_of_day INTEGER NOT NULL,        -- the shop day
    as_of_tick INTEGER NOT NULL,       -- the tick; before the shop lands it holds the day before's
    hotel VARCHAR NOT NULL,            -- the hotel whose comp set was shopped
    stay_day INTEGER NOT NULL,
    competitor VARCHAR NOT NULL,
    rate DOUBLE NOT NULL,
    PRIMARY KEY (as_of_day, as_of_tick, hotel, stay_day, competitor)
);

-- The schedule as filed by the day, counted to arriving seats per day the way
-- seats_by_day counts them: scheduled passenger flights only, codeshares
-- dropped, both of the city's airports. The passengers are the seats at each
-- flight's load factor, as passengers_by_day counts them, and they are what
-- the demand rule and the agent read. A warehouse fed by a schedule service
-- would keep the flight-level snapshot as well and make this a view over it.
CREATE TABLE IF NOT EXISTS schedule_snapshots (
    as_of_day INTEGER NOT NULL,        -- the day the schedule was read
    as_of_tick INTEGER NOT NULL,       -- the tick; before the filing lands it holds the day before's
    stay_day INTEGER NOT NULL,         -- the day the seats arrive
    seats INTEGER NOT NULL,
    passengers DOUBLE NOT NULL,        -- the seats at each flight's load factor
    PRIMARY KEY (as_of_day, as_of_tick, stay_day)
);

-- The events known on the day: an event has a row for every day from its
-- announcement on, so that a day's rows are the whole calendar as of that day.
CREATE TABLE IF NOT EXISTS events (
    as_of_day INTEGER NOT NULL,
    as_of_tick INTEGER NOT NULL,       -- the tick; before the events land it holds the day before's
    name VARCHAR NOT NULL,
    known_day INTEGER NOT NULL,        -- the day the event was announced
    start_day INTEGER NOT NULL,        -- first night affected
    end_day INTEGER NOT NULL,          -- last night affected
    hotels VARCHAR NOT NULL,           -- keys of the hotels whose demand rises, comma-separated
    uplift DOUBLE NOT NULL,            -- 0.35 means demand is 35% higher
    comp_rate_raise DOUBLE NOT NULL,   -- 0.15 means those hotels' competitors charge 15% more
    PRIMARY KEY (as_of_day, as_of_tick, name)
);

-- The agent's flags for the day: consecutive nights of a hotel with the same
-- causes make one flag. The agent's three tables also carry as_of_tick, the
-- tick of the day the row was made on, which is 1 on the daily clock.
CREATE TABLE IF NOT EXISTS flags (
    as_of_day INTEGER NOT NULL,
    as_of_tick INTEGER NOT NULL,       -- the tick of the day; 1 with one tick a day
    hotel VARCHAR NOT NULL,
    first_stay INTEGER NOT NULL,
    last_stay INTEGER NOT NULL,
    causes VARCHAR NOT NULL,           -- comma-separated, as detect.py names them
    PRIMARY KEY (as_of_day, as_of_tick, hotel, first_stay, last_stay)
);

-- Every candidate the agent scored: one row per flag, day of the week and
-- candidate, with the exact rates and estimates, so that a day's plans can be
-- rebuilt and checked.
CREATE TABLE IF NOT EXISTS plans (
    as_of_day INTEGER NOT NULL,
    as_of_tick INTEGER NOT NULL,
    hotel VARCHAR NOT NULL,
    first_stay INTEGER NOT NULL,
    last_stay INTEGER NOT NULL,
    weekday INTEGER NOT NULL,          -- Monday is 0
    candidate VARCHAR NOT NULL,        -- hold, raise 5%, raise 10%, lower 5%, lower halfway to the new median
    rates VARCHAR NOT NULL,            -- JSON: the candidate's rate by night
    estimates VARCHAR NOT NULL,        -- JSON: the candidate's estimate by night, summing to estimate
    estimate DOUBLE NOT NULL,          -- estimated contribution (or room revenue) on the unsold rooms
    versus_hold DOUBLE NOT NULL,       -- the estimate minus hold's
    band_low DOUBLE,                   -- cautious rule only: the estimate at the band's low elasticity
    band_high DOUBLE,                  -- and at its high one
    is_best BOOLEAN NOT NULL,          -- the candidate the plan takes for this day of the week
    PRIMARY KEY (as_of_day, as_of_tick, hotel, first_stay, last_stay, weekday, candidate)
);

-- One row per entry and advice of the day, in the order of the decisions
-- file. The record column holds the file's line.
CREATE TABLE IF NOT EXISTS decisions (
    as_of_day INTEGER NOT NULL,
    as_of_tick INTEGER NOT NULL,
    position INTEGER NOT NULL,         -- the row's place in the tick's log: entries first, then advice
    hotel VARCHAR NOT NULL,
    first_stay INTEGER NOT NULL,
    last_stay INTEGER NOT NULL,
    causes VARCHAR NOT NULL,
    plan VARCHAR,                      -- the changes in words; NULL when nothing beat holding
    value_at_stake DOUBLE,             -- NULL for advice
    queued BOOLEAN NOT NULL,
    action VARCHAR NOT NULL,           -- the plan, hold, or the minimum-stay advice
    reason VARCHAR NOT NULL,
    reason_source VARCHAR NOT NULL,    -- code, template or model
    elasticity DOUBLE,                 -- the elasticity the estimates assumed; NULL for advice
    elasticity_mode VARCHAR,           -- true, fixed or learn
    new_rates VARCHAR,                 -- JSON: the accepted rate by night, rounded (plans has the exact rates)
    simulated BOOLEAN NOT NULL,        -- FALSE for advice the simulator cannot test
    event VARCHAR,                     -- advice only
    record VARCHAR NOT NULL,           -- the decisions.jsonl line
    request_digest VARCHAR,            -- queued entries only: the sha256 of the request's sorted-keys JSON
    prompt_digest VARCHAR,             -- the sha256 of the system prompt the model answered under; NULL for the template or an older record
    model VARCHAR,                     -- the model asked, from the cache record; NULL for the template or an uncached client
    request VARCHAR,                   -- JSON: the request the hotel's queue was asked with, every figure a display string
    answer VARCHAR,                    -- JSON: the decisions answered, one per entry of the request
    PRIMARY KEY (as_of_day, as_of_tick, position)
);

-- The outcome of each accepted plan on each night it changed, written by
-- run-day once the night has passed: the rooms sold and the room revenue over
-- every booking day, the plan's estimate for the night on the rooms then
-- unsold, and what the rooms sold after the decision earned in the same
-- measure. Keyed by the day the plan was accepted, so the plan is one join
-- away, and complete only for the nights up to the last day run.
CREATE TABLE IF NOT EXISTS outcomes (
    decision_day INTEGER NOT NULL,     -- the day the plan was accepted
    hotel VARCHAR NOT NULL,
    stay_day INTEGER NOT NULL,         -- the night, which has passed
    rooms_sold INTEGER NOT NULL,       -- on the books at the end of the night
    room_revenue DOUBLE NOT NULL,      -- over every booking day of the night
    estimated DOUBLE NOT NULL,         -- the plan's estimate for the night: contribution, or room revenue under that target
    realised DOUBLE NOT NULL,          -- the same measure on the rooms sold after the decision day
    PRIMARY KEY (decision_day, hotel, stay_day)
);
