-- =========================================
-- 🏆 Football Data Platform Schema v1.0
-- =========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================
-- 🏠 Teams & Organizations
-- =========================================

-- 国家表
CREATE TABLE countries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(3) NOT NULL UNIQUE, -- ISO 3166-1 alpha-3
    fifa_code VARCHAR(3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 联赛表
CREATE TABLE leagues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(20),
    country_id UUID REFERENCES countries(id),
    level INTEGER DEFAULT 1, -- 联赛级别 (1=顶级, 2=次级)
    season_format VARCHAR(20) DEFAULT 'autumn_spring', -- 赛季格式
    external_api_id INTEGER, -- 外部API的ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, country_id)
);

-- 球队表
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(20),
    country_id UUID REFERENCES countries(id),
    league_id UUID REFERENCES leagues(id),
    founded_year INTEGER,
    venue VARCHAR(100),
    external_api_id INTEGER UNIQUE, -- 外部API的ID
    
    -- 当前统计数据 (缓存字段，定期更新)
    current_season VARCHAR(10),
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    goals_scored INTEGER DEFAULT 0,
    goals_conceded INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, league_id)
);

-- =========================================
-- ⚽ 比赛数据
-- =========================================

-- 赛季表
CREATE TABLE seasons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    league_id UUID REFERENCES leagues(id),
    name VARCHAR(20) NOT NULL, -- e.g., "2023-24"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    external_api_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(league_id, name)
);

-- 比赛表 - 核心数据
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    season_id UUID REFERENCES seasons(id),
    home_team_id UUID REFERENCES teams(id),
    away_team_id UUID REFERENCES teams(id),
    
    -- 比赛基本信息
    match_date TIMESTAMP WITH TIME ZONE NOT NULL,
    venue VARCHAR(100),
    matchday INTEGER, -- 第几轮比赛
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, in_progress, finished, postponed, cancelled
    external_api_id INTEGER UNIQUE,
    
    -- 比赛结果
    home_score INTEGER,
    away_score INTEGER,
    result CHAR(1), -- H, D, A
    
    -- 半场数据
    home_score_ht INTEGER,
    away_score_ht INTEGER,
    
    -- 比赛统计 (可扩展)
    home_possession DECIMAL(5,2),
    away_possession DECIMAL(5,2),
    home_shots INTEGER,
    away_shots INTEGER,
    home_shots_on_target INTEGER,
    away_shots_on_target INTEGER,
    home_corners INTEGER,
    away_corners INTEGER,
    home_fouls INTEGER,
    away_fouls INTEGER,
    home_yellow_cards INTEGER,
    away_yellow_cards INTEGER,
    home_red_cards INTEGER,
    away_red_cards INTEGER,
    
    -- 数据质量标记
    data_quality_score DECIMAL(3,2) DEFAULT 1.0, -- 0-1的数据质量评分
    is_verified BOOLEAN DEFAULT false,
    source_reliability VARCHAR(20) DEFAULT 'unknown',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_score CHECK (
        (home_score IS NULL AND away_score IS NULL) OR 
        (home_score IS NOT NULL AND away_score IS NOT NULL)
    ),
    CONSTRAINT valid_possession CHECK (
        (home_possession IS NULL AND away_possession IS NULL) OR
        (ABS(home_possession + away_possession - 100) < 1)
    )
);

-- =========================================
-- 💰 赔率数据
-- =========================================

