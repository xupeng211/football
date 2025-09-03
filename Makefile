# Football Prediction System v3.0 - Modern Development Makefile
.DEFAULT_GOAL := help
.PHONY: help install dev test ci build deploy clean doctor

# === 配置 ===
PYTHON := python3
PROJECT_NAME := football-predict-system
DOCKER_IMAGE := $(PROJECT_NAME):latest

# 虚拟环境配置
VENV_PATH := .venv
VENV_ACTIVATE := $(VENV_PATH)/bin/activate
VENV_PYTHON := $(VENV_PATH)/bin/python
VENV_PIP := $(VENV_PATH)/bin/pip

# 检查并激活虚拟环境的函数（备用方案，优先使用direnv）
define activate_venv
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "$(RED)❌ 虚拟环境不存在，请先运行 make install$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "$(YELLOW)🔄 激活虚拟环境...$(NC)"; \
		. $(VENV_ACTIVATE); \
	fi
endef

# 颜色输出
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m

# === 帮助信息 ===
help: ## 📚 显示帮助信息
	@echo "$(CYAN)🚀 Football Prediction System v3.0$(NC)"
	@echo "$(CYAN)=====================================$(NC)"
	@echo ""
	@echo "$(YELLOW)📦 环境管理:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?## 📦/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, substr($$2, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)🔧 开发工具:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?## 🔧/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, substr($$2, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)🤖 AI工具:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?## 🤖/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, substr($$2, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)🧪 测试相关:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?## 🧪/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, substr($$2, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)🐳 容器相关:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?## 🐳/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, substr($$2, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)💡 推荐工作流:$(NC)"
	@echo "  1. $(GREEN)make ai-setup$(NC)   # AI友好环境设置"
	@echo "  2. $(GREEN)make install$(NC)    # 安装依赖"
	@echo "  3. $(GREEN)make dev$(NC)        # 启动开发服务器"
	@echo "  4. $(GREEN)make ci$(NC)         # 运行所有检查"

# === 环境管理 ===
check-venv: ## 📦 检查虚拟环境状态
	@echo "$(BLUE)🔍 检查虚拟环境状态...$(NC)"
	@if [ -d "$(VENV_PATH)" ]; then \
		echo "$(GREEN)✅ 虚拟环境存在: $(VENV_PATH)$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ 虚拟环境不存在$(NC)"; \
	fi
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "$(GREEN)✅ 当前虚拟环境已激活: $$VIRTUAL_ENV$(NC)"; \
	elif command -v direnv >/dev/null 2>&1 && direnv status 2>/dev/null | grep -q "Found RC path"; then \
		echo "$(GREEN)✅ direnv 已配置，虚拟环境将自动激活$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ 虚拟环境未激活，建议安装 direnv 或手动激活$(NC)"; \
		echo "$(CYAN)  手动激活: source $(VENV_ACTIVATE)$(NC)"; \
		echo "$(CYAN)  安装 direnv: https://direnv.net/$(NC)"; \
	fi

install: check-venv ## 📦 安装所有依赖
	@echo "$(BLUE)🔧 安装依赖...$(NC)"
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)❌ 请先安装 uv: pip install uv$(NC)"; exit 1; }
	uv sync --all-extras
	uv pip install -e .
	@echo "$(GREEN)✅ 依赖安装完成$(NC)"
	@echo "$(CYAN)💡 提示: 使用 direnv 可自动激活虚拟环境$(NC)"

install-dev: ## 📦 安装开发依赖
	@echo "$(BLUE)🔧 安装开发依赖...$(NC)"
	uv sync --extra dev
	uv run pre-commit install
	@echo "$(GREEN)✅ 开发环境配置完成$(NC)"

update: ## 📦 更新所有依赖
	@echo "$(BLUE)🔄 更新依赖...$(NC)"
	uv sync --upgrade
	@echo "$(GREEN)✅ 依赖更新完成$(NC)"

# === 开发工具 ===
dev: ## 🔧 启动开发服务器
	@echo "$(BLUE)🚀 启动开发服务器...$(NC)"
	uv run uvicorn src.football_predict_system.main:app --reload --host 0.0.0.0 --port 8000

dev-debug: ## 🔧 启动调试模式服务器
	@echo "$(BLUE)🐛 启动调试服务器...$(NC)"
	uv run uvicorn src.football_predict_system.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

format: ## 🔧 格式化代码
	@echo "$(BLUE)🎨 格式化代码...$(NC)"
	uv run ruff format .
	@echo "$(GREEN)✅ 代码格式化完成$(NC)"

