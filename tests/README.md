# 测试套件架构指南

## 📁 目录结构

```
tests/
├── conftest.py              # 全局测试配置和异步夹具
├── fixtures/                # 测试数据和夹具
│   ├── __init__.py
│   ├── api_fixtures.py      # API测试夹具
│   ├── database_fixtures.py # 数据库测试夹具
│   ├── cache_fixtures.py    # 缓存测试夹具
│   └── factories.py         # 测试数据工厂
├── unit/                    # 单元测试（快速，隔离）
│   ├── api/                 # API路由和端点单元测试
│   ├── domain/              # 业务逻辑单元测试
│   ├── core/                # 核心组件单元测试
│   └── utils/               # 工具函数单元测试
├── integration/             # 集成测试（真实依赖）
│   ├── api/                 # API集成测试
│   ├── database/            # 数据库集成测试
│   ├── cache/               # 缓存集成测试
│   └── services/            # 服务集成测试
├── e2e/                     # 端到端测试
│   ├── user_workflows/      # 用户完整工作流测试
│   └── api_workflows/       # API完整工作流测试
├── performance/             # 性能测试
│   ├── benchmarks/          # 基准测试
│   ├── load_tests/          # 负载测试
│   └── stress_tests/        # 压力测试
└── regression/              # 回归测试
    ├── model_stability/     # 模型稳定性测试
    └── api_compatibility/   # API兼容性测试
```

## 🔧 测试类型分类

### 单元测试 (Unit Tests)

- **目标**: 测试单个函数/类的行为
- **特点**: 快速、独立、模拟外部依赖
- **运行时间**: < 1秒
- **标记**: `@pytest.mark.unit`

### 集成测试 (Integration Tests)

- **目标**: 测试组件间交互
- **特点**: 使用真实数据库/缓存，较慢
- **运行时间**: 1-10秒
- **标记**: `@pytest.mark.integration`

### 端到端测试 (E2E Tests)

- **目标**: 测试完整用户场景
- **特点**: 完整系统测试，最慢
- **运行时间**: 10-60秒
- **标记**: `@pytest.mark.e2e`

## ⚡ 异步测试最佳实践

### 1. 使用异步测试函数

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

async def test_async_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/status")
    assert response.status_code == 200
```

### 2. 异步数据库测试

```python
@pytest_asyncio.fixture
async def async_db_session():
    async with async_session_factory() as session:
        yield session
        await session.rollback()

async def test_database_operation(async_db_session):
    result = await some_async_db_operation(async_db_session)
    assert result is not None
```

### 3. 并发测试

```python
import asyncio

async def test_concurrent_operations():
    tasks = [async_operation(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 10
```

## 🏷️ 测试标记策略

```python
# pytest.ini 配置
markers = [
    "unit: 快速单元测试",
    "integration: 需要外部依赖的集成测试",
    "e2e: 端到端测试",
    "slow: 慢速测试 (>10秒)",
    "fast: 快速测试 (<1秒)",
    "api: API相关测试",
    "database: 数据库相关测试",
    "cache: 缓存相关测试",
    "async: 异步测试",
    "concurrent: 并发测试",
]
```

## 🎯 运行策略

```bash
# 开发时快速测试
pytest -m "unit and fast"

# 完整集成测试
pytest -m "integration"

# 性能测试
pytest -m "performance"

# 所有测试（CI环境）
pytest -m "not slow"
```

## 📊 覆盖率目标

- **单元测试覆盖率**: > 90%
- **集成测试覆盖率**: > 80%  
- **关键路径覆盖率**: 100%
- **分支覆盖率**: > 85%