-- 博彩公司表
CREATE TABLE bookmakers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    country_id UUID REFERENCES countries(id),
    is_active BOOLEAN DEFAULT true,
    reliability_score DECIMAL(3,2) DEFAULT 0.8, -- 可靠性评分
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 赔率历史表
CREATE TABLE odds_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id),
    bookmaker_id UUID REFERENCES bookmakers(id),
    
    -- 赔率数据
    home_odds DECIMAL(6,3) NOT NULL,
    draw_odds DECIMAL(6,3) NOT NULL,
    away_odds DECIMAL(6,3) NOT NULL,
    
    -- 时间戳
    odds_time TIMESTAMP WITH TIME ZONE NOT NULL, -- 赔率时间
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- 采集时间
    
    -- 赔率分析
    implied_home_prob DECIMAL(5,4), -- 隐含主胜概率
    implied_draw_prob DECIMAL(5,4), -- 隐含平局概率  
    implied_away_prob DECIMAL(5,4), -- 隐含客胜概率
    overround DECIMAL(5,4), -- 赔率商利润率
    
    -- 数据质量
    is_opening_odds BOOLEAN DEFAULT false, -- 是否为开盘赔率
    is_closing_odds BOOLEAN DEFAULT false, -- 是否为封盘赔率
    source_confidence DECIMAL(3,2) DEFAULT 1.0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_odds CHECK (
        home_odds > 1.0 AND draw_odds > 1.0 AND away_odds > 1.0
    ),
    UNIQUE(match_id, bookmaker_id, odds_time)
);

-- =========================================
-- 🧮 特征数据
-- =========================================

-- 特征类型定义
CREATE TABLE feature_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(30) NOT NULL, -- form, head2head, stats, market
    data_type VARCHAR(20) NOT NULL, -- numerical, categorical, boolean
    description TEXT,
    calculation_method TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 特征数据表
CREATE TABLE match_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id),
    feature_type_id UUID REFERENCES feature_types(id),
    
    -- 特征值 (使用JSONB存储灵活的数据类型)
    feature_value JSONB NOT NULL,
    
    -- 元数据
    calculation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    feature_version VARCHAR(20) DEFAULT '1.0',
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    
    -- 溯源信息
    source_matches TEXT[], -- 计算此特征使用的历史比赛ID
    calculation_window_days INTEGER, -- 计算窗口天数
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(match_id, feature_type_id, feature_version)
);

-- =========================================
-- 🤖 预测与模型
-- =========================================

-- 模型表
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    algorithm VARCHAR(50) NOT NULL,
    
    -- 模型元数据
    description TEXT,
    hyperparameters JSONB,
    feature_names TEXT[],
    
    -- 性能指标
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    roc_auc DECIMAL(5,4),
    log_loss DECIMAL(8,6),
    
    -- 训练信息
    training_data_size INTEGER,
    training_date TIMESTAMP WITH TIME ZONE,
    validation_method VARCHAR(50),
    
    -- 状态
    is_active BOOLEAN DEFAULT true,
    is_production BOOLEAN DEFAULT false,
    
    -- 文件路径
    model_path TEXT,
    metrics_path TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(name, version)
);

-- 预测表
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id),
    model_id UUID REFERENCES models(id),
    
    -- 预测结果
    predicted_result CHAR(1) NOT NULL, -- H, D, A
    home_win_probability DECIMAL(5,4) NOT NULL,
    draw_probability DECIMAL(5,4) NOT NULL,
    away_win_probability DECIMAL(5,4) NOT NULL,
    
    -- 预期比分
    expected_home_score DECIMAL(4,2),
    expected_away_score DECIMAL(4,2),
    
    -- 置信度
    confidence_level VARCHAR(20) NOT NULL, -- low, medium, high, very_high
    confidence_score DECIMAL(5,4) NOT NULL,
    
    -- 模型信息
    model_version VARCHAR(50) NOT NULL,
    features_used TEXT[],
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_probabilities CHECK (
        ABS(home_win_probability + draw_probability + away_win_probability - 1.0) < 0.01
    ),
    UNIQUE(match_id, model_id)
);

-- =========================================
-- 📈 数据管理
-- =========================================

