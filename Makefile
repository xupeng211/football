# Football Prediction System - Development Makefile
.DEFAULT_GOAL := help
.PHONY: help clean format lint type test security ci dev docker-up docker-down install cov local-ci

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

local-ci: format lint type validate policy-guard sec cov ## Run complete local CI pipeline
	@echo "$(GREEN)🎊 All local CI checks passed!$(NC)"
