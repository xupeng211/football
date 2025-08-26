#!/bin/bash
# 快速CI检查脚本 - 模拟GitHub Actions的完整检查

echo "⚡ 快速CI检查（模拟GitHub Actions）"
echo "================================="

# 1. 检查requirements.txt格式
echo "📋 检查依赖文件格式..."
if ! python -m pip install --dry-run -r requirements.txt >/dev/null 2>&1; then
    echo "❌ requirements.txt格式错误！"
    exit 1
fi

# 2. 运行完整CI流程
echo "📋 运行完整CI检查..."
if ! make ci; then
    echo "❌ CI检查失败！"
    exit 1
fi

echo "🎉 所有CI检查通过！可以安全推送到GitHub！"
