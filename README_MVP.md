# 足球预测系统 MVP

## 🎯 概述

这是足球预测系统的MVP（最小可行产品）版本，实现了从数据摄取到预测服务的完整流程。

**功能闭环：** 数据摄取 → 特征抽取 → 训练 XGBoost → 评估与登记 → FastAPI 预测接口 → Docker Compose 本地运行

## 🏗️ 架构

```
数据层          处理层          模型层          服务层
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│PostgreSQL│    │特征工程  │    │XGBoost  │    │FastAPI  │
│   +     │ => │  +     │ => │训练/评估 │ => │预测接口  │
│CSV样例  │    │数据摄取  │    │模型保存  │    │  +UI   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

## 📦 核心模块

### 1. 数据层

- **PostgreSQL**: 存储比赛、赔率、特征、模型和预测数据
- **CSV样例数据**: `sql/sample/` 目录下的测试数据

### 2. 数据摄取 (`data_pipeline/ingest/`)

- `base.py`: 抽象数据源接口
- `csv_adapter.py`: CSV文件适配器

### 3. 特征工程 (`data_pipeline/features/`)

- `rolling.py`: 滚动统计特征（球队状态、进球趋势）
- `build.py`: 特征构建主函数

### 4. 训练模块 (`trainer/`)

- `fit_xgb.py`: XGBoost多分类模型训练

### 5. 预测服务 (`apps/api/`, `models/`)

- `predictor.py`: 模型加载和预测逻辑
- `main.py`: FastAPI接口实现

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repo-url>
cd football-predict-system

# 安装依赖
make install
source .venv/bin/activate
```

### 2. MVP环境启动

```bash
# 启动数据库和API服务
make mvp-up

# 查看服务状态
make mvp-logs
```

服务启动后可访问：

- API文档: <http://localhost:8000/docs>
- 健康检查: <http://localhost:8000/health>
- 版本信息: <http://localhost:8000/version>

### 3. 训练模型

```bash
# 训练XGBoost模型
make train
```

模型将保存到 `models/xgb_{timestamp}/` 目录。

### 4. 测试预测API

```bash
# 测试预测接口
make test-api

# 或者手动调用
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "home": "Arsenal",
      "away": "Chelsea",
      "home_form": 2.1,
      "away_form": 1.8,
      "odds_h": 2.1,
      "odds_d": 3.3,
      "odds_a": 3.2
    }
  ]'
```

期望响应：

```json
[
  {
    "home_win": 0.47,
    "draw": 0.28,
    "away_win": 0.25,
    "model_version": "xgb_20241227_143021"
  }
]
```

### 5. 完整演示

```bash
# 运行完整MVP演示流程
make mvp-demo
```

## 📊 API 接口

### POST /predict

批量预测比赛结果

**请求体示例：**

```json
[
  {
    "home": "Manchester United",
    "away": "Liverpool",
    "home_form": 1.8,
    "away_form": 2.2,
    "odds_h": 2.5,
    "odds_d": 3.2,
    "odds_a": 2.8
  }
]
```

**响应示例：**

```json
[
  {
    "home_win": 0.35,
    "draw": 0.30,
    "away_win": 0.35,
    "model_version": "xgb_20241227_143021"
  }
]
```

### GET /health

健康检查接口

### GET /version

获取API和模型版本信息

## 🧪 运行测试

```bash
# 运行所有测试
make test

# 运行特定测试
python -m pytest tests/test_ingest_csv.py -v
python -m pytest tests/test_features_rolling.py -v
python -m pytest tests/test_api_predict.py -v

# 查看覆盖率
make cov
```

## 📂 项目结构

```
├── apps/api/           # FastAPI应用
├── data_pipeline/      # 数据处理管道
│   ├── ingest/        # 数据摄取
│   └── features/      # 特征工程
├── trainer/           # 模型训练
├── models/            # 模型和预测器
├── sql/               # 数据库相关
│   ├── schema.sql     # 数据库结构
│   └── sample/        # 样例数据
├── tests/             # 单元测试
├── docker-compose.mvp.yml  # MVP环境配置
├── Dockerfile.api     # API服务镜像
└── README_MVP.md      # 本文档
```

## 🔧 开发命令

```bash
# 环境管理
make mvp-up           # 启动MVP环境
make mvp-down         # 停止MVP环境
make mvp-logs         # 查看日志
make mvp-clean        # 清理环境

# 数据和模型
make ingest           # 数据摄取
make train            # 训练模型
make serve            # 启动本地API

# 测试和质量
make test             # 运行测试
make lint             # 代码检查
make ci               # 完整CI检查
```

## 📋 数据库结构

### 核心表

- `teams`: 球队信息
- `matches`: 比赛记录（含结果）
- `odds_raw`: 赔率数据
- `features`: 特征数据（JSON格式）
- `models`: 模型注册表
- `predictions`: 预测结果

详见 `sql/schema.sql`

## 🎯 MVP验收标准

- ✅ 能训练：从样例数据训练XGBoost模型
- ✅ 能预测：通过API接口进行批量预测
- ✅ 能验收：完整的测试覆盖和质量检查
- ✅ 容器化：Docker Compose一键启动
- ✅ 文档化：完整的API文档和使用说明

## 🔄 清理

```bash
# 停止并清理所有资源
make mvp-clean

# 或者手动清理
docker-compose -f docker-compose.mvp.yml down -v
docker system prune -f
```

## 📈 后续扩展

MVP版本为后续扩展奠定了基础：

- 实时数据源接入
- 更复杂的特征工程
- 模型版本管理和A/B测试
- 性能监控和告警
- 数据质量校验

---

**MVP目标：** 一周内实现能训练、能预测、能验收的完整系统 ✅