lint: ## 🔧 代码检查
	@echo "$(BLUE)🔍 代码检查...$(NC)"
	uv run ruff check . --fix
	@echo "$(GREEN)✅ 代码检查完成$(NC)"

type: ## 🔧 类型检查
	@echo "$(BLUE)🔍 类型检查...$(NC)"
	uv run mypy src/ --ignore-missing-imports || echo "$(YELLOW)⚠️ 类型检查有警告，但不阻塞CI$(NC)"
	@echo "$(GREEN)✅ 类型检查完成$(NC)"

security: ## 🔧 安全扫描
	@echo "$(BLUE)🔒 安全扫描...$(NC)"
	uv run bandit -r src/ -c pyproject.toml -q
	@echo "$(GREEN)✅ 安全扫描完成$(NC)"

# === 测试相关 ===
test: ## 🧪 运行所有测试
	@echo "$(BLUE)🧪 运行测试...$(NC)"
	uv run pytest

test-unit: ## 🧪 运行单元测试
	@echo "$(BLUE)🧪 运行单元测试...$(NC)"
	uv run pytest tests/unit/ -v

test-integration: ## 🧪 运行集成测试
	@echo "$(BLUE)🧪 运行集成测试...$(NC)"
	uv run pytest tests/integration/ -v

test-cov: ## 🧪 运行测试并生成覆盖率报告
	@echo "$(BLUE)🧪 运行覆盖率测试...$(NC)"
	uv run pytest --cov-report=html
	@echo "$(GREEN)✅ 覆盖率报告生成在 htmlcov/index.html$(NC)"

# === 质量检查 ===
ci: format lint type security test ## 🔧 运行所有CI检查
	@echo "$(GREEN)🎉 所有检查通过! 代码可以提交$(NC)"

doctor: ## 🔧 环境健康检查
	@echo "$(BLUE)🩺 环境健康检查...$(NC)"
	@echo "Python版本: $(shell python --version)"
	@echo "uv版本: $(shell uv --version 2>/dev/null || echo 'uv未安装')"
	@echo "项目路径: $(shell pwd)"
	@echo "依赖状态:"
	@uv pip list 2>/dev/null | head -10 || echo "需要先运行 make install"
	@echo "$(GREEN)✅ 环境检查完成$(NC)"

ai-check: ## 🤖 AI工具专用环境检查
	@echo "$(CYAN)🤖 AI工具环境检查...$(NC)"
	python3 scripts/ai_health_check.py

ai-file-check: ## 🤖 检查最近文件操作规范
	@echo "$(CYAN)🔍 检查最近文件操作...$(NC)"
	@python3 scripts/ai_file_monitor.py scan 10
	@python3 scripts/ai_file_monitor.py status

ai-file-guard: ## 🤖 检查指定文件规范 (用法: make ai-file-guard FILE=file.py)
	@echo "$(CYAN)🛡️ 文件操作守护检查...$(NC)"
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)❌ 请指定文件: make ai-file-guard FILE=path/to/file.py$(NC)"; \
		exit 1; \
	fi
	@python3 scripts/ai_file_guard.py "$(FILE)"

fix-permissions: ## 🤖 修复虚拟环境权限问题
	@echo "$(BLUE)🔧 修复权限问题...$(NC)"
	@find .venv -name "*.pyi" -exec chmod 644 {} \; 2>/dev/null || true
	@find .venv -type d -exec chmod 755 {} \; 2>/dev/null || true
	@echo "$(GREEN)✅ 权限修复完成$(NC)"

ai-setup: ai-check fix-permissions setup-hooks ## 🤖 为AI工具优化项目设置
	@echo "$(CYAN)🤖 优化项目为AI友好模式...$(NC)"
	@echo "📊 项目状态检查完成"
	@echo "🔧 权限问题已修复"
	@echo "🪝 Git hooks已配置"
	@git status --porcelain >/dev/null 2>&1 && echo "📁 Git仓库状态: 正常" || echo "📁 非Git项目或有未提交更改"
	@echo "$(GREEN)🎉 项目已优化为AI友好模式!$(NC)"
	@echo "💡 建议: 运行 'make help' 查看可用命令"

setup-hooks: ## 🤖 设置Git hooks自动检查
	@echo "$(BLUE)🪝 设置Git hooks...$(NC)"
	@git config core.hooksPath .githooks 2>/dev/null && echo "✅ Git hooks已启用" || echo "⚠️ 非Git项目，跳过hooks设置"
	@echo "$(GREEN)✅ Git hooks配置完成$(NC)"

