# 足球赛果预测系统 - 架构设计 (MVP)

本文档旨在提供项目在 MVP (Minimum Viable Product) 阶段的核心架构视图，确保团队对模块职责、数据流和技术选型有统一的理解。

## 1. 核心模块职责

| 模块 (Module) | 核心职责 (Core Responsibility) | 关键技术/库 |
| :--- | :--- | :--- |
| **`apps/api`** | 提供 RESTful API 接口，用于模型推理、健康检查和指标监控。 | FastAPI, Pydantic, Uvicorn |
| **`apps/trainer`** | 负责模型的训练、验证和调优。 | XGBoost, scikit-learn, pandas |
| **`apps/backtest`** | 提供回测引擎，用于评估模型在历史数据上的表现。 | pandas, numpy |
| **`apps/workers`** | 定义和执行后台任务和数据流水线。 | Prefect (or Celery) |
| **`data_pipeline`** | 包含数据采集、特征工程和特征存储的完整流程。 | requests, pandas, SQLAlchemy |
| **`models`** | 模型注册表，负责模型的版本管理、存储和加载。 | pickle, JSON, file system |
| **`infra`** | 基础设施配置，包括 Docker、数据库脚本和部署配置。 | Docker Compose, shell scripts |
| **`evaluation`** | 模型评估模块，生成详细的性能报告和可视化图表。 | scikit-learn, matplotlib |

## 2. 数据与调用流 (Data & Calling Flow)

下图描述了从数据采集到最终 API 推理的完整流程：

```mermaid
graph LR
    %% ========= 数据与调用流（MVP） =========
    subgraph "A. 数据层 (Data Layer)"
        direction LR
        A1[外部 API] --> A2(<b>data_pipeline/sources</b><br/>采集原始数据)
        A2 --> A3(<b>data_pipeline/transforms</b><br/>清洗与特征工程)
        A3 --> A4(<b>data_pipeline/feature_store</b><br/>存储特征)
    end

    subgraph "B. 模型层 (Model Layer)"
        direction LR
        A4 --> B1(<b>apps/trainer</b><br/>训练/验证)
        B1 --> B2(<b>models/registry</b><br/>版本化与注册)
    end

    subgraph "C. 应用层 (Application Layer)"
        direction TB
        B2 --> C1(<b>apps/api</b><br/>在线推理)
        B2 --> C2(<b>apps/backtest</b><br/>离线回测)
    end

    subgraph "D. 评估层 (Evaluation Layer)"
        direction TB
        C2 --> D1(<b>evaluation</b><br/>性能评估/报告)
    end

    subgraph "E. 基础设施 (Infrastructure)"
        direction LR
        E1[(PostgreSQL)]
        E2[(Docker / Compose)]
        A2 -- 写入原始表 --> E1
        A4 -- 写入特征表 --> E1
    end

    %% ========= 样式 =========
    classDef data fill:#F8E8FF,stroke:#333,stroke-width:1px
    classDef model fill:#E6F0FF,stroke:#333,stroke-width:1px
    classDef app fill:#E9FFE6,stroke:#333,stroke-width:1px
    classDef eval fill:#FFE6FA,stroke:#333,stroke-width:1px
    classDef infra fill:#EEEEEE,stroke:#333,stroke-width:1px

    class A2,A3,A4 data
    class B1,B2 model
    class C1,C2 app
    class D1 eval
    class E1,E2 infra

    %% Legend
    %% data=数据层, model=模型层, app=应用层, eval=评估层, infra=基础设施
```

