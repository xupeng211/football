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
	pytest -q --disable-warnings --cov=. --cov-report=term --cov-fail-under=20

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
