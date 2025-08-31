#!/bin/bash
# 🔧 统一环境管理脚本 - 整合所有虚拟环境管理功能
#
# 功能：整合activate-venv.sh、check-venv.sh、run-in-venv.sh、setup-dev-env.sh
# 支持多种运行模式，提供统一的环境管理入口
#
# 使用方式：
#   ./scripts/env-manager.sh --setup      # 完整开发环境设置
#   ./scripts/env-manager.sh --activate   # 激活虚拟环境
#   ./scripts/env-manager.sh --check      # 检查环境状态
#   ./scripts/env-manager.sh --run "cmd"  # 在环境中执行命令

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# 帮助信息
show_help() {
    cat << EOF
🔧 统一环境管理脚本

用法: $0 [选项]

模式选项:
  --setup      完整开发环境设置 (Python版本检查 + 虚拟环境 + 依赖安装)
  --activate   激活虚拟环境 (创建虚拟环境 + 激活 + 安装依赖)
  --check      检查环境状态 (验证虚拟环境 + 工具 + Python版本)
  --run "cmd"  在虚拟环境中执行命令

其他选项:
  --verbose    详细输出模式
  --help       显示此帮助信息

示例:
  $0 --setup                        # 完整环境设置
  $0 --activate                     # 激活环境
  $0 --check                        # 检查环境
  $0 --run "make test"             # 在环境中运行测试
  $0 --run "pip list"              # 在环境中查看包列表

EOF
}

# 检查Python版本
check_python_version() {
    log_info "🔍 检查 Python 版本..."

    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python3 未安装"
        exit 1
    fi

    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    required_version="3.11"

    if [[ $python_version == *"$required_version"* ]]; then
        log_success "Python 版本符合要求: $python_version"
        return 0
    else
        log_error "Python 版本不符合要求"
        log_error "   当前版本: $python_version"
        log_error "   要求版本: Python $required_version.x"
        exit 1
    fi
}

# 创建虚拟环境
create_venv() {
    log_info "🔧 设置虚拟环境..."

    if [ ! -d ".venv" ]; then
        log_info "   创建新的虚拟环境..."
        python3 -m venv .venv
        log_success "虚拟环境创建成功"
    else
        log_success "虚拟环境已存在"
    fi
}

# 激活虚拟环境
activate_venv() {
    log_info "⚡ 激活虚拟环境..."

    # 检查不同操作系统的激活脚本
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        log_success "虚拟环境已激活 (Linux/Mac)"
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
        log_success "虚拟环境已激活 (Windows)"
    else
        log_error "无法找到激活脚本"
        exit 1
    fi

    # 验证激活状态
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_error "虚拟环境激活失败"
        exit 1
    fi

    log_success "虚拟环境已激活: $VIRTUAL_ENV"
}

# 安装和升级依赖
install_dependencies() {
    log_info "📦 安装和升级依赖..."

    # 升级基础工具
    log_info "⬆️  升级基础工具..."
    python -m pip install --upgrade pip uv >/dev/null 2>&1

    # 安装项目依赖
    if [ -f "requirements.txt" ]; then
        log_info "🔧 安装项目依赖..."
        if ! python -c "import fastapi, pandas, numpy" >/dev/null 2>&1; then
            pip install -r requirements.txt >/dev/null
            pip install -e . >/dev/null
            log_success "依赖安装完成"
        else
            log_success "依赖已安装"
        fi
    fi

    # 安装开发工具
    log_info "🛠️  确保开发工具可用..."
    local tools=("ruff" "mypy" "pytest" "bandit")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_warning "$tool 未安装，正在安装..."
            pip install "$tool" >/dev/null
        fi
    done

    log_success "所有依赖和工具准备就绪"
}

