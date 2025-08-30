#!/bin/bash
# 代码质量预推送检查脚本
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 开始代码质量检查...${NC}"

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ] && [ "$CI" != "true" ]; then
    echo -e "${RED}❌ 请先激活虚拟环境！${NC}"
    echo -e "${YELLOW}运行: source .venv/bin/activate${NC}"
    exit 1
fi

# 1. 代码格式化检查
echo -e "${BLUE}1️⃣ 代码格式化检查...${NC}"
if ! ruff format --check .; then
    echo -e "${YELLOW}⚠️ 代码格式需要修复，正在自动修复...${NC}"
    ruff format .
    echo -e "${GREEN}✅ 代码格式已修复${NC}"
fi

# 2. 代码质量检查
echo -e "${BLUE}2️⃣ 代码质量检查...${NC}"
if ! ruff check .; then
    echo -e "${YELLOW}⚠️ 发现代码质量问题，尝试自动修复...${NC}"
    ruff check --fix .

    # 再次检查是否还有问题
    if ! ruff check .; then
        echo -e "${RED}❌ 存在无法自动修复的代码质量问题${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ 代码质量检查通过${NC}"

# 3. 类型检查
echo -e "${BLUE}3️⃣ 类型检查...${NC}"
if ! mypy apps/ data_pipeline/ --ignore-missing-imports --no-error-summary; then
    echo -e "${RED}❌ 类型检查失败${NC}"
    echo -e "${YELLOW}💡 提示: 运行 'mypy apps/ data_pipeline/' 查看详细错误${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 类型检查通过${NC}"

# 4. 安全检查
echo -e "${BLUE}4️⃣ 安全检查...${NC}"
if ! bandit -r . -c pyproject.toml -q; then
    echo -e "${RED}❌ 安全检查发现问题${NC}"
    echo -e "${YELLOW}💡 提示: 运行 'bandit -r . -c pyproject.toml' 查看详细信息${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 安全检查通过${NC}"

# 5. 快速测试
echo -e "${BLUE}5️⃣ 快速测试...${NC}"
if ! python -m pytest tests/ -x --tb=short --disable-warnings -m "not slow" -q; then
    echo -e "${RED}❌ 快速测试失败${NC}"
    echo -e "${YELLOW}💡 提示: 运行 'pytest tests/ -v' 查看详细错误${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 快速测试通过${NC}"

# 6. 覆盖率检查
echo -e "${BLUE}6️⃣ 覆盖率检查...${NC}"
COVERAGE_MIN=${COV_MIN:-70}
if ! python -m pytest --cov=apps --cov=data_pipeline --cov=models \
    --cov-report=term-missing --cov-fail-under=$COVERAGE_MIN \
    --disable-warnings -q; then
    echo -e "${RED}❌ 测试覆盖率低于 ${COVERAGE_MIN}%${NC}"
    echo -e "${YELLOW}💡 提示: 添加更多测试或调整覆盖率要求${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 覆盖率检查通过${NC}"

# 7. 配置文件验证
echo -e "${BLUE}7️⃣ 配置文件验证...${NC}"
python -c "
import tomllib
import yaml
import sys

try:
    # 验证 pyproject.toml
    with open('pyproject.toml', 'rb') as f:
        tomllib.load(f)

    # 验证 CI 配置
    with open('.github/workflows/ci.yml', 'r') as f:
        yaml.safe_load(f)

    print('✅ 配置文件验证通过')
except Exception as e:
    print(f'❌ 配置文件验证失败: {e}')
    sys.exit(1)
"

# 8. Git状态检查
echo -e "${BLUE}8️⃣ Git状态检查...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️ 检测到未提交的更改:${NC}"
    git status --porcelain
    echo -e "${YELLOW}💡 请确保所有更改都已暂存${NC}"
fi

echo -e "${GREEN}🎉 所有检查通过！代码可以安全推送${NC}"
echo -e "${BLUE}📊 质量报告:${NC}"
echo -e "  - 代码格式: ✅ 符合标准"
echo -e "  - 代码质量: ✅ 无问题"
echo -e "  - 类型安全: ✅ 通过检查"
echo -e "  - 安全扫描: ✅ 无漏洞"
echo -e "  - 测试状态: ✅ 全部通过"
echo -e "  - 覆盖率: ✅ 达标 (≥${COVERAGE_MIN}%)"

exit 0
