#!/bin/bash
# 🎭 Local CI Orchestrator - Docker容器编排和CI执行管理
# 负责启动Docker容器，执行CI，并清理资源

set -euo pipefail

# 配置变量
DOCKER_IMAGE="football-predict-ci:latest"
CONTAINER_NAME="football-ci-$(date +%s)"
PROJECT_ROOT="$(pwd)"
CI_TIMEOUT=600  # 10分钟超时

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${BLUE}🔄 $1${NC}"; }

# 清理函数
cleanup() {
    local exit_code=$?
    log_step "清理Docker资源..."
    
    # 停止并删除容器
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    fi
    
    if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
        docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
    fi
    
    # 清理临时文件
    rm -f /tmp/ci-output.log /tmp/ci-error.log
    
    exit $exit_code
}

# 设置清理陷阱
trap cleanup EXIT INT TERM

# 检查Docker环境
check_docker() {
    log_step "检查Docker环境"
    
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker未安装或不可用"
        return 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon未运行"
        return 1
    fi
    
    log_success "Docker环境正常"
    return 0
}

# 构建CI镜像
build_ci_image() {
    log_step "构建本地CI镜像"
    
    # 检查镜像是否存在且是最新的
    if docker images -q "$DOCKER_IMAGE" | grep -q .; then
        local image_age=$(docker inspect -f '{{.Created}}' "$DOCKER_IMAGE" | xargs -I {} date -d {} +%s)
        local current_time=$(date +%s)
        local age_hours=$(( (current_time - image_age) / 3600 ))
        
        if [ $age_hours -lt 24 ]; then
            log_info "使用现有CI镜像 (${age_hours}小时前构建)"
            return 0
        else
            log_warning "CI镜像已过期 (${age_hours}小时前构建)，重新构建..."
        fi
    fi
    
    # 构建镜像
    log_step "构建Docker镜像 $DOCKER_IMAGE"
    if docker build -t "$DOCKER_IMAGE" -f Dockerfile.ci .; then
        log_success "CI镜像构建成功"
        return 0
    else
        log_error "CI镜像构建失败"
        return 1
    fi
}

# 启动CI容器
start_ci_container() {
    log_step "启动CI容器: $CONTAINER_NAME"
    
    # 创建共享卷挂载点
    local temp_volume=$(mktemp -d)
    
    # 启动容器
    docker run \
        --name "$CONTAINER_NAME" \
        --rm \
        --detach \
        --workdir /workspace \
        --volume "$PROJECT_ROOT:/workspace:ro" \
        --volume "$temp_volume:/tmp/ci-output" \
        --env PYTHONPATH=/workspace/src \
        --env ENVIRONMENT=testing \
        --env CI=true \
        --env TERM=xterm-256color \
        --network none \
        "$DOCKER_IMAGE" \
        tail -f /dev/null
    
    # 验证容器启动
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        log_success "CI容器启动成功"
        return 0
    else
        log_error "CI容器启动失败"
        return 1
    fi
}

# 执行CI检查
execute_ci() {
    log_step "执行CI检查 (超时: ${CI_TIMEOUT}秒)"
    
    # 在容器内执行CI脚本
    local ci_start_time=$(date +%s)
    
    if timeout $CI_TIMEOUT docker exec "$CONTAINER_NAME" /usr/local/bin/local_ci_runner.sh; then
        local ci_end_time=$(date +%s)
        local ci_duration=$((ci_end_time - ci_start_time))
        log_success "CI检查完成 (耗时: ${ci_duration}秒)"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_error "CI检查超时 (>${CI_TIMEOUT}秒)"
        else
            log_error "CI检查失败 (退出码: $exit_code)"
        fi
        return $exit_code
    fi
}

# 收集CI日志
collect_ci_logs() {
    log_step "收集CI执行日志"
    
    # 获取容器日志
    if docker logs "$CONTAINER_NAME" > /tmp/ci-output.log 2> /tmp/ci-error.log; then
        log_info "CI日志已保存到 /tmp/ci-output.log"
        
        # 显示关键信息
        if [ -f /tmp/ci-output.log ]; then
            echo ""
            echo "📋 CI执行摘要:"
            echo "=============="
            grep -E "(✅|❌|⚠️)" /tmp/ci-output.log | tail -10 || echo "无摘要信息"
        fi
        
        return 0
    else
        log_warning "无法收集CI日志"
        return 1
    fi
}

