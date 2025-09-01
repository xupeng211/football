# 🤖 AI工具使用指南

> 简单实用的AI编程工具使用指南

## 🚀 快速开始

### 1. **环境检查**

```bash
# AI专用环境检查
make ai-check

# 完整AI设置（推荐首次使用）
make ai-setup
```

### 2. **开发流程**

```bash
# 标准开发流程
make install    # 安装依赖
make dev       # 启动开发服务器
make ci        # 代码质量检查
make test      # 运行测试
```

## 🎯 AI工具友好特性

### **环境标识**

- 终端提示: `🤖 AI-DEV`
- VS Code配置: AI Development profile
- 专用健康检查: `make ai-check`

### **一键命令**

| 命令 | 功能 | AI使用场景 |
|------|------|------------|
| `make help` | 查看所有命令 | 了解项目能力 |
| `make doctor` | 环境诊断 | 排查问题 |
| `make ai-check` | AI环境检查 | 快速状态确认 |
| `make ai-setup` | AI优化设置 | 初始化AI友好环境 |
| `make ci` | 代码质量检查 | 确保代码质量 |

### **项目结构**

```
football-predict-system/
├── 📄 pyproject.toml         # 统一配置文件
├── ⚡ Makefile               # 一键命令系统
├── 🤖 .vscode/               # VS Code AI配置
├── 📊 data/feedback/         # AI反馈数据
├── 🏗️ src/                   # 源代码
└── 🧪 tests/                 # 测试代码
```

## 📊 AI状态监控

### **状态文件**

```json
// data/feedback/ai_environment_status.json
{
  "python_version": "3.11.9",
  "tools_available": ["uv", "ruff", "pytest"],
  "project_files_ok": ["pyproject.toml", "Makefile", ...]
}
```

### **VS Code集成**

- 自动代码格式化 (ruff)
- 类型检查 (mypy)
- 智能补全增强
- AI开发环境配置

## 🔧 常见问题解决

### **权限问题**

```bash
make fix-permissions  # 修复虚拟环境权限
```

### **环境问题**

```bash
make clean           # 清理缓存
make install         # 重新安装依赖
make ai-check        # 检查状态
```

### **代码质量**

```bash
make format          # 代码格式化
make lint           # 代码检查
make type           # 类型检查
```

## 🤖 自动触发机制

### **VS Code自动化**

当打开项目工作区时：

- ✅ 自动推荐AI相关扩展（Copilot、Pylance等）
- ✅ 自动运行 `make ai-setup` 初始化环境
- ✅ 智能补全和自动导入已配置

### **Git Hooks自动化**

每次提交代码时：

- ✅ 自动运行 `make ai-check` 环境检查
- ✅ 自动运行 `make ci` 代码质量检查
- ✅ 检查失败时阻止提交

### **启用自动化**

```bash
# 一键启用所有自动化功能
make ai-setup

# 或分别启用
make setup-hooks    # 仅启用Git hooks
```

## 💡 AI工具最佳实践

### **1. 使用前检查**

```bash
# 每次开始工作前
make ai-setup
```

### **2. 实时状态监控**

- 观察终端提示 `🤖 AI-DEV`
- 查看 `data/feedback/ai_environment_status.json`
- 使用 `make doctor` 诊断问题

### **3. 代码质量保证**

```bash
# 提交前必做
make ci              # 全面检查
```

### **4. 项目理解**

- 阅读 `README.md` - 项目概述
- 查看 `pyproject.toml` - 配置信息
- 运行 `make help` - 可用命令
- 检查 `src/` - 源代码结构

## 🎉 AI友好性评分

当前项目评分: **9.0/10** ⭐

### **评分标准**

- ✅ 环境标识清晰 (2分)
- ✅ 一键命令完整 (2分)
- ✅ 项目结构合理 (2分)
- ✅ 工具链现代化 (2分)
- ✅ 文档完善 (1分)

---

📧 **问题反馈**: 遇到问题请查看项目Issues或联系维护者
🔄 **更新日志**: 查看 `VERSION_HISTORY.md`
📚 **更多文档**: 查看 `docs/` 目录
