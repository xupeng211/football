# Football Prediction System v3.0 - Modern Development Makefile
.DEFAULT_GOAL := help
.PHONY: help install dev test ci build deploy clean doctor

# === 配置 ===
PYTHON := python3
PROJECT_NAME := football-predict-system
DOCKER_IMAGE := $(PROJECT_NAME):latest

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
	@echo "$(YELLOW)🧪 测试相关:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?## 🧪/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, substr($$2, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)🐳 容器相关:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?## 🐳/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, substr($$2, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)💡 推荐工作流:$(NC)"
	@echo "  1. $(GREEN)make install$(NC)    # 安装依赖"
	@echo "  2. $(GREEN)make dev$(NC)        # 启动开发服务器"
	@echo "  3. $(GREEN)make ci$(NC)         # 运行所有检查"
	@echo "  4. $(GREEN)make test$(NC)       # 运行测试"

# === 环境管理 ===
install: ## 📦 安装所有依赖
	@echo "$(BLUE)🔧 安装依赖...$(NC)"
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)❌ 请先安装 uv: pip install uv$(NC)"; exit 1; }
	uv sync --all-extras
	uv pip install -e .
	@echo "$(GREEN)✅ 依赖安装完成$(NC)"

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
	uv run mypy src/ --ignore-missing-imports
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
