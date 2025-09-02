# 🎬 本地CI演练系统 - 演示示例

## 🚀 完整演示流程

### 📋 系统概述

您的项目现在拥有完整的**推送前本地CI演练机制**：

```
🔄 完整工作流程
================

开发代码 → git push → 🐳 Docker CI演练 → ✅ 通过 → 🚀 推送成功
                        ↓ 失败 
                     🚫 阻止推送 + 🔧 修复建议
```

### 🎯 核心文件说明

| 文件/目录 | 作用 | 说明 |
|-----------|------|------|
| `Dockerfile.ci` | CI环境定义 | 与GitHub Actions 100%一致 |
| `.git/hooks/pre-push` | 推送前Hook | 自动触发CI检查 |
| `scripts/ci/local_ci_orchestrator.sh` | Docker编排器 | 管理容器生命周期 |
| `scripts/ci/local_ci_runner.sh` | CI执行器 | 运行完整CI流程 |
| `Makefile` (新增任务) | 任务集成 | 便捷的命令接口 |

## 🎮 互动演示

### 1. 环境验证

```bash
# 检查CI环境
make ci.doctor
```

**期望输出**：

```
🏥 CI环境诊断...

📋 环境检查:
============
🐍 Python: Python 3.11.9
📦 UV: uv 0.x.x
🐳 Docker: Docker version 24.x.x
🔧 Make: GNU Make 4.x

📁 项目文件:
===========
pyproject.toml: ✅ 存在
Dockerfile.ci: ✅ 存在
CI编排器: ✅ 存在
CI执行器: ✅ 存在

🐳 Docker状态:
=============
✅ Docker daemon运行正常
```

### 2. 首次构建CI镜像

```bash
# 构建Docker CI镜像
make ci.docker.build
```

**期望输出**：

```
🐳 构建本地CI Docker镜像...
[+] Building 45.2s (15/15) FINISHED
 => [internal] load build definition from Dockerfile.ci
 => => transferring dockerfile: 1.52kB
 => [internal] load .dockerignore
 => ...
 => exporting to image
 => => writing image sha256:abc123...
✅ CI镜像构建完成
```

### 3. 测试Docker CI

```bash
# 运行完整Docker CI检查
make ci.docker.new
```

**期望输出**：

```
🎭 本地CI编排器 - 完整CI演练
=================================
📍 项目路径: /path/to/football-predict-system
🐳 Docker镜像: football-predict-ci:latest
⏰ 超时设置: 600秒

✅ Docker环境正常
ℹ️  使用现有CI镜像 (2小时前构建)
✅ CI容器启动成功

🚀 启动本地CI - 模拟GitHub Actions环境
================================================
📍 工作目录: /workspace
🐍 Python版本: Python 3.11.9
📦 UV版本: uv 0.x.x

🔄 环境检查
✅ Python 3.11
✅ UV包管理器
✅ 项目结构
⏱️  环境检查 耗时: 1秒

🔄 安装依赖 (模拟 GitHub Actions)
✅ 依赖安装
⏱️  依赖安装 耗时: 8秒

🔄 🎨 代码质量门禁 (严格检查)
🔄 格式检查 (ruff format --check)
✅ 代码格式
🔄 代码质量检查 (ruff check)
✅ 代码质量
⏱️  代码质量门禁 耗时: 3秒

🔄 🔒 安全扫描
✅ Bandit扫描
✅ AI安全检查
⏱️  安全扫描 耗时: 2秒

🔄 🧪 测试执行
✅ 单元测试
⏱️  测试执行 耗时: 12秒

🔄 🏗️ 构建验证
✅ 模块导入
✅ 语法检查
⏱️  构建验证 耗时: 1秒

======================================
🎯 本地CI执行报告
======================================
⏱️  总执行时间: 27秒
📊 检查项目: 12

✅ Python 3.11
✅ UV包管理器
✅ 项目结构
✅ 依赖安装
✅ 代码格式
✅ 代码质量
✅ Bandit扫描
✅ AI安全检查
✅ 单元测试
✅ 模块导入
✅ 语法检查

🎉 所有检查通过！可以安全推送到远程仓库。

✅ CI检查完成 (耗时: 27秒)
✅ 本地CI检查通过，可以安全推送
```

### 4. 模拟推送流程

