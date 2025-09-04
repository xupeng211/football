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

-- Data sources table
CREATE TABLE IF NOT EXISTS data_sources (
    id TEXT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    source_type VARCHAR(30) NOT NULL,
    base_url TEXT,
    api_key_required BOOLEAN DEFAULT false,
    rate_limit_per_minute INTEGER DEFAULT 60,
    reliability_score DECIMAL(3,2) DEFAULT 0.8,
    is_active BOOLEAN DEFAULT true,
    headers_template TEXT,
    auth_method VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data collection logs table
CREATE TABLE IF NOT EXISTS data_collection_logs (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES data_sources(id),
    task_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    records_fetched INTEGER DEFAULT 0,
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    api_response_time_ms INTEGER DEFAULT 0,
    total_execution_time_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
CREATE INDEX IF NOT EXISTS idx_data_sources_name ON data_sources(name);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_source ON data_collection_logs(source_id);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_status ON data_collection_logs(status);
CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id); 