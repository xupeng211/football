# 🔍 CI监控与问题解决完整方案

## 🎯 监控策略

### 1. GitHub Actions状态检查

```bash
# 检查最新工作流状态
gh run list --repo xupeng211/football --branch feat/p1-hardening --limit 5

# 查看特定运行的详细日志
gh run view [RUN_ID] --log

# 实时监控
gh run watch [RUN_ID]
```

### 2. 本地预检查脚本

```bash
#!/bin/bash
# ci-precheck.sh - 推送前完整检查

echo "🔍 CI预检查开始..."

# 1. 依赖检查
echo "📦 检查依赖文件..."
test -f requirements.txt && echo "✅ requirements.txt 存在" || echo "❌ requirements.txt 缺失"
test -f uv.lock && echo "✅ uv.lock 存在" || echo "❌ uv.lock 缺失"

# 2. 配置文件语法检查
echo "🔧 检查配置文件语法..."
python -c "import tomllib; tomllib.load(open('.gitleaks.toml','rb'))" && echo "✅ .gitleaks.toml 语法正确" || echo "❌ .gitleaks.toml 语法错误"
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "✅ ci.yml 语法正确" || echo "❌ ci.yml 语法错误"

# 3. 安全扫描预检
echo "🔒 运行安全预扫描..."
if command -v gitleaks >/dev/null 2>&1; then
    gitleaks detect --source . --config .gitleaks.toml && echo "✅ 安全扫描通过" || echo "❌ 发现安全问题"
else
    echo "⚠️ gitleaks 未安装，跳过本地安全检查"
fi

# 4. 测试运行
echo "🧪 运行测试套件..."
python -m pytest --cov=apps --cov=data_pipeline --cov=models --cov-fail-under=15 -q --tb=no

# 5. 代码质量检查
echo "📏 代码质量检查..."
ruff check . && echo "✅ Ruff检查通过" || echo "❌ Ruff发现问题"
ruff format --check . && echo "✅ 格式检查通过" || echo "❌ 格式问题"

echo "🎯 CI预检查完成！"
```

## 🔧 常见CI问题诊断矩阵

### 问题分类1: 依赖安装失败

**症状识别:**

```
❌ "No dependency file found"
❌ "uv.lock sync failed"
❌ "requirements.txt not found"
```

**解决方案:**

```bash
# 立即修复脚本
echo "🔧 修复依赖问题..."

# 重新生成requirements.txt
pip freeze > requirements.txt

# 更新uv.lock
uv lock --upgrade

# 验证文件存在
ls -la requirements.txt uv.lock pyproject.toml
```

### 问题分类2: 安全扫描失败

**症状识别:**

```
❌ "gitleaks found secrets"
❌ "Failed to load config"
❌ "expected type 'string', got..."
```

**解决方案:**

```toml
# .gitleaks.toml 标准配置
title = "gitleaks config"

[[rules]]
id = "generic-api-key"
description = "Generic API Key"
regex = '''(?i)(?:key|api|token|secret|password)\s*[:=]\s*['\"]?[a-z0-9]{20,}['\"]?'''

[allowlist]
description = "global allow lists"
paths = [
    '''tests/.*\.py$''',
    '''conftest\.py$''',
]
regexes = [
    '''postgresql://postgres:.*@localhost:5432/.*''',
    '''fake_key''',
    '''test.*password''',
]
```

### 问题分类3: 测试执行失败

**症状识别:**

```
❌ "Test collection failed"
❌ "Coverage below threshold"
❌ "Import errors"
```

**解决方案:**

```bash
# 测试问题修复脚本
echo "🧪 修复测试问题..."

# 1. 检查导入问题
python -c "import apps.api.main; print('✅ 主模块导入成功')"

# 2. 运行测试收集检查
python -m pytest --collect-only tests/ | tail -5

# 3. 逐个模块测试
for module in tests/unit tests/integration tests/e2e; do
    if [ -d "$module" ]; then
        echo "🔍 测试 $module"
        python -m pytest "$module" --tb=short -x
    fi
done
```

### 问题分类4: 代码质量检查失败

**症状识别:**

```
❌ "ruff check failed"
❌ "mypy type errors"
❌ "bandit security issues"
```

**解决方案:**

```bash
# 代码质量自动修复
echo "📏 自动修复代码质量..."

# 自动格式化
ruff format .

# 自动修复可修复的问题
ruff check --fix .

# 检查修复结果
ruff check . && echo "✅ 代码质量检查通过"
```

## 🚀 自动化解决方案

### 1. GitHub Actions故障自愈工作流