```bash
# 创建测试修改
echo "# 测试本地CI系统" >> test_file.md
git add test_file.md
git commit -m "test: 验证本地CI系统"

# 推送 - 自动触发CI
git push
```

**期望输出**：

```
🚦 Pre-Push Hook - 本地CI演练启动
=======================================
📍 项目路径: /path/to/project
📅 时间: 2024-09-02 20:30:15

ℹ️  推送目标: origin (https://github.com/user/repo.git)
ℹ️  推送分支: main (a1b2c3d4)

🐳 使用Docker化CI演练 (与远程环境100%一致)
🔄 启动Docker化本地CI演练

[... CI执行过程 ...]

🎉 所有CI检查通过！
🚀 继续推送到远程仓库...

Enumerating objects: 4, done.
Counting objects: 100% (4/4), done.
Delta compression using up to 8 threads
Compressing objects: 100% (2/2), done.
Writing objects: 100% (3/3), 284 bytes | 284.00 KiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0
To https://github.com/user/repo.git
   abc1234..def5678  main -> main
```

### 5. 模拟CI失败场景

```bash
# 故意引入格式问题
echo "def  bad_format( ):" >> src/test_module.py
git add src/test_module.py
git commit -m "test: 故意的格式问题"

# 推送 - 应该被阻止
git push
```

**期望输出**：

```
🚦 Pre-Push Hook - 本地CI演练启动
=======================================

[... CI执行过程 ...]

❌ 代码格式: 格式不符合标准

❌ 发现的问题:
   • 代码格式: 格式不符合标准

💡 建议修复方法:
   • 运行 'make format' 自动修复格式问题
   • 运行 'make lint' 查看详细代码问题
   • 运行 'make ci' 本地完整检查

🔧 建议的自动修复命令:
====================
   make format  # 自动修复代码格式

🤖 是否自动执行修复命令? (y/N): y

🔄 执行自动修复
ℹ️  执行: make format (自动修复代码格式)
✅ 修复成功: 自动修复代码格式

❌ 本地CI检查失败，推送被阻止

💡 完整的修复步骤:
   1. 查看详细日志: cat /tmp/ci-output.log
   2. 手动修复问题: make ci
   3. 重新尝试推送
   4. 跳过检查推送: git push --no-verify
```

## 🛠️ 可用命令演示

### 诊断命令

```bash
# 完整环境诊断
make ci.doctor

# 检查Docker镜像
docker images | grep football-predict-ci
```

### 维护命令

```bash
# 重建CI镜像 (解决环境问题)
make ci.docker.rebuild

# 清理Docker资源
make ci.docker.clean

# 交互式调试容器
make ci.docker.run
```

### 应急命令

```bash
# 跳过CI检查推送
SKIP_CI=true git push

# 完全跳过hook
git push --no-verify

# 只运行本地轻量CI
make ci.enhanced
```

## 📊 系统特点演示

### 🔄 自动容错

1. **Docker可用** → 使用Docker CI (100%准确)
2. **Docker失败** → 自动降级到本地CI (快速检查)
3. **两者都失败** → 提供详细错误信息和修复建议

### 🎯 智能修复

系统会自动识别常见问题并提供修复建议：

- **格式问题** → `make format`
- **依赖问题** → `uv sync --extra dev`
- **导入问题** → 设置PYTHONPATH

### 📝 详细日志

所有执行日志保存在 `/tmp/ci-output.log`：

```bash
# 查看完整日志
cat /tmp/ci-output.log

# 查看错误摘要
grep -E "(❌|⚠️)" /tmp/ci-output.log
```

## 🎉 成功验证标准

系统正常工作的标志：

1. ✅ `make ci.doctor` 所有检查通过
2. ✅ `make ci.docker.build` 成功构建镜像
3. ✅ `make ci.docker.new` 完整CI通过
4. ✅ `git push` 自动触发并通过CI
5. ✅ 故意破坏代码时正确阻止推送
6. ✅ 修复后能够正常推送

## 🌟 系统优势

- **零配置**：开箱即用，无需复杂设置
- **高保真**：本地环境与远程CI 100%一致
- **智能化**：自动检测、修复、降级
- **用户友好**：清晰的日志和错误提示
- **高效率**：本地验证避免远程CI失败
- **可扩展**：易于添加新的检查项目

---

**🎯 恭喜！您现在拥有了一个专业级的本地CI演练系统，确保每次推送都是成功的！** 🚀
