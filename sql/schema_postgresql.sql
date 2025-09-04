-- PostgreSQL Schema for Football Prediction System
-- ===================================================

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    external_api_id INTEGER UNIQUE,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(50),
    tla VARCHAR(3),
    code VARCHAR(10) UNIQUE,
    founded INTEGER,
    venue VARCHAR(100),
    website VARCHAR(200),
    league_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    external_api_id INTEGER UNIQUE,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    match_date TIMESTAMP NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status VARCHAR(20),
    competition_id INTEGER,
    season_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id)
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL,
    predicted_home_score REAL,
    predicted_away_score REAL,
    predicted_winner VARCHAR(10),
    confidence_score REAL,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_teams_external_api_id ON teams(external_api_id);
CREATE INDEX IF NOT EXISTS idx_matches_external_api_id ON matches(external_api_id);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id); 