#!/bin/bash
# CI预检查脚本 - 推送前完整验证

set -e

echo "🔍 CI预检查开始..."
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数器
CHECKS_PASSED=0
CHECKS_TOTAL=0

check_status() {
    ((CHECKS_TOTAL++))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $2${NC}"
        return 1
    fi
}

echo "📦 1. 检查依赖文件..."
test -f requirements.txt && check_status 0 "requirements.txt 存在" || check_status 1 "requirements.txt 缺失"
test -f uv.lock && check_status 0 "uv.lock 存在" || check_status 1 "uv.lock 缺失"
test -f pyproject.toml && check_status 0 "pyproject.toml 存在" || check_status 1 "pyproject.toml 缺失"

echo ""
echo "🔧 2. 检查配置文件语法..."
python -c "import tomllib; tomllib.load(open('.gitleaks.toml','rb'))" 2>/dev/null && \
    check_status 0 ".gitleaks.toml 语法正确" || check_status 1 ".gitleaks.toml 语法错误"

python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" 2>/dev/null && \
    check_status 0 "ci.yml 语法正确" || check_status 1 "ci.yml 语法错误"

echo ""
echo "🔒 3. 运行安全预扫描..."
if command -v gitleaks >/dev/null 2>&1; then
    gitleaks detect --source . --config .gitleaks.toml >/dev/null 2>&1 && \
        check_status 0 "Gitleaks安全扫描通过" || check_status 1 "发现安全问题"
else
    echo -e "${YELLOW}⚠️ gitleaks 未安装，跳过本地安全检查${NC}"
fi

echo ""
echo "🧪 4. 运行测试套件..."
python -m pytest --cov=apps --cov=data_pipeline --cov=models --cov-fail-under=15 -q --tb=no >/dev/null 2>&1 && \
    check_status 0 "测试套件通过" || check_status 1 "测试失败"

echo ""
echo "📏 5. 代码质量检查..."
ruff check . >/dev/null 2>&1 && \
    check_status 0 "Ruff检查通过" || check_status 1 "Ruff发现问题"

ruff format --check . >/dev/null 2>&1 && \
    check_status 0 "格式检查通过" || check_status 1 "格式问题"

echo ""
echo "🎯 CI预检查完成！"
echo "========================================"
echo -e "结果: ${GREEN}${CHECKS_PASSED}/${CHECKS_TOTAL}${NC} 检查通过"

if [ $CHECKS_PASSED -eq $CHECKS_TOTAL ]; then
    echo -e "${GREEN}🎉 所有检查通过，可以安全推送！${NC}"
    exit 0
else
    echo -e "${RED}❌ 有检查失败，建议修复后再推送${NC}"
    echo ""
    echo "🔧 快速修复建议:"
    echo "1. 运行 ruff format . 修复格式问题"
    echo "2. 运行 ruff check --fix . 自动修复可修复的问题"
    echo "3. 检查测试失败原因: python -m pytest -v"
    exit 1
fi
