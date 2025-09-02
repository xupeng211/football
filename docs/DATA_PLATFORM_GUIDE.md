# 🏗️ 足球数据中台完整指南

> 📊 **一站式足球数据解决方案** - 从数据采集到分析的完整流程

## 🎯 概述

数据中台为足球预测系统提供了：

- **多源数据采集** - Football-Data.org、API-Football等
- **自动化调度** - Prefect驱动的定时任务  
- **数据质量保障** - 验证、去重、异常检测
- **企业级存储** - PostgreSQL + Redis缓存
- **实时监控** - Prometheus指标 + 健康检查

## 🚀 快速开始

### 1. 一键启动 (推荐)

```bash
# 设置数据中台
make data-quick-start
```

这将自动完成：

- ✅ 数据库schema创建
- ✅ API访问验证
- ✅ 样本数据生成
- ✅ 健康检查验证

### 2. 分步设置

```bash
# 1. 设置数据库
make data-setup

# 2. 检查健康状态
make data-health

# 3. 运行首次数据采集
make data-collect
```

## 📊 核心功能

### 数据采集

#### 日常数据更新

```bash
# 采集最近7天的数据
make data-collect
```

#### 历史数据回填

```bash
# 回填英超2023-24赛季
make data-backfill COMP_ID=2021 START=2023-08-01 END=2024-05-31

# 回填西甲2023-24赛季  
make data-backfill COMP_ID=2014 START=2023-08-01 END=2024-05-31
```

#### 支持的联赛ID

| 联赛 | ID | 覆盖范围 |
|------|-----|----------|
| 英超 | 2021 | ⭐⭐⭐⭐⭐ |
| 西甲 | 2014 | ⭐⭐⭐⭐⭐ |
| 德甲 | 2002 | ⭐⭐⭐⭐⭐ |
| 意甲 | 2019 | ⭐⭐⭐⭐⭐ |
| 法甲 | 2015 | ⭐⭐⭐⭐⭐ |
| 欧冠 | 2001 | ⭐⭐⭐⭐ |
| 欧联 | 2018 | ⭐⭐⭐ |

### 数据监控

#### 质量检查

```bash
# 检查数据质量
make data-monitor

# 健康状态检查
make data-health
```

#### 监控指标

- 📈 数据新鲜度 (24小时内更新)
- 🎯 数据完整性 (比分缺失率 < 5%)
- ⚡ 响应时间 (API调用 < 2秒)
- 🔄 成功率 (采集成功率 > 95%)

## 🗄️ 数据库结构

### 核心表

#### 1. 比赛数据 (`matches`)

```sql
-- 核心字段
id              UUID PRIMARY KEY
home_team_id    UUID REFERENCES teams(id)  
away_team_id    UUID REFERENCES teams(id)
match_date      TIMESTAMP WITH TIME ZONE
home_score      INTEGER
away_score      INTEGER
result          CHAR(1)  -- H/D/A

-- 扩展统计
home_possession     DECIMAL(5,2)
home_shots         INTEGER
home_shots_on_target INTEGER
-- ... 更多统计字段

-- 数据质量
data_quality_score  DECIMAL(3,2)
is_verified        BOOLEAN
source_reliability VARCHAR(20)
```

#### 2. 赔率数据 (`odds_history`)

```sql
match_id        UUID REFERENCES matches(id)
bookmaker_id    UUID REFERENCES bookmakers(id)
home_odds       DECIMAL(6,3)
draw_odds       DECIMAL(6,3)  
away_odds       DECIMAL(6,3)
odds_time       TIMESTAMP WITH TIME ZONE
implied_home_prob DECIMAL(5,4)  -- 自动计算
```

#### 3. 特征数据 (`match_features`)

```sql
match_id         UUID REFERENCES matches(id)
feature_type_id  UUID REFERENCES feature_types(id)
feature_value    JSONB -- 灵活存储
confidence_score DECIMAL(3,2)
source_matches   TEXT[] -- 溯源信息
```

### 优化视图

#### 球队统计视图

```sql
-- 实时计算的球队赛季统计
SELECT * FROM team_season_stats 
WHERE team_name = 'Liverpool' AND season = '2023-24';
```

#### 最新赔率视图

```sql
-- 获取最新赔率
SELECT * FROM latest_odds 
WHERE match_id = 'xxx' AND bookmaker_name = 'bet365';
```

## 🤖 自动化调度

### Prefect Flow部署

```bash
# 部署所有流程
make data-deploy-flows
```

部署的流程：

#### 1. 日常数据采集 (`daily-data-collection`)

