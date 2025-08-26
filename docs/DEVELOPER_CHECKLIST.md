# 开发者检查清单

## 📋 **开发前检查**

### ✅ **环境设置**

- [ ] 激活虚拟环境 (`source .venv/bin/activate`)
- [ ] Python版本为3.11.x (`python --version`)
- [ ] 依赖已安装 (`pip install -e .`)
- [ ] 开发工具已安装 (`ruff`, `mypy`, `pytest`, `bandit`)
- [ ] Pre-commit钩子已设置 (`pre-commit install`)

### ✅ **IDE配置**

- [ ] Python解释器指向 `.venv/bin/python`
- [ ] 启用保存时自动格式化 (ruff)
- [ ] 启用类型检查提示 (mypy)
- [ ] 配置导入自动排序

### ✅ **基础验证**

- [ ] 运行 `make validate-configs` 验证配置文件
- [ ] 运行 `make quality-check` 确保基础质量
- [ ] 检查 `.env` 文件是否正确配置

---

## 📝 **编码期间检查**

### ✅ **类型注解**

- [ ] 所有函数都有返回类型注解
- [ ] 参数类型注解完整
- [ ] 复杂类型使用正确的类型提示

```python
# ✅ 正确示例
async def predict_match(request: PredictionRequest) -> PredictionResponse:
    return PredictionResponse(...)

# ❌ 错误示例
async def predict_match(request):  # 缺少类型注解
    pass
```

### ✅ **导入管理**

- [ ] 按标准顺序导入：标准库 → 第三方 → 本地
- [ ] 删除未使用的导入
- [ ] 使用绝对导入路径

```python
# ✅ 正确的导入顺序
from datetime import date, datetime      # 标准库
from uuid import uuid4

import structlog                         # 第三方库
from fastapi import APIRouter

from apps.api.core.logging import logger # 本地导入
```

### ✅ **代码格式**

- [ ] 遵循 88 字符行长度限制
- [ ] 使用 ruff 格式化标准
- [ ] 函数和类有适当的文档字符串

### ✅ **错误处理**

- [ ] 异常处理使用 `raise ... from e`
- [ ] 日志记录包含足够的上下文信息
- [ ] 避免裸露的 `except:` 语句

---

## 🧪 **提交前检查**

### ✅ **自动化检查**

- [ ] 运行 `make pre-commit-check` 全面检查
- [ ] 或者运行 `python scripts/quality-check.py`
- [ ] 确保所有检查都通过

### ✅ **手动验证**

- [ ] 代码格式化：`ruff format --check .`
- [ ] 代码规范：`ruff check .`
- [ ] 类型检查：`mypy apps/ data_pipeline/`
- [ ] 安全检查：`bandit -r . -c pyproject.toml`
- [ ] 测试通过：`pytest -v`

### ✅ **Git检查**

- [ ] 提交信息清晰且遵循规范
- [ ] 没有敏感信息 (密码、token等)
- [ ] 文件大小合理 (避免大文件)
- [ ] 分支是最新的

---

## 🚀 **推送前确认**

### ✅ **最终验证**

- [ ] 本地CI通过：`make ci`
- [ ] 分支与远程同步
- [ ] PR描述清晰

### ✅ **CI预期**

- [ ] 代码格式化检查会通过
- [ ] 所有lint规则会通过
- [ ] 类型检查会通过
- [ ] 安全扫描会通过
- [ ] 测试会通过

---

## 🔧 **常见问题快速修复**

### **代码格式问题**

```bash
# 自动修复格式化问题
make fix
# 或者
ruff format .
ruff check --fix .
```

### **类型注解问题**

```bash
# 检查具体的类型错误
mypy apps/api/routers/predictions.py --show-error-codes

# 常见修复模式
- 函数缺少返回类型：添加 -> ReturnType
- 参数缺少类型：添加 param: ParamType
- 返回类型不匹配：检查实际返回值类型
```

### **导入问题**

```bash
# 自动修复导入排序
ruff check --fix .

# 手动清理未使用导入
# 删除代码时记得删除相关导入
```

### **测试失败**

```bash
# 运行特定测试
pytest tests/test_specific.py -v

# 查看详细错误
pytest tests/ -v --tb=long

# 跳过失败的测试 (临时)
pytest tests/ -k "not failing_test"
```

---

## 📚 **有用的命令速查**

### **日常开发**

```bash
make help              # 查看所有可用命令
make quality-check     # 快速质量检查
make fix              # 自动修复问题
make pre-commit-check # 提交前检查
```

### **CI调试**

```bash
make ci               # 完整CI流程
make validate-configs # 验证配置文件
python scripts/quality-check.py # 详细质量检查
```

### **环境管理**

```bash
source .venv/bin/activate    # 激活虚拟环境
make setup-dev              # 自动化环境设置
make install                # 安装依赖
make clean                  # 清理临时文件
```

---

## 💡 **最佳实践提醒**

1. **预防胜于治疗**：开发时就保持高质量，而不是事后修复
2. **环境一致性**：确保本地环境与CI环境配置一致
3. **自动化优先**：依赖工具自动检查，减少人工错误
4. **渐进改善**：逐步提高代码质量标准
5. **文档更新**：及时更新文档和配置

---

## 🆘 **遇到问题时**

1. **检查虚拟环境**：确保在正确的虚拟环境中工作
2. **查看错误日志**：仔细阅读错误信息，通常包含修复提示
3. **运行自动修复**：使用 `make fix` 自动解决常见问题
4. **查看文档**：参考 `CI_PROBLEM_ANALYSIS_SUMMARY.md`
5. **寻求帮助**：在团队中分享问题和解决方案

---

**记住：良好的开发习惯是避免CI问题的最佳方法！** 🎯
