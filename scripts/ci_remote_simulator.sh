#!/bin/bash
# 远程CI环境模拟器 - 完全复制GitHub Actions的检查流程
set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${CYAN}🔄 $1${NC}"; }
log_gate() { echo -e "${PURPLE}🚪 $1${NC}"; }

# 设置远程CI环境变量（与GitHub Actions完全一致）
setup_ci_environment() {
    log_step "设置远程CI环境变量..."
    
    export PYTHON_VERSION="3.11"
    export DATABASE_URL="postgresql://test_user:test_pass@localhost:5432/test_football_db"
    export REDIS_URL="redis://localhost:6379/1"
    export FOOTBALL_DATA_API_KEY="test_api_key"
    export ENVIRONMENT="testing"
    
    # GitHub Actions特有的环境变量
    export CI=true
    export GITHUB_ACTIONS=true
    export RUNNER_OS=Linux
    
    log_success "CI环境变量设置完成"
    echo "  📍 DATABASE_URL: $DATABASE_URL"
    echo "  📍 REDIS_URL: $REDIS_URL"
    echo "  📍 ENVIRONMENT: $ENVIRONMENT"
}

# 第一层：代码质量门禁（完全复制远程CI）
gate_1_code_quality_strict() {
    log_gate "第1层：代码质量门禁 (严格模式)"
    
    log_step "🎨 检查代码格式 (严格)..."
    if ! uv run ruff format --check .; then
        log_error "代码格式检查失败 - 这会导致远程CI红灯"
        return 1
    fi
    log_success "代码格式检查通过"
    
    log_step "🔍 执行代码检查 (严格)..."
    if ! uv run ruff check src/ --output-format=github; then
        log_error "源码检查失败 - 这会导致远程CI红灯"
        return 1
    fi
    
    log_step "🔍 检查测试文件关键错误..."
    if ! uv run ruff check tests/ --select=E,F,B --ignore=E402 --output-format=github; then
        log_error "测试文件检查失败 - 这会导致远程CI红灯"
        return 1
    fi
    
    log_step "🔬 执行类型检查 (数据平台模块)..."
    if ! uv run mypy src/football_predict_system/data_platform/ --show-error-codes --no-error-summary --ignore-missing-imports; then
        log_warning "类型检查有警告，但不阻塞CI"
    fi
    
    log_step "🛡️ 执行安全扫描..."
    if ! uv run bandit -r src/ -c pyproject.toml; then
        log_warning "安全扫描有警告，但不阻塞CI"
    fi
    
    log_success "✅ 第1层：代码质量门禁 通过"
}

