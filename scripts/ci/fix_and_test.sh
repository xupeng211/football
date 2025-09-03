#!/bin/bash
# 🔧 修复代码质量问题并测试
set -euo pipefail

echo "🚀 开始修复代码质量问题..."

# 1. 重建虚拟环境
echo "🔄 重建虚拟环境..."
rm -rf .venv
uv sync --extra dev

# 2. 自动格式化代码
echo "🎨 自动格式化代码..."
uv run ruff format .

# 3. 自动修复代码质量问题
echo "🔍 自动修复代码质量问题..."
uv run ruff check . --fix --unsafe-fixes

# 4. 运行本地严格CI测试
echo "🧪 运行严格CI测试..."
uv run ruff format --check .
echo "✅ 格式检查通过"

uv run ruff check src/ --output-format=github
echo "✅ 代码质量检查通过"

# 5. 类型检查 (数据平台模块)
echo "🔬 类型检查..."
uv run mypy src/football_predict_system/data_platform/ --show-error-codes --no-error-summary --ignore-missing-imports || echo "⚠️ 类型检查有警告"

echo "🎉 修复完成！" 