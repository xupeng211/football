#!/bin/bash
# 🚀 Football Prediction System - 环境设置脚本
# 用法: source scripts/setup_env.sh [环境类型]

set -e

# 默认环境类型
ENV_TYPE="${1:-development}"

echo "🚀 设置 $ENV_TYPE 环境..."

# 根据环境类型设置不同的配置
case $ENV_TYPE in
    "development"|"dev")
        echo "📊 配置开发环境..."
        export ENVIRONMENT=development
        export DATABASE_URL="sqlite:///./football_dev.db"
        export REDIS_URL="redis://localhost:6379/0"
        export DEBUG=true
        export LOG_LEVEL=info
        ;;
    "testing"|"test")
        echo "🧪 配置测试环境..."
        export ENVIRONMENT=testing
        export DATABASE_URL="sqlite:///./test_football.db"
        export REDIS_URL="redis://localhost:6379/1"
        export DEBUG=false
        export LOG_LEVEL=warning
        export CI=true
        ;;
    "ci")
        echo "🔄 配置CI环境..."
        export ENVIRONMENT=testing
        export DATABASE_URL="sqlite:///./test_football.db"
        export REDIS_URL="redis://localhost:6379/1"
        export DEBUG=false
        export LOG_LEVEL=info
        export CI=true
        ;;
    *)
        echo "❌ 未知环境类型: $ENV_TYPE"
        echo "支持的环境: development, testing, ci"
        return 1
        ;;
esac

# 通用配置
export APP_NAME="Football Prediction System"
export APP_VERSION="3.0.0"
export API_HOST="127.0.0.1"
export API_PORT="8000"
export SECRET_KEY="dev-secret-key-for-local-development-only"
export FOOTBALL_DATA_API_KEY="${FOOTBALL_DATA_API_KEY:-your-api-key-here}"

echo "✅ $ENV_TYPE 环境配置完成!"
echo "📊 数据库: $DATABASE_URL"
echo "🔄 缓存: $REDIS_URL"
echo "🐍 Python: $(python --version 2>&1)"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" ]]; then
    echo "🐍 虚拟环境: $(basename $VIRTUAL_ENV)"
else
    echo "⚠️  未检测到虚拟环境，建议运行: source .venv/bin/activate"
fi 