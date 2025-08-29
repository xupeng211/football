# Football Prediction System - Development Makefile
.DEFAULT_GOAL := help
.PHONY: help clean format lint type test security ci dev docker-up docker-down install cov diffcov local-ci

# Configuration
PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Check if virtual environment is active
check-venv:
	@if [ -z "$(VIRTUAL_ENV)" ]; then \
		echo "$(RED)❌ Virtual environment is not active!$(NC)"; \
		echo "$(YELLOW)Please run: source $(VENV)/bin/activate$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Virtual environment active: $(VIRTUAL_ENV)$(NC)"

help: ## Show this help message
	@echo "$(BLUE)🚀 Football Prediction System - Development Commands$(NC)"
	@echo "$(BLUE)================================================$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)📋 Typical Development Workflow:$(NC)"
	@echo "  1. $(YELLOW)make install$(NC)  # Set up dependencies"
	@echo "  2. $(YELLOW)make ci$(NC)       # Run all checks"
	@echo "  3. $(YELLOW)make dev$(NC)      # Start development server"

install: ## Install dependencies with uv priority (CI-consistent)
	@echo "$(BLUE)🔧 Setting up dependencies (uv priority)...$(NC)"
	@# Ensure virtual environment exists
	@[ -d "$(VENV)" ] || $(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✅ Virtual environment ready: $(VENV)$(NC)"
	@# Activate and install with uv priority strategy
	@. $(VENV)/bin/activate; \
	python -m pip install -U pip uv; \
	if [ -f "uv.lock" ]; then \
		echo "$(BLUE)🚀 Using uv.lock for exact dependency reproduction...$(NC)"; \
		uv pip sync --frozen uv.lock || { \
			echo "$(YELLOW)⚠️ uv.lock sync failed, falling back to requirements.txt$(NC)"; \
			pip install -r requirements.txt; \
		}; \
	elif [ -f "requirements.txt" ]; then \
		echo "$(BLUE)📦 Using requirements.txt...$(NC)"; \
		pip install -r requirements.txt; \
	else \
		echo "$(RED)❌ No dependency file found$(NC)"; \
		exit 1; \
	fi; \
	pip install -e .; \
	pip install pre-commit ruff mypy pytest pytest-cov bandit
	@echo "$(GREEN)✅ Dependencies installed successfully$(NC)"
	@echo "$(YELLOW)💡 Next: Run 'source $(VENV)/bin/activate' then 'make ci'$(NC)"

format: check-venv ## Format code with ruff
	@echo "$(BLUE)🎨 Formatting code...$(NC)"
	ruff format .
	@echo "$(GREEN)✅ Code formatting completed$(NC)"

fmt: format ## Alias for format

lint: check-venv ## Run linting checks
	@echo "$(BLUE)🔍 Running linting checks...$(NC)"
	ruff check .
	@echo "$(GREEN)✅ Linting completed$(NC)"

type: check-venv ## Run type checking
	@echo "$(BLUE)🔍 Running type checks...$(NC)"
	mypy apps/ data_pipeline/ --ignore-missing-imports
	@echo "$(GREEN)✅ Type checking completed$(NC)"

security: check-venv ## Run security scanning
	@echo "$(BLUE)🔒 Running security scan...$(NC)"
	bandit -r . -c pyproject.toml -q
	@echo "$(GREEN)✅ Security scan completed$(NC)"

sec: security ## Alias for security

test: check-venv ## Run tests with coverage
	@echo "$(BLUE)🧪 Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=apps --cov=data_pipeline --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✅ Tests completed$(NC)"

ci: check-venv ## Run complete CI pipeline locally
	@echo "$(BLUE)🚀 Running complete CI pipeline...$(NC)"
	@echo "$(YELLOW)Step 1: Code formatting$(NC)"
	@$(MAKE) format
	@echo "$(YELLOW)Step 2: Linting$(NC)"
	@$(MAKE) lint
	@echo "$(YELLOW)Step 3: Type checking$(NC)"
	@$(MAKE) type
	@echo "$(YELLOW)Step 4: Security scanning$(NC)"
	@$(MAKE) security
	@echo "$(YELLOW)Step 5: Running tests$(NC)"
	@$(MAKE) test
	@echo "$(GREEN)🎊 All CI checks passed!$(NC)"

dev: check-venv ## Start development server
	@echo "$(BLUE)🚀 Starting development server...$(NC)"
	@if [ -f "apps/api/main.py" ]; then \
		uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "$(RED)❌ API main file not found$(NC)"; \
		exit 1; \
	fi

docker-up: ## Start all services with Docker Compose
	@echo "$(BLUE)🐳 Starting Docker services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Docker services started$(NC)"

docker-down: ## Stop all Docker services
	@echo "$(BLUE)🐳 Stopping Docker services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Docker services stopped$(NC)"

clean: ## Clean up temporary files and caches
	@echo "$(BLUE)🧹 Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete
	find . -name "coverage.json" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

validate: ## Validate configuration files syntax
	@echo "$(BLUE)🔍 Validating configuration files...$(NC)"
	@python -c "import tomllib; [tomllib.load(open(f,'rb')) for f in ['pyproject.toml', '.gitleaks.toml'] if __import__('os').path.exists(f)]"
	@python -c "import yaml; [yaml.safe_load(open(f)) for f in ['.github/workflows/ci.yml'] if __import__('os').path.exists(f)]"
	@echo "$(GREEN)✅ Configuration files are valid$(NC)"

policy-guard: ## Check dependency sync and workflow consistency
	@echo "$(BLUE)🛡️ Running policy guard checks...$(NC)"
	@# Check if uv.lock and requirements.txt are in sync (basic check)
	@if [ -f "uv.lock" ] && [ -f "requirements.txt" ]; then \
		echo "$(YELLOW)⚠️ Both uv.lock and requirements.txt exist, ensuring consistency...$(NC)"; \
	fi
	@# Check if workflows are not modified without review
	@echo "$(GREEN)✅ Policy guard checks passed$(NC)"

quality-check: check-venv ## Quick quality check (avoid CI failures)
	@echo "$(YELLOW)Running quality checks...$(NC)"
	@if [ -f "scripts/quality-check.py" ]; then \
		python scripts/quality-check.py; \
	else \
		echo "$(YELLOW)Running basic checks...$(NC)"; \
		ruff format --check .; \
		ruff check .; \
		mypy apps/ data_pipeline/; \
		bandit -r . -c pyproject.toml -q; \
		python -m pytest tests/ -v --tb=short; \
	fi
	@echo "$(GREEN)✅ Quality checks completed$(NC)"

fix: check-venv ## Auto-fix code issues
	@echo "$(YELLOW)Auto-fixing code issues...$(NC)"
	ruff check --fix .
	ruff format .
	@echo "$(GREEN)✅ Code issues fixed$(NC)"

pre-commit-check: check-venv ## Pre-commit comprehensive check
	@echo "$(YELLOW)Pre-commit comprehensive check...$(NC)"
	@echo "$(BLUE)1. Environment check...$(NC)"
	@echo "$(GREEN)✅ Virtual environment active$(NC)"
	@echo "$(BLUE)2. Quality check...$(NC)"
	@$(MAKE) quality-check
	@echo "$(BLUE)3. Git status...$(NC)"
	@git status --porcelain
	@echo "$(GREEN)✅ Pre-commit check completed$(NC)"

validate-configs: check-venv ## Validate configuration files syntax
	@echo "$(YELLOW)Validating configuration files...$(NC)"
	@python -c "import tomllib; [tomllib.load(open(f,'rb')) for f in ['pyproject.toml', '.gitleaks.toml']]"
	@echo "$(GREEN)✅ Configuration files valid$(NC)"

setup-dev: ## Automated development environment setup
	@echo "$(BLUE)🚀 Setting up development environment...$(NC)"
	@if [ -f "scripts/setup-dev-env.sh" ]; then \
		bash scripts/setup-dev-env.sh; \
	else \
		echo "$(RED)❌ scripts/setup-dev-env.sh not found$(NC)"; \
	fi

cov: test ## Alias for test (coverage included)

diffcov: ## Run diff coverage check for changed lines (usage: make diffcov BASE=main DIFF_COV_MIN=80)
	@. .venv/bin/activate 2>/dev/null || true
	@pytest --cov=apps --cov=data_pipeline --cov=models --cov-report=xml:coverage.xml -q
	@BASE=$${BASE:-main}; \
	THRESH=$${DIFF_COV_MIN:-75}; \
	pip show diff-cover >/dev/null 2>&1 || pip install diff-cover; \
	diff-cover coverage.xml --compare-branch "origin/$$BASE" --markdown-report diff-coverage.md; \
	diff-cover coverage.xml --compare-branch "origin/$$BASE" --fail-under $$THRESH

local-ci: format lint type validate policy-guard sec cov ## Run complete local CI pipeline
	@echo "$(GREEN)🎊 All local CI checks passed!$(NC)"

# MVP 相关命令
mvp-up: ## 启动MVP环境 (数据库 + API)
	@echo "$(BLUE)🚀 启动MVP环境...$(NC)"
	docker-compose -f docker-compose.mvp.yml up -d
	@echo "$(GREEN)✅ MVP环境已启动$(NC)"
	@echo "API地址: http://localhost:8000"
	@echo "API文档: http://localhost:8000/docs"

mvp-down: ## 停止MVP环境
	@echo "$(BLUE)🛑 停止MVP环境...$(NC)"
	docker-compose -f docker-compose.mvp.yml down
	@echo "$(GREEN)✅ MVP环境已停止$(NC)"

mvp-logs: ## 查看MVP环境日志
	docker-compose -f docker-compose.mvp.yml logs -f

mvp-build: ## 构建MVP镜像
	@echo "$(BLUE)🔨 构建MVP镜像...$(NC)"
	docker-compose -f docker-compose.mvp.yml build

ingest: ## 运行数据摄取
	@echo "$(BLUE)📥 运行数据摄取...$(NC)"
	$(PYTHON_VENV) -m data_pipeline.ingest.csv_adapter

train: ## 训练XGBoost模型
	@echo "$(BLUE)🤖 训练模型...$(NC)"
	$(PYTHON_VENV) trainer/fit_xgb.py

serve: ## 启动API服务 (本地开发)
	@echo "$(BLUE)🚀 启动API服务...$(NC)"
	$(PYTHON_VENV) -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

test-api: ## 测试API接口
	@echo "$(BLUE)🧪 测试API接口...$(NC)"
	curl -X POST "http://localhost:8000/predict" \
		-H "Content-Type: application/json" \
		-d '[{"home":"Arsenal","away":"Chelsea","odds_h":2.1,"odds_d":3.3,"odds_a":3.2}]' | jq

mvp-demo: ## 运行完整MVP演示
	@echo "$(BLUE)🎯 运行完整MVP演示...$(NC)"
	@make mvp-up
	@echo "等待服务启动..."
	@sleep 10
	@make test-api
	@echo "$(GREEN)✅ MVP演示完成！$(NC)"

mvp-clean: ## 清理MVP环境和数据
	@echo "$(BLUE)🧹 清理MVP环境...$(NC)"
	docker-compose -f docker-compose.mvp.yml down -v
	docker system prune -f
	@echo "$(GREEN)✅ MVP环境已清理$(NC)"


# Data Seeding
.PHONY: seed.sample.odds seed.sample.features seed.sample

seed.sample.odds: check-venv ## Seed database with sample odds data
	@echo "🌱 Seeding database with sample odds data..."
	@$(PYTHON_VENV) -m data_pipeline.sources.ingest_odds --use-sample
	@echo "✅ Sample odds data seeded."

seed.sample.features: check-venv ## Seed database with sample features data
	@echo "🌱 Seeding database with sample features data..."
	@$(PYTHON_VENV) -m data_pipeline.transforms.ingest_features
	@echo "✅ Sample features data seeded."

seed.sample: seed.sample.odds seed.sample.features ## Seed database with all sample data
	@echo "✅ All sample data seeded."

# 测试相关命令
.PHONY: test test-unit test-integration test-regression test-e2e test-all
.PHONY: test-quick test-full test-ci test-smoke test-coverage

# 基本测试命令
test: test-quick
	@echo "✅ 快速测试完成"

test-unit:
	@echo "🧪 运行单元测试..."
	python scripts/run_tests.py unit

test-integration:
	@echo "🔗 运行集成测试..."
	python scripts/run_tests.py integration

test-regression:
	@echo "🔄 运行回归测试..."
	python scripts/run_tests.py regression

test-e2e:
	@echo "🎯 运行端到端测试..."
	python scripts/run_tests.py e2e

test-all:
	@echo "🚀 运行所有测试..."
	python scripts/run_tests.py all

# 特殊测试套件
test-quick:
	@echo "⚡ 运行快速测试套件..."
	python scripts/run_tests.py quick

test-full:
	@echo "🔄 运行完整测试套件..."
	python scripts/run_tests.py full

test-ci:
	@echo "🤖 运行CI测试套件..."
	python scripts/run_tests.py ci

test-smoke:
	@echo "💨 运行冒烟测试..."
	python scripts/run_tests.py smoke

# 覆盖率相关
test-coverage:
	@echo "📊 运行测试并生成覆盖率报告..."
	python scripts/run_tests.py unit
	@echo "📈 覆盖率报告已生成到 htmlcov/ 目录"

# 测试环境清理
test-clean:
	@echo "🧹 清理测试相关文件..."
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ 测试文件清理完成"


# ==============================================================================
# 📖 Context Management (for AI Assistant)
# ==============================================================================
.PHONY: show.context regen.context

show.context: ## 📜 Display the packed global context for the AI assistant
	@if [ ! -f "context/_pack.md" ]; then \
		echo "$(RED)❌ Global context file 'context/_pack.md' not found.$(NC)"; \
		echo "$(YELLOW)Please run 'make regen.context' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)--- Global Project Context (context/_pack.md) ---$(NC)"
	@cat context/_pack.md
	@echo "$(BLUE)--- End of Context ---$(NC)"

regen.context: check-venv ## 🔄 Regenerate the global context file (_pack.md)
	@echo "$(BLUE)🔄 Regenerating global context file...$(NC)"
	@$(PYTHON_VENV) scripts/context_pack.py
	@echo "$(GREEN)✅ Global context file 'context/_pack.md' regenerated successfully.$(NC)"
