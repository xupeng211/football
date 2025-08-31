#!/bin/bash
# 🎯 增强版脚手架模块化安装器
#
# 功能：智能模块管理，支持依赖解析、冲突检测、版本控制
# 版本：v2.1.0 (Enhanced)

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MODULES_DIR="${PROJECT_ROOT}/scaffold-modules"
TOOLS_DIR="${MODULES_DIR}/tools"
MODULE_MANAGER="${TOOLS_DIR}/module-manager.py"

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

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

log_highlight() {
    echo -e "${PURPLE}[HIGHLIGHT]${NC} $*"
}

# 显示欢迎界面
show_welcome() {
    clear
    cat << 'EOF'
🎯 增强版脚手架模块化安装器 v2.1
=====================================
智能依赖解析 | 冲突检测 | 版本控制 | 回滚支持

🎉 新功能：
✨ Python智能模块管理器集成
🔍 实时依赖关系分析
⚡ 自动冲突检测和解决
🔄 安装失败自动回滚
📊 详细安装报告和统计

=====================================
EOF
    echo ""
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        return 1
    fi

    # 检查PyYAML
    if ! python3 -c "import yaml" &> /dev/null; then
        log_warning "PyYAML 未安装，正在安装..."
        python3 -m pip install pyyaml --quiet
    fi

    # 检查模块管理器
    if [[ ! -f "$MODULE_MANAGER" ]]; then
        log_error "模块管理器未找到: $MODULE_MANAGER"
        return 1
    fi

    log_success "系统要求检查完成"
    return 0
}

# 显示模块列表
show_modules() {
    log_info "正在获取可用模块..."
    echo ""

    python3 "$MODULE_MANAGER" list
    echo ""
}

# 显示模块状态
show_status() {
    log_info "获取模块状态..."
    echo ""

    python3 "$MODULE_MANAGER" status
    echo ""
}