- **频率**: 每6小时
- **覆盖**: 5大联赛最近7天数据
- **自动重试**: 3次，间隔60秒

#### 2. 数据质量监控 (`data-quality-monitoring`)  

- **频率**: 每小时
- **检查**: 数据完整性、新鲜度、异常
- **告警**: 自动记录质量问题

#### 3. 历史回填 (`historical-backfill`)

- **触发**: 手动触发
- **批处理**: 30天为一批
- **限流**: 6秒间隔，遵守API限制

### 自定义调度

```python
from prefect import flow
from football_predict_system.data_platform.flows.data_collection import daily_data_collection_flow

# 自定义联赛采集
@flow
async def custom_collection():
    await daily_data_collection_flow(
        competitions=[2021, 2014],  # 仅英超和西甲
        date_range_days=14
    )
```

## 📈 数据源策略

### 免费方案 (推荐起步)

- **Football-Data.org**
  - 🆓 免费使用
  - 📊 10请求/分钟
  - 🏆 5大联赛 + 欧战
  - 🎯 适合MVP和测试

### 付费方案 (生产推荐)

- **API-Football**
  - 💰 $10-50/月
  - 📊 100-1000请求/分钟
  - 🌍 1100+联赛
  - 📈 实时数据 + 历史

### 混合方案 (最佳实践)

```python
# 核心联赛使用付费API (高频率)
premium_leagues = [2021, 2014, 2002, 2019, 2015]

# 次要联赛使用免费API (低频率)  
free_leagues = [2016, 2017, 2003]
```

## 🔧 配置管理

### 环境变量

```bash
# 必需配置
FOOTBALL_DATA_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/football_db
REDIS_URL=redis://localhost:6379/0

# 可选配置  
API_FOOTBALL_KEY=your_premium_api_key  # 付费API
PREFECT_API_URL=http://localhost:4200/api
DATA_RETENTION_DAYS=1095  # 3年保留期
```

### 高级配置

```python
# src/football_predict_system/data_platform/config.py
config = DataPlatformConfig(
    football_data_org=DataSourceConfig(
        rate_limit_per_minute=10,
        reliability_score=0.9
    ),
    schedule=CollectionSchedule(
        daily_collection_cron="0 */6 * * *",
        quality_check_cron="0 * * * *"
    )
)
```

## 📊 使用场景

### 1. 回测分析

```sql
-- 获取英超最近100场比赛用于回测
SELECT m.*, oh.home_odds, oh.draw_odds, oh.away_odds
FROM matches m
JOIN latest_odds oh ON m.id = oh.match_id  
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
WHERE m.status = 'finished'
  AND ht.league_id = (SELECT id FROM leagues WHERE name = 'Premier League')
ORDER BY m.match_date DESC
LIMIT 100;
```

### 2. 特征工程数据

```sql
-- 获取球队近期表现特征
SELECT 
    t.name,
    tss.wins,
    tss.goals_scored,
    tss.goals_conceded,
    (tss.goals_scored::float / NULLIF(tss.goals_conceded, 0)) as attack_defense_ratio
FROM team_season_stats tss
JOIN teams t ON tss.team_id = t.id
WHERE tss.season = '2023-24';
```

### 3. 市场分析

```sql
-- 分析赔率变化趋势
SELECT 
    DATE(odds_time) as date,
    AVG(home_odds) as avg_home_odds,
    AVG(draw_odds) as avg_draw_odds,
    AVG(away_odds) as avg_away_odds,
    AVG(overround) as avg_margin
FROM odds_history oh
JOIN matches m ON oh.match_id = m.id
WHERE m.match_date >= NOW() - INTERVAL '30 days'
GROUP BY DATE(odds_time)
ORDER BY date;
```

## 🚨 故障排除

### 常见问题

#### API调用失败

```bash
# 检查API密钥
echo $FOOTBALL_DATA_API_KEY

# 测试API连接
curl -H "X-Auth-Token: $FOOTBALL_DATA_API_KEY" \
     https://api.football-data.org/v4/competitions

# 重新验证
make data-health
```

#### 数据库连接问题

```bash
# 检查数据库
docker-compose ps postgres

# 重启数据库服务  
docker-compose restart postgres

# 重新设置schema
make data-setup
```

#### 数据质量问题

```bash
# 运行质量检查
make data-monitor

# 查看详细日志
docker-compose logs app | grep "data_platform"

# 手动验证数据
psql $DATABASE_URL -c "SELECT COUNT(*) FROM matches WHERE status='finished' AND home_score IS NULL;"
```

### 性能优化

#### 提升采集速度

