#!/bin/bash
# 虚拟环境检查脚本 - 用于AI开发工具强制验证

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 虚拟环境状态检查${NC}"
echo "=========================="

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${RED}❌ 错误: 未激活虚拟环境${NC}"
    echo -e "${YELLOW}💡 请运行: source .venv/bin/activate${NC}"
    echo
    echo -e "${BLUE}或使用自动激活脚本:${NC}"
    echo -e "${YELLOW}source scripts/activate-venv.sh${NC}"
    exit 1
fi

# 检查虚拟环境路径
EXPECTED_VENV=$(pwd)/.venv
if [[ "$VIRTUAL_ENV" != "$EXPECTED_VENV" ]]; then
    echo -e "${YELLOW}⚠️  警告: 虚拟环境路径不匹配${NC}"
    echo -e "当前: $VIRTUAL_ENV"
    echo -e "期望: $EXPECTED_VENV"
fi

# 检查Python版本
PYTHON_VERSION=$(python --version 2>&1)
if [[ ! "$PYTHON_VERSION" =~ "Python 3.11" ]]; then
    echo -e "${RED}❌ 错误: Python版本不正确${NC}"
    echo -e "当前: $PYTHON_VERSION"
    echo -e "期望: Python 3.11.x"
    exit 1
fi

# 检查关键开发工具
echo -e "${BLUE}📦 检查开发工具...${NC}"
TOOLS=("ruff" "mypy" "pytest" "bandit")
for tool in "${TOOLS[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $tool: $(which $tool)${NC}"
    else
        echo -e "${RED}❌ $tool: 未安装${NC}"
        echo -e "${YELLOW}💡 请运行: make install${NC}"
        exit 1
    fi
done

# 检查项目是否以开发模式安装
if python -c "import football_predictor" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ 项目已以开发模式安装${NC}"
else
    echo -e "${YELLOW}⚠️  项目未以开发模式安装${NC}"
    echo -e "${YELLOW}💡 请运行: pip install -e .${NC}"
fi

echo
echo -e "${GREEN}🎉 虚拟环境检查通过！${NC}"
echo -e "${BLUE}虚拟环境: $VIRTUAL_ENV${NC}"
echo -e "${BLUE}Python: $PYTHON_VERSION${NC}"
echo -e "${BLUE}工作目录: $(pwd)${NC}"
