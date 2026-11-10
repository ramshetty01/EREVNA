.PHONY: setup test lint typecheck security run api evaluate live-evaluate docker-build smoke

PYTHON ?= python3

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.lock

test:
	$(PYTHON) -m pytest tests/ -v --cov=research --cov=agents --cov=tools --cov-report=term-missing

lint:
	$(PYTHON) -m ruff check .
	@test -z "$$(git ls-files '*__pycache__*' '*.pyc')" || (echo "tracked generated Python cache files found" && exit 1)

typecheck:
	$(PYTHON) -m mypy agents tools utils research app.py

security:
	$(PYTHON) -m pip_audit -r requirements.lock --disable-pip --no-deps

run:
	$(PYTHON) -m streamlit run app.py

api:
	$(PYTHON) -m uvicorn research.api:app --host 127.0.0.1 --port 8000

evaluate:
	$(PYTHON) -m research.evaluate

live-evaluate:
	$(PYTHON) -m research.evaluate --live --limit 3 --output artifacts/live-evaluation.json

docker-build:
	docker build -t erevna:local .

smoke:
	$(PYTHON) -m compileall -q agents tools utils research app.py


support-evaluate:
	$(PYTHON) -m research.evaluate_support

support-live-evaluate:
	$(PYTHON) -m research.evaluate_support --live --limit 16 --workers 2 --output artifacts/support-live-evaluation.json --review-template artifacts/support-human-review.csv
