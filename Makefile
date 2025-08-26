.PHONY: install fmt lint type test sec leaks ci clean help check-venv
.DEFAULT_GOAL := help

# 颜色定义
YELLOW := \033[1;33m
GREEN := \033[1;32m
RED := \033[1;31m
BLUE := \033[0;34m
NC := \033[0m

# 虚拟环境检查
check-venv: ## 检查虚拟环境状态（AI开发强制要求）
	@echo "$(BLUE)🤖 AI开发环境检查$(NC)"
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "$(RED)❌ AI开发工具必须在虚拟环境中运行！$(NC)"; \
		echo "$(YELLOW)💡 请先运行: source scripts/activate-venv.sh$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ 虚拟环境已激活: $$VIRTUAL_ENV$(NC)"
	@echo "$(GREEN)✅ Python版本: $$(python --version)$(NC)"

help: ## 显示帮助信息
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo "$(BLUE)🤖 AI开发强制要求: 所有命令必须在虚拟环境中运行$(NC)"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-12s$(NC) %s\n", $$1, $$2}'

install: check-venv ## 安装项目依赖和开发工具
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	pip install -U pip uv
	pip install -r requirements.txt
	pip install -e .
	pip install pre-commit ruff mypy pytest pytest-cov bandit
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

fmt: check-venv ## 格式化代码 (ruff + black)
	@echo "$(YELLOW)Formatting code...$(NC)"
	ruff format .
	ruff check --fix .
	@echo "$(GREEN)✅ Code formatted$(NC)"

lint: check-venv ## 代码风格检查 (ruff)
	@echo "$(YELLOW)Running linter...$(NC)"
	ruff check .
	@echo "$(GREEN)✅ Linting passed$(NC)"

type: check-venv ## 类型检查 (mypy)
	@echo "$(YELLOW)Running type checker...$(NC)"
	mypy .
	@echo "$(GREEN)✅ Type checking passed$(NC)"

test: check-venv ## 运行测试 (pytest)
	@echo "$(YELLOW)Running tests...$(NC)"
	pytest -v
	@echo "$(GREEN)✅ Tests passed$(NC)"

sec: check-venv ## 安全检查 (bandit)
	@echo "$(YELLOW)Running security check...$(NC)"
	bandit -r . -f json -o bandit-report.json --exit-zero
	bandit -r . --configfile pyproject.toml
	@echo "$(GREEN)✅ Security check passed$(NC)"

leaks: check-venv ## 秘密泄露检查 (gitleaks)
	@echo "$(YELLOW)Running secrets scan...$(NC)"
	@if command -v gitleaks >/dev/null 2>&1; then \
		gitleaks detect --config .gitleaks.toml --verbose --no-banner; \
		echo "$(GREEN)✅ No secrets detected$(NC)"; \
	else \
		echo "$(RED)⚠️  gitleaks not installed, skipping...$(NC)"; \
	fi

ci: install fmt lint type sec test ## 完整CI检查流程（强制虚拟环境）
	@echo "$(GREEN)�� All CI checks passed!$(NC)"
	@echo "$(BLUE)🤖 AI开发环境验证通过$(NC)"

clean: ## 清理生成的文件
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov/ .coverage coverage.xml
	rm -f bandit-report.json
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# AI开发工具快速启动
ai-setup: ## AI开发工具快速环境设置
	@echo "$(BLUE)🤖 AI开发工具环境设置$(NC)"
	@echo "$(YELLOW)正在设置虚拟环境...$(NC)"
	@if [ ! -d ".venv" ]; then python -m venv .venv; fi
	@echo "$(YELLOW)请运行以下命令激活环境:$(NC)"
	@echo "$(GREEN)source .venv/bin/activate$(NC)"
	@echo "$(GREEN)make install$(NC)"
	@echo "$(GREEN)make ci$(NC)"