# 自动修复建议
suggest_auto_fixes() {
    log_step "分析可自动修复的问题"
    
    if [ ! -f /tmp/ci-output.log ]; then
        return 0
    fi
    
    local suggestions=()
    
    # 检查格式问题
    if grep -q "代码格式.*格式不符合标准" /tmp/ci-output.log; then
        suggestions+=("make format  # 自动修复代码格式")
    fi
    
    # 检查依赖问题
    if grep -q "依赖安装.*失败" /tmp/ci-output.log; then
        suggestions+=("uv sync --extra dev  # 重新同步依赖")
    fi
    
    # 检查导入问题
    if grep -q "模块导入.*失败" /tmp/ci-output.log; then
        suggestions+=("export PYTHONPATH=\$(pwd)/src  # 设置Python路径")
    fi
    
    # 显示建议
    if [ ${#suggestions[@]} -gt 0 ]; then
        echo ""
        echo "🔧 建议的自动修复命令:"
        echo "===================="
        for suggestion in "${suggestions[@]}"; do
            echo "   $suggestion"
        done
        echo ""
        
        # 询问是否自动修复
        read -p "🤖 是否自动执行修复命令? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            execute_auto_fixes "${suggestions[@]}"
        fi
    fi
}

# 执行自动修复
execute_auto_fixes() {
    local fixes=("$@")
    
    log_step "执行自动修复"
    
    for fix in "${fixes[@]}"; do
        local cmd=$(echo "$fix" | cut -d'#' -f1 | xargs)
        local desc=$(echo "$fix" | cut -d'#' -f2 | xargs)
        
        log_info "执行: $cmd ($desc)"
        if eval "$cmd"; then
            log_success "修复成功: $desc"
        else
            log_warning "修复失败: $desc"
        fi
    done
}

# 主执行流程
main() {
    echo "🎭 本地CI编排器 - 完整CI演练"
    echo "================================="
    echo "📍 项目路径: $PROJECT_ROOT"
    echo "🐳 Docker镜像: $DOCKER_IMAGE"
    echo "⏰ 超时设置: ${CI_TIMEOUT}秒"
    echo ""
    
    # 执行流程
    if ! check_docker; then
        log_error "Docker环境检查失败"
        exit 1
    fi
    
    if ! build_ci_image; then
        log_error "CI镜像构建失败"
        exit 1
    fi
    
    if ! start_ci_container; then
        log_error "CI容器启动失败"
        exit 1
    fi
    
    # 执行CI并收集结果
    local ci_success=false
    if execute_ci; then
        ci_success=true
    fi
    
    # 总是收集日志
    collect_ci_logs
    
    # 如果CI失败，提供修复建议
    if [ "$ci_success" = false ]; then
        suggest_auto_fixes
        echo ""
        log_error "本地CI检查失败，推送被阻止"
        echo ""
        echo "💡 完整的修复步骤:"
        echo "   1. 查看详细日志: cat /tmp/ci-output.log"
        echo "   2. 手动修复问题: make ci"
        echo "   3. 重新尝试推送"
        echo "   4. 跳过检查推送: git push --no-verify"
        echo ""
        exit 1
    else
        log_success "本地CI检查通过，可以安全推送"
        exit 0
    fi
}

# 参数处理
while [[ $# -gt 0 ]]; do
    case $1 in
        --timeout)
            CI_TIMEOUT="$2"
            shift 2
            ;;
        --image)
            DOCKER_IMAGE="$2"
            shift 2
            ;;
        --no-build)
            SKIP_BUILD=true
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --timeout SECONDS    设置CI超时时间 (默认: 600)"
            echo "  --image IMAGE        指定Docker镜像名称"
            echo "  --no-build           跳过镜像构建"
            echo "  --help               显示此帮助信息"
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# 执行主流程
main "$@" 