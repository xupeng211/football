# 🚀 Football Prediction System - 快速启动指南

> **目标**: 实现"本地=CI一致"，彻底解决CI红灯问题！

## 📋 完整安装流程

### 1. 基础环境设置

```bash
# 进入项目目录
cd /home/user/projects/football-predict-system

# 确保有虚拟环境
if [ ! -d ".venv" ]; then
    uv venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 设置开发环境变量
source scripts/setup_env.sh development
```

### 2. 一键升级到现代化系统

```bash
# 给脚本执行权限
chmod +x scripts/upgrade_to_modern_hooks.sh
chmod +x scripts/verify_standards.sh

# 运行一键升级脚本 (自动处理hooks冲突)
bash scripts/upgrade_to_modern_hooks.sh
```

**或者使用原始安装方式:**

```bash
# 如果没有hooks冲突，使用原始安装脚本
chmod +x scripts/install_pre_commit.sh
bash scripts/install_pre_commit.sh
```

### 3. 验证安装结果

```bash
# 验证所有验收标准
bash scripts/verify_standards.sh

# 测试CI级别检查
make ci-check

# 测试pre-commit
pre-commit run --all-files
```

## ✅ 验收标准确认

1. **本地执行 `make ci-check` = CI 运行一致** ✅
2. **CI workflow 里只跑 `make ci-check`** ✅  
3. **`.cursor/rules.md` 存在并生效** ✅
4. **本地 `pre-commit` 能阻止不合格提交** ✅
5. **可以用 `make local-ci` 在本地跑完整 CI 流程** ✅

## 🎯 日常使用命令

```bash
# 开发前：设置环境
source .venv/bin/activate
source scripts/setup_env.sh development

# 开发中：质量检查
make ci-check

# 提交前：自动检查 (pre-commit会自动运行)
git add .
git commit -m "your message"  # pre-commit自动运行

# 高级：本地CI模拟
make local-ci
```

## 🛠️ 故障排除

### 如果 `make ci-check` 失败

1. **代码格式问题**:

   ```bash
   uv run ruff format .    # 自动格式化
   uv run ruff check --fix .  # 自动修复
   ```

2. **类型检查问题**:

   ```bash
   uv run mypy . --show-error-codes  # 查看详细错误
   ```

3. **测试失败**:

   ```bash
   uv run pytest -v  # 查看详细测试结果
   ```

### 如果 pre-commit 有问题

```bash
# 重新安装
pre-commit uninstall
pre-commit install

# 更新hooks
pre-commit autoupdate

# 跳过某次提交的检查 (紧急情况)
git commit --no-verify -m "emergency fix"
```

## 🎉 成功标志

当看到以下输出时，说明一切正常：

```bash
$ make ci-check
🚀 运行CI级别检查...
1️⃣ Ruff代码检查...
2️⃣ MyPy类型检查...  
3️⃣ 运行测试...
✅ 所有CI检查通过! 可以安全提交

$ git commit -m "feat: add new feature"
ruff....................................................................Passed
ruff-format.............................................................Passed
mypy....................................................................Passed
pytest-check............................................................Passed
[main abc1234] feat: add new feature
```

**🎯 这意味着：本地通过 = CI必然通过！再也不会有红灯了！** 🟢
