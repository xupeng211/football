#!/bin/bash
# GitHub Actions监控脚本

set -e

# 配置
REPO="xupeng211/football"
BRANCH="feat/p1-hardening"
WORKFLOW="CI"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔍 GitHub Actions监控启动..."
echo "========================================"
echo "📦 仓库: $REPO"
echo "🌿 分支: $BRANCH"
echo "⚙️ 工作流: $WORKFLOW"
echo ""

# 检查gh cli是否安装
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) 未安装${NC}"
    echo "请安装: https://cli.github.com/"
    exit 1
fi

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️ 未登录GitHub CLI${NC}"
    echo "请运行: gh auth login"
    exit 1
fi

# 获取最新的工作流运行
echo "📋 获取最新的工作流运行..."
RUNS=$(gh run list --repo $REPO --workflow "$WORKFLOW" --branch $BRANCH --limit 5 --json databaseId,status,conclusion,createdAt,headBranch,event,displayTitle)

if [ -z "$RUNS" ] || [ "$RUNS" = "[]" ]; then
    echo -e "${YELLOW}⚠️ 未找到相关的工作流运行${NC}"
    echo "可能原因:"
    echo "1. 分支名称不正确"
    echo "2. 工作流名称不匹配"
    echo "3. 还未触发任何运行"
    exit 1
fi

echo "$RUNS" | jq -r '.[] | "\(.databaseId) \(.status) \(.conclusion) \(.createdAt) \(.displayTitle)"' | while read -r run_id status conclusion created_at title; do
    # 状态图标
    if [ "$status" = "completed" ]; then
        if [ "$conclusion" = "success" ]; then
            status_icon="🟢"
            status_text="${GREEN}SUCCESS${NC}"
        elif [ "$conclusion" = "failure" ]; then
            status_icon="🔴"
            status_text="${RED}FAILURE${NC}"
        elif [ "$conclusion" = "cancelled" ]; then
            status_icon="⚪"
            status_text="${YELLOW}CANCELLED${NC}"
        else
            status_icon="🟡"
            status_text="${YELLOW}${conclusion}${NC}"
        fi
    else
        status_icon="🔄"
        status_text="${BLUE}RUNNING${NC}"
    fi

    # 格式化时间
    formatted_time=$(date -d "$created_at" +"%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$created_at")

    echo -e "${status_icon} Run #${run_id} - ${status_text}"
    echo -e "   📅 ${formatted_time}"
    echo -e "   📝 ${title}"
    echo ""
done

# 获取最新运行的详细信息
LATEST_RUN_ID=$(echo "$RUNS" | jq -r '.[0].databaseId')
LATEST_STATUS=$(echo "$RUNS" | jq -r '.[0].status')
LATEST_CONCLUSION=$(echo "$RUNS" | jq -r '.[0].conclusion')

echo "🔍 最新运行详情 (ID: $LATEST_RUN_ID)"
echo "========================================"

if [ "$LATEST_STATUS" = "completed" ]; then
    if [ "$LATEST_CONCLUSION" = "success" ]; then
        echo -e "${GREEN}🎉 CI成功！所有检查都通过了！${NC}"

        # 获取运行时间
        echo ""
        echo "📊 运行统计:"
        gh run view $LATEST_RUN_ID --repo $REPO --json jobs | jq -r '.jobs[] | "  \(.name): \(.conclusion)"'

    elif [ "$LATEST_CONCLUSION" = "failure" ]; then
        echo -e "${RED}❌ CI失败！正在分析问题...${NC}"

        # 显示失败的作业
        echo ""
        echo "💥 失败的作业:"
        gh run view $LATEST_RUN_ID --repo $REPO --json jobs | jq -r '.jobs[] | select(.conclusion == "failure") | "  ❌ \(.name)"'

        echo ""
        echo "📋 完整日志:"
        echo "gh run view $LATEST_RUN_ID --repo $REPO --log"

        echo ""
        echo "🔧 快速修复建议:"
        echo "1. 查看详细日志: gh run view $LATEST_RUN_ID --repo $REPO --log"
        echo "2. 运行本地预检: ./scripts/ci-precheck.sh"
        echo "3. 检查代码质量: ./scripts/ci-dashboard.py"
        echo "4. 修复后重新推送触发CI"

    else
        echo -e "${YELLOW}⚠️ CI状态: $LATEST_CONCLUSION${NC}"
    fi
else
    echo -e "${BLUE}🔄 CI正在运行中...${NC}"
    echo ""
    echo "实时监控命令:"
    echo "gh run watch $LATEST_RUN_ID --repo $REPO"
fi

echo ""
echo "🔗 快速链接:"
echo "📱 Web界面: https://github.com/$REPO/actions/runs/$LATEST_RUN_ID"
echo "📋 查看日志: gh run view $LATEST_RUN_ID --repo $REPO --log"
echo "🔄 重新运行: gh run rerun $LATEST_RUN_ID --repo $REPO"

# 如果是失败状态，提供自动修复选项
if [ "$LATEST_CONCLUSION" = "failure" ]; then
    echo ""
    echo -e "${YELLOW}🔧 是否要运行自动诊断和修复？ (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        echo "🔧 开始自动诊断..."

        # 运行本地检查
        if [ -x "./scripts/ci-precheck.sh" ]; then
            echo "📋 运行CI预检查..."
            ./scripts/ci-precheck.sh || true
        fi

        # 运行质量监控
        if [ -x "./scripts/ci-dashboard.py" ]; then
            echo ""
            echo "📊 运行质量监控..."
            python ./scripts/ci-dashboard.py || true
        fi

        echo ""
        echo "🔧 自动修复建议："
        echo "1. ruff format . # 修复格式问题"
        echo "2. ruff check --fix . # 自动修复lint问题"
        echo "3. pytest tests/ -x # 检查测试问题"
        echo "4. 修复后提交并推送"
    fi
fi