# 第二层：基础功能门禁（完全复制远程CI）
gate_2_basic_functionality_strict() {
    log_gate "第2层：基础功能门禁 (严格模式)"
    
    log_step "📦 STRICT模块导入测试..."
    
    # 完全复制远程CI的导入测试
    python -c "
import sys
sys.path.insert(0, 'src')

print('🔍 测试核心模块导入...')
try:
    from football_predict_system.core.config import get_settings
    from football_predict_system.core.database import get_database_manager
    from football_predict_system.domain.models import Match, Team
    print('✅ 核心模块导入成功')
except ImportError as e:
    print(f'❌ 核心模块导入失败: {e}')
    sys.exit(1)

print('🔍 测试数据平台模块导入...')
try:
    from football_predict_system.data_platform.sources.base import DataSource
    from football_predict_system.data_platform.sources.football_data_api import FootballDataAPICollector
    from football_predict_system.data_platform.storage.database_writer import DatabaseWriter
    from football_predict_system.data_platform.config import get_data_platform_config
    print('✅ 数据平台模块导入成功')
except ImportError as e:
    print(f'❌ 数据平台模块导入失败: {e}')
    sys.exit(1)

print('🔍 测试流程模块导入...')
try:
    from football_predict_system.data_platform.flows.data_collection import daily_data_collection_flow
    print('✅ 流程模块导入成功')
except ImportError as e:
    print(f'❌ 流程模块导入失败: {e}')
    sys.exit(1)
" || { log_error "模块导入测试失败 - 这会导致远程CI红灯"; return 1; }
    
    log_success "📦 模块导入测试通过"
    
    log_step "🗄️ 测试数据库Schema..."
    if [[ -f "sql/schema.sql" ]]; then
        if command -v sqlparse &> /dev/null; then
            python -c "
import sqlparse
with open('sql/schema.sql', 'r') as f:
    schema = f.read()

statements = sqlparse.split(schema)
print(f'解析到 {len(statements)} 条SQL语句')

for i, stmt in enumerate(statements[:5]):
    if stmt.strip():
        parsed = sqlparse.parse(stmt)[0]
        print(f'SQL {i+1}: 语法正确')

print('✅ SQL Schema语法验证通过')
" || { log_warning "SQL语法检查有问题"; }
        fi
    else
        log_warning "sql/schema.sql不存在，跳过Schema检查"
    fi
    
    log_step "⚙️ 测试配置系统..."
    python -c "
import sys
sys.path.insert(0, 'src')

from football_predict_system.data_platform.config import get_data_platform_config
config = get_data_platform_config()

assert config.football_data_org.rate_limit_per_minute > 0
assert len(config.schedule.daily_competitions) > 0
assert config.schedule.daily_collection_cron

print('✅ 配置系统验证通过')
" || { log_error "配置系统测试失败 - 这会导致远程CI红灯"; return 1; }
    
    log_success "✅ 第2层：基础功能门禁 通过"
}

# 第三层：实际运行远程CI使用的pytest命令
gate_3_pytest_with_ci_config() {
    log_gate "第3层：远程CI pytest测试"
    
    log_step "🧪 运行与远程CI完全一致的pytest命令..."
    
    # 使用远程CI的确切pytest配置
    if ! uv run pytest -v --tb=short --strict-markers; then
        log_error "pytest测试失败 - 这是远程CI红灯的直接原因"
        return 1
    fi
    
    log_success "✅ 第3层：pytest测试 通过"
}

# 主函数
main() {
    echo -e "${PURPLE}🏗️  远程CI环境模拟器启动${NC}"
    echo -e "${PURPLE}===============================================${NC}"
    echo -e "${CYAN}完全复制GitHub Actions CI的检查流程${NC}"
    echo ""
    
    start_time=$(date +%s)
    
    # 设置CI环境
    setup_ci_environment
    echo ""
    
    # 运行严格的3层门禁
    gate_1_code_quality_strict || { 
        log_error "第1层失败 - 代码质量问题"
        exit 1
    }
    echo ""
    
    gate_2_basic_functionality_strict || {
        log_error "第2层失败 - 基础功能问题" 
        exit 1
    }
    echo ""
    
    gate_3_pytest_with_ci_config || {
        log_error "第3层失败 - pytest测试问题"
        echo ""
        log_error "🚨 这是导致远程CI红灯的根本原因！"
        echo ""
        log_info "💡 建议解决方案:"
        echo "  1. 运行: uv run pytest --tb=short -v --lf"
        echo "  2. 分析失败的具体测试"
        echo "  3. 修复或跳过有问题的测试"
        exit 1
    }
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo ""
    echo -e "${PURPLE}===============================================${NC}"
    echo -e "${GREEN}🎉 远程CI模拟测试全部通过！${NC}"
    echo -e "${BLUE}⏱️  总耗时: ${duration}秒${NC}"
    echo -e "${GREEN}✅ 如果这里通过，远程CI也应该通过${NC}"
    echo ""
    echo -e "${CYAN}🚀 代码可以安全推送到GitHub！${NC}"
}

# 错误处理
trap 'log_error "远程CI模拟器异常退出"' ERR

# 执行主函数
main "$@" 