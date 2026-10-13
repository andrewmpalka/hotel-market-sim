-- The five tables the demo page reads, written by hotel-market demo-data into the
-- same file as the seven stored tables (schema.sql). The page formats and draws
-- these rows and computes nothing, so every figure here is final: code wrote it.
-- Every table but hotels is keyed by as_of_day and hotel, the page's two choices.

-- The hotels of the market, in the customer file's order.
CREATE TABLE IF NOT EXISTS hotels (
    position INTEGER NOT NULL,
    key VARCHAR NOT NULL,              -- the hotel's key in the customer file
    name VARCHAR NOT NULL,
    rooms INTEGER NOT NULL,
    PRIMARY KEY (key)
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

-- One row per stay date in the day's window: the chart's lines and marks.
CREATE TABLE IF NOT EXISTS stay_dates (
    as_of_day INTEGER NOT NULL,
    hotel VARCHAR NOT NULL,
    stay_day INTEGER NOT NULL,
    rate DOUBLE NOT NULL,              -- the hotel's rate in force on the day
    comp_median DOUBLE NOT NULL,       -- the comp set median shopped on the day
    rooms_on_books INTEGER NOT NULL,
    pace DOUBLE NOT NULL,              -- rooms the pace curve expects on the books by now
    flagged BOOLEAN NOT NULL,          -- whether the agent raised a flag covering the date
    causes VARCHAR NOT NULL,           -- the flag's causes, comma-separated; empty when not flagged
    PRIMARY KEY (as_of_day, hotel, stay_day)
);

-- The day's flags for the hotel in the agent's order: the queued plans with the
-- model's or the template's reason, and the flags held by code with their cause.
CREATE TABLE IF NOT EXISTS queue (
    as_of_day INTEGER NOT NULL,
    hotel VARCHAR NOT NULL,
    position INTEGER NOT NULL,
    stays VARCHAR NOT NULL,            -- "stay date 46" or "stay dates 45 to 48"
    causes VARCHAR NOT NULL,
    plan VARCHAR NOT NULL,             -- the changes in words, or hold
    value DOUBLE NOT NULL,             -- the plan's estimated gain over holding
    value_text VARCHAR NOT NULL,       -- the same as the request shows it
    reason VARCHAR NOT NULL,
    reason_source VARCHAR NOT NULL,    -- code, template or model
    queued BOOLEAN NOT NULL,
    outcome VARCHAR NOT NULL,          -- accepted, declined or held
    PRIMARY KEY (as_of_day, hotel, position)
);

-- The scorecard to date: every booking made through the day, over stay dates
-- 0 to 149, for the agent run, the fixed-rate run and their difference.
CREATE TABLE IF NOT EXISTS scorecard (
    as_of_day INTEGER NOT NULL,
    hotel VARCHAR NOT NULL,
    run VARCHAR NOT NULL,              -- agent, fixed or delta
    occupancy DOUBLE NOT NULL,         -- rooms on the books over rooms available
    adr DOUBLE NOT NULL,               -- room revenue over rooms on the books
    revpar DOUBLE NOT NULL,            -- room revenue over rooms available
    room_revenue DOUBLE NOT NULL,
    contribution DOUBLE NOT NULL,      -- room revenue minus the cost of every room sold
    PRIMARY KEY (as_of_day, hotel, run)
);