-- 数据源表
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    source_type VARCHAR(30) NOT NULL, -- api, file, scraping
    base_url TEXT,
    api_key_required BOOLEAN DEFAULT false,
    rate_limit_per_minute INTEGER DEFAULT 60,
    reliability_score DECIMAL(3,2) DEFAULT 0.8,
    is_active BOOLEAN DEFAULT true,
    
    -- API配置
    headers_template JSONB,
    auth_method VARCHAR(20), -- none, api_key, bearer, basic
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 数据采集日志
CREATE TABLE data_collection_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES data_sources(id),
    task_name VARCHAR(100) NOT NULL,
    
    -- 执行信息
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL, -- running, success, failed, timeout
    
    -- 统计信息
    records_fetched INTEGER DEFAULT 0,
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    
    -- 错误信息
    error_message TEXT,
    error_details JSONB,
    
    -- 性能指标
    api_response_time_ms INTEGER,
    total_execution_time_ms INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =========================================
-- 🔍 索引优化
-- =========================================

-- 比赛查询优化
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_teams ON matches(home_team_id, away_team_id);
CREATE INDEX idx_matches_season ON matches(season_id);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_external_id ON matches(external_api_id);

-- 赔率查询优化
CREATE INDEX idx_odds_match_time ON odds_history(match_id, odds_time);
CREATE INDEX idx_odds_bookmaker ON odds_history(bookmaker_id);
CREATE INDEX idx_odds_collected_at ON odds_history(collected_at);

-- 特征查询优化
CREATE INDEX idx_features_match ON match_features(match_id);
CREATE INDEX idx_features_type ON match_features(feature_type_id);
CREATE INDEX idx_features_calculation_date ON match_features(calculation_date);

-- 预测查询优化
CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_model ON predictions(model_id);
CREATE INDEX idx_predictions_date ON predictions(prediction_date);

-- =========================================
-- 🛡️ 数据完整性约束
-- =========================================

-- 防止重复数据
CREATE UNIQUE INDEX idx_unique_match_external 
ON matches(external_api_id) WHERE external_api_id IS NOT NULL;

-- 确保赛季日期逻辑
ALTER TABLE seasons ADD CONSTRAINT valid_season_dates 
CHECK (start_date < end_date);

-- 确保比赛在赛季范围内
CREATE FUNCTION validate_match_season_date() RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM seasons s 
        WHERE s.id = NEW.season_id 
        AND (NEW.match_date::DATE < s.start_date OR NEW.match_date::DATE > s.end_date)
    ) THEN
        RAISE EXCEPTION 'Match date % is outside season range', NEW.match_date;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_match_season_date
    BEFORE INSERT OR UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION validate_match_season_date();

-- =========================================
-- 📊 视图定义
-- =========================================

-- 球队当前赛季统计视图
CREATE VIEW team_season_stats AS
SELECT 
    t.id as team_id,
    t.name as team_name,
    s.name as season,
    COUNT(m.id) as matches_played,
    COUNT(CASE WHEN (m.home_team_id = t.id AND m.result = 'H') 
               OR (m.away_team_id = t.id AND m.result = 'A') THEN 1 END) as wins,
    COUNT(CASE WHEN m.result = 'D' THEN 1 END) as draws,
    COUNT(CASE WHEN (m.home_team_id = t.id AND m.result = 'A') 
               OR (m.away_team_id = t.id AND m.result = 'H') THEN 1 END) as losses,
    SUM(CASE WHEN m.home_team_id = t.id THEN m.home_score 
             WHEN m.away_team_id = t.id THEN m.away_score 
             ELSE 0 END) as goals_scored,
    SUM(CASE WHEN m.home_team_id = t.id THEN m.away_score 
             WHEN m.away_team_id = t.id THEN m.home_score 
             ELSE 0 END) as goals_conceded
FROM teams t
JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
JOIN seasons s ON m.season_id = s.id
WHERE m.status = 'finished'
GROUP BY t.id, t.name, s.id, s.name;

-- 最新赔率视图
CREATE VIEW latest_odds AS
SELECT DISTINCT ON (oh.match_id, oh.bookmaker_id)
    oh.match_id,
    oh.bookmaker_id,
    b.name as bookmaker_name,
    oh.home_odds,
    oh.draw_odds,
    oh.away_odds,
    oh.odds_time,
    oh.is_closing_odds
