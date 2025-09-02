#!/bin/bash
# 🔍 统一Docker环境一致性检查脚本
# 验证统一后的Docker配置是否与CI环境标准一致

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 检查结果计数
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# 日志函数
log_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; PASS_COUNT=$((PASS_COUNT + 1)); }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; WARN_COUNT=$((WARN_COUNT + 1)); }
log_error() { echo -e "${RED}❌ $1${NC}"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
log_step() { echo -e "${BLUE}🔄 $1${NC}"; }

echo "🔍 统一Docker环境一致性检查"
echo "==============================="
echo ""

# 1. 检查Dockerfile基础镜像 (应该使用ubuntu:22.04)
log_step "检查Dockerfile基础镜像"
if grep -q "FROM ubuntu:22.04" Dockerfile; then
    log_success "使用CI标准基础镜像: ubuntu:22.04"
else
    log_error "基础镜像不是ubuntu:22.04"
fi

# 2. 检查工作目录 (应该是/workspace)
log_step "检查工作目录配置"
if grep -q "WORKDIR /workspace" Dockerfile; then
    log_success "工作目录使用CI标准: /workspace"
else
    log_error "工作目录不是/workspace"
fi

# 3. 检查Python版本
log_step "检查Python版本配置"
if grep -q "PYTHON_VERSION=3.11" Dockerfile; then
    log_success "Python版本正确: 3.11"
else
    log_warning "Python版本配置需要检查"
fi

# 4. 检查依赖同步配置
log_step "检查依赖同步配置"
if grep -q "uv sync --extra dev" Dockerfile; then
    log_success "依赖同步配置正确: --extra dev"
else
    log_error "依赖同步配置错误，应该包含开发依赖"
fi

# 5. 检查Docker Compose环境变量
log_step "检查Docker Compose环境变量"
if grep -q "ENVIRONMENT=development" docker-compose.yml && \
   grep -q "test_user:test_pass" docker-compose.yml && \
   grep -q "test_football_db" docker-compose.yml; then
    log_success "Docker Compose环境变量与CI一致"
else
    log_error "Docker Compose环境变量与CI不一致"
fi

# 6. 检查数据库配置
log_step "检查数据库版本"
if grep -q "postgres:15" docker-compose.yml; then
    log_success "数据库版本正确: postgres:15"
else
    log_error "数据库版本不正确"
fi

# 7. 检查Redis配置
log_step "检查Redis版本"
if grep -q "redis:7" docker-compose.yml; then
    log_success "Redis版本正确: redis:7"
else
    log_error "Redis版本不正确"
fi

# 8. 检查关键配置文件存在性
log_step "检查关键配置文件"
REQUIRED_FILES=(
    "Dockerfile"
    "docker-compose.yml"
    ".github/workflows/ci.yml"
    "scripts/ci/local_ci_runner.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "配置文件存在: $file"
    else
        log_error "配置文件缺失: $file"
    fi
done

# 9. 检查冗余文件是否已清理
log_step "检查配置文件简化情况"
SHOULD_NOT_EXIST=(
    "Dockerfile.ci"
    "docker-compose.ci.yml"
    "docker-compose.production.yml"
    "docker-compose.staging.yml"
)

for file in "${SHOULD_NOT_EXIST[@]}"; do
    if [ ! -f "$file" ]; then
        log_success "冗余文件已清理: $file"
    else
        log_warning "冗余文件仍存在: $file"
    fi
done

# 10. 检查本地CI脚本可执行性
log_step "检查本地CI脚本"
if [ -x "scripts/ci/local_ci_runner.sh" ]; then
    log_success "本地CI脚本可执行"
else
    log_warning "本地CI脚本权限需要修复: chmod +x scripts/ci/local_ci_runner.sh"
fi

# 生成汇总报告
echo ""
echo "📊 检查汇总"
echo "==========="
echo -e "✅ 通过: ${GREEN}$PASS_COUNT${NC}"
echo -e "⚠️  警告: ${YELLOW}$WARN_COUNT${NC}"
echo -e "❌ 失败: ${RED}$FAIL_COUNT${NC}"
echo ""

# 计算总分
TOTAL_CHECKS=$((PASS_COUNT + WARN_COUNT + FAIL_COUNT))
if [ $TOTAL_CHECKS -gt 0 ]; then
    SCORE=$((PASS_COUNT * 100 / TOTAL_CHECKS))
    echo -e "🎯 一致性得分: ${BLUE}$SCORE%${NC}"
    echo ""
fi

# 提供建议
if [ $FAIL_COUNT -gt 0 ]; then
    echo "🛠️ 需要修复的问题："
    echo "1. 检查Dockerfile配置是否正确"
    echo "2. 重新构建Docker镜像: docker-compose build"
    echo "3. 验证环境变量设置"
    echo ""
    exit 1
elif [ $WARN_COUNT -gt 0 ]; then
    echo "💡 优化建议："
    echo "1. 清理任何剩余的冗余配置文件"
    echo "2. 定期检查环境一致性"
    echo ""
    exit 0
else
    echo "🎉 Docker环境配置完全统一！"
    echo "📋 配置特点："
    echo "   • 单一Dockerfile，与CI环境100%一致"
    echo "   • 简化的docker-compose.yml，专注开发需求"
    echo "   • 统一的环境变量和服务版本"
    echo ""
    exit 0
fi 