-- matches Table
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    home_team VARCHAR(255) NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    result VARCHAR(50)
);

-- odds Table
CREATE TABLE IF NOT EXISTS odds (
    id SERIAL PRIMARY KEY,
    match_id INT REFERENCES matches(id),
    bookmaker VARCHAR(255) NOT NULL,
    home_odds FLOAT,
    draw_odds FLOAT,
    away_odds FLOAT
);


-- Create a unique index to prevent duplicate odds for the same match and bookmaker
CREATE UNIQUE INDEX IF NOT EXISTS idx_odds_match_book ON odds(match_id, bookmaker);

-- Insert sample matches to satisfy foreign key constraints for odds_sample.json
INSERT INTO matches (id, date, home_team, away_team, result) VALUES
(1001, '2025-08-24 12:00:00', 'Team A', 'Team B', '3-1'),
(1002, '2025-08-24 15:00:00', 'Team C', 'Team D', '2-2')
ON CONFLICT (id) DO NOTHING;

-- Create a unique index on matches to support ON CONFLICT
CREATE UNIQUE INDEX IF NOT EXISTS idx_matches_id ON matches(id);

-- features Table (recreated with expanded columns)
DROP TABLE IF EXISTS features CASCADE;
CREATE TABLE features (
    match_id INT PRIMARY KEY REFERENCES matches(id),
    -- Base Probability Features
    implied_prob_home FLOAT NOT NULL,
    implied_prob_draw FLOAT NOT NULL,
    implied_prob_away FLOAT NOT NULL,
    bookie_margin FLOAT NOT NULL,
    -- Derived Odds Features
    odds_spread_home FLOAT NOT NULL,
    fav_flag INT NOT NULL, -- 1: home, 0: draw, -1: away
    log_home FLOAT NOT NULL,
    log_away FLOAT NOT NULL,
    odds_ratio FLOAT NOT NULL,
    prob_diff FLOAT NOT NULL,
    -- Additional Features
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



