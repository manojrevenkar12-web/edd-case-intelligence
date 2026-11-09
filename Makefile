PY ?= python3
export PYTHONPATH := src

.PHONY: check lint test web-test dev heldout lock lock-check report api
check: lint test web-test lock-check
lint:
	ruff format --check src tests scripts && ruff check src tests scripts
test:
	$(PY) -m pytest -q
web-test:
	cd web && npx vitest run
dev:
	$(PY) scripts/evaluate.py dev
heldout:
	$(PY) scripts/evaluate.py heldout
lock:
	$(PY) scripts/lock.py write
lock-check:
	$(PY) scripts/lock.py verify
report:
	$(PY) scripts/report.py
api:
	$(PY) -m uvicorn edd.api:app --reload