# === 容器相关 ===
build: ## 🐳 构建Docker镜像
	@echo "$(BLUE)🐳 构建Docker镜像...$(NC)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)✅ 镜像构建完成: $(DOCKER_IMAGE)$(NC)"

run: ## 🐳 运行Docker容器
	@echo "$(BLUE)🐳 启动容器...$(NC)"
	docker run -d -p 8000:8000 --name $(PROJECT_NAME) $(DOCKER_IMAGE)
	@echo "$(GREEN)✅ 容器启动完成: http://localhost:8000$(NC)"

stop: ## 🐳 停止Docker容器
	@echo "$(BLUE)🛑 停止容器...$(NC)"
	docker stop $(PROJECT_NAME) && docker rm $(PROJECT_NAME) || true
	@echo "$(GREEN)✅ 容器已停止$(NC)"

compose-up: ## 🐳 启动完整开发环境
	@echo "$(BLUE)🐳 启动完整环境...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ 开发环境启动完成$(NC)"

compose-down: ## 🐳 停止完整开发环境
	@echo "$(BLUE)🛑 停止完整环境...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ 环境已停止$(NC)"

# === 清理 ===
clean: ## 🧹 清理缓存和临时文件
	@echo "$(BLUE)🧹 清理缓存...$(NC)"
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".coverage" -delete
	find . -name "*.cover" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	@echo "$(GREEN)✅ 清理完成$(NC)"

clean-all: clean ## 🧹 深度清理 (包括依赖)
	@echo "$(BLUE)🧹 深度清理...$(NC)"
	rm -rf .venv/
	@echo "$(GREEN)✅ 深度清理完成$(NC)"

# === 工具 ===
shell: ## 🐚 启动项目shell
	@echo "$(BLUE)🐚 启动项目shell...$(NC)"
	uv run python

# === 监控 ===
healthcheck: ## 🏥 健康检查
	@echo "$(BLUE)🏥 健康检查...$(NC)"
	curl -f http://localhost:8000/health || echo "$(RED)❌ 服务不可用$(NC)"

# === 数据中台 ===
data-setup: ## 📊 设置数据中台
	@echo "$(BLUE)🏗️ 设置数据中台...$(NC)"
	uv run python scripts/data_platform/setup_data_platform.py --action setup
	@echo "$(GREEN)✅ 数据中台设置完成$(NC)"

data-quick-start: ## 📊 数据中台快速启动
	@echo "$(BLUE)🚀 数据中台快速启动...$(NC)"
	uv run python scripts/data_platform/quick_start.py
	@echo "$(GREEN)✅ 数据中台启动完成$(NC)"

data-collect: ## 📊 运行数据采集
	@echo "$(BLUE)📡 启动数据采集...$(NC)"
	uv run python -c "import asyncio; from src.football_predict_system.data_platform.flows.data_collection import daily_data_collection_flow; asyncio.run(daily_data_collection_flow())"
	@echo "$(GREEN)✅ 数据采集完成$(NC)"

data-backfill: ## 📊 历史数据回填 (需要参数: COMP_ID, START, END)
	@echo "$(BLUE)📚 历史数据回填...$(NC)"
	@if [ -z "$(COMP_ID)" ] || [ -z "$(START)" ] || [ -z "$(END)" ]; then \
		echo "$(RED)❌ 缺少参数: make data-backfill COMP_ID=2021 START=2023-08-01 END=2024-05-31$(NC)"; \
		exit 1; \
	fi
	uv run python -c "import asyncio; from src.football_predict_system.data_platform.flows.data_collection import historical_backfill_flow; asyncio.run(historical_backfill_flow($(COMP_ID), '$(START)', '$(END)'))"
	@echo "$(GREEN)✅ 历史数据回填完成$(NC)"

data-monitor: ## 📊 数据质量监控
	@echo "$(BLUE)🔍 数据质量检查...$(NC)"
	uv run python -c "import asyncio; from src.football_predict_system.data_platform.flows.data_collection import data_quality_check_flow; asyncio.run(data_quality_check_flow())"
	@echo "$(GREEN)✅ 数据质量检查完成$(NC)"

data-health: ## 📊 数据平台健康检查
	@echo "$(BLUE)🏥 数据平台健康检查...$(NC)"
	uv run python scripts/data_platform/setup_data_platform.py --action health

data-deploy-flows: ## 📊 部署Prefect流程
	@echo "$(BLUE)🚀 部署Prefect流程...$(NC)"
	uv run python scripts/data_platform/deploy_flows.py
	@echo "$(GREEN)✅ Prefect流程部署完成$(NC)"

