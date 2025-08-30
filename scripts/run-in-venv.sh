#!/bin/bash
# 强制在虚拟环境中执行命令的脚本

# 颜色定义
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 获取脚本所在的目录
SCRIPT_DIR=$(dirname "$0")

# 激活虚拟环境
# shellcheck source=scripts/activate-venv.sh
source "$SCRIPT_DIR/activate-venv.sh"

# 检查是否传入了命令
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: No command provided.${NC}"
    echo "Usage: $0 <command-to-execute>"
    exit 1
fi

# 执行传入的命令
echo -e "${BLUE}🚀 Executing command in venv: $@${NC}"
echo "======================================"
"$@"
