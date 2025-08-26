# 🤖 AI 开发工具快速入门

## ⚡ 30秒快速开始

```bash
# 1. 克隆项目后立即运行
source scripts/activate-venv.sh

# 2. 安装依赖
make install

# 3. 验证环境
make ci

# 4. 开始开发！
```

## 🎯 常用AI开发命令

| 命令 | 说明 | 必须在虚拟环境 |
|------|------|----------------|
| `make check-venv` | 检查虚拟环境状态 | ✅ |
| `make ci` | 完整CI检查 | ✅ |
| `make fmt` | 格式化代码 | ✅ |
| `make test` | 运行测试 | ✅ |

## 🛡️ AI 安全规则

### ✅ 允许的操作
- 在虚拟环境中安装项目依赖
- 运行测试和代码检查
- 生成符合项目标准的代码

### ❌ 禁止的操作
- 在系统Python中安装包
- 修改全局Python环境
- 绕过虚拟环境检查

## 🔧 故障排除

### 问题：未激活虚拟环境
```bash
# 解决方案
source scripts/activate-venv.sh
```

### 问题：Python版本不正确
```bash
# 检查版本
python --version

# 应该显示：Python 3.11.9
```

### 问题：缺少开发工具
```bash
# 重新安装
make install
```

## 📱 编辑器集成

### VS Code / Cursor
- 使用项目提供的 `.vscode/settings.json`
- 自动激活虚拟环境
- 集成代码检查工具

### 命令行工具
- 使用 `direnv`（如果安装）自动激活
- 或手动运行 `source scripts/activate-venv.sh`

---

**💡 记住：好的AI开发从虚拟环境开始！**
