# ==== Repo defaults (override by: make REPO=xxx OWNER=yyy) ====
OWNER ?= xupeng211
REPO  ?= football

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


.PHONY: install hooks.install docker-up docker-down dev
install:
	pip install -e .
	@echo "项目依赖已安装"

hooks.install:
	@python -m pip install -U pre-commit >/dev/null
	@pre-commit install || true
	@echo "pre-commit hooks installed."

docker-up:
	docker-compose up -d postgres redis prefect-server
	@echo "基础服务已启动"

docker-down:
	docker-compose down
	@echo "所有服务已停止"

dev:
	docker-compose up --build api
	@echo "开发服务已启动"

.PHONY: repo.protect
repo.protect:
	@echo "[保护] applying branch protection to main & dev on $(OWNER)/$(REPO)"
	@mkdir -p .github
	@echo '{ "required_status_checks": { "strict": true, "checks": [{"context":"CI"},{"context":"CodeQL"},{"context":"Gitleaks"}] }, "enforce_admins": true, "required_pull_request_reviews": { "dismiss_stale_reviews": true, "required_approving_review_count": 1 }, "restrictions": null, "allow_force_pushes": false, "allow_deletions": false, "required_linear_history": true, "block_creations": false, "lock_branch": false, "allow_fork_syncing": false }' > .github/branch_protection.json
	@gh api -X PUT "repos/$(OWNER)/$(REPO)/branches/main/protection" -H "Accept: application/vnd.github+json" --input .github/branch_protection.json
	@# dev 不存在时跳过
	@if git ls-remote --heads origin dev | grep -q dev; then \
	  gh api -X PUT "repos/$(OWNER)/$(REPO)/branches/dev/protection" -H "Accept: application/vnd.github+json" --input .github/branch_protection.json; \
	else \
	  echo "⚠️  远端无 dev 分支，跳过 dev 保护（如需：git push -u origin dev）"; \
	fi

.PHONY: repo.check
repo.check:
	@OWNER=$$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.+)/(.+)\.git#\1#'); \
	REPO=$$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.+)/(.+)\.git#\2#'); \
	for BR in main dev; do \
	  echo "=== 分支保护检查: $$BR ==="; \
	  gh api repos/$$OWNER/$$REPO/branches/$$BR/protection -H "Accept: application/vnd.github+json" | sed -n '1,120p' || echo "gh 未配置或无权限"; \
	done
	@echo "=== 工作流文件 ==="; ls -la .github/workflows || true
