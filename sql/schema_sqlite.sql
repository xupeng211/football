-- SQLite Schema for Football Prediction System
-- Converted from PostgreSQL schema for compatibility

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_api_id INTEGER UNIQUE,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    match_date TIMESTAMP NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled',
    season VARCHAR(10),
    matchday INTEGER,
    competition VARCHAR(50),
    venue VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id)
);

-- Data collection logs table
CREATE TABLE IF NOT EXISTS data_collection_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source VARCHAR(50) NOT NULL,
    collection_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    records_collected INTEGER DEFAULT 0,
    error_message TEXT,
    api_response_time_ms INTEGER,
    total_execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches(home_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches(away_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_status ON data_collection_logs(status);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_created_at ON data_collection_logs(created_at); 