#!/bin/bash
# 🔧 环境变量统一加载脚本
#
# 功能：根据指定环境加载相应的环境变量文件
# 使用：source scripts/load-env.sh --env=development

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 颜色输出
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[ENV]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[ENV]${NC} $*"
}

log_error() {
    echo -e "${RED}[ENV]${NC} $*"
}

# 帮助信息
show_help() {
    cat << EOF
🔧 环境变量统一加载脚本

用法: source $0 --env=ENVIRONMENT

环境选项:
  --env=development  加载开发环境配置
  --env=testing      加载测试环境配置
  --env=production   加载生产环境配置
  --env=local        加载本地开发配置

其他选项:
  --create-template  从模板创建环境配置文件
  --validate         验证环境变量完整性
  --help             显示此帮助信息

示例:
  source $0 --env=development
  source $0 --env=production --validate
  $0 --create-template --env=development

环境文件位置:
  开发环境: .env.development
  测试环境: .env.testing
  生产环境: .env.production
  模板文件: env-templates/template.env

EOF
}

# 解析命令行参数
ENVIRONMENT=""
CREATE_TEMPLATE=false
VALIDATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --env=*)
            ENVIRONMENT="${1#*=}"
            shift
            ;;
        --create-template)
            CREATE_TEMPLATE=true
            shift
            ;;
        --validate)
            VALIDATE=true
            shift
            ;;
        --help)
            show_help
            return 0 2>/dev/null || exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            return 1 2>/dev/null || exit 1
            ;;
    esac
done

# 验证环境参数
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "必须指定环境"
    show_help
    return 1 2>/dev/null || exit 1
fi

case "$ENVIRONMENT" in
    development|testing|production|local)
        ;;
    *)
        log_error "无效的环境: $ENVIRONMENT"
        show_help
        return 1 2>/dev/null || exit 1
        ;;
esac

# 环境文件路径
ENV_FILE="${PROJECT_ROOT}/.env.${ENVIRONMENT}"
TEMPLATE_FILE="${PROJECT_ROOT}/env-templates/template.env"

# 创建模板功能
create_template() {
    log_info "创建 $ENVIRONMENT 环境配置文件..."

    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        log_error "模板文件不存在: $TEMPLATE_FILE"
        return 1
    fi

    if [[ -f "$ENV_FILE" ]]; then
        log_warning "环境文件已存在: $ENV_FILE"
        read -p "是否覆盖? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "操作取消"
            return 0
        fi
    fi

    # 复制模板并根据环境调整
    cp "$TEMPLATE_FILE" "$ENV_FILE"

    # 根据环境调整配置
    case "$ENVIRONMENT" in
        development)
            sed -i 's/ENV=development/ENV=development/' "$ENV_FILE"
            sed -i 's/DEBUG=true/DEBUG=true/' "$ENV_FILE"
            ;;
        testing)
            sed -i 's/ENV=development/ENV=testing/' "$ENV_FILE"
            sed -i 's/DEBUG=true/DEBUG=false/' "$ENV_FILE"
            sed -i 's/football_predict/football_predict_test/g' "$ENV_FILE"
            ;;
        production)
            sed -i 's/ENV=development/ENV=production/' "$ENV_FILE"
            sed -i 's/DEBUG=true/DEBUG=false/' "$ENV_FILE"
            sed -i 's/localhost/your-production-host/' "$ENV_FILE"
            ;;
        local)
            sed -i 's/ENV=development/ENV=local/' "$ENV_FILE"
            sed -i 's/DEBUG=true/DEBUG=true/' "$ENV_FILE"
            ;;
    esac

    log_info "✅ 环境配置文件已创建: $ENV_FILE"
    log_warning "⚠️ 请编辑文件并设置正确的密钥和密码"
}

# 验证环境变量
validate_env() {
    log_info "验证环境变量完整性..."

    # 必需的环境变量
    local required_vars=(
        "ENV"
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
    )

    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "缺少必需的环境变量:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        return 1
    fi

    # 检查数据库连接
    if command -v psql > /dev/null 2>&1; then
        if ! psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
            log_warning "数据库连接测试失败"
        fi
    fi

    # 检查Redis连接
    if command -v redis-cli > /dev/null 2>&1; then
        local redis_host redis_port
        redis_host=$(echo "$REDIS_URL" | sed -n 's|redis://\([^:]*\):.*|\1|p')
        redis_port=$(echo "$REDIS_URL" | sed -n 's|redis://[^:]*:\([0-9]*\).*|\1|p')

        if ! redis-cli -h "${redis_host:-localhost}" -p "${redis_port:-6379}" ping > /dev/null 2>&1; then
            log_warning "Redis连接测试失败"
        fi
    fi

    log_info "✅ 环境变量验证完成"
}

# 加载环境变量
load_environment() {
    log_info "加载 $ENVIRONMENT 环境配置..."

    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "环境文件不存在: $ENV_FILE"
        log_info "运行以下命令创建模板："
        log_info "  $0 --create-template --env=$ENVIRONMENT"
        return 1
    fi

    # 加载环境变量
    set -a  # 自动导出变量
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a

    log_info "✅ 环境配置已加载: $ENVIRONMENT"
    log_info "📋 当前环境信息:"
    echo "  ENV: ${ENV:-未设置}"
    echo "  DEBUG: ${DEBUG:-未设置}"
    echo "  DATABASE_URL: ${DATABASE_URL:0:30}..."
    echo "  REDIS_URL: ${REDIS_URL:-未设置}"
}

# 主执行逻辑
main() {
    cd "$PROJECT_ROOT"

    if $CREATE_TEMPLATE; then
        create_template
        return $?
    fi

    load_environment

    if $VALIDATE; then
        validate_env
    fi
}

# 执行主函数
main "$@"
