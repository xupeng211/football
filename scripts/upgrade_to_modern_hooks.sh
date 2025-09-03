#!/bin/bash
# 🚀 升级到现代化pre-commit系统脚本

set -e

echo "🚀 Football Prediction System - hooks系统升级"
echo "============================================="

# 检查当前目录
if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

echo "📍 当前目录: $(pwd)"

# 1. 显示老系统信息
echo ""
echo "📋 老hooks系统信息："
echo "==================="
if [[ -f ".githooks/pre-commit" ]]; then
    echo "🔍 当前.githooks/pre-commit内容："
    echo "---"
    head -10 .githooks/pre-commit
    echo "---"
    echo "📏 文件大小: $(wc -l < .githooks/pre-commit) 行"
else
    echo "⚠️ 未找到.githooks/pre-commit"
fi

# 检查当前git hooks配置
echo ""
echo "🔧 当前git hooks配置："
current_hooks_path=$(git config --get core.hooksPath 2>/dev/null || echo "未设置")
echo "   core.hooksPath = $current_hooks_path"

# 2. 升级确认
echo ""
echo "🔄 开始升级到新系统..."
echo "📋 新系统优势："
echo "   ✅ 与CI完全一致的检查 (make ci-check)"
echo "   ✅ 现代化工具 (ruff + mypy + pytest)"
echo "   ✅ 更快更准确的代码检查"
echo "   ✅ Python社区标准化实践"
echo ""

# 3. 备份老系统
if [[ -f ".githooks/pre-commit" ]]; then
    echo "💾 备份老hooks系统..."
    cp .githooks/pre-commit .githooks/pre-commit.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 备份完成: .githooks/pre-commit.backup.*"
fi

# 4. 清除老配置
echo ""
echo "🧹 清除老的hooks配置..."
if git config --get core.hooksPath >/dev/null 2>&1; then
    git config --unset core.hooksPath
    echo "✅ 已清除 core.hooksPath 配置"
else
    echo "ℹ️ core.hooksPath 未设置，无需清除"
fi

# 验证配置已清除
if git config --get core.hooksPath >/dev/null 2>&1; then
    echo "❌ 配置清除失败"
    exit 1
else
    echo "✅ 确认 core.hooksPath 已清除"
fi

# 5. 确保虚拟环境已激活
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "🐍 激活虚拟环境..."
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
    else
        echo "❌ 虚拟环境不存在，请先运行: uv venv && source .venv/bin/activate"
        exit 1
    fi
else
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
fi

# 6. 安装新的pre-commit系统
echo ""
echo "🔧 安装新的pre-commit系统..."
pre-commit install
echo "✅ pre-commit hooks已安装到标准位置"

# 7. 测试新系统
echo ""
echo "🧪 测试新的pre-commit系统..."
echo "📝 运行pre-commit检查 (可能需要一些时间)..."
if pre-commit run --all-files; then
    echo "✅ pre-commit检查全部通过"
else
    echo "⚠️ pre-commit检查发现问题，但这是正常的首次运行"
    echo "   问题会在提交时自动修复"
fi

# 8. 测试CI级别检查
echo ""
echo "🚀 测试CI级别检查..."
if make ci-check; then
    echo "✅ make ci-check 全部通过"
else
    echo "⚠️ make ci-check 发现问题，需要修复后再提交"
fi

# 9. 验证验收标准
echo ""
echo "📊 验证所有验收标准..."
if [[ -f "scripts/verify_standards.sh" ]]; then
    bash scripts/verify_standards.sh
else
    echo "⚠️ 验证脚本不存在，手动检查："
    
    # 手动检查关键项
    echo "1️⃣ make ci-check: $(grep -q 'ci-check:' Makefile && echo '✅ 存在' || echo '❌ 不存在')"
    echo "2️⃣ CI workflow: $(grep -q 'make ci-check' .github/workflows/*.yml && echo '✅ 已配置' || echo '❌ 未配置')"
    echo "3️⃣ Cursor规则: $([[ -f '.cursor/rules.md' ]] && echo '✅ 存在' || echo '❌ 不存在')"
    echo "4️⃣ pre-commit配置: $([[ -f '.pre-commit-config.yaml' ]] && echo '✅ 存在' || echo '❌ 不存在')"
    echo "5️⃣ pre-commit安装: $([[ -f '.git/hooks/pre-commit' ]] && echo '✅ 已安装' || echo '❌ 未安装')"
    echo "6️⃣ local-ci: $(grep -q 'local-ci:' Makefile && echo '✅ 存在' || echo '❌ 不存在')"
fi

# 10. 升级完成总结
echo ""
echo "🎉 升级完成！"
echo "============="
echo ""
echo "📊 新系统 vs 老系统对比："
echo "   老系统: make format/lint/security (跳过测试)"
echo "   新系统: ruff + mypy + pytest (完整验证)"
echo ""
echo "✨ 新系统特点："
echo "   🎯 与GitHub CI完全一致"
echo "   ⚡ 更快的代码检查 (ruff)"
echo "   🛡️ 类型检查 (mypy)"
echo "   🧪 完整测试覆盖"
echo "   📐 Python社区标准"
echo ""
echo "🔧 日常使用："
echo "   make ci-check                    # 本地CI级别检查"
echo "   pre-commit run --all-files       # 手动运行所有检查"
echo "   git commit -m '...'              # 提交时自动运行检查"
echo "   make local-ci                    # Docker环境CI模拟"
echo ""
echo "🚀 现在可以提交代码了，pre-commit会自动运行质量检查！"
echo "🎯 目标达成：本地通过 = CI通过，告别红灯时代！" 