# 检查虚拟环境状态
check_venv_status() {
    log_info "🔍 虚拟环境状态检查"
    echo "=========================="

    # 检查是否在虚拟环境中
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_error "未激活虚拟环境"
        log_warning "请运行: $0 --activate"
        return 1
    fi

    # 检查虚拟环境路径
    local expected_venv="$(pwd)/.venv"
    if [[ "$VIRTUAL_ENV" != "$expected_venv" ]]; then
        log_warning "虚拟环境路径不匹配"
        log_warning "当前: $VIRTUAL_ENV"
        log_warning "期望: $expected_venv"
    fi

    # 检查Python版本
    local python_version=$(python --version 2>&1)
    if [[ ! "$python_version" =~ "Python 3.11" ]]; then
        log_error "Python版本不正确"
        log_error "当前: $python_version"
        log_error "期望: Python 3.11.x"
        return 1
    fi

    log_success "Python: $python_version"

    # 检查关键开发工具
    log_info "📦 检查开发工具..."
    local tools=("ruff" "mypy" "pytest" "bandit")
    local missing_tools=()

    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            log_success "$tool: $(which $tool)"
        else
            log_error "$tool: 未安装"
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_warning "缺少工具，请运行: $0 --setup"
        return 1
    fi

    # 检查项目是否以开发模式安装
    if python -c "import football_predict_system" >/dev/null 2>&1; then
        log_success "项目已以开发模式安装"
    else
        log_warning "项目未以开发模式安装"
        log_warning "请运行: $0 --setup"
    fi

    echo
    log_success "🎉 虚拟环境检查通过！"
    log_info "虚拟环境: $VIRTUAL_ENV"
    log_info "Python: $python_version"
    log_info "工作目录: $(pwd)"

    return 0
}

# 在虚拟环境中执行命令
run_in_venv() {
    local command_to_run="$1"

    if [ -z "$command_to_run" ]; then
        log_error "未提供要执行的命令"
        echo "用法: $0 --run \"<command-to-execute>\""
        exit 1
    fi

    # 确保在虚拟环境中
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_info "虚拟环境未激活，正在激活..."
        create_venv
        activate_venv
    fi

    log_info "🚀 在虚拟环境中执行: $command_to_run"
    echo "======================================"

    # 执行命令
    eval "$command_to_run"
}

# 完整环境设置
setup_environment() {
    log_info "🚀 开始设置 Football Prediction System 开发环境..."
    echo "================================================"

    check_python_version
    create_venv
    activate_venv
    install_dependencies

    # 设置pre-commit hooks
    if [ -f ".pre-commit-config.yaml" ]; then
        log_info "🔧 设置 pre-commit hooks..."
        pre-commit install --hook-type pre-commit --hook-type pre-push >/dev/null 2>&1 || true
        log_success "Pre-commit hooks 设置完成"
    fi

    echo
    log_success "🎉 开发环境设置完成！"
    log_info "现在可以安全地进行AI辅助开发！"
    echo
    log_info "🎯 环境信息:"
    log_info "虚拟环境: $VIRTUAL_ENV"
    log_info "Python: $(python --version)"
    log_info "工作目录: $(pwd)"
    echo
    log_info "💡 下一步："
    log_info "  - 运行测试: $0 --run \"make test\""
    log_info "  - 检查环境: $0 --check"
    log_info "  - 开发工作: 正常使用IDE进行开发"
}

# 解析命令行参数
MODE=""
VERBOSE=false
COMMAND_TO_RUN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --setup)
            MODE="setup"
            shift
            ;;
        --activate)
            MODE="activate"
            shift
            ;;
        --check)
            MODE="check"
            shift
            ;;
        --run)
            MODE="run"
            COMMAND_TO_RUN="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证模式
if [ -z "$MODE" ]; then
    log_error "必须指定一个模式"
    show_help
    exit 1
fi

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 执行相应的功能
case "$MODE" in
    setup)
        setup_environment
        ;;
    activate)
        log_info "🚀 自动激活虚拟环境"
        echo "======================"
        create_venv
        activate_venv
        install_dependencies
        echo
        log_info "🎯 环境信息:"
        log_info "虚拟环境: $VIRTUAL_ENV"
        log_info "Python: $(python --version)"
        log_info "工作目录: $(pwd)"
        echo
        log_success "💡 现在可以安全地进行AI辅助开发！"
        ;;
    check)
        check_venv_status
        ;;
    run)
        run_in_venv "$COMMAND_TO_RUN"
        ;;
    *)
        log_error "无效的运行模式: $MODE"
        show_help
        exit 1
        ;;
esac
