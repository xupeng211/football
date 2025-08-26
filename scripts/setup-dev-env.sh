#!/bin/bash
"""
开发环境自动化设置脚本
确保所有开发者都有一致的环境配置
"""

set -e  # 遇到错误时退出

echo "🚀 开始设置 Football Prediction System 开发环境..."
echo "================================================"

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [[ $python_version == *"$required_version"* ]]; then
    echo "✅ Python 版本符合要求: $python_version"
else
    echo "❌ Python 版本不符合要求"
    echo "   当前版本: $python_version"
    echo "   要求版本: Python $required_version.x"
    echo "   请安装正确的 Python 版本后重试"
    exit 1
fi

# 创建虚拟环境
echo "🔧 设置虚拟环境..."
if [ ! -d ".venv" ]; then
    echo "   创建新的虚拟环境..."
    python3 -m venv .venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "⚡ 激活虚拟环境..."
source .venv/bin/activate

# 检查虚拟环境是否激活
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ 虚拟环境激活失败"
    exit 1
fi
echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"

# 升级基础工具
echo "⬆️  升级基础工具..."
python -m pip install --upgrade pip uv
echo "✅ pip 和 uv 升级完成"

# 安装项目依赖
echo "📦 安装项目依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ requirements.txt 依赖安装完成"
else
    echo "⚠️  requirements.txt 文件不存在"
fi

# 安装项目本身
echo "🔧 安装项目模块..."
pip install -e .
echo "✅ 项目模块安装完成"

# 安装开发工具
echo "🛠️  安装开发工具..."
pip install pre-commit ruff mypy pytest pytest-cov bandit
echo "✅ 开发工具安装完成"

# 设置 pre-commit 钩子
echo "🪝 设置 pre-commit 钩子..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    echo "✅ pre-commit 钩子安装完成"
else
    echo "⚠️  .pre-commit-config.yaml 文件不存在"
fi

# 创建 .env 文件（如果不存在）
echo "🌍 设置环境变量..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "✅ .env 文件已从 .env.example 创建"
    echo "   请根据需要编辑 .env 文件"
elif [ -f ".env" ]; then
    echo "✅ .env 文件已存在"
else
    echo "⚠️  .env.example 文件不存在，跳过 .env 创建"
fi

# 运行初始质量检查
echo "🧪 运行初始质量检查..."
if [ -f "scripts/quality-check.py" ]; then
    echo "   运行质量检查脚本..."
    python scripts/quality-check.py || true  # 不因质量检查失败而退出
else
    echo "   手动运行基本检查..."
    echo "   - 格式化检查..."
    ruff format --check . || echo "   需要运行 'ruff format .' 修复格式化"
    echo "   - 代码规范检查..."
    ruff check . || echo "   需要运行 'ruff check --fix .' 修复规范问题"
fi

# 显示完成信息和下一步提示
echo ""
echo "🎉 开发环境设置完成！"
echo "===================="
echo ""
echo "📋 环境信息:"
echo "   Python: $(python --version)"
echo "   虚拟环境: $VIRTUAL_ENV"
echo "   工作目录: $(pwd)"
echo ""
echo "🎯 下一步操作:"
echo "   1. 激活虚拟环境: source .venv/bin/activate"
echo "   2. 编辑 .env 文件配置环境变量"
echo "   3. 运行测试: make test 或 python -m pytest"
echo "   4. 运行质量检查: python scripts/quality-check.py"
echo "   5. 启动开发服务器: make dev"
echo ""
echo "📚 有用的命令:"
echo "   make help          - 查看所有可用命令"
echo "   make local-ci      - 运行本地CI检查"
echo "   make fmt           - 格式化代码"
echo "   make lint          - 检查代码规范"
echo "   make test          - 运行测试"
echo ""
echo "💡 提示: 建议在IDE中配置以下设置:"
echo "   - Python 解释器: $(pwd)/.venv/bin/python"
echo "   - 启用保存时自动格式化"
echo "   - 启用类型检查提示"
echo ""
echo "✨ 祝您开发愉快！"
