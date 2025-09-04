-- SQLite Schema for Football Prediction System
-- Converted from PostgreSQL schema for compatibility

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id TEXT PRIMARY KEY,
    external_api_id INTEGER UNIQUE,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(50),
    tla VARCHAR(3),
    code VARCHAR(10) UNIQUE,
    founded INTEGER,
    venue VARCHAR(100),
    website VARCHAR(200),
    league_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id TEXT PRIMARY KEY,
    external_api_id INTEGER UNIQUE,
    home_team_id TEXT NOT NULL,
    away_team_id TEXT NOT NULL,
    match_date TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled',
    season VARCHAR(10),
    matchday INTEGER,
    competition VARCHAR(50),
    venue VARCHAR(100),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
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
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches(home_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches(away_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_data_sources_name ON data_sources(name);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_source ON data_collection_logs(source_id);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_status ON data_collection_logs(status);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_created_at ON data_collection_logs(created_at); 