#!/bin/bash
# 🔍 验收标准验证脚本

echo "🔍 验收标准验证"
echo "=============="

# 标准1: 本地执行 make ci-check = CI 运行一致
echo "1️⃣ 检查make ci-check命令..."
if grep -q "ci-check:" Makefile; then
    echo "   ✅ make ci-check存在"
    if grep -A 5 "ci-check:" Makefile | grep -q "uv run ruff check"; then
        echo "   ✅ 包含ruff check"
    fi
    if grep -A 5 "ci-check:" Makefile | grep -q "uv run mypy"; then
        echo "   ✅ 包含mypy检查"
    fi
    if grep -A 5 "ci-check:" Makefile | grep -q "uv run pytest"; then
        echo "   ✅ 包含pytest测试"
    fi
else
    echo "   ❌ make ci-check不存在"
fi

# 标准2: CI workflow 里只跑 make ci-check
echo "2️⃣ 检查CI workflow..."
if grep -q "make ci-check" .github/workflows/ci.yml; then
    echo "   ✅ ci.yml调用make ci-check"
else
    echo "   ❌ ci.yml未调用make ci-check"
fi

if grep -q "make ci-check" .github/workflows/lightweight-ci.yml; then
    echo "   ✅ lightweight-ci.yml调用make ci-check"
else
    echo "   ❌ lightweight-ci.yml未调用make ci-check"
fi

# 标准3: .cursor/rules.md 存在并生效
echo "3️⃣ 检查Cursor规则..."
if [[ -f ".cursor/rules.md" ]]; then
    echo "   ✅ .cursor/rules.md存在"
    if grep -q "make ci-check" .cursor/rules.md; then
        echo "   ✅ 包含ci-check规则"
    fi
else
    echo "   ❌ .cursor/rules.md不存在"
fi

# 标准4: 本地 pre-commit 能阻止不合格提交
echo "4️⃣ 检查pre-commit配置..."
if [[ -f ".pre-commit-config.yaml" ]]; then
    echo "   ✅ .pre-commit-config.yaml存在"
    if grep -q "ruff" .pre-commit-config.yaml; then
        echo "   ✅ 包含ruff检查"
    fi
    if grep -q "mypy" .pre-commit-config.yaml; then
        echo "   ✅ 包含mypy检查"
    fi
    if grep -q "pytest" .pre-commit-config.yaml; then
        echo "   ✅ 包含pytest检查"
    fi
else
    echo "   ❌ .pre-commit-config.yaml不存在"
fi

# 检查pre-commit是否已安装
if [[ -f ".git/hooks/pre-commit" ]]; then
    echo "   ✅ pre-commit hooks已安装"
else
    echo "   ⚠️ pre-commit hooks未安装 (需要运行scripts/install_pre_commit.sh)"
fi

# 标准5: 可以用 make local-ci 在本地跑完整 CI 流程
echo "5️⃣ 检查local-ci配置..."
if grep -q "local-ci:" Makefile; then
    echo "   ✅ make local-ci存在"
else
    echo "   ❌ make local-ci不存在"
fi

if [[ -f "docker-compose.ci.yml" ]]; then
    echo "   ✅ docker-compose.ci.yml存在"
    if grep -q "make ci-check" docker-compose.ci.yml; then
        echo "   ✅ Docker配置调用make ci-check"
    fi
else
    echo "   ❌ docker-compose.ci.yml不存在"
fi

echo ""
echo "📊 验收结果总结："
echo "=================="

# 统计结果
total_checks=5
passed_checks=0

# 重新检查每个标准
if grep -q "ci-check:" Makefile; then ((passed_checks++)); fi
if grep -q "make ci-check" .github/workflows/ci.yml; then ((passed_checks++)); fi
if [[ -f ".cursor/rules.md" ]]; then ((passed_checks++)); fi
if [[ -f ".pre-commit-config.yaml" ]]; then ((passed_checks++)); fi
if grep -q "local-ci:" Makefile; then ((passed_checks++)); fi

echo "通过标准: $passed_checks/$total_checks"

if [[ $passed_checks -eq $total_checks ]]; then
    echo "🎉 所有验收标准都已配置完成！"
    if [[ ! -f ".git/hooks/pre-commit" ]]; then
        echo "⚠️ 还需要运行: bash scripts/install_pre_commit.sh"
    else
        echo "✨ 完全符合所有验收标准！"
    fi
else
    echo "⚠️ 还有 $((total_checks - passed_checks)) 个标准需要完善"
fi 