FROM odds_history oh
JOIN bookmakers b ON oh.bookmaker_id = b.id
ORDER BY oh.match_id, oh.bookmaker_id, oh.odds_time DESC;

-- =========================================
-- 🔧 数据维护函数
-- =========================================

-- 更新球队统计数据
CREATE OR REPLACE FUNCTION update_team_stats(team_uuid UUID, season_name VARCHAR DEFAULT NULL) 
RETURNS void AS $$
DECLARE
    season_filter UUID;
BEGIN
    -- 获取当前赛季或指定赛季
    IF season_name IS NOT NULL THEN
        SELECT id INTO season_filter FROM seasons 
        WHERE name = season_name AND league_id = (
            SELECT league_id FROM teams WHERE id = team_uuid
        );
    ELSE
        SELECT id INTO season_filter FROM seasons 
        WHERE is_current = true AND league_id = (
            SELECT league_id FROM teams WHERE id = team_uuid
        );
    END IF;
    
    -- 更新统计数据
    UPDATE teams SET
        matches_played = (
            SELECT COUNT(*) FROM matches 
            WHERE (home_team_id = team_uuid OR away_team_id = team_uuid)
            AND status = 'finished'
            AND (season_filter IS NULL OR season_id = season_filter)
        ),
        wins = (
            SELECT COUNT(*) FROM matches 
            WHERE ((home_team_id = team_uuid AND result = 'H') 
                OR (away_team_id = team_uuid AND result = 'A'))
            AND status = 'finished'
            AND (season_filter IS NULL OR season_id = season_filter)
        ),
        draws = (
            SELECT COUNT(*) FROM matches 
            WHERE (home_team_id = team_uuid OR away_team_id = team_uuid)
            AND result = 'D' AND status = 'finished'
            AND (season_filter IS NULL OR season_id = season_filter)
        ),
        losses = (
            SELECT COUNT(*) FROM matches 
            WHERE ((home_team_id = team_uuid AND result = 'A') 
                OR (away_team_id = team_uuid AND result = 'H'))
            AND status = 'finished'
            AND (season_filter IS NULL OR season_id = season_filter)
        ),
        updated_at = NOW()
    WHERE id = team_uuid;
END;
$$ LANGUAGE plpgsql;

-- =========================================
-- 📋 初始数据
-- =========================================

-- 插入常用国家
INSERT INTO countries (name, code, fifa_code) VALUES
('England', 'ENG', 'ENG'),
('Spain', 'ESP', 'ESP'),
('Germany', 'DEU', 'GER'),
('Italy', 'ITA', 'ITA'),
('France', 'FRA', 'FRA'),
('China', 'CHN', 'CHN')
ON CONFLICT (code) DO NOTHING;

-- 插入主要博彩公司
INSERT INTO bookmakers (name, display_name, reliability_score) VALUES
('bet365', 'Bet365', 0.95),
('pinnacle', 'Pinnacle', 0.98),
('betfair', 'Betfair', 0.92),
('william_hill', 'William Hill', 0.88),
('1xbet', '1xBet', 0.85)
ON CONFLICT (name) DO NOTHING;

-- 插入基础特征类型
INSERT INTO feature_types (name, category, data_type, description) VALUES
('home_form_5', 'form', 'numerical', '主队最近5场比赛得分'),
('away_form_5', 'form', 'numerical', '客队最近5场比赛得分'),
('head2head_home_wins', 'head2head', 'numerical', '历史交锋主队胜场数'),
('head2head_draws', 'head2head', 'numerical', '历史交锋平局场数'),
('home_goals_avg', 'stats', 'numerical', '主队平均进球数'),
('away_goals_avg', 'stats', 'numerical', '客队平均进球数'),
('market_confidence', 'market', 'numerical', '市场信心指数')
ON CONFLICT (name) DO NOTHING; 