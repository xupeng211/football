# 项目任务看板 (SSOT)

本文档是项目核心任务的唯一可信来源 (Single Source of Truth)，用于跟踪 P1 阶段的开发进度。

## 任务列表

| ID | 模块 | 输入 | 输出 | 验收标准 | 依赖 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T-001** | `infra` | `docker-compose.yml`, SQL 脚本 | 一个可运行的 PostgreSQL 容器，包含初始化的 schema | 1. 服务在端口 5432 监听。<br>2. `matches`, `odds` 表已创建。 | - | `todo` |
| **T-002** | `data_pipeline` | 外部赔率 API | 存储在 PG `odds` 表中的赔率数据 | 1. 采集脚本可按日期范围运行。<br>2. 数据结构符合预定义 schema。 | T-001 | `todo` |
| **T-003** | `data_pipeline` | PG `matches`, `odds` 表 | 存储在 PG `features` 表或 Parquet 文件中的特征数据 | 1. 特征工程 pipeline 可运行。<br>2. 生成至少 10 个核心特征 (implied_prob_*, bookie_margin, odds_spread_home, fav_flag, log_home, log_away, odds_ratio, prob_diff)。<br>3. 特征值无 `NaN` 或 `inf`。 | T-002 | `todo` |
| **T-004** | `apps/trainer` | 特征数据 | 一个已训练的 XGBoost 模型文件 (`.xgb`) 和元数据 (`.json`) | 1. 训练脚本可运行。<br>2. 模型 AUC > 0.55。<br>3. 模型文件被保存到 `models/artifacts`。 | T-003 | `todo` |
| **T-005** | `apps/api` | 比赛 ID 或球队信息 | 一个包含预测概率的 JSON 响应 | 1. `/api/v1/predictions` 端点可用。<br>2. 输入验证有效。<br>3. 能加载最新模型并返回预测结果。 | T-004 | `todo` |
| **T-006** | `apps/backtest` | 历史特征数据、已训练模型 | 回测报告（例如，利润曲线、命中率） | 1. 回测引擎可运行。<br>2. 输出关键性能指标（KPIs）。<br>3. 结果可复现。 | T-004 | `todo` |
