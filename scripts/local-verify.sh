#!/bin/bash
set -e

echo "🎯 本地全面验证开始..."
echo "================================="

echo "📋 1. 代码格式化..."
make fmt

echo "📋 2. 代码风格检查..."
make lint

echo "📋 3. 类型检查..."
make type

echo "📋 4. 安全检查..."
make sec

echo "📋 5. 运行测试..."
make test

echo "📋 6. 检查依赖格式..."
python -m pip install --dry-run -r requirements.txt > /dev/null 2>&1

echo "🎉 **所有本地验证通过！可以安全推送！**"
echo "运行 'git status' 检查是否有需要提交的改动"
