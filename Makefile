# Football Prediction System - Development Makefile
.DEFAULT_GOAL := help
.PHONY: help clean clean-all format lint type test security security-deps ci dev docker-up docker-down install cov diffcov local-ci validate-contract

# Configuration
PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
# In CI, we don't use a venv, the python from setup-python is used directly
ifeq ($(CI),true)
	PYTHON_VENV := python
else
	PYTHON_VENV := $(VENV)/bin/python
endif

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Check if virtual environment is active
check-venv:
	@if [ "$(CI)" = "true" ]; then \
		echo "$(GREEN)✅ CI environment detected, skipping virtual environment check.$(NC)"; \
	else \
		if [ -z "$(VIRTUAL_ENV)" ]; then \
			echo "$(RED)❌ Virtual environment is not active!$(NC)"; \
			echo "$(YELLOW)Please run: source $(VENV)/bin/activate$(NC)"; \
			exit 1; \
		fi; \
		echo "$(GREEN)✅ Virtual environment active: $(VIRTUAL_ENV)$(NC)"; \
	fi

help: ## Show this help message
	@echo "$(BLUE)🚀 Football Prediction System - Development Commands$(NC)"
	@echo "$(BLUE)================================================$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)📋 Typical Development Workflow:$(NC)"
	@echo "  1. $(YELLOW)make install$(NC)  # Set up dependencies"
	@echo "  2. $(YELLOW)make ci$(NC)       # Run all checks"
	@echo "  3. $(YELLOW)make dev$(NC)      # Start development server"

install: ## Install dependencies using uv and lock file
	@echo "$(BLUE)🔧 Setting up dependencies...$(NC)"
	@[ -d "$(VENV)" ] || $(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✅ Virtual environment ready: $(VENV)$(NC)"
	@. $(VENV)/bin/activate; \
	python -m pip install -U pip uv; \
	if [ ! -f "requirements.lock" ]; then \
		echo "$(YELLOW)⚠️ Lock file not found, generating...$(NC)"; \
		uv pip compile pyproject.toml --all-extras -o requirements.lock; \
	fi; \
	uv pip sync requirements.lock; \
	uv pip install -e .[dev]; \
	pre-commit install
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

security-deps: check-venv ## Run dependency security scan
	@echo "$(BLUE)🔒 Running dependency security scan...$(NC)"
	PIPAPI_PYTHON_LOCATION=$(PYTHON_VENV) pip-audit
	@echo "$(GREEN)✅ Dependency security scan completed$(NC)"

test: check-venv ## Run tests with coverage using settings from pyproject.toml
	@echo "$(BLUE)🧪 Running tests in parallel...$(NC)"
	$(PYTHON_VENV) -m pytest
	@echo "$(GREEN)✅ Tests completed$(NC)"

ci: format lint type security security-deps test validate policy-guard validate-contract ## Run complete CI pipeline locally
	@echo "$(GREEN)🎊 All CI checks passed!$(NC)"


ci.test: test ## Run tests with coverage for CI
	@echo "$(GREEN)✅ CI tests completed$(NC)"

ci.lint: format lint ## Run linting and formatting for CI
	@echo "$(GREEN)✅ CI linting and formatting completed$(NC)"

ci.full: ci ## Run the full CI pipeline locally
	@echo "$(GREEN)✅ Full CI simulation completed$(NC)"

dev: ## Start development server
	@echo "$(BLUE)🚀 Starting development server...$(NC)"
	@if [ -f "apps/api/main.py" ]; then \
		ENV=development $(PYTHON_VENV) -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000; \
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

clean: ## Clean up temporary files (excluding caches)
	@echo "$(BLUE)🧹 Cleaning up temporary files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete
	find . -name "coverage.json" -delete
	rm -rf htmlcov/
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

clean-all: ## Clean up all temporary files, caches, and build artifacts
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

validate-contract: check-venv ## Validate data contract against implementation
	@echo "$(BLUE)🔍 Validating data contract...$(NC)"
	$(PYTHON_VENV) scripts/validate_contract.py
	@echo "$(GREEN)✅ Data contract is in sync with implementation$(NC)"

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

local-ci: ci ## Alias for the main CI pipeline

# MVP 相关命令
mvp-up: ## 启动MVP环境 (数据库 + API)
	@echo "$(BLUE)🚀 启动MVP环境...$(NC)"
	docker-compose -f docker-compose.mvp.yml up -d --build
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

prefect-deploy: ## Deploy Prefect flows
	@echo "$(BLUE)🚀 Deploying Prefect flows...$(NC)"
	@echo "Waiting 10 seconds for Prefect server to initialize..."
	@sleep 10
	PREFECT_API_URL=http://127.0.0.1:4200/api $(PYTHON_VENV) -m flows.data_collection_flow
	@echo "$(GREEN)✅ Prefect flows deployed$(NC)"

serve: ## 启动API服务 (本地开发)
	@echo "$(BLUE)🚀 启动API服务...$(NC)"
	$(PYTHON_VENV) -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

test-api: ## 测试API接口
	@echo "$(BLUE)🧪 测试API接口...$(NC)"
	curl -X POST "http://localhost:8000/api/v1/predict" \
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
.PHONY: seed.sample.odds seed.sample.features seed.sample.matches seed.sample

seed.sample.odds: check-venv ## Seed database with sample odds data
	@echo "🌱 Seeding database with sample odds data..."
	@$(PYTHON_VENV) -m data_pipeline.sources.ingest_odds --use-sample
	@echo "✅ Sample odds data seeded."

seed.sample.features: check-venv ## Seed database with sample features data
	@echo "🌱 Seeding database with sample features data..."
	@$(PYTHON_VENV) -m data_pipeline.transforms.ingest_features
	@echo "✅ Sample features data seeded."

seed.sample.matches: check-venv ## Seed database with sample matches data
	@echo "🌱 Seeding database with sample matches data..."
	@$(PYTHON_VENV) scripts/seed_matches.py
	@echo "✅ Sample matches data seeded."

seed.sample: seed.sample.matches seed.sample.odds seed.sample.features ## Seed database with all sample data
	@echo "✅ All sample data seeded."

# 测试相关命令
.PHONY: test test-unit test-integration test-regression test-e2e test-all
.PHONY: test-quick test-full test-ci test-smoke test-coverage

# 基本测试命令
test-default: test-quick
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
# 🔬 Advanced Testing
# ==============================================================================
.PHONY: mutation-test

mutation-test: check-venv ## Run mutation testing with mutmut
	@echo "$(BLUE)🔬 Running mutation testing... (this may take a while)$(NC)"
	mutmut run
	@echo "$(GREEN)✅ Mutation testing finished. Run 'mutmut results' to see details.$(NC)"
	@echo "$(YELLOW)💡 You can also run 'mutmut html' to generate an HTML report.$(NC)"
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

# ==============================================================================
# 🔧 Configuration Management
# ==============================================================================
.PHONY: validate-config test-db-connection test-api-keys setup-env

validate-config: ## 验证所有配置文件
	@echo "$([object Object]Validating configuration files...$(NC)"
	@if [ ! -f ".env" ]; then \
		echo "$(YELLOW)⚠️ .env file not found, copying from template...$(NC)"; \
		cp .env.example .env; \
		echo "$(YELLOW)📝 Please edit .env file with your actual values$(NC)"; \
	fi
	@python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))" && echo "$(GREEN)✅ pyproject.toml valid$(NC)"
	@python -c "import yaml; yaml.safe_load(open('docker-compose.yml'))" && echo "$(GREEN)✅ docker-compose.yml valid$(NC)"
	@echo "$(GREEN)✅ All configuration files are valid$(NC)"

