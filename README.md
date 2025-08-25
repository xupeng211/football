# ⚽ 足球赛果预测系统

一个基于机器学习的足球比赛结果预测系统，采用现代化的Python技术栈，支持数据采集、特征工程、模型训练、实时预测和回测分析。

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-orange.svg)](https://xgboost.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

## 🎯 核心特性

- **🔮 智能预测**: 基于XGBoost的三分类预测（主胜/平局/客胜）
- **📊 特征工程**: 30+个足球专业特征，包括攻防数据、状态指标、主客场优势等
- **⚡ 实时API**: FastAPI构建的高性能预测API，支持单场和批量预测
- **🔄 自动化流水线**: Prefect编排的数据采集、训练、推理工作流
- **📈 回测分析**: 完整的历史数据回测框架，支持多策略对比
- **🐳 容器化部署**: Docker Compose一键部署，支持开发和生产环境
- **📝 结构化日志**: 全链路可观测，便于问题诊断和性能优化
- **🧪 测试驱动**: 完善的单元测试，确保代码质量和系统稳定性

## 📋 项目架构

```
football-predict-system/
├── 🚀 api/                    # FastAPI Web服务
│   ├── main.py               # 应用入口
│   ├── routers/              # API路由
│   └── core/                 # 核心配置
├── 📊 data_pipeline/          # 数据管道
│   ├── collectors/           # 数据采集器
│   ├── processors/           # 数据处理器
│   └── loaders/             # 数据加载器
├── 🧠 trainer/                # 模型训练
│   ├── xgboost_trainer.py   # XGBoost训练器
│   └── hyperopt/            # 超参数优化
├── 🎯 models/                 # 模型管理
│   ├── registry.py          # 模型注册表
│   └── artifacts/           # 模型文件存储
├── ⚡ workers/               # 工作流任务
│   ├── flows/               # Prefect工作流
│   └── tasks/               # 任务定义
├── 📈 backtest/              # 回测框架
│   ├── engine.py            # 回测引擎
│   └── strategies/          # 回测策略
├── 📊 evaluation/            # 模型评估
│   ├── metrics/             # 评估指标
│   └── reports/             # 评估报告
└── 🏗️ infra/                  # 基础设施
    ├── docker/              # Docker配置
    ├── scripts/             # 部署脚本
    └── config/              # 环境配置
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 1. 克隆项目

```bash
git clone <repository-url>
cd football-predict-system
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp env_example.txt .env

# 编辑配置文件（填入API密钥等）
vim .env
```

### 3. 安装依赖

```bash
# 安装Python依赖
make install

# 或使用pip
pip install -r requirements.txt
pip install -e .
```

### 4. 启动服务

```bash
# 启动所有基础服务（PostgreSQL, Redis, Prefect）
make docker-up

# 启动API服务
make dev
```

### 5. 验证安装

```bash
# 检查服务健康状态
curl http://localhost:8000/api/v1/health

# 查看API文档
open http://localhost:8000/docs
```

## 📖 使用指南

### 数据采集

```python
from data_pipeline.collectors.football_api import FootballAPICollector
from datetime import date

# 采集最近一周的比赛数据
async with FootballAPICollector() as collector:
    matches = await collector.collect_matches_by_date(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 7),
        leagues=["PL", "BL1", "SA"]  # 英超、德甲、意甲
    )
```

### 特征工程

```python
from data_pipeline.processors.feature_engineer import FeatureEngineer
import pandas as pd

# 初始化特征工程器
engineer = FeatureEngineer(window_days=30, min_games=5)

# 为单场比赛生成特征
features = engineer.create_match_features(
    match_id="PL_2024_001",
    home_team="Manchester United",
    away_team="Arsenal", 
    match_date=datetime(2024, 1, 15),
    historical_data=historical_matches_df
)
```

### 模型训练

```python
from trainer.xgboost_trainer import XGBoostTrainer, TrainingConfig

# 配置训练参数
config = TrainingConfig(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.05
)

# 训练模型
trainer = XGBoostTrainer(config)
X_train, X_test, y_train, y_test = trainer.prepare_data(features_df, targets_df)
result = trainer.train(X_train, X_test, y_train, y_test)

print(f"模型准确率: {result.test_score:.3f}")
```

### 预测API

```bash
# 单场比赛预测
curl -X POST "http://localhost:8000/api/v1/predictions/single" \
     -H "Content-Type: application/json" \
     -d '{
       "home_team": "Manchester United",
       "away_team": "Arsenal", 
       "match_date": "2024-01-15",
       "league": "PL"
     }'

# 批量预测
curl -X POST "http://localhost:8000/api/v1/predictions/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "matches": [
         {"home_team": "Chelsea", "away_team": "Liverpool", "match_date": "2024-01-16", "league": "PL"},
         {"home_team": "Bayern Munich", "away_team": "Dortmund", "match_date": "2024-01-16", "league": "BL1"}
       ]
     }'
```

### 回测分析

```python
from backtest.engine import BacktestEngine

# 运行回测
engine = BacktestEngine()
result = engine.run_backtest(
    model=trained_model,
    historical_data=historical_df,
    odds_data=odds_df,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 3, 31),
    min_confidence=0.65,
    stake_per_bet=10.0
)

print(f"回测收益率: {result.roi:.3f}")
print(f"预测准确率: {result.accuracy:.3f}")
```

## 🔧 开发命令

```bash
# 安装依赖
make install

# 代码格式化
make format

# 代码检查
make lint

# 类型检查  
make type

# 运行测试
make test

# 完整CI检查
make ci

# 启动开发服务
make dev

# Docker环境管理
make docker-up      # 启动服务
make docker-down    # 停止服务

# 清理临时文件
make clean
```

## 📊 系统监控

### 健康检查

- API健康状态: `GET /api/v1/health`
- 系统指标: `GET /api/v1/metrics`
- Prefect监控面板: http://localhost:4200

### 日志查看

```bash
# API服务日志
docker-compose logs -f api

# 工作流日志
docker-compose logs -f data-worker

# 数据库日志
docker-compose logs -f postgres
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_api/ -v

# 测试覆盖率报告
pytest tests/ --cov=. --cov-report=html
```

## 📈 性能指标

### 模型性能目标

- **预测准确率**: ≥ 55% (超过随机预测的33%)
- **投注收益率**: ≥ 5% (基于赔率的长期收益)
- **预测置信度**: 平均 ≥ 0.65

### 系统性能指标

- **API响应时间**: < 500ms (单次预测)
- **并发处理能力**: 1000+ 请求/秒
- **数据采集效率**: 10000+ 比赛/小时
- **特征计算性能**: < 2秒/场比赛

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

- 项目维护者: Development Team
- 邮箱: dev@example.com
- 项目地址: https://github.com/your-org/football-predict-system

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [XGBoost](https://xgboost.readthedocs.io/) - 高性能梯度提升框架
- [Prefect](https://www.prefect.io/) - 现代化的工作流编排平台
- [Football-Data.org](https://www.football-data.org/) - 足球数据API服务

---

⭐ **如果这个项目对你有帮助，请给它一个星标！** 