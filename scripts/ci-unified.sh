#!/bin/bash
# 🔧 统一CI检查脚本 - 整合所有CI相关检查功能
#
# 功能：整合ci-check.sh、ci-precheck.sh等重复功能
# 支持多种运行模式，提供统一的CI检查入口
#
# 使用方式：
#   ./scripts/ci-unified.sh --mode=quick     # 快速检查
#   ./scripts/ci-unified.sh --mode=full      # 完整检查
#   ./scripts/ci-unified.sh --mode=pre-push  # 推送前检查
#   ./scripts/ci-unified.sh --mode=local     # 本地开发检查

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${PROJECT_ROOT}/logs/ci-unified.log"

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "${LOG_FILE:-/dev/null}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "${LOG_FILE:-/dev/null}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "${LOG_FILE:-/dev/null}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${LOG_FILE:-/dev/null}"
}

# 帮助信息
show_help() {
    cat << EOF
🔧 统一CI检查脚本

用法: $0 [选项]

模式选项:
  --mode=quick       快速检查 (格式化 + 基础检查)
  --mode=full        完整检查 (所有检查项目)
  --mode=pre-push    推送前检查 (质量门禁)
  --mode=local       本地开发检查 (优化版)

其他选项:
  --verbose         详细输出模式
  --skip-tests      跳过测试执行
  --help            显示此帮助信息

示例:
  $0 --mode=quick --verbose
  $0 --mode=full --skip-tests
  $0 --mode=pre-push

EOF
}

# 解析命令行参数
MODE=""
VERBOSE=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode=*)
            MODE="${1#*=}"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证模式参数
if [[ -z "$MODE" ]]; then
    log_error "必须指定运行模式"
    show_help
    exit 1
fi

case "$MODE" in
    quick|full|pre-push|local)
        ;;
    *)
        log_error "无效的运行模式: $MODE"
        show_help
        exit 1
        ;;
esac

# 初始化
init_ci_environment() {
    log_info "🚀 初始化CI环境..."

    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"

    # 设置工作目录
    cd "$PROJECT_ROOT"

    # 检查必要工具
    local required_tools=("python" "poetry" "git")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "缺少必要工具: $tool"
            return 1
        fi
    done

    # 激活虚拟环境
    if [[ -f "scripts/activate-venv.sh" ]]; then
        log_info "激活虚拟环境..."
        # shellcheck source=scripts/activate-venv.sh
        source scripts/activate-venv.sh > /dev/null 2>&1 || {
            log_warning "虚拟环境激活失败，继续执行..."
        }
    fi

    log_success "CI环境初始化完成"
}

# 代码格式化检查
check_formatting() {
    log_info "🎨 检查代码格式化..."

    if $VERBOSE; then
        poetry run ruff format --check .
        poetry run ruff check .
    else
        poetry run ruff format --check . > /dev/null
        poetry run ruff check . > /dev/null
    fi

    log_success "代码格式化检查通过"
}

# 类型检查
check_types() {
    log_info "🔍 执行类型检查..."

    local type_check_cmd="poetry run mypy apps/ data_pipeline/ --ignore-missing-imports"

    if $VERBOSE; then
        $type_check_cmd
    else
        $type_check_cmd > /dev/null
    fi

    log_success "类型检查通过"
}

# 安全检查
check_security() {
    log_info "🔒 执行安全检查..."

    # Bandit安全扫描
    local bandit_cmd="poetry run bandit -r . -c pyproject.toml -q"

    if $VERBOSE; then
        $bandit_cmd
    else
        $bandit_cmd > /dev/null
    fi

    log_success "安全检查通过"
}

# 测试执行
run_tests() {
    if $SKIP_TESTS; then
        log_warning "跳过测试执行"
        return 0
    fi

    log_info "🧪 执行测试..."

    case "$MODE" in
        quick|local)
            # 快速测试：只运行单元测试
            local test_cmd="poetry run pytest tests/unit/ -x --tb=short"
            ;;
        full|pre-push)
            # 完整测试：所有测试
            local test_cmd="poetry run pytest --cov=. --cov-report=term-missing"
            ;;
    esac

    if $VERBOSE; then
        $test_cmd
    else
        $test_cmd > /dev/null 2>&1 || {
            log_error "测试失败，查看详细输出："
            $test_cmd
            return 1
        }
    fi

    log_success "测试执行完成"
}

# 依赖检查
check_dependencies() {
    log_info "📦 检查依赖状态..."

    # 检查poetry.lock是否最新
    if ! poetry check > /dev/null 2>&1; then
        log_warning "Poetry配置可能有问题"
    fi

    # 检查依赖冲突
    if [[ -f "scripts/dependency-conflict-detector.py" ]]; then
        if $VERBOSE; then
            python scripts/dependency-conflict-detector.py
        else
            python scripts/dependency-conflict-detector.py > /dev/null 2>&1 || {
                log_warning "依赖冲突检测发现问题"
            }
        fi
    fi

    log_success "依赖检查完成"
}

# Git状态检查
check_git_status() {
    log_info "📋 检查Git状态..."

    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        log_warning "存在未提交的更改"
        if $VERBOSE; then
            git status --porcelain
        fi
    fi

    # 检查分支状态
    local current_branch
    current_branch=$(git branch --show-current)
    log_info "当前分支: $current_branch"

    log_success "Git状态检查完成"
}

# 系统健康检查
check_system_health() {
    log_info "🩺 系统健康检查..."

    # 检查磁盘空间
    local disk_usage
    disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        log_warning "磁盘空间不足: ${disk_usage}%"
    fi

    # 检查内存使用
    if command -v free &> /dev/null; then
        local mem_usage
        mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
        if [[ $mem_usage -gt 85 ]]; then
            log_warning "内存使用率较高: ${mem_usage}%"
        fi
    fi

    log_success "系统健康检查完成"
}

# 主执行函数
main() {
    local start_time
    start_time=$(date +%s)

    log_info "🔧 启动统一CI检查 (模式: $MODE)"

    # 初始化环境
    init_ci_environment

    # 根据模式执行不同的检查
    case "$MODE" in
        quick)
            log_info "🚀 快速检查模式"
            check_formatting
            check_types
            run_tests
            ;;
        full)
            log_info "🔍 完整检查模式"
            check_git_status
            check_dependencies
            check_formatting
            check_types
            check_security
            run_tests
            check_system_health
            ;;
        pre-push)
            log_info "📤 推送前检查模式"
            check_formatting
            check_types
            check_security
            run_tests
            check_git_status
            ;;
        local)
            log_info "💻 本地开发检查模式"
            check_dependencies
            check_formatting
            check_types
            run_tests
            ;;
    esac

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "✅ CI检查完成 (耗时: ${duration}秒)"
    log_info "📋 模式: $MODE | 详细输出: $VERBOSE | 跳过测试: $SKIP_TESTS"
}

# 错误处理
error_handler() {
    local exit_code=$?
    log_error "CI检查失败 (退出码: $exit_code)"
    log_info "查看日志文件: $LOG_FILE"
    exit $exit_code
}

# 设置错误处理
trap error_handler ERR

# 执行主函数
main "$@"