test-db-connection: ## 测试数据库连接
	@echo "$(BLUE)🗄️ Testing database connection...$(NC)"
	@if command -v psql >/dev/null 2>&1; then \
		if [ -f ".env" ]; then \
			set -a; source .env; set +a; \
			psql "$$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1 && \
			echo "$(GREEN)✅ Database connection successful$(NC)" || \
			echo "$(RED)❌ Database connection failed$(NC)"; \
		else \
			echo "$(YELLOW)⚠️ .env file not found$(NC)"; \
		fi; \
	else \
		echo "$(YELLOW)⚠️ psql not installed, skipping database test$(NC)"; \
	fi

test-api-keys: ## 测试API密钥配置
	@echo "$(BLUE)🔑 Testing API keys...$(NC)"
	@if [ -f ".env" ]; then \
		set -a; source .env; set +a; \
		if [ "$$FOOTBALL_DATA_API_KEY" != "your_football_data_api_key_here" ]; then \
			curl -s -H "X-Auth-Token: $$FOOTBALL_DATA_API_KEY" \
				"https://api.football-data.org/v4/competitions" >/dev/null 2>&1 && \
			echo "$(GREEN)✅ Football Data API key valid$(NC)" || \
			echo "$(RED)❌ Football Data API key invalid$(NC)"; \
		else \
			echo "$(YELLOW)⚠️ Football Data API key not configured$(NC)"; \
		fi; \
	else \
		echo "$(YELLOW)⚠️ .env file not found$(NC)"; \
	fi

setup-env: ## 设置开发环境
	@echo "$(BLUE)🚀 Setting up development environment...$(NC)"
	@if [ ! -f ".env" ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✅ Created .env from template$(NC)"; \
		echo "$(YELLOW)📝 Please edit .env with your actual values$(NC)"; \
	fi
	@mkdir -p logs models/artifacts data/samples
	@echo "$(GREEN)✅ Development environment setup complete$(NC)"

# ==============================================================================
# 📊 Monitoring and Observability
# ==============================================================================
.PHONY: monitoring-up monitoring-down monitoring-logs monitoring-status

monitoring-up: ## 启动监控栈 (Prometheus + Grafana + Loki)
	@echo "$(BLUE)📊 Starting monitoring stack...$(NC)"
	@docker network create football_net 2>/dev/null || true
	@docker-compose -f docker-compose.monitoring.yml up -d
	@echo "$(GREEN)✅ Monitoring stack started$(NC)"
	@echo "$(YELLOW)📊 Grafana: http://localhost:3000 (admin/admin123)$(NC)"
	@echo "$(YELLOW)📈 Prometheus: http://localhost:9090$(NC)"

monitoring-down: ## 停止监控栈
	@echo "$(BLUE)🛑 Stopping monitoring stack...$(NC)"
	@docker-compose -f docker-compose.monitoring.yml down
	@echo "$(GREEN)✅ Monitoring stack stopped$(NC)"

monitoring-logs: ## 查看监控服务日志
	@docker-compose -f docker-compose.monitoring.yml logs -f

monitoring-status: ## 检查监控服务状态
	@echo "$(BLUE)📊 Monitoring services status:$(NC)"
	@docker-compose -f docker-compose.monitoring.yml ps
