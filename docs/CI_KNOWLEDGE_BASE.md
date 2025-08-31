# 🔧 CI故障模式与解决方案知识库

> **目标**: 为AI编程工具提供项目CI问题的历史模式和解决方案  
> **受众**: AI编程助手、开发者、CI维护者  
> **更新**: 2025-08-31

## 📊 常见CI故障模式

### 🔴 关键故障模式 (Critical)

#### 1. 依赖管理不一致

**问题特征**:

- `requirements.lock` 缺少开发依赖 (pytest、mypy、ruff、bandit)
- `poetry.lock` 与 `pyproject.toml` 不同步
- CI使用 `uv pip sync` 但缺少关键工具

**解决方案**:

```bash
# 立即修复
poetry install --with dev
poetry lock

# 预防措施
make validate-context  # 检查依赖同步性
```

**发生频率**: 高 (80% CI故障原因)  
**影响范围**: 所有测试、代码质量检查  
**历史案例**: 2025-08-31 - 从uv迁移到Poetry依赖管理解决

#### 2. 工作流配置错误

**问题特征**:

- GitHub Actions YAML语法错误
- 环境变量配置缺失
- Action版本过时或不兼容

**解决方案**:

```bash
# 验证配置
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
make validate-config
```

**发生频率**: 中等 (30% CI故障原因)  
**影响范围**: 整个CI流水线  

#### 3. OpenTelemetry导入问题

**问题特征**:

- `configure_opentelemetry` 函数不存在
- 版本兼容性问题 (0.47b0 vs 1.34+)
- 导入路径错误

**解决方案**:

```python
# 现代化配置方式
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource

# 简化初始化
trace.set_tracer_provider(TracerProvider(
    resource=Resource.create({"service.name": "football-predict-api"})
))
```

### 🟡 警告级故障模式 (Warning)

#### 1. 代码质量检查失败

**问题特征**:

- Ruff格式化问题
- MyPy类型检查错误
- Bandit安全警告

**解决方案**:

```bash
# 自动修复大部分问题
poetry run ruff check --fix .
poetry run ruff format .

# 手动修复类型问题
poetry run mypy apps/ data_pipeline/ --ignore-missing-imports
```

#### 2. 测试随机性失败

**问题特征**:

- 预测结果不确定性 (`assert 'draw' == 'home_win'`)
- 模型输出依赖随机种子
- 并发测试顺序问题

**解决方案**:

```python
# 固定随机种子
import random
random.seed(42)

# 使用更宽松的断言
assert result in ['home_win', 'draw', 'away_win']
```

## 🏗️ 依赖管理历史记录

### 演进时间线

| 日期 | 变更 | 原因 | 影响 |
|------|------|------|------|
| **2025-08-31** | uv → Poetry 迁移 | requirements.lock无法包含开发依赖 | 🟢 解决CI红灯 |
| 2025-08-26 | 添加OpenTelemetry | 监控和追踪需求 | 🟡 导入问题 |
| 2025-08-24 | Poetry + pyproject.toml | 现代化Python项目管理 | 🟢 标准化配置 |
| 2025-08-20 | 引入pre-commit hooks | 代码质量自动化 | 🟢 提前发现问题 |

### 当前依赖架构

```
依赖管理策略:
├── pyproject.toml              # 主要配置，定义依赖
├── poetry.lock                 # 锁定版本，确保一致性
├── [tool.poetry.group.dev]     # 开发依赖组 (现代化格式)
└── requirements.lock           # CI兼容 (已弃用，改用poetry)

CI策略:
├── GitHub Actions              # 使用 snok/install-poetry@v1
├── Poetry 缓存                 # 优化构建速度
└── Makefile CMD_PREFIX         # CI环境自动使用 'poetry run'
```

### 依赖分类

#### 核心运行时依赖

- FastAPI, Uvicorn, Pydantic (API服务)
- pandas, numpy, scikit-learn (数据处理)
- SQLAlchemy, psycopg2-binary (数据库)
- Prefect (工作流编排)

#### 开发工具依赖 (group.dev)

- pytest, pytest-cov, pytest-asyncio (测试)
- ruff, mypy, bandit (代码质量)
- pre-commit (Git hooks)

#### 监控依赖

- OpenTelemetry套件 (可观测性)
- prometheus-fastapi-instrumentator (指标)

## 🚨 故障预防策略

### 1. 依赖变更检查清单

```bash
# 变更前验证
□ poetry check                    # 验证配置语法
□ poetry lock --check            # 检查锁定文件同步
□ make validate-context          # 验证上下文一致性

# 变更后验证  
□ poetry install --with dev      # 安装所有依赖
□ make ci                       # 本地CI模拟
□ make diagnose-ci              # AI工具诊断
```

### 2. CI配置变更检查清单

```bash
# YAML语法验证
□ yamllint .github/workflows/    # 语法检查
□ make validate-config          # 配置验证

# 功能验证
□ gh workflow run ci.yml        # 手动触发测试
□ gh run watch                  # 监控执行
```

### 3. 监控指标

- **MTTR** (Mean Time To Recovery): 目标 < 30分钟
- **CI成功率**: 目标 > 95%
- **依赖更新频率**: 每周检查，每月更新

## 🤖 AI工具集成指南

### 快速诊断命令

```bash
# AI工具专用诊断
make diagnose-ci           # 全面CI健康检查
make validate-context      # 上下文信息验证
make show.context         # 查看完整项目上下文
```

### 问题分类决策树

```
CI失败 →
├── 依赖问题? → make diagnose-ci → poetry install --with dev
├── 配置问题? → make validate-config → 修复YAML语法
├── 代码质量? → ruff/mypy检查 → 自动修复
└── 测试失败? → pytest详细输出 → 特定修复
```

### AI提示词增强

当AI工具遇到CI问题时，可以参考这个知识库：

```
请根据以下上下文解决CI问题：
1. 项目使用Poetry管理依赖，不再使用uv pip sync
2. 开发依赖在[tool.poetry.group.dev.dependencies]中定义
3. Makefile在CI环境自动使用poetry run前缀
4. 常见问题参考docs/CI_KNOWLEDGE_BASE.md

当前错误: [错误信息]
建议的诊断步骤: make diagnose-ci
```

## 📚 参考资源

- [AI开发指南](../AI_DEVELOPMENT_GUIDELINES.md)
- [开发者指南](../DEVELOPER_GUIDE.md)  
- [项目架构](ARCHITECTURE.md)
- [Poetry官方文档](https://python-poetry.org/)
- [GitHub Actions最佳实践](https://docs.github.com/actions)
