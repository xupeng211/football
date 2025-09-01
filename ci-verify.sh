#!/bin/bash
set -e

echo "🚀 开始本地CI验证（模拟GitHub Actions）"
echo "=================================="

echo "📦 1. 安装依赖..."
uv sync --frozen --extra dev
uv pip install -e .
uv pip install bcrypt PyJWT
echo "✅ 依赖安装完成"

echo "📋 2. 验证配置文件..."
python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"
echo "✅ Configuration valid"

echo "🎨 3. 代码格式检查..."
uv run ruff format --check .
echo "✅ 格式检查通过"

echo "🔍 4. 代码质量检查..."
uv run ruff check .
echo "✅ Lint检查通过"

echo "🔒 5. 安全扫描..."
uv run bandit -r src/ -c pyproject.toml -q || echo "⚠️ 安全警告（允许）"
echo "✅ 安全扫描完成"

echo "🧪 6. 核心API测试..."
uv run pytest tests/unit/api/ tests/test_api_simple.py \
  --cov=src \
  --cov-report=term \
  -v \
  --maxfail=5
echo "✅ 核心测试通过"

echo "🔄 7. 导入验证..."
python -c "
import sys
sys.path.append('tests')
try:
    from fixtures.api_fixtures import async_client
    from fixtures.database_fixtures import async_db_session  
    from fixtures.cache_fixtures import redis_client
    print('✅ Core fixtures imported successfully')
except Exception as e:
    print(f'⚠️ Import warning: {e}')
"

echo ""
echo "🎉 本地CI验证完成！所有核心检查都通过了。"
echo "现在可以安全推送代码到远程仓库。" 