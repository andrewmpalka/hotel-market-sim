-- The tables the demo page reads, written by hotel-market demo-data into the
-- same file as the eight stored tables (schema.sql). The page formats and draws
-- these rows and computes nothing, so every figure here is final: code wrote it.
-- Every date reads as a calendar date with its day of the week and the day
-- number in brackets, such as "Thu 18 Feb [45]". A table keyed by as_of_day and
-- hotel answers the page's two choices.

-- The hotels of the market, in the customer file's order, with the rate chart's
-- y axis: 75% to 125% of the start rate.
CREATE TABLE IF NOT EXISTS hotels (
    position INTEGER NOT NULL,
    key VARCHAR NOT NULL,              -- the hotel's key in the customer file
    name VARCHAR NOT NULL,
    rooms INTEGER NOT NULL,
    start_rate DOUBLE NOT NULL,
    rate_axis_low DOUBLE NOT NULL,     -- 75% of the start rate
    rate_axis_high DOUBLE NOT NULL,    -- 125% of the start rate
    PRIMARY KEY (key)
);

-- One row per simulation day: the day as the title shows it, and the window of
-- stay dates the charts span.
CREATE TABLE IF NOT EXISTS days (
    as_of_day INTEGER NOT NULL,
    label VARCHAR NOT NULL,            -- "Thu 14 Jan 2027 [day 10]"
    stay_window VARCHAR NOT NULL,      -- "Thu 14 Jan [10] to Tue 13 Apr [99]"
    PRIMARY KEY (as_of_day)
);

-- What became known on the day, in plain words: an event, a schedule filing, a
-- comp set move, or one row saying nothing new became known.
CREATE TABLE IF NOT EXISTS news (
    as_of_day INTEGER NOT NULL,
    hotel VARCHAR NOT NULL,
    position INTEGER NOT NULL,
    kind VARCHAR NOT NULL,             -- event, schedule, comp set or none
    text VARCHAR NOT NULL,
    PRIMARY KEY (as_of_day, hotel, position)
);

-- One row per stay date in the day's window: the charts' lines, labels and marks.
CREATE TABLE IF NOT EXISTS stay_dates (
    as_of_day INTEGER NOT NULL,
    hotel VARCHAR NOT NULL,
    stay_day INTEGER NOT NULL,
    label VARCHAR NOT NULL,            -- "Thu 18 Feb [45]", the x axis value
    tick BOOLEAN NOT NULL,             -- whether the x axis labels this date (the Mondays)
    rate DOUBLE NOT NULL,              -- the hotel's rate in force on the day
    comp_median DOUBLE NOT NULL,       -- the comp set median shopped on the day
    rooms_on_books INTEGER NOT NULL,
    pace DOUBLE NOT NULL,              -- rooms the pace curve expects on the books by now
    flagged BOOLEAN NOT NULL,          -- whether the agent raised a flag covering the date
    causes VARCHAR NOT NULL,           -- the flag's causes, comma-separated; empty when not flagged
    flag VARCHAR NOT NULL,             -- the flag's id, "45-48"; empty when not flagged
    planned_rate DOUBLE,               -- the rate an accepted plan sets from tomorrow; NULL without one
    PRIMARY KEY (as_of_day, hotel, stay_day)
);

-- The day's flags for the hotel in the agent's order: the queued plans with the
-- model's or the template's reason, and the flags held by code with their cause
-- and the best alternative to holding.
CREATE TABLE IF NOT EXISTS queue (
    as_of_day INTEGER NOT NULL,
    hotel VARCHAR NOT NULL,
    position INTEGER NOT NULL,
    stays VARCHAR NOT NULL,            -- "Thu 18 Feb [45]" or "Thu 18 Feb [45] to Sun 21 Feb [48]"
    causes VARCHAR NOT NULL,
    plan VARCHAR NOT NULL,             -- the changes in words, or hold
    value DOUBLE NOT NULL,             -- the plan's estimated gain over holding
    value_text VARCHAR NOT NULL,       -- the same as the request shows it
    reason VARCHAR NOT NULL,
    reason_source VARCHAR NOT NULL,    -- code, template or model
    queued BOOLEAN NOT NULL,
    outcome VARCHAR NOT NULL,          -- accepted, declined or held
    alternative VARCHAR NOT NULL,      -- held only: the best alternative to holding, in words
    alternative_text VARCHAR NOT NULL, -- held only: how far it fell short of holding or of the minimum
    PRIMARY KEY (as_of_day, hotel, position)
);

-- The scorecard's tiles for the nights already stayed as of the day: one row per
-- measure, for each hotel and for all the hotels together (hotel = all). The
-- figures count every booking for stay dates 0 to the day before. Day 0 has no
-- rows, because no night has been stayed yet.
CREATE TABLE IF NOT EXISTS scorecard (
    as_of_day INTEGER NOT NULL,
    hotel VARCHAR NOT NULL,            -- a hotel's key, or all
    title VARCHAR NOT NULL,            -- the hotel's name, or "All four hotels"
    nights VARCHAR NOT NULL,           -- "Mon 4 Jan [0] to Wed 13 Jan [9]"
    position INTEGER NOT NULL,         -- the tile's place, 0 to 4
    measure VARCHAR NOT NULL,          -- Occupancy, ADR, RevPAR, Room revenue or Contribution
    agent DOUBLE NOT NULL,             -- the agent run's figure
    fixed DOUBLE NOT NULL,             -- the fixed-rate run's figure
    delta DOUBLE NOT NULL,             -- agent minus fixed
    value_text VARCHAR NOT NULL,       -- the agent run's figure as the tile shows it
    delta_text VARCHAR NOT NULL,       -- the change as the tile shows it; "0" when there is none
    PRIMARY KEY (as_of_day, hotel, measure)
);

-- The same tiles once every stay date is complete: every booking through day
-- 149 for stay dates 0 to 149. The same on every day, so there is one row per
-- hotel and measure.
CREATE TABLE IF NOT EXISTS outcome (
    hotel VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    nights VARCHAR NOT NULL,           -- "Mon 4 Jan [0] to Wed 2 Jun [149]"
    position INTEGER NOT NULL,
    measure VARCHAR NOT NULL,
    agent DOUBLE NOT NULL,
    fixed DOUBLE NOT NULL,
    delta DOUBLE NOT NULL,
    value_text VARCHAR NOT NULL,
    delta_text VARCHAR NOT NULL,
    PRIMARY KEY (hotel, measure)
);

-- The contribution difference by stay date once every stay date is complete,
-- for each hotel and for all together: the scorecard's small line.
CREATE TABLE IF NOT EXISTS gains (
    hotel VARCHAR NOT NULL,            -- a hotel's key, or all
    title VARCHAR NOT NULL,
    stay_day INTEGER NOT NULL,
    label VARCHAR NOT NULL,            -- "Thu 18 Feb [45]"
    tick BOOLEAN NOT NULL,             -- whether the x axis labels this date (every fourth Monday)
    agent DOUBLE NOT NULL,             -- the agent run's contribution on the stay date
    fixed DOUBLE NOT NULL,
    difference DOUBLE NOT NULL,        -- agent minus fixed
    PRIMARY KEY (hotel, stay_day)
);
