# 🔍 CI监控工具使用指南

## 🚀 快速开始

### 1. 推送前预检查

```bash
# 在每次git push前运行
./scripts/ci-precheck.sh

# 如果检查失败，会给出具体的修复建议
```

### 2. 监控GitHub Actions状态

```bash
# 查看最新的CI运行状态
./scripts/gh-monitor.sh

# 如果CI失败，脚本会提供详细的诊断和修复选项
```

### 3. 本地代码质量检查

```bash
# 生成详细的代码质量报告
python ./scripts/ci-dashboard.py

# 查看保存的指标
cat ci-metrics.json
```

## 📋 监控工具详解

### 🔧 CI预检查脚本 (ci-precheck.sh)

**功能:**

- ✅ 检查依赖文件完整性
- ✅ 验证配置文件语法
- ✅ 运行安全扫描
- ✅ 执行测试套件
- ✅ 代码质量检查

**使用场景:**

- Git commit前自动检查
- 推送前最终验证
- 快速问题诊断

**示例输出:**

```
🔍 CI预检查开始...
========================================
📦 1. 检查依赖文件...
✅ requirements.txt 存在
✅ uv.lock 存在
✅ pyproject.toml 存在

🔧 2. 检查配置文件语法...
✅ .gitleaks.toml 语法正确
✅ ci.yml 语法正确

🧪 4. 运行测试套件...
✅ 测试套件通过

📏 5. 代码质量检查...
✅ Ruff检查通过
✅ 格式检查通过

🎯 CI预检查完成！
========================================
结果: 6/6 检查通过
🎉 所有检查通过，可以安全推送！
```

### 📊 CI质量监控 (ci-dashboard.py)

**功能:**

- 📈 测试覆盖率统计
- 🧪 测试通过率分析
- 🔒 安全问题检测
- 📏 代码质量评分
- 📦 依赖完整性检查

**使用场景:**

- 定期质量检查
- 项目健康度评估
- 趋势分析

**示例输出:**

```
============================================================
📊 CI质量报告 - 2025-01-27 18:15:32
============================================================
🟢 测试覆盖率: 78.32%
🟢 测试结果: 225/247 通过
🟢 安全问题: 0
🟢 代码质量: 100/100
🟢 依赖文件: 完整
============================================================
🎉 总体评分: 95/100 - 优秀！
```

### 🔄 GitHub Actions监控 (gh-monitor.sh)

**功能:**

- 📋 显示最新的工作流运行
- 🔍 分析失败原因
- 🔗 提供快速链接
- 🔧 自动修复建议

**前置条件:**

```bash
# 安装GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# 登录GitHub
gh auth login
```

**使用示例:**

```bash
# 监控当前分支的CI状态
./scripts/gh-monitor.sh

# 如果发现CI失败，脚本会显示：
# - 失败的作业详情
# - 完整日志链接
# - 自动修复建议
# - 交互式修复选项
```

## 🔄 自动化集成

### 1. Git Hooks集成

```bash
# 设置pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "🔍 运行pre-commit检查..."
./scripts/ci-precheck.sh
EOF
chmod +x .git/hooks/pre-commit

# 设置pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
echo "🚀 推送前最终检查..."
./scripts/ci-precheck.sh || {
    echo "❌ CI预检查失败，取消推送"
    exit 1
}
EOF
chmod +x .git/hooks/pre-push
```

### 2. 定时监控 (Crontab)

```bash
# 每小时检查一次CI状态
# 编辑crontab: crontab -e
0 * * * * cd /path/to/football-predict-system && ./scripts/gh-monitor.sh >> ci-monitor.log 2>&1

# 每日生成质量报告
0 9 * * * cd /path/to/football-predict-system && python ./scripts/ci-dashboard.py > daily-quality-$(date +\%Y\%m\%d).log
```

### 3. VS Code任务集成

```json
// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "CI预检查",
            "type": "shell",
            "command": "./scripts/ci-precheck.sh",
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "质量监控",
            "type": "shell",
            "command": "python ./scripts/ci-dashboard.py",
            "group": "test"
        },
        {
            "label": "CI状态监控",
            "type": "shell",
            "command": "./scripts/gh-monitor.sh",
            "group": "test"
        }
    ]
}
```

## 🔧 故障排除指南

### 常见问题及解决方案

#### 1. CI预检查失败

```bash
# 自动修复格式问题
ruff format .

# 自动修复可修复的lint问题
ruff check --fix .

# 查看详细测试失败信息
python -m pytest -v --tb=short
```

#### 2. GitHub CLI相关问题

```bash
# 重新认证
gh auth logout
gh auth login

# 检查权限
gh auth status

# 手动指定仓库
gh run list --repo xupeng211/football --limit 5
```

#### 3. 依赖问题

```bash
# 重新生成requirements.txt
pip freeze > requirements.txt

# 更新uv.lock
uv lock --upgrade

# 重新安装依赖
pip install -r requirements.txt
```

## 📈 高级用法

### 1. 自定义质量阈值

```python
# 修改 scripts/ci-dashboard.py 中的评分标准
def calculate_overall_score(self):
    # 自定义权重
    coverage_weight = 40  # 提高覆盖率权重
    test_weight = 30      # 提高测试权重
    quality_weight = 20   # 降低代码质量权重
    security_weight = 5   # 安全权重
    deps_weight = 5       # 依赖权重
```

### 2. 集成Slack通知

```bash
# 在 gh-monitor.sh 中添加Slack通知
if [ "$LATEST_CONCLUSION" = "failure" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🔴 CI失败: $REPO - $LATEST_RUN_ID\"}" \
        $SLACK_WEBHOOK_URL
fi
```

### 3. 生成趋势报告

```python
# 创建历史趋势脚本
import json
import matplotlib.pyplot as plt
from datetime import datetime

def plot_coverage_trend():
    # 读取历史数据
    metrics = []
    for file in glob.glob("ci-metrics-*.json"):
        with open(file) as f:
            metrics.append(json.load(f))

    # 绘制趋势图
    dates = [m['timestamp'] for m in metrics]
    coverage = [m['coverage'] for m in metrics]

    plt.plot(dates, coverage)
    plt.title('Test Coverage Trend')
    plt.ylabel('Coverage %')
    plt.savefig('coverage-trend.png')
```

## 🎯 最佳实践

1. **推送前检查**: 始终运行 `./scripts/ci-precheck.sh`
2. **定期监控**: 每日检查CI状态和质量指标
3. **快速修复**: 使用自动修复工具处理简单问题
4. **趋势分析**: 定期查看质量趋势，预防问题
5. **团队共享**: 确保所有开发者都使用相同的监控工具

---

**📞 获取帮助:**

- CI预检查失败: 查看脚本输出的具体建议
- GitHub Actions问题: 使用 `gh-monitor.sh` 获取详细分析
- 质量问题: 运行 `ci-dashboard.py` 获取完整报告

这些工具将帮助你实现CI/CD的完整监控和自动化质量保障！