```python
# 增加并发数 (谨慎使用，注意API限制)
config.max_concurrent_requests = 10

# 优化批处理大小
config.max_batch_size = 2000

# 缓存优化
config.cache_ttl_hours = 6
```

#### 数据库优化

```sql
-- 添加自定义索引
CREATE INDEX idx_matches_recent ON matches(match_date DESC) 
WHERE match_date >= NOW() - INTERVAL '30 days';

-- 分区历史数据 (大数据量时)
CREATE TABLE matches_2023 PARTITION OF matches 
FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
```

## 🎮 实际使用示例

### 获取最新比赛数据

```python
from football_predict_system.data_platform.sources.football_data_api import (
    FootballDataAPICollector, POPULAR_COMPETITIONS
)

# 获取英超最新数据
collector = FootballDataAPICollector()
matches_df = await collector.fetch_matches(
    competition_id=POPULAR_COMPETITIONS["premier_league"],
    date_from=datetime.utcnow() - timedelta(days=7)
)

print(f"收集到 {len(matches_df)} 场比赛")
```

### 启动历史回填

```python
from football_predict_system.data_platform.flows.data_collection import (
    historical_backfill_flow
)

# 回填英超2023-24赛季完整数据
result = await historical_backfill_flow(
    competition_id=2021,
    season_start="2023-08-01", 
    season_end="2024-05-31"
)

print(f"回填完成: {result}")
```

### 数据质量监控

```python
from football_predict_system.data_platform.storage.database_writer import (
    DatabaseWriter
)

writer = DatabaseWriter()
quality_stats = await writer.get_data_quality_stats()

print(f"数据质量评分: {quality_stats}")
```

## 📋 生产部署检查单

### 部署前检查

- [ ] 📊 API密钥已配置 (`FOOTBALL_DATA_API_KEY`)
- [ ] 🗄️ 数据库连接正常 (`DATABASE_URL`)
- [ ] 🚀 Redis缓存可用 (`REDIS_URL`)
- [ ] 🔧 Prefect服务运行
- [ ] 📈 监控系统配置

### 生产配置

```bash
# 生产环境变量
ENV=production
DATA_RETENTION_DAYS=1095
PREFECT_API_URL=https://your-prefect-server.com/api
PROMETHEUS_ENABLED=true

# 高可用配置
DATABASE_POOL_SIZE=20
REDIS_POOL_SIZE=10
MAX_CONCURRENT_REQUESTS=5
```

### 监控告警

```yaml
# prometheus/alerts.yml
groups:
  - name: football_data_platform
    rules:
      - alert: DataCollectionFailed
        expr: increase(data_collection_failures_total[1h]) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "数据采集失败率过高"
          
      - alert: DataStale
        expr: time() - football_last_successful_update > 86400
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "数据超过24小时未更新"
```

## 🔄 扩展指南

### 添加新数据源

1. **继承基类**

```python
from football_predict_system.data_platform.sources.base import MatchDataSource

class NewAPICollector(MatchDataSource):
    async def fetch(self, **kwargs) -> pd.DataFrame:
        # 实现具体采集逻辑
        pass
```

2. **配置数据源**

```python
new_source_config = DataSourceConfig(
    name="new-api",
    source_type="api",
    base_url="https://new-api.com/v1",
    rate_limit_per_minute=100
)
```

3. **集成到流程**

```python
@flow
async def new_collection_flow():
    collector = NewAPICollector()
    data, stats = await collector.collect()
    # 处理数据...
```

### 自定义特征计算

```python
# 添加新特征类型
INSERT INTO feature_types (name, category, data_type, description) VALUES
('home_scoring_form', 'form', 'numerical', '主队近期进球表现'),
('market_volatility', 'market', 'numerical', '赔率波动性指标');

# 计算特征
async def calculate_custom_features(match_id: str):
    # 自定义特征计算逻辑
    pass
```

## 🎉 下一步行动

### 立即可执行

1. **启动数据中台**

   ```bash
   make data-quick-start
   ```

2. **开始收集数据**

   ```bash
   make data-collect
   ```

3. **回填核心联赛历史数据**

   ```bash
   # 英超最近一个赛季
   make data-backfill COMP_ID=2021 START=2023-08-01 END=2024-05-31
   ```

### 7天内目标

- ✅ 5大联赛当前赛季数据收集完整
- ✅ 自动化调度正常运行
- ✅ 数据质量监控建立
- ✅ 基础回测数据准备就绪

### 1个月内目标

- 📈 历史3年数据完整回填
- 🔄 多数据源集成
- 📊 高级特征工程
- 🚀 预测模型训练数据就绪

---

**🎯 数据中台就绪，开始您的足球预测之旅！**
