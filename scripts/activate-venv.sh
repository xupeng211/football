#!/bin/bash
# 虚拟环境自动激活脚本 - AI开发工具使用

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 自动激活虚拟环境${NC}"
echo "======================"

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 虚拟环境不存在，正在创建...${NC}"
    python -m venv .venv
    echo -e "${GREEN}✅ 虚拟环境已创建${NC}"
fi

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
    echo -e "${GREEN}✅ 虚拟环境已激活 (Windows)${NC}"
else
    echo -e "${RED}❌ 无法找到激活脚本${NC}"
    exit 1
fi

# 升级pip
python -m pip install --upgrade pip >/dev/null 2>&1

# 检查依赖是否安装
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📋 检查项目依赖...${NC}"
    if ! python -c "import fastapi, pandas, numpy" >/dev/null 2>&1; then
        echo -e "${YELLOW}🔧 安装项目依赖...${NC}"
        pip install -r requirements.txt
        pip install -e .
        echo -e "${GREEN}✅ 依赖安装完成${NC}"
    else
        echo -e "${GREEN}✅ 依赖已安装${NC}"
    fi
fi

echo
echo -e "${GREEN}🎯 环境信息:${NC}"
echo -e "${BLUE}虚拟环境: $VIRTUAL_ENV${NC}"
echo -e "${BLUE}Python: $(python --version)${NC}"
echo -e "${BLUE}工作目录: $(pwd)${NC}"
echo
echo -e "${GREEN}💡 现在可以安全地进行AI辅助开发！${NC}"
