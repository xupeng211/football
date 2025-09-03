-- ===========================================
-- 🏆 Football Prediction System - SQLite Schema
-- ===========================================
-- 实际使用的数据库架构（基于现有数据结构）

-- 数据源表（用于跟踪不同的数据提供商）
CREATE TABLE IF NOT EXISTS data_sources (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    url TEXT,
    api_key_required BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 国家表
CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    code TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 联赛表
CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY,
    name TEXT,
    country_id INTEGER,
    external_api_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

-- 球队表（实际使用的结构）
CREATE TABLE IF NOT EXISTS real_teams (
    id INTEGER PRIMARY KEY,
    api_id INTEGER UNIQUE,
    name TEXT NOT NULL,
    short_name TEXT,
    crest TEXT,
    founded INTEGER,
    venue TEXT,
    league_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 比赛表（实际使用的结构）  
CREATE TABLE IF NOT EXISTS real_matches (
    id INTEGER PRIMARY KEY,
    api_id INTEGER UNIQUE,
    league_id INTEGER,
    league_name TEXT,
    season TEXT,
    matchday INTEGER,
    status TEXT,
    utc_date TEXT,
    home_team_id INTEGER,
    home_team_name TEXT,
    away_team_id INTEGER, 
    away_team_name TEXT,
    home_score INTEGER,
    away_score INTEGER,
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据采集日志表
CREATE TABLE IF NOT EXISTS collection_logs (
    id INTEGER PRIMARY KEY,
    source TEXT,
    operation TEXT,
    records_processed INTEGER,
    status TEXT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 新设计的表（用于未来扩展）
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    external_api_id INTEGER UNIQUE,
    name TEXT NOT NULL,
    short_name TEXT,
    league_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,
    external_api_id INTEGER UNIQUE,
    home_team_id INTEGER,
    away_team_id INTEGER,
    match_date TEXT,
    status TEXT,
    home_score INTEGER,
    away_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS data_collection_logs (
    id INTEGER PRIMARY KEY,
    source_name TEXT,
    operation_type TEXT,
    records_affected INTEGER,
    status TEXT,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_real_matches_api_id ON real_matches(api_id);
CREATE INDEX IF NOT EXISTS idx_real_matches_date ON real_matches(utc_date);
CREATE INDEX IF NOT EXISTS idx_real_matches_teams ON real_matches(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_real_teams_api_id ON real_teams(api_id);

-- 触发器：自动更新 updated_at
CREATE TRIGGER IF NOT EXISTS teams_updated_at 
    AFTER UPDATE ON teams
BEGIN
    UPDATE teams SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 