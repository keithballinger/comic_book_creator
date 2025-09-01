.PHONY: install test build clean run lint format dev-install

# Virtual environment directory
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

install: $(VENV)/bin/activate
	$(PIP) install -r requirements.txt

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

dev-install: install
	$(PIP) install -e .

test: install
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing

build: install
	$(PYTHON) -m py_compile src/**/*.py

run: install
	$(PYTHON) -m src.cli

lint: install
	$(PYTHON) -m ruff check src/
	$(PYTHON) -m mypy src/ --ignore-missing-imports

format: install
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m isort src/ tests/

clean:
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .cache
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Development helpers
shell: install
	$(PYTHON)

freeze: install
	$(PIP) freeze > requirements-lock.txt