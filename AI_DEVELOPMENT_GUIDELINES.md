# 🤖 AI开发项目CI绿灯保障指南

> **目标**: 确保AI协助开发的项目100%通过CI检查  
> **适用**: 所有使用AI工具进行软件开发的项目  
> **版本**: v1.0 (2025-08-26)

## 🚦 CI绿灯三大保障

### 🟢 Tier 1: 必须遵守 (阻塞性问题)
- ✅ 所有配置文件语法正确
- ✅ 依赖版本锁定且可安装  
- ✅ 虚拟环境强制使用
- ✅ 代码格式化通过
- ✅ 基础类型检查通过

### 🟡 Tier 2: 强烈建议 (质量问题)
- ⚠️ 完整的类型注解
- ⚠️ 安全检查无警告
- ⚠️ 测试覆盖率>80%
- ⚠️ 文档与代码同步
- ⚠️ Git提交规范

### 🔵 Tier 3: 最佳实践 (优化建议)
- 💡 性能测试通过
- 💡 代码复杂度控制
- 💡 依赖安全扫描
- 💡 自动化部署就绪
- 💡 监控指标完善

## 🛠️ AI开发工具集成

### VS Code/Cursor 配置
```json
{
  "python.defaultInterpreter": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### AI Assistant 提示词模板
```
请帮我编写Python代码，要求：
1. 使用Python 3.11语法
2. 包含完整的类型注解
3. 遵循ruff格式化标准
4. 添加docstring文档
5. 异常处理使用 "from" 语法
6. 确保代码可以通过mypy检查

代码需求：[具体需求描述]
```

### 开发工作流
```bash
# 1. 环境准备
source scripts/activate-venv.sh
make pre-dev-check

# 2. AI辅助开发
# 使用AI工具编写代码

# 3. 本地验证
make local-ci

# 4. 提交代码
git add .
git commit -m "feat: AI generated feature with full CI compliance"
git push

# 5. 监控CI
gh run watch
```

## 📋 AI开发检查清单

### 🔄 每次开发前
```bash
□ 虚拟环境已激活 (source .venv/bin/activate)
□ 依赖已更新 (pip install -r requirements.txt)
□ 配置验证通过 (make validate-configs)
□ Git状态清洁 (git status)
```

### 🔄 代码编写中
```bash
□ 类型注解完整 (mypy .)
□ 格式化正确 (ruff format .)
□ 导入顺序正确 (ruff check --fix .)
□ 安全检查通过 (bandit -r .)
```

### 🔄 提交推送前
```bash
□ 本地CI通过 (make ci)
□ 测试覆盖充分 (pytest --cov)
□ 文档已更新 (相关README/docs)
□ 提交信息规范 (conventional commits)
```

## 🆘 应急处理指南

### 配置文件语法错误
```bash
# TOML语法检查
python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"

# YAML语法检查  
yamllint .github/workflows/

# 修复建议: 使用模板生成器
make generate-configs
```

### 依赖安装失败
```bash
# 清理环境重试
pip cache purge
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 版本冲突解决
pip install --force-reinstall -r requirements.txt
```

### CI工作流失败
```bash
# 本地模拟CI
docker run --rm -v $(PWD):/app -w /app python:3.11.9-slim \
  bash -c "pip install -r requirements.txt && make ci"

# 查看详细错误
gh run view --log

# 常见修复
make fix-common-issues
```

## 🎯 AI工具使用最佳实践

### 1. 代码生成提示
- ✅ 明确指定Python版本和依赖
- ✅ 要求完整的类型注解
- ✅ 包含异常处理和日志
- ✅ 请求单元测试代码
- ❌ 避免生成复杂的配置文件

### 2. 配置文件处理
- ✅ 使用成熟的模板和生成器
- ✅ 逐步验证每个配置项
- ✅ 参考官方文档和示例
- ❌ 避免手动编写复杂配置

### 3. 问题调试
- ✅ 提供完整的错误日志
- ✅ 说明环境和版本信息
- ✅ 分享相关配置文件内容
- ❌ 避免描述模糊的问题

## 📊 质量度量指标

### CI健康度评分
```
基础分 (60分):
- 配置语法正确: +10分
- 依赖安装成功: +10分  
- 代码格式化通过: +10分
- 基础测试通过: +10分
- 安全扫描通过: +10分
- 类型检查通过: +10分

加分项 (40分):
- 测试覆盖率>90%: +10分
- 零安全警告: +10分
- 文档完整性: +10分
- 性能基准达标: +10分

评级:
- 90-100分: 🟢 优秀
- 80-89分: 🟡 良好  
- 70-79分: 🟠 合格
- <70分: 🔴 需改进
```