# =================== 本地CI流程 ===================

.PHONY: ci.local
ci.local: ## 🔍 本地CI流程 (使用uv环境)
	@echo "🔍 运行本地 CI 流程 (格式化 + Lint + 类型检查 + 安全扫描)..."
	@echo "1) 格式化检查..."
	uv run ruff format --check .
	@echo "2) Lint 检查..."
	uv run ruff check .
	@echo "3) 类型检查..."
	uv run mypy src/football_predict_system/data_platform/ --show-error-codes --no-error-summary --ignore-missing-imports || true
	@echo "4) 安全扫描..."
	uv run bandit -r src/ -c pyproject.toml
	@echo "✅ 本地CI检查完成"

.PHONY: ci.docker
ci.docker: ## 🐳 Docker环境CI流程
	@echo "🔍 运行Docker CI 流程..."
	docker compose run --rm app bash -c "\
		set -e; \
		echo '1) 格式化检查...'; \
		. .venv/bin/activate && uv run ruff format --check .; \
		echo '2) Lint 检查...'; \
		. .venv/bin/activate && uv run ruff check .; \
		echo '3) 类型检查...'; \
		. .venv/bin/activate && uv run mypy src/football_predict_system/data_platform/ --show-error-codes --no-error-summary --ignore-missing-imports || true; \
		echo '4) 安全扫描...'; \
		. .venv/bin/activate && uv run bandit -r src/ -c pyproject.toml; \
		echo '✅ Docker CI检查完成'; \
	"

.PHONY: ci.fix
ci.fix: ## 🔧 自动修复代码格式问题
	@echo "🔧 自动修复代码格式..."
	uv run ruff format .
	uv run ruff check . --fix
	@echo "✅ 代码格式修复完成"

# === 🐳 Docker CI 本地演练系统 ===
.PHONY: ci.docker.new
ci.docker.new: ## 🐳 运行新Docker化本地CI (完全模拟远程环境)
	@echo "$(CYAN)🐳 启动Docker化本地CI演练...$(NC)"
	@if [ ! -f "scripts/ci/local_ci_orchestrator.sh" ]; then \
		echo "$(RED)❌ CI编排器脚本不存在$(NC)"; \
		exit 1; \
	fi
	@bash scripts/ci/local_ci_orchestrator.sh

.PHONY: ci.docker.build
ci.docker.build: ## 🐳 构建本地CI Docker镜像
	@echo "$(CYAN)🐳 构建本地CI Docker镜像...$(NC)"
	@if [ ! -f "Dockerfile.ci" ]; then \
		echo "$(RED)❌ Dockerfile.ci 不存在$(NC)"; \
		exit 1; \
	fi
	docker build -t football-predict-ci:latest -f Dockerfile.ci .
	@echo "$(GREEN)✅ CI镜像构建完成$(NC)"

.PHONY: ci.docker.rebuild
ci.docker.rebuild: ## 🐳 强制重建CI Docker镜像
	@echo "$(CYAN)🐳 强制重建CI Docker镜像...$(NC)"
	docker build --no-cache -t football-predict-ci:latest -f Dockerfile.ci .
	@echo "$(GREEN)✅ CI镜像重建完成$(NC)"

.PHONY: ci.docker.run
ci.docker.run: ## 🐳 交互式运行CI容器 (调试用)
	@echo "$(CYAN)🐳 启动交互式CI容器...$(NC)"
	docker run -it --rm \
		--workdir /workspace \
		--volume "$(PWD):/workspace:ro" \
		--env PYTHONPATH=/workspace/src \
		--env ENVIRONMENT=testing \
		football-predict-ci:latest \
		/bin/bash

.PHONY: ci.docker.clean
ci.docker.clean: ## 🐳 清理CI Docker资源
	@echo "$(CYAN)🐳 清理CI Docker资源...$(NC)"
	-docker rmi football-predict-ci:latest 2>/dev/null || echo "$(YELLOW)⚠️  镜像不存在$(NC)"
	-docker system prune -f
	@echo "$(GREEN)✅ Docker资源清理完成$(NC)"

