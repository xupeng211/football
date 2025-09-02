#!/bin/bash
# Football Data Platform - Production Quick Setup
set -e

echo "⚽ 足球数据中台 - 生产环境快速设置"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查依赖
echo -e "${BLUE}🔍 检查系统依赖...${NC}"

command -v docker >/dev/null 2>&1 || { echo -e "${RED}❌ Docker未安装${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}❌ Docker Compose未安装${NC}"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo -e "${RED}❌ uv未安装${NC}"; exit 1; }

echo -e "${GREEN}✅ 系统依赖检查通过${NC}"

# 环境配置检查
echo -e "${BLUE}🔧 检查环境配置...${NC}"

if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}⚠️ 生产环境配置文件不存在${NC}"
    echo -e "${BLUE}📋 复制配置模板...${NC}"
    cp .env.production.template .env.production
    echo -e "${YELLOW}📝 请编辑 .env.production 文件，填入真实配置${NC}"
    echo -e "${YELLOW}   特别是：FOOTBALL_DATA_API_KEY, DATABASE_URL, REDIS_URL${NC}"
    echo
    echo -e "${RED}❌ 请先配置 .env.production 然后重新运行此脚本${NC}"
    exit 1
fi

# 加载环境变量
echo -e "${BLUE}📁 加载生产环境配置...${NC}"
set -a
source .env.production
set +a

# 验证关键配置
if [ -z "$FOOTBALL_DATA_API_KEY" ] || [ "$FOOTBALL_DATA_API_KEY" = "your_real_api_key_here" ]; then
    echo -e "${RED}❌ FOOTBALL_DATA_API_KEY 未正确配置${NC}"
    exit 1
fi

if [ -z "$DATABASE_URL" ] || [[ "$DATABASE_URL" == *"username:password"* ]]; then
    echo -e "${RED}❌ DATABASE_URL 未正确配置${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境配置验证通过${NC}"

# 启动基础服务
echo -e "${BLUE}🚀 启动基础服务...${NC}"
docker-compose -f docker-compose.production.yml up -d

# 等待服务启动
echo -e "${BLUE}⏳ 等待服务启动 (30秒)...${NC}"
sleep 30

# 安装依赖
echo -e "${BLUE}📦 安装Python依赖...${NC}"
uv sync --frozen

# 数据库初始化
echo -e "${BLUE}🗄️ 初始化数据库...${NC}"
uv run python scripts/data_platform/setup_data_platform.py --action setup

# API连接测试
echo -e "${BLUE}📡 测试API连接...${NC}"
uv run python scripts/data_platform/setup_data_platform.py --action verify

# 运行生产就绪度检查
echo -e "${BLUE}🏭 运行生产就绪度检查...${NC}"
uv run python scripts/production/production_checklist.py

# 启动监控
echo -e "${BLUE}📈 启动监控服务...${NC}"
docker-compose -f docker-compose.production.yml up -d prometheus grafana

echo
echo -e "${GREEN}🎉 生产环境设置完成！${NC}"
echo
echo -e "${BLUE}📋 下一步操作：${NC}"
echo "  1. 访问 Grafana: http://localhost:3000 (admin/admin)"
echo "  2. 导入监控面板: monitoring/grafana/dashboards/"
echo "  3. 运行首次数据采集: make data-collect"
echo "  4. 部署定时任务: make data-deploy-flows"
echo
echo -e "${YELLOW}💡 提示：生产环境建议使用外部托管的PostgreSQL和Redis${NC}" 