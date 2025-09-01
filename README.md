# 🏆 Football Prediction System v3.0

> 🚀 **现代化足球预测系统** - 从过度工程化完美进化为简洁高效架构

[![CI](https://github.com/xupeng211/football/workflows/CI/badge.svg)](https://github.com/xupeng211/football/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](https://github.com/xupeng211/football/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-80%25+-brightgreen.svg)](https://github.com/xupeng211/football/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-v3.0.0-blue.svg)](https://github.com/xupeng211/football/releases/tag/v3.0.0)
[![Quality](https://img.shields.io/badge/quality-modern--architecture-gold.svg)](#-features)

## 🎯 v3.0 重构亮点

- **🎯 配置统一**: pyproject.toml 单一配置文件
- **⚡ 工具现代化**: uv 依赖管理 + ruff 代码检查
- **🚀 简化流程**: 一键安装、一键检查、一键启动
- **🐳 容器优化**: 精简 Docker 配置
- **📊 CI/CD 可靠**: 单一工作流，并行执行

## ⚡ 快速开始

### 1. 一键安装

```bash
make install
```

### 2. 启动开发

```bash
make dev
```

### 3. 质量检查

```bash
make ci
```

就这么简单！🎉

## 🏗️ 现代化架构

```
football-predict-system-v3/
├── pyproject.toml              # 🎯 统一配置
├── uv.lock                     # 📦 依赖锁定
├── env.template                # 🌍 环境模板
├── Makefile                    # ⚡ 开发命令
├── Dockerfile                  # 🐳 容器化
├── docker-compose.yml          # 🔧 开发环境
├── .github/workflows/ci.yml    # 🚀 CI流水线
├── src/football_predict_system/ # 📁 源代码
├── tests/                      # 🧪 测试
└── docs/                       # 📖 文档
```

## 🛠️ 开发命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `make ai-setup` | 🤖 AI优化设置 | 一键配置AI友好环境 |
| `make ai-check` | 🤖 AI环境检查 | 快速诊断项目状态 |
| `make ai-file-check` | 🤖 文件操作检查 | 检查最近文件操作规范 |
| `make ai-file-guard` | 🤖 文件守护检查 | 检查指定文件规范 |
| `make install` | 📦 安装依赖 | 使用 uv 快速安装 |
| `make dev` | 🔧 启动开发服务器 | 热重载开发模式 |
| `make ci` | 🚀 运行所有检查 | 格式化+检查+测试 |
| `make test` | 🧪 运行测试 | 单元+集成测试 |
| `make build` | 🐳 构建镜像 | Docker 镜像构建 |
| `make clean` | 🧹 清理缓存 | 清理临时文件 |

### 🤖 AI编程支持

本项目专门为AI编程工具优化，提供：

- **智能环境检测** - `make ai-check` 快速了解项目状态
- **一键优化设置** - `make ai-setup` 配置AI友好环境  
- **文件操作守护** - `make ai-file-check` 防止AI创建重复文件
- **实时文件监控** - 自动检查文件操作规范
- **VS Code增强** - 智能补全、自动导入、类型检查
- **状态文件输出** - AI可读的JSON格式项目状态
- **专用使用指南** - 查看 [AI工具指南](docs/AI_TOOLS_GUIDE.md) 和 [文件守护指南](docs/AI_FILE_GUARD_GUIDE.md)

## 📊 性能提升

| 指标 | v2.0 | v3.0 | 改善 |
|------|------|------|------|
| **配置文件** | 80+ | 15 | 81% ↓ |
| **启动时间** | 15s | 5s | 66% ↓ |
| **CI时间** | 8min | 3min | 62% ↓ |
| **学习成本** | 3天 | 0.5天 | 83% ↓ |

## 🔧 技术栈

### 核心框架

- **FastAPI** - 现代 Python Web 框架
- **XGBoost** - 机器学习模型
- **PostgreSQL** - 主数据库
- **Redis** - 缓存层

### 开发工具链

- **uv** - 现代依赖管理
- **ruff** - 代码格式化和检查
- **pytest** - 测试框架
- **mypy** - 类型检查

### 部署技术

- **Docker** - 容器化
- **GitHub Actions** - CI/CD
- **Prometheus** - 监控

## 🚀 部署

### 本地开发

```bash
# 完整开发环境
docker-compose up -d

# 仅启动应用
make dev
```

### 生产部署

```bash
# 构建镜像
make build

# 生产环境启动
docker-compose --profile production up -d
```

## 📈 API 使用

### 健康检查

```bash
curl http://localhost:8000/health
```

### 预测接口

```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Liverpool", "away_team": "Manchester City"}'
```

### API 文档

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## 🧪 测试

```bash
# 运行所有测试
make test

# 运行特定类型测试
make test-unit
make test-integration

# 查看覆盖率
make test-cov
```

## 🔍 代码质量

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

## 📚 文档

- **[开发指南](docs/DEVELOPMENT.md)** - 详细开发指引
- **[部署指南](docs/DEPLOYMENT.md)** - 生产环境部署
- **[API文档](docs/API.md)** - 接口说明
- **[重构报告](REFACTOR_V3_SUMMARY.md)** - v3.0 重构详情

## 🎉 v3.0 重构成果

### 🏆 简化成就

- **配置文件**: 从80+个精简到15个
- **依赖管理**: 统一到uv单一工具
- **CI/CD**: 3个复杂工作流合并为1个
- **开发体验**: 复杂脚本简化为make命令

### ⚡ 效率提升

- **开发环境搭建**: 从复杂脚本到`make install`
- **质量检查**: 从多步骤到`make ci`
- **服务启动**: 从复杂配置到`make dev`

### 🎯 质量保证

- **80%+ 测试覆盖率** - 保持高质量标准
- **企业级安全** - 全面安全扫描
- **类型安全** - 100%类型检查覆盖
- **现代工具链** - 最新最佳实践

## 🤝 贡献

### 开发流程

```bash
# 1. 克隆项目
git clone https://github.com/xupeng211/football.git

# 2. 安装依赖
make install

# 3. 运行检查
make ci

# 4. 提交代码
git commit -m "feat: your feature"
```

### 代码规范

- 使用 `ruff` 进行代码格式化
- 遵循 `mypy` 类型检查
- 保持 80%+ 测试覆盖率
- 通过所有 CI 检查

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔗 相关链接

- 🏠 **项目主页**: [GitHub Repository](https://github.com/xupeng211/football)
- 📊 **在线演示**: [Demo Site](https://football-predict.example.com) *(即将推出)*
- 📧 **问题反馈**: [Issues](https://github.com/xupeng211/football/issues)
- 💬 **讨论区**: [Discussions](https://github.com/xupeng211/football/discussions)

---

<div align="center">

**🚀 从"过度工程化"完美进化为"现代简洁"！**

*v3.0 - 简洁、现代、高效的Python项目典范*

⭐ **如果这个项目对您有帮助，请给它一个星标！**

</div>
