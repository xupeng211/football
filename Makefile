.PHONY: fmt lint type sec test ci

fmt:
	ruff check . --fix && black .

lint:
	ruff check . && black --check .

type:
	mypy .

sec:
	bandit -r apps/ data_pipeline/ models/ --skip B101

test:
	python -m pytest
ci: lint type sec test

.PHONY: context.pack
context.pack:
	python3 scripts/context_pack.py


.PHONY: ingest.odds seed.sample.odds
ingest.odds:
	python3 data_pipeline/sources/ingest_odds.py --start $${START} --end $${END}

seed.sample.odds:
	USE_SAMPLE_ODDS=true python3 data_pipeline/sources/ingest_odds.py --start 2024-01-01 --end 2024-01-02 --use-sample


.PHONY: show.context
show.context:
	@echo "--- Project Context (SSOT) ---"
	@cat context/_pack.md


.PHONY: ingest.features seed.sample.features
ingest.features:
	python3 data_pipeline/transforms/ingest_features.py

seed.sample.features:
	make seed.sample.odds
	python3 data_pipeline/transforms/ingest_features.py


.PHONY: hooks.install
hooks.install:
	@python -m pip install -U pre-commit >/dev/null
	@pre-commit install || true
	@echo "pre-commit hooks installed."

.PHONY: repo.protect
repo.protect:
	@if ! command -v gh >/dev/null 2>&1; then \
	  echo "缺少 gh CLI。请手动执行以下命令为 main/dev 设置保护："; \
	  echo 'gh auth login'; \
	  echo 'gh api -X PUT repos/:owner/:repo/branches/main/protection \\'; \
	  echo '    -f required_status_checks.strict=true \\'; \
	  echo '    -f required_pull_request_reviews.dismiss_stale_reviews=true \\'; \
	  echo '    -f required_pull_request_reviews.required_approving_review_count=1 \\'; \
	  echo '    -f enforce_admins=true \\'; \
	  echo '    -f restrictions= -H "Accept: application/vnd.github+json"'; \
	  echo 'gh api -X PUT repos/:owner/:repo/branches/dev/protection 同上'; \
	  exit 0; \
	fi
	@OWNER=$$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.+)/(.+)\.git#\1#'); \
	REPO=$$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.+)/(.+)\.git#\2#'); \
	for BR in main dev; do \
	  echo "[保护] $$BR"; \
	  gh api -X PUT repos/$$OWNER/$$REPO/branches/$$BR/protection \
	    -f required_status_checks.strict=true \
	    -f required_pull_request_reviews.dismiss_stale_reviews=true \
	    -f required_pull_request_reviews.required_approving_review_count=1 \
	    -f enforce_admins=true \
	    -f required_linear_history=true \
	    -H "Accept: application/vnd.github+json" >/dev/null || true; \
	  gh api -X PUT repos/$$OWNER/$$REPO/branches/$$BR/protection/required_status_checks \
	    -f strict=true \
	    -f contexts[]="CI" \
	    -f contexts[]="CodeQL" \
	    -f contexts[]="Gitleaks" \
	    -H "Accept: application/vnd.github+json" >/dev/null || true; \
	done
	@echo "分支保护尝试完成（如未安装 gh，请按提示手动设置）。"

.PHONY: repo.check
repo.check:
	@OWNER=$$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.+)/(.+)\.git#\1#'); \
	REPO=$$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.+)/(.+)\.git#\2#'); \
	for BR in main dev; do \
	  echo "=== 分支保护检查: $$BR ==="; \
	  gh api repos/$$OWNER/$$REPO/branches/$$BR/protection -H "Accept: application/vnd.github+json" | sed -n '1,120p' || echo "gh 未配置或无权限"; \
	done
	@echo "=== 工作流文件 ==="; ls -la .github/workflows || true
