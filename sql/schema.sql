-- Football Prediction System Database Schema
-- PostgreSQL compatible

-- 球队表
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 比赛表
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    home INTEGER NOT NULL REFERENCES teams(id),
    away INTEGER NOT NULL REFERENCES teams(id),
    home_goals INTEGER,
    away_goals INTEGER,
    result CHAR(1) CHECK (result IN ('H', 'D', 'A')), -- Home/Draw/Away
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, home, away)
);

-- 赔率原始数据表
CREATE TABLE IF NOT EXISTS odds_raw (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    h DECIMAL(5,2) NOT NULL, -- 主胜赔率
    d DECIMAL(5,2) NOT NULL, -- 平局赔率
    a DECIMAL(5,2) NOT NULL, -- 客胜赔率
    provider VARCHAR(50) NOT NULL DEFAULT 'unknown',
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, provider, ts)
);

-- 特征数据表
CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    payload_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id)
);

-- 模型表
CREATE TABLE IF NOT EXISTS models (
    id SERIAL PRIMARY KEY,
    version VARCHAR(100) NOT NULL UNIQUE,
    path VARCHAR(255) NOT NULL,
    metrics_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 预测结果表
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    model_id INTEGER NOT NULL REFERENCES models(id),
    p_h DECIMAL(5,4) NOT NULL, -- 主胜概率
    p_d DECIMAL(5,4) NOT NULL, -- 平局概率
    p_a DECIMAL(5,4) NOT NULL, -- 客胜概率
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, model_id),
    CHECK (p_h >= 0 AND p_h <= 1),
    CHECK (p_d >= 0 AND p_d <= 1),
    CHECK (p_a >= 0 AND p_a <= 1),
    CHECK (ABS((p_h + p_d + p_a) - 1.0) < 0.001) -- 概率和为1
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date);
CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(home, away);
CREATE INDEX IF NOT EXISTS idx_odds_match_id ON odds_raw(match_id);
CREATE INDEX IF NOT EXISTS idx_features_match_id ON features(match_id);
CREATE INDEX IF NOT EXISTS idx_predictions_match_model ON predictions(match_id, model_id);
CREATE INDEX IF NOT EXISTS idx_models_created_at ON models(created_at);

-- 插入一些示例球队数据
INSERT INTO teams (name) VALUES
    ('Arsenal'), ('Chelsea'), ('Liverpool'), ('Manchester City'),
    ('Manchester United'), ('Tottenham'), ('Barcelona'), ('Real Madrid'),
    ('Bayern Munich'), ('Juventus')
ON CONFLICT (name) DO NOTHING;