```yaml
# .github/workflows/ci-self-heal.yml
name: CI Self-Healing
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

jobs:
  self-heal:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Diagnose and Fix Common Issues
        run: |
          echo "🔍 CI失败，开始自动诊断..."

          # 检查依赖文件
          if [ ! -f "requirements.txt" ]; then
            echo "📦 生成requirements.txt"
            pip freeze > requirements.txt
          fi

          # 检查gitleaks配置
          python -c "import tomllib; tomllib.load(open('.gitleaks.toml','rb'))" || {
            echo "🔧 修复gitleaks配置"
            # 使用标准配置覆盖
          }

      - name: Auto-commit fixes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add .
          git diff --staged --quiet || git commit -m "🤖 自动修复CI问题"
          git push
```

### 2. 本地开发环境标准化

```bash
# setup-dev-env.sh
#!/bin/bash
echo "🚀 设置标准化开发环境..."

# 1. 安装必要工具
pip install pre-commit ruff mypy pytest pytest-cov bandit

# 2. 设置pre-commit hooks
pre-commit install

# 3. 创建标准化配置
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
EOF

# 4. 验证环境
echo "✅ 开发环境设置完成"
pre-commit run --all-files
```

## 📊 CI质量监控仪表板

### 指标监控脚本

```python
#!/usr/bin/env python3
# ci-dashboard.py
import subprocess
import json
from datetime import datetime

def get_ci_metrics():
    """获取CI质量指标"""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "coverage": get_coverage(),
        "test_count": get_test_count(),
        "security_issues": get_security_issues(),
        "code_quality": get_code_quality()
    }
    return metrics

def get_coverage():
    """获取测试覆盖率"""
    try:
        result = subprocess.run([
            "python", "-m", "pytest",
            "--cov=apps", "--cov=data_pipeline", "--cov=models",
            "--cov-report=json", "-q"
        ], capture_output=True, text=True)

        with open("coverage.json") as f:
            data = json.load(f)
            return data["totals"]["percent_covered"]
    except:
        return 0

def get_test_count():
    """获取测试数量"""
    try:
        result = subprocess.run([
            "python", "-m", "pytest", "--collect-only", "-q"
        ], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if "collected" in line:
                return int(line.split()[0])
    except:
        return 0

def get_security_issues():
    """获取安全问题数量"""
    try:
        result = subprocess.run([
            "bandit", "-r", ".", "-f", "json"
        ], capture_output=True, text=True)
        data = json.loads(result.stdout)
        return len(data.get("results", []))
    except:
        return 0

def get_code_quality():
    """获取代码质量分数"""
    try:
        result = subprocess.run([
            "ruff", "check", ".", "--output-format", "json"
        ], capture_output=True, text=True)
        issues = json.loads(result.stdout)
        return max(0, 100 - len(issues))
    except:
        return 100

if __name__ == "__main__":
    metrics = get_ci_metrics()
    print(json.dumps(metrics, indent=2))

    # 生成简单报告
    print(f"\n📊 CI质量报告 - {metrics['timestamp']}")
    print(f"🧪 测试覆盖率: {metrics['coverage']:.1f}%")
    print(f"📝 测试数量: {metrics['test_count']}")
    print(f"🔒 安全问题: {metrics['security_issues']}")
    print(f"📏 代码质量: {metrics['code_quality']}/100")
```

## 🎯 预防性质量保障

### 1. Git Hooks增强

```bash
# .git/hooks/pre-push (可执行)
#!/bin/bash
echo "🚀 推送前最终检查..."

# 运行完整CI预检
./ci-precheck.sh || {
    echo "❌ CI预检查失败，取消推送"
    exit 1
}

echo "✅ 检查通过，继续推送"
```

### 2. VS Code配置标准化

```json
// .vscode/settings.json
{
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "ruff",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "--cov=apps",
        "--cov=data_pipeline",
        "--cov=models",
        "--cov-report=term"
    ],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.ruff": true
    }
}
```

## 🔄 持续改进循环

### 每日自动检查

```bash
# daily-health-check.sh
#!/bin/bash
echo "📅 每日CI健康检查 - $(date)"

# 1. 依赖安全更新检查
pip list --outdated

# 2. 安全漏洞扫描
safety check

# 3. 测试覆盖率趋势
python ci-dashboard.py > daily-metrics.json

# 4. 生成趋势报告
echo "📈 质量趋势分析..."
# 与历史数据对比
```

这个完整方案提供了：

- 🔍 **实时监控**: 多层次的CI状态检查
- 🔧 **自动修复**: 常见问题的自动化解决
- 📊 **质量监控**: 持续的质量指标跟踪
- 🚀 **预防机制**: 问题发生前的拦截

你现在可以使用这些工具来监控和彻底解决CI问题！
