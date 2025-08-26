.PHONY: ci lint type security test install
install:
	uv pip install --no-cache --strict --resolution=lowest-direct -r requirements.txt
	python -m pip check

lint:
	ruff check .

type:
	mypy .

security:
	bandit -q -r .

test:
	pytest -q --disable-warnings --maxfail=1 --cov=apps --cov-report=term-missing

ci: install lint type security test