# 显示预设包
show_presets() {
    echo ""
    log_highlight "🎚️ 可用预设包："
    echo "================================"

    # 读取预设包配置
    local presets_dir="${MODULES_DIR}/presets"
    if [[ -d "$presets_dir" ]]; then
        for preset_file in "$presets_dir"/*.yaml; do
            if [[ -f "$preset_file" ]]; then
                local preset_name=$(basename "$preset_file" .yaml)
                local display_name=$(grep "display_name:" "$preset_file" | cut -d'"' -f2)
                local description=$(grep "description:" "$preset_file" | cut -d'"' -f2)

                echo "📦 $display_name"
                echo "   $description"
                echo ""
            fi
        done
    fi
}

# 交互式主菜单
interactive_menu() {
    while true; do
        echo ""
        log_highlight "🎯 请选择操作："
        echo "================================"
        echo "1. 🚀 安装预设包"
        echo "2. 🔧 自定义模块安装"
        echo "3. 📦 查看可用模块"
        echo "4. 📊 查看模块状态"
        echo "5. 🗑️  卸载模块"
        echo "6. 🔄 更新模块"
        echo "7. 🔍 模块依赖分析"
        echo "8. ❌ 退出"
        echo ""

        read -p "您的选择 (1-8): " choice
        case $choice in
            1)
                install_preset_interactive
                ;;
            2)
                install_custom_modules
                ;;
            3)
                show_modules
                ;;
            4)
                show_status
                ;;
            5)
                uninstall_module_interactive
                ;;
            6)
                update_modules_interactive
                ;;
            7)
                analyze_dependencies_interactive
                ;;
            8)
                log_info "感谢使用脚手架模块化安装器！"
                exit 0
                ;;
            *)
                log_warning "无效选择，请输入1-8"
                ;;
        esac
    done
}

# 交互式预设包安装
install_preset_interactive() {
    echo ""
    log_info "🎚️ 选择预设包"
    show_presets

    echo "可用预设包："
    echo "1. 🚀 Minimal (个人项目)"
    echo "2. 🏢 Professional (团队项目)"
    echo "3. 🌟 Enterprise (企业项目)"
    echo "4. 🤖 AI-Enhanced (AI驱动项目)"
    echo ""

    read -p "请选择预设包 (1-4): " preset_choice

    case $preset_choice in
        1)
            install_preset "minimal"
            ;;
        2)
            install_preset "professional"
            ;;
        3)
            install_preset "enterprise"
            ;;
        4)
            install_preset "ai-enhanced"
            ;;
        *)
            log_warning "无效选择"
            ;;
    esac
}

# 安装预设包
install_preset() {
    local preset_name="$1"
    local preset_file="${MODULES_DIR}/presets/${preset_name}.yaml"

    if [[ ! -f "$preset_file" ]]; then
        log_error "预设包配置文件不存在: $preset_file"
        return 1
    fi

    log_info "正在安装预设包: $preset_name"

    # 从YAML文件解析模块列表
    local modules=($(python3 -c "
import yaml
with open('$preset_file', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
modules = [m['name'] for m in config.get('modules', [])]
print(' '.join(modules))
"))

    if [[ ${#modules[@]} -eq 0 ]]; then
        log_error "预设包中没有找到模块配置"
        return 1
    fi

    log_info "预设包包含模块: ${modules[*]}"

    # 使用Python模块管理器安装
    if python3 "$MODULE_MANAGER" install "${modules[@]}"; then
        log_success "预设包 $preset_name 安装完成！"
        show_post_install_summary "$preset_name"
    else
        log_error "预设包 $preset_name 安装失败"
        return 1
    fi
}

# 自定义模块安装
install_custom_modules() {
    echo ""
    log_info "🔧 自定义模块安装"

    # 显示可用模块
    show_modules

    echo "请输入要安装的模块名称（用空格分隔）："
    read -p "模块列表: " -a selected_modules

    if [[ ${#selected_modules[@]} -eq 0 ]]; then
        log_warning "未选择任何模块"
        return
    fi

    log_info "将安装模块: ${selected_modules[*]}"

    # 确认安装
    read -p "确认安装这些模块？(y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        if python3 "$MODULE_MANAGER" install "${selected_modules[@]}"; then
            log_success "自定义模块安装完成！"
        else
            log_error "模块安装失败"
        fi
    else
        log_info "安装已取消"
    fi
}

# 交互式卸载模块
uninstall_module_interactive() {
    echo ""
    log_info "🗑️ 卸载模块"

    # 获取已安装模块
    local installed_modules=($(python3 "$MODULE_MANAGER" status | grep "已安装模块" | cut -d: -f2 | tr -d ' '))

    if [[ ${#installed_modules[@]} -eq 0 ]]; then
        log_warning "没有已安装的模块"
        return
    fi

    echo "已安装的模块："
    local i=1
    for module in "${installed_modules[@]}"; do
        echo "$i. $module"
        ((i++))
    done

    read -p "选择要卸载的模块编号: " module_index

    if [[ $module_index -ge 1 && $module_index -le ${#installed_modules[@]} ]]; then
        local module_to_remove="${installed_modules[$((module_index-1))]}"
        read -p "确认卸载模块 $module_to_remove？(y/N): " confirm

        if [[ $confirm =~ ^[Yy]$ ]]; then
            if python3 "$MODULE_MANAGER" uninstall "$module_to_remove"; then
                log_success "模块 $module_to_remove 卸载完成"
            else
                log_error "模块卸载失败"
            fi
        else
            log_info "卸载已取消"
        fi
    else
        log_warning "无效的模块编号"
    fi
}

# 交互式更新模块
update_modules_interactive() {
    echo ""
    log_info "🔄 检查模块更新"

    # 这里可以扩展为检查可更新的模块
    python3 "$MODULE_MANAGER" status
    log_info "模块更新功能将在后续版本中实现"
}

# 交互式依赖分析
analyze_dependencies_interactive() {
    echo ""
    log_info "🔍 模块依赖分析"

    read -p "输入要分析的模块名称（用空格分隔）: " -a modules_to_analyze

    if [[ ${#modules_to_analyze[@]} -eq 0 ]]; then
        log_warning "未指定模块"
        return
    fi

    # 这里可以调用Python模块管理器的依赖分析功能
    log_info "分析模块: ${modules_to_analyze[*]}"
    log_info "依赖分析功能将在后续版本中实现"
}

# 显示安装后总结
show_post_install_summary() {
    local preset_name="$1"

    echo ""
    log_highlight "🎉 安装完成总结"
    echo "================================"
    echo "📦 已安装预设包: $preset_name"
    echo "⏰ 安装时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # 显示后续步骤
    log_info "🚀 后续步骤："
    echo "1. 查看 SCAFFOLD_INDEX.md 了解所有功能"
    echo "2. 运行 scripts/ci-unified.sh --mode=quick 进行快速检查"
    echo "3. 使用 docker-compose up 启动开发环境"
    echo ""
}

# 显示使用帮助
show_help() {
    cat << 'EOF'
🎯 增强版脚手架模块化安装器使用说明

用法:
  ./enhanced-installer.sh [选项]

选项:
  -h, --help              显示此帮助信息
  -i, --interactive       启动交互式模式
  -l, --list             列出所有可用模块
  -s, --status           显示模块状态
  --install <modules...>  直接安装指定模块
  --preset <name>        安装预设包

示例:
  ./enhanced-installer.sh --interactive
  ./enhanced-installer.sh --install core cicd docker
  ./enhanced-installer.sh --preset professional
  ./enhanced-installer.sh --list

EOF
}

# 主函数
main() {
    # 解析命令行参数
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -l|--list)
            check_requirements || exit 1
            show_modules
            exit 0
            ;;
        -s|--status)
            check_requirements || exit 1
            show_status
            exit 0
            ;;
        --install)
            shift
            if [[ $# -eq 0 ]]; then
                log_error "请指定要安装的模块"
                exit 1
            fi
            check_requirements || exit 1
            python3 "$MODULE_MANAGER" install "$@"
            exit 0
            ;;
        --preset)
            if [[ $# -lt 2 ]]; then
                log_error "请指定预设包名称"
                exit 1
            fi
            check_requirements || exit 1
            install_preset "$2"
            exit 0
            ;;
        -i|--interactive|"")
            # 默认启动交互式模式
            show_welcome
            check_requirements || exit 1
            interactive_menu
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
}

# 脚本入口
main "$@"
