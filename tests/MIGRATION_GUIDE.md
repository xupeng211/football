# 异步测试迁移指南

## 🎯 迁移目标

将现有的同步测试套件迁移到异步测试架构，以更好地测试我们的异步FastAPI应用。

## 📋 迁移检查清单

### ✅ 已完成

- [x] 创建新的测试目录结构
- [x] 设计异步测试夹具系统
- [x] 更新pytest配置
- [x] 创建测试数据工厂
- [x] 编写异步测试示例

### 🔄 进行中

- [ ] 迁移现有API测试
- [ ] 迁移服务层测试
- [ ] 迁移数据库集成测试

### ⏳ 待办事项

- [ ] 清理旧的重复测试文件
- [ ] 更新CI/CD配置
- [ ] 编写性能基准测试

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pytest-asyncio httpx
```

### 2. 运行异步测试示例

```bash
# 运行快速单元测试
python tests/run_tests.py fast

# 运行异步测试
python tests/run_tests.py async

# 运行API测试
python tests/run_tests.py api
```

### 3. 查看测试结构

```bash
tree tests/
```

## 📝 迁移模式

### 从同步到异步API测试

#### ❌ 旧方式 (同步)

```python
def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
```

#### ✅ 新方式 (异步)

```python
@pytest.mark.unit
@pytest.mark.api
async def test_health_endpoint_async(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
```

### 异步服务测试

#### ❌ 旧方式

```python
def test_prediction_service():
    service = PredictionService()
    # 无法正确测试异步方法
```

#### ✅ 新方式

```python
@pytest.mark.unit
async def test_prediction_service_async():
    service = PredictionService()
    result = await service.generate_prediction(match_data)
    assert result is not None
```

### 并发测试

#### ✅ 新功能 (异步特有)

```python
@pytest.mark.concurrent
async def test_concurrent_requests(async_client: AsyncClient):
    tasks = [async_client.get("/health") for _ in range(10)]
    responses = await asyncio.gather(*tasks)
    
    for response in responses:
        assert response.status_code == 200
```

## 🏗️ 测试架构变化

### 测试类型重新分类

| 类型 | 目的 | 运行时间 | 依赖 |
|------|------|----------|------|
| **单元测试** | 测试单个函数/类 | < 1秒 | 无外部依赖 |
| **集成测试** | 测试组件交互 | 1-10秒 | 数据库/缓存 |
| **端到端测试** | 测试完整流程 | 10-60秒 | 完整系统 |
| **性能测试** | 测试性能指标 | 变化 | 负载工具 |

### 新的测试标记

```python
@pytest.mark.unit          # 单元测试
@pytest.mark.integration   # 集成测试
@pytest.mark.e2e          # 端到端测试
@pytest.mark.async        # 异步测试
@pytest.mark.concurrent   # 并发测试
@pytest.mark.performance  # 性能测试
@pytest.mark.slow         # 慢速测试
@pytest.mark.fast         # 快速测试
```

## 🔧 常用测试模式

### 1. 异步HTTP客户端测试

```python
@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

async def test_endpoint(async_client: AsyncClient):
    response = await async_client.post("/api/endpoint", json=data)
    assert response.status_code == 200
```

### 2. 异步数据库测试

```python
async def test_database_operation(async_db_session):
    result = await some_async_db_operation(async_db_session)
    assert result is not None
```

### 3. 异步缓存测试

```python
async def test_cache_operation(redis_client):
    await redis_client.set("key", "value")
    result = await redis_client.get("key")
    assert result == "value"
```

### 4. 性能基准测试

```python
@pytest.mark.performance
async def test_response_time(async_client: AsyncClient):
    import time
    
    start = time.time()
    response = await async_client.get("/api/fast-endpoint")
    end = time.time()
    
    assert response.status_code == 200
    assert (end - start) < 0.1  # 100ms内响应
```

## 📊 测试运行策略

### 开发阶段

```bash
# 只运行快速测试
pytest -m "unit and fast"

# 运行API相关测试
pytest -m "api"

# 运行异步测试
pytest -m "async"
```

### CI/CD阶段

```bash
# 运行所有非慢速测试
pytest -m "not slow"

# 运行集成测试
pytest -m "integration"

# 生成覆盖率报告
pytest --cov=src --cov-report=xml
```

### 性能测试

```bash
# 运行性能测试
pytest -m "performance"

# 运行并发测试
pytest -m "concurrent"
```

## 🐛 常见问题

### 1. 异步夹具问题

**问题**: `TypeError: object AsyncGenerator can't be used in 'await' expression`

**解决**: 确保使用 `@pytest_asyncio.fixture`

```python
@pytest_asyncio.fixture  # ✅ 正确
async def async_client():
    ...

@pytest.fixture  # ❌ 错误
async def async_client():
    ...
```

### 2. 事件循环问题

**问题**: `RuntimeError: There is no current event loop`

**解决**: 在conftest.py中配置事件循环

```python
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
```

### 3. 异步Mock问题

**问题**: 无法正确模拟异步函数

**解决**: 使用 `AsyncMock`

```python
from unittest.mock import AsyncMock

service.async_method = AsyncMock(return_value=expected_result)
```

## 📈 迁移进度追踪

### 文件迁移状态

| 文件 | 状态 | 优先级 | 备注 |
|------|------|--------|------|
| `test_api_simple.py` | 🔄 进行中 | 高 | 核心API测试 |
| `test_api_basic.py` | ⏳ 待办 | 高 | 基础API测试 |
| `test_predictions_api.py` | ⏳ 待办 | 高 | 预测API测试 |
| `test_models.py` | ⏳ 待办 | 中 | 模型测试 |
| `test_basic.py` | ⏳ 待办 | 低 | 基础测试 |

### 下一步行动

1. **立即行动** (本周)
   - 迁移 `test_api_simple.py` 中的核心测试
   - 验证异步测试夹具工作正常
   - 运行新的异步测试套件

2. **短期目标** (下周)
   - 迁移所有API相关测试
   - 添加并发测试用例
   - 设置性能基准

3. **长期目标** (本月)
   - 完成所有测试迁移
   - 删除旧的重复测试文件
   - 优化CI/CD流水线

## 🎓 最佳实践

1. **标记使用**: 为每个测试添加适当的标记
2. **夹具复用**: 使用fixtures目录中的共享夹具
3. **工厂模式**: 使用factories生成测试数据
4. **性能意识**: 为关键路径添加性能测试
5. **清理资源**: 确保异步资源正确清理

---

💡 **提示**: 这是一个渐进式迁移过程。您可以保留现有测试的同时逐步添加异步测试。
