#!/bin/bash
# Football Data Platform - Database Backup Script
# 足球数据平台数据库备份脚本

set -e

# 配置
BACKUP_DIR="/backup/football_data"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_DIR/backup.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🗄️ 开始数据库备份...${NC}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 从环境变量获取数据库连接信息
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL 环境变量未设置${NC}"
    exit 1
fi

# 执行备份
BACKUP_FILE="$BACKUP_DIR/football_db_$DATE.sql"
echo -e "${YELLOW}📦 备份到: $BACKUP_FILE${NC}"

pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
gzip "$BACKUP_FILE"

echo -e "${GREEN}✅ 数据库备份完成: ${BACKUP_FILE}.gz${NC}"

# 清理旧备份 (保留30天)
echo -e "${YELLOW}�� 清理30天前的备份...${NC}"
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

# 记录日志
echo "$(date): Backup completed - ${BACKUP_FILE}.gz" >> "$LOG_FILE"

# 显示备份大小
BACKUP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
echo -e "${GREEN}📊 备份大小: $BACKUP_SIZE${NC}"

echo -e "${GREEN}🎉 备份流程完成！${NC}"
