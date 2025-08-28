# AI 编程工具开发规则

## 🤖 AI 开发强制规范

本文档为所有 AI 编程工具（包括但不限于 Cursor、GitHub Copilot、Claude、GPT等）制定强制性开发规范。

---

## ⚠️ **核心规则：强制虚拟环境**

### 🔒 **规则 #1: 虚拟环境强制启用**

**所有 AI 编程工具在进行代码开发时必须在虚拟环境中运行**

```bash
# ✅ 正确：始终在虚拟环境中开发
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# ❌ 错误：直接在系统Python中开发
python script.py  # 没有激活虚拟环境
```

### 📋 **检查清单**

在开始任何开发任务前，AI工具必须验证：

- [ ] ✅ 虚拟环境已激活 (`which python` 应指向 `.venv/`)
- [ ] ✅ Python版本正确 (`python --version` 应显示 3.11.9)
- [ ] ✅ 项目依赖已安装 (`pip list` 包含项目依赖)
- [ ] ✅ 开发工具可用 (ruff, mypy, pytest 等)

---

## 🛠️ **强制执行机制**

### 1. **Makefile 自动检查**

所有 `make` 命令都会自动检查虚拟环境：

```bash
make install   # 自动检查并提示
make ci        # 强制虚拟环境运行
make test      # 虚拟环境中执行测试
```

### 2. **脚本级别验证**

项目包含虚拟环境检查脚本：

```bash
# 检查虚拟环境状态
./scripts/check-venv.sh

# 自动激活虚拟环境
source scripts/activate-venv.sh
```

### 3. **Pre-commit 钩子**

所有提交前检查都在虚拟环境中运行：

```bash
pre-commit run --all-files  # 自动使用虚拟环境
```

---

## 🎯 **AI 工具特定指令**

### **对于 Cursor / VS Code**
```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

### **对于命令行 AI 工具**
```bash
# 每次会话开始时
source .venv/bin/activate && python --version
```

### **对于代码生成 AI**
- 生成的代码必须假设在虚拟环境中运行
- 导入语句使用项目已安装的依赖版本
- 不得建议全局安装包

---

## 🚨 **违规处理**

### **轻微违规（警告）**
- 在系统Python中运行单个命令
- 建议全局安装包

### **严重违规（拒绝执行）**
- 修改系统Python环境
- 安装与项目requirements.txt冲突的包
- 在未激活虚拟环境状态下执行复杂开发任务

---

## 📚 **快速参考**

### **环境设置**
```bash
# 创建虚拟环境（仅首次）
python -m venv .venv

# 激活虚拟环境（每次开发）
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 安装依赖
make install

# 验证环境
make ci
```

### **常用开发命令**
```bash
make fmt      # 格式化代码
make lint     # 代码检查
make type     # 类型检查
make test     # 运行测试
make ci       # 完整CI检查
```

---

## 🎯 **目标效果**

遵循本规则后，项目将实现：

- ✅ **环境一致性**: 所有AI工具使用相同的Python环境
- ✅ **依赖隔离**: 不污染系统Python环境
- ✅ **版本一致**: 确保Python 3.11.9和锁定的依赖版本
- ✅ **工具兼容**: 所有开发工具在统一环境中工作
- ✅ **问题减少**: 避免"在我机器上能运行"的问题

---

**💡 记住：好的开发习惯从虚拟环境开始！**