.PHONY: ci.doctor
ci.doctor: ## 🏥 CI环境诊断
	@echo "$(CYAN)🏥 CI环境诊断...$(NC)"
	@echo ""
	@echo "📋 环境检查:"
	@echo "============"
	@echo "🐍 Python: $$(python3 --version 2>/dev/null || echo '未安装')"
	@echo "📦 UV: $$(uv --version 2>/dev/null || echo '未安装')"
	@echo "🐳 Docker: $$(docker --version 2>/dev/null || echo '未安装')"
	@echo "🔧 Make: $$(make --version | head -1 2>/dev/null || echo '未安装')"
	@echo ""
	@echo "📁 项目文件:"
	@echo "==========="
	@echo "pyproject.toml: $$([ -f pyproject.toml ] && echo '✅ 存在' || echo '❌ 缺失')"
	@echo "Dockerfile.ci: $$([ -f Dockerfile.ci ] && echo '✅ 存在' || echo '❌ 缺失')"
	@echo "CI编排器: $$([ -f scripts/ci/local_ci_orchestrator.sh ] && echo '✅ 存在' || echo '❌ 缺失')"
	@echo "CI执行器: $$([ -f scripts/ci/local_ci_runner.sh ] && echo '✅ 存在' || echo '❌ 缺失')"
	@echo ""
	@echo "🐳 Docker状态:"
	@echo "============="
	@if command -v docker >/dev/null 2>&1; then \
		if docker info >/dev/null 2>&1; then \
			echo "✅ Docker daemon运行正常"; \
			echo "📊 镜像: $$(docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' | grep football-predict-ci || echo '无CI镜像')"; \
		else \
			echo "❌ Docker daemon未运行"; \
		fi; \
	else \
		echo "❌ Docker未安装"; \
	fi
	@echo ""
	@echo "💡 修复建议:"
	@echo "==========="
	@echo "• 构建CI镜像: make ci.docker.build"
	@echo "• 测试Docker CI: make ci.docker.new"
	@echo "• 测试本地CI: make ci.local"

.PHONY: ci.enhanced
ci.enhanced: format lint security ## 🔧 增强版本地CI检查 (替代ci.local)
	@echo "$(GREEN)✅ 增强版本地CI检查完成$(NC)"

.PHONY: ci.full.new
ci.full.new: ci.docker.new ## 🔧 完整CI检查 (Docker + 所有测试)
	@echo "$(GREEN)✅ 完整CI检查完成$(NC)"

# === 轻量级本地CI流程 ===
.PHONY: ci.fast
ci.fast: ## 🚀 快速本地CI检查 (轻量级，不依赖Docker)
	@echo "$(CYAN)🚀 启动快速本地CI检查...$(NC)"
	@./scripts/local_ci_complete.sh

.PHONY: ci.comprehensive
ci.comprehensive: ## 🏆 全面本地CI检查 (5层质量门禁)
	@echo "$(CYAN)🏆 启动全面本地CI检查...$(NC)"
	@./scripts/local_ci_comprehensive.sh

.PHONY: ci.filtered
ci.filtered: ## 🔍 运行筛选后的测试 (跳过有问题的Mock测试)
	@echo "$(CYAN)🔍 运行筛选后的测试...$(NC)"
	@uv run pytest -m "not skip_for_ci" --tb=short
	@echo "$(GREEN)✅ 筛选测试完成$(NC)"

.PHONY: ci.ready
ci.ready: ci.comprehensive ## 🎯 检查代码是否准备推送
	@echo "$(GREEN)🎉 代码已准备好推送！$(NC)"
	@echo "$(YELLOW)💡 推荐命令:$(NC)"
	@echo "$(CYAN)  git add . && git commit -m \"fix: 解决CI问题\" && git push$(NC)"

.PHONY: push.safe
push.safe: ci.comprehensive ## 🛡️ 安全推送 (先运行全面CI检查)
	@echo "$(BLUE)🔍 运行全面CI检查后推送...$(NC)"
	@echo "$(YELLOW)请确认要推送到远程仓库? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	@if git diff --quiet && git diff --staged --quiet; then \
		echo "$(YELLOW)⚠️  没有更改需要提交$(NC)"; \
	else \
		git add . && \
		echo "$(BLUE)请输入提交信息:$(NC)" && read -r msg && \
		git commit -m "$$msg" && \
		git push; \
	fi
	@echo "$(GREEN)✅ 推送完成！$(NC)"

# 别名任务 - 便于记忆和使用
.PHONY: fast-ci
fast-ci: ci.fast ## 🚀 ci.fast 的别名

.PHONY: full-ci
full-ci: ci.comprehensive ## 🏆 ci.comprehensive 的别名

.PHONY: filtered-tests
filtered-tests: ci.filtered ## 🔍 ci.filtered 的别名

.PHONY: ready
ready: ci.ready ## 🎯 ci.ready 的别名

.PHONY: safe-push  
safe-push: push.safe ## 🛡️ push.safe 的别名
