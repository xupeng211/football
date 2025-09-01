# 🔧 开发指南 - Football Prediction System v3.0

> 现代化开发工作流指南

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.11+
- **Docker**: 20.0+
- **uv**: 最新版本

### 2. 一键设置

```bash
# 克隆项目
git clone https://github.com/xupeng211/football.git
cd football-predict-system

# 安装依赖
make install

# 启动开发
make dev
```

## 🛠️ 开发工具链

### 📦 依赖管理 (uv)

```bash
# 安装依赖
uv sync

# 添加新依赖
uv add fastapi

# 添加开发依赖
uv add --dev pytest

# 更新依赖
uv sync --upgrade
```

### 🎨 代码质量

```bash
# 代码格式化
make format

# 代码检查
make lint

# 类型检查
make type

# 安全扫描
make security

# 一键全部检查
make ci
```

### 🧪 测试

```bash
# 运行所有测试
make test

# 单元测试
make test-unit

# 集成测试
make test-integration

# 覆盖率报告
make test-cov
```

## 📁 项目结构

```
src/football_predict_system/
├── main.py                 # FastAPI应用入口
├── api/                    # API路由
│   └── v1/                 # API版本
├── core/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── cache.py           # 缓存管理
│   └── logging.py         # 日志配置
├── domain/                 # 业务逻辑
│   ├── models/            # 数据模型
│   └── services/          # 业务服务
└── infrastructure/         # 基础设施
    ├── repositories/      # 数据访问
    └── external/          # 外部服务
```

## 🔧 开发配置

### 环境变量

```bash
# 复制环境模板
cp env.template .env

# 编辑配置
vim .env
```

### 数据库

```bash
# 启动数据库
docker-compose up -d postgres redis

# 运行迁移
alembic upgrade head
```

### IDE配置

#### VS Code

推荐扩展：

- Python
- Pylance
- Ruff
- Docker

#### PyCharm

设置：

- 解释器：项目虚拟环境
- 代码格式化：Ruff
- 类型检查：mypy

## 📝 开发流程

### 1. 功能开发

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发代码
# ...

# 运行检查
make ci

# 提交代码
git commit -m "feat: add new feature"
```

### 2. 代码规范

- 使用 `ruff` 格式化代码
- 遵循 `mypy` 类型检查
- 编写单元测试
- 保持 80%+ 覆盖率

### 3. 提交规范

```bash
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```

## 🐳 本地开发

### Docker开发

```bash
# 启动完整环境
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 进入容器
docker-compose exec app bash
```

### 数据库管理

```bash
# 连接数据库
psql postgresql://postgres:password@localhost:5432/football_db

# 备份数据
pg_dump -h localhost -U postgres football_db > backup.sql

# 恢复数据
psql -h localhost -U postgres football_db < backup.sql
```

## 🔍 调试

### 本地调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 breakpoint()
breakpoint()
```

### 日志调试

```python
import structlog
logger = structlog.get_logger(__name__)

logger.info("Debug info", extra_data=data)
logger.error("Error occurred", error=str(e))
```

### API调试

```bash
# 使用 httpie
http GET localhost:8000/health

# 使用 curl
curl -X GET "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Liverpool", "away_team": "Chelsea"}'
```

## 📊 性能优化

### 性能分析

```bash
# 安装性能分析工具
uv add --dev line-profiler memory-profiler

# 性能分析
python -m line_profiler script.py
python -m memory_profiler script.py
```

### 数据库优化

- 使用索引
- 查询优化
- 连接池配置
- 分页查询

### 缓存策略

- Redis缓存热点数据
- 应用级缓存
- CDN缓存静态资源

## 🚨 故障排除

### 常见问题

#### 依赖问题

```bash
# 清理缓存
uv cache clean

# 重新安装
rm -rf .venv
make install
```

#### 数据库连接

```bash
# 检查数据库状态
docker-compose ps postgres

# 重启数据库
docker-compose restart postgres
```

#### 端口冲突

```bash
# 查看端口占用
lsof -i :8000

# 修改端口
export API_PORT=8001
make dev
```

## 📚 学习资源

### 项目相关

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [XGBoost文档](https://xgboost.readthedocs.io/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)

### 工具文档

- [uv文档](https://docs.astral.sh/uv/)
- [ruff文档](https://docs.astral.sh/ruff/)
- [pytest文档](https://docs.pytest.org/)

## 🤝 贡献指南

### 代码贡献

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 运行 `make ci`
5. 提交PR

### 文档贡献

- 更新API文档
- 添加使用示例
- 改进开发指南

---

*Happy Coding! 🎉*
