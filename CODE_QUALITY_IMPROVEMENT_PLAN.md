# 🚀 代码质量提升方案 - 避免CI红灯

## 📋 问题分析总结

基于你的项目分析，主要CI失败原因包括：

### 🔴 历史问题分析

1. **依赖冲突** - pycodestyle、flake8、pydantic等版本冲突
2. **测试覆盖率不足** - 从10%提升到78%的历程
3. **安全扫描问题** - Gitleaks检测到敏感信息
4. **API接口不一致** - 端点路径和响应格式问题
5. **类型检查错误** - mypy类型注解问题

## 🛠️ 综合解决方案

### 1. Pre-commit Hooks 强化配置

```yaml
# .pre-commit-config.yaml (增强版)
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements
      - id: check-json
      - id: pretty-format-json
        args: ['--autofix']

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
        exclude: ^(tests/|scripts/|src/aiculture-kit)

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
        additional_dependencies: ["bandit[toml]"]

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: [--tb=short, -x, --disable-warnings]
```

### 2. 本地质量检查脚本

创建 `scripts/pre-push-check.sh`:

```bash
#!/bin/bash
set -e

echo[object Object]量检查..."

# 1. 代码格式化
echo "1️⃣ 代码格式化..."
ruff format .
ruff check --fix .

# 2. 类型检查
echo "2️⃣ 类型检查..."
mypy apps/ data_pipeline/ --ignore-missing-imports

# 3. 安全检查
echo "3️⃣ 安全检查..."
bandit -r . -c pyproject.toml -q

# 4. 快速测试
echo "4️⃣ 快速测试..."
pytest tests/ -x --tb=short --disable-warnings -m "not slow"

# 5. 覆盖率检查
echo "5️⃣ 覆盖率检查..."
pytest --cov=apps --cov=data_pipeline --cov=models --cov-report=term-missing --cov-fail-under=70

echo "✅ 所有检查通过，可以安全推送！"
```

### 3. 智能CI配置优化

增强 `.github/workflows/ci.yml`:

```yaml
# 在现有CI基础上添加以下jobs

  quality-gate:
    name: "Quality Gate"
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v5

      - name: Quality Pre-check
        run: |
          # 快速失败检查
          python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"
          python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

      - name: Dependency Conflict Check
        run: |
          python -m pip install pip-tools
          pip-compile --dry-run pyproject.toml

  parallel-tests:
    name: "Parallel Tests"
    runs-on: ubuntu-22.04
    strategy:
      matrix:
        test-group: [unit, integration, api, models]
    steps:
      - uses: actions/checkout@v5
      - name: Run Test Group
        run: pytest tests/ -m ${{ matrix.test-group }} --tb=short
```

### 4. 开发工作流改进

#### 4.1 Git Hooks 设置

```bash
# 设置 pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
exec scripts/pre-push-check.sh
EOF
chmod +x .git/hooks/pre-push
```

#### 4.2 开发环境检查脚本

创建 `scripts/dev-env-check.py`:

```python
#!/usr/bin/env python3
"""开发环境健康检查"""
import subprocess
import sys
from pathlib import Path

def check_dependencies():
    """检查依赖一致性"""
    try:
        result = subprocess.run(
            ["uv", "pip", "check"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("❌ 依赖冲突检测到:")
            print(result.stdout)
            return False
        print("✅ 依赖检查通过")
        return True
    except FileNotFoundError:
        print("⚠️ uv未安装，跳过依赖检查")
        return True

def check_code_quality():
    """代码质量快速检查"""
    checks = [
        (["ruff", "check", "."], "Ruff检查"),
        (["mypy", "apps/", "--ignore-missing-imports"], "类型检查"),
        (["bandit", "-r", ".", "-c", "pyproject.toml", "-q"], "安全检查")
    ]

    for cmd, name in checks:
        try:
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                print(f"✅ {name}通过")
            else:
                print(f"❌ {name}失败")
                return False
        except FileNotFoundError:
            print(f"⚠️ {name}工具未安装")
    return True

if __name__ == "__main__":
    print("🔍 开发环境健康检查...")

    success = True
    success &= check_dependencies()
    success &= check_code_quality()

    if success:
        print("🎉 开发环境检查全部通过！")
        sys.exit(0)
    else:
        print("💥 发现问题，请修复后再提交")
        sys.exit(1)
```

### 5. 测试策略优化

#### 5.1 测试分层策略

```python
# pytest.ini 增强配置
[tool.pytest.ini_options]
markers = [
    "unit: 快速单元测试 (<1s)",
    "integration: 集成测试 (1-10s)",
    "e2e: 端到端测试 (>10s)",
    "smoke: 冒烟测试 (关键路径)",
    "regression: 回归测试",
    "slow: 慢速测试 (CI可选)",
    "api: API接口测试",
    "model: 机器学习模型测试",
    "db: 数据库相关测试"
]

# 并行执行配置
addopts = [
    "-n", "auto",                    # 自动并行
    "--dist=loadscope",             # 按scope分发
    "--tb=short",                   # 简短错误信息
    "--strict-markers",             # 严格标记检查
    "--cov-fail-under=75",          # 覆盖率要求
    "--maxfail=3",                  # 最多3个失败就停止
]
```

#### 5.2 智能测试选择

创建 `scripts/smart-test.py`:

```python
#!/usr/bin/env python3
"""智能测试选择器 - 根据变更文件选择相关测试"""
import subprocess
import sys
from pathlib import Path

def get_changed_files():
    """获取变更的文件"""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split('\n') if result.stdout.strip() else []

def select_tests(changed_files):
    """根据变更文件选择测试"""
    test_patterns = []

    for file in changed_files:
        if file.startswith('apps/api/'):
            test_patterns.append('tests/test_api_*.py')
        elif file.startswith('data_pipeline/'):
            test_patterns.append('tests/data_pipeline/')
        elif file.startswith('models/'):
            test_patterns.append('tests/test_models.py')
        elif file.endswith('.py'):
            # 通用Python文件，运行单元测试
            test_patterns.append('-m unit')

    return list(set(test_patterns)) or ['tests/']

if __name__ == "__main__":
    changed = get_changed_files()
    patterns = select_tests(changed)

    print(f"🔍 检测到变更文件: {len(changed)}")
    print(f"📝 将运行测试: {' '.join(patterns)}")

    # 执行选定的测试
    cmd = ["pytest"] + patterns + ["--tb=short", "-v"]
    sys.exit(subprocess.call(cmd))
```

## 🎯 实施步骤

### 第一阶段：基础设施搭建 (1-2天)

1. **配置Pre-commit Hooks**

```bash
# 安装和配置
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push

# 首次运行
pre-commit run --all-files
```

2. **创建质量检查脚本**

```bash
mkdir -p scripts
chmod +x scripts/pre-push-check.sh
chmod +x scripts/dev-env-check.py
chmod +x scripts/smart-test.py
```

3. **配置IDE集成**

```json
// .vscode/settings.json
{
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.banditEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests",
        "--tb=short",
        "-v"
    ],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true,
        "source.fixAll": true
    }
}
```

```
