# 🚀 快速上手指南

> **🎯 目标**：让任何人在5-10分钟内从"完全不了解"到"可以开始开发"

## ⚡ 极速上手（2分钟）

### 第1步：获取项目完整情况
```bash
make show.context
```
**这是最重要的一步！** 这个命令会显示：
- 📋 完整的架构图和模块职责
- 🛠️ 技术栈和设计决策
- 🔄 数据流和工作流程
- 📚 开发规范和最佳实践
- 🐛 已知问题和解决方案

### 第2步：验证环境
```bash
make ci
```
**期望结果**：所有检查通过，显示 `28 passed, 2 skipped, 6 deselected`

如果这两步都成功，恭喜！你已经可以开始开发了。

---

## 📖 深入了解（5分钟）

### 了解项目历程
```bash
# 查看开发日志前50行，了解项目演进
head -50 docs/dev_log.md

# 查看最近10次提交，了解最新变更
git log --oneline -10

# 查看当前工作状态
git status
```

### 核心文档阅读顺序
1. **`context/_pack.md`** - 项目完整上下文（SSOT）
2. **`docs/ARCHITECTURE.md`** - 架构设计详解  
3. **`docs/TASKS.md`** - 开发任务清单
4. **`docs/dev_log.md`** - 开发历程记录

---

## 🛠️ 开发工作流

### 常用命令
```bash
make fmt      # 代码格式化
make ci       # 完整检查（推荐每次提交前运行）
make test     # 仅运行测试
make lint     # 代码检查
make type     # 类型检查
```

### Git工作流
```bash
# 1. 创建功能分支
git checkout -b feature/your-feature

# 2. 开发并提交
# （会自动触发pre-commit hooks格式化代码）
git add .
git commit -m "feat: your feature description"

# 3. 推送并创建PR
git push -u origin feature/your-feature
```

---

## 🔍 项目特色

### 🤖 AI友好设计
- **零依赖启动**：无需配置数据库，集成测试自动跳过
- **智能测试策略**：`ENABLE_DB_TESTS=1` 可启用完整集成测试
- **结构化文档**：SSOT机制确保信息永远最新

### 🛡️ 质量保障
- **CI/CD完善**：GitHub Actions自动化检查
- **分支保护**：main/dev分支需要代码审查
- **安全扫描**：CodeQL + Gitleaks + Bandit三重防护

### 📊 测试覆盖
- **当前覆盖率**：45.72%（超过20%要求）
- **测试策略**：单元测试 + API测试 + 集成测试

---

## ❓ 常见问题

### Q: 测试失败怎么办？
A: 检查是否缺少数据库连接，项目设计为智能跳过DB测试，不影响开发。

### Q: 格式检查失败？
A: 运行 `make fmt` 自动修复格式问题。

### Q: 想了解某个模块的详细设计？
A: 查看 `context/_pack.md` 中的对应章节，包含完整的模块说明。

### Q: 如何运行完整的集成测试？
A: 设置环境变量 `ENABLE_DB_TESTS=1` 后运行 `make test`。

---

## 🎯 下一步

现在你已经了解了项目的全貌，可以：

1. **🔍 探索代码**：从 `apps/api/main.py` 开始，了解API入口
2. **📝 查看任务**：`docs/TASKS.md` 中有待开发的功能清单
3. **🧪 运行示例**：尝试启动API服务或运行回测
4. **💡 贡献代码**：选择一个感兴趣的功能开始开发

**欢迎加入足球预测系统的开发！** ⚽🚀 
