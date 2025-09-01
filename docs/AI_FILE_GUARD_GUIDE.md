# 🤖 AI文件操作守护系统使用指南

## 📖 概述

AI文件操作守护系统是一套专门设计的工具，用于防止AI编程工具在不合适的地方创建重复文件，引导AI进行正确的文件操作。

### 🎯 解决的核心问题

- **重复文件创建** - AI工具经常创建 `test_api_copy.py`, `config_new.py` 等重复文件
- **位置不当** - 在错误的目录创建文件
- **命名混乱** - 使用临时、备份等不规范的文件名
- **缺乏上下文** - AI不了解项目结构和现有文件

## 🛡️ 系统组件

### 1. **AI文件守护程序** (`scripts/ai_file_guard.py`)

**功能**: 检查单个文件的创建是否合规

```bash
# 检查文件是否应该创建
make ai-file-guard FILE=test_new_api.py

# 或直接使用脚本
python3 scripts/ai_file_guard.py test_new_api.py
```

**输出示例**:

```
🤖 AI文件操作检查
========================================
❌ 不建议创建此文件:
  • 避免使用 '_new' 后缀
💡 建议:
  • 使用更明确的文件名
📁 相似文件:
  • ./tests/unit/test_api.py (0.85)
📍 推荐路径:
  1. tests/unit/test_api.py
  2. tests/integration/test_api.py
========================================
```

### 2. **实时文件监控器** (`scripts/ai_file_monitor.py`)

**功能**: 监控最近修改的文件并自动检查

```bash
# 检查最近10分钟的文件操作
make ai-file-check

# 或指定时间范围
python3 scripts/ai_file_monitor.py scan 30  # 30分钟
python3 scripts/ai_file_monitor.py status   # 查看状态
```

### 3. **文件操作规则** (`ai_file_rules.json`)

**功能**: 定义项目的文件组织规范

```json
{
  "forbidden_patterns": {
    "suffixes": ["_copy", "_backup", "_new", "_old", "_temp"],
    "names": ["temp.py", "test.py", "new_file.py"]
  },
  "location_rules": {
    "test_files": {
      "pattern": "test_*.py",
      "allowed_locations": ["tests/unit/", "tests/integration/"],
      "prefer_location": "tests/unit/"
    }
  }
}
```

## 🚀 快速开始

### 1. **基础检查**

```bash
# 检查环境是否就绪
make ai-check

# 检查最近的文件操作
make ai-file-check
```

### 2. **VS Code集成**

1. 打开命令面板 (`Ctrl+Shift+P`)
2. 选择 `Tasks: Run Task`
3. 选择以下任务之一：
   - `🤖 AI: 检查文件操作` - 检查最近文件变化
   - `🤖 AI: 检查当前文件` - 检查当前打开的文件

### 3. **Git集成**

每次提交时自动运行文件检查：

```bash
# 启用Git hooks (已在ai-setup中包含)
make setup-hooks

# 提交时会自动检查
git commit -m "add new feature"
```

## 📋 使用场景

### 场景1: AI想创建重复测试文件

**问题**: AI建议创建 `test_api_enhanced.py`

**解决**:

```bash
make ai-file-guard FILE=test_api_enhanced.py
```

**结果**:

- 检测到已有 `test_api.py` (相似度 0.85)
- 建议修改现有文件而不是创建新文件

### 场景2: AI在错误位置创建文件

**问题**: AI在根目录创建 `user_service.py`

**解决**:

- 系统自动检测位置不当
- 建议移动到 `src/football_predict_system/domain/`

### 场景3: 定期检查项目文件健康度

**定期运行**:

```bash
# 每天检查
make ai-file-check

# 查看历史状态
python3 scripts/ai_file_monitor.py status
```

## ⚙️ 高级配置

### 自定义规则

编辑 `ai_file_rules.json`:

```json
{
  "location_rules": {
    "my_custom_files": {
      "pattern": "my_*.py",
      "allowed_locations": ["src/custom/"],
      "max_similar_files": 1
    }
  }
}
```

### 调整敏感度

```python
# 在脚本中修改相似度阈值
similarity_threshold = 0.6  # 降低=更严格，提高=更宽松
```

## 🔧 常见问题

### Q: 如何让AI工具自动遵循这些规则？

**A**: 在AI提示中包含：

```
在创建文件前，请运行：make ai-file-guard FILE=<filename>
根据输出调整文件名和位置
```

### Q: 系统误报怎么办？

**A**:

1. 检查 `ai_file_rules.json` 配置
2. 调整相似度阈值
3. 添加例外规则

### Q: 如何集成到CI/CD？

**A**:

```yaml
# .github/workflows/ci.yml
- name: Check file operations
  run: make ai-file-check
```

## 📊 监控和反馈

### 状态文件

系统会生成状态文件：

- `data/feedback/ai_file_status.json` - 文件检查状态
- `data/feedback/ai_environment_status.json` - 环境状态

### 查看统计

```bash
# 查看详细状态
python3 scripts/ai_file_monitor.py status

# 查看JSON格式
cat data/feedback/ai_file_status.json | jq .summary
```

## 🎯 最佳实践

### 1. **与AI工具协作**

在与AI对话时：

```
我要创建一个新的API测试文件，请先检查：
make ai-file-guard FILE=test_new_api.py

根据检查结果决定是创建新文件还是修改现有文件。
```

### 2. **定期健康检查**

```bash
# 每周运行
make ai-file-check

# 检查是否有重复或不规范的文件
```

### 3. **团队协作**

1. 所有成员都启用 `make ai-setup`
2. 统一的 `ai_file_rules.json` 配置
3. 在代码评审中检查文件组织

## 🔗 相关文档

- [AI工具指南](AI_TOOLS_GUIDE.md)
- [开发指南](DEVELOPMENT.md)
- [项目README](../README.md)

---

*这个系统会持续学习和改进，帮助AI工具更好地理解项目结构！* 🚀
