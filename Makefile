.PHONY: install test build clean run lint format dev-install test-refexp run-refexp

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
	GEMINI_API_KEY=test-key $(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing

test-refexp: install
	GEMINI_API_KEY=test-key $(PYTHON) -m pytest tests/test_refexp/ -v

build: install
	$(PYTHON) -m py_compile src/**/*.py

run: install
	$(PYTHON) -m src.cli

run-refexp: install
	$(PYTHON) comic_creator.py ref-exp examples/reference_experiments/simple_test.yaml --iterations 2

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
	rm -rf output/reference_experiments/session_*
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.bak" -delete

# Development helpers
shell: install
	$(PYTHON)

freeze: install
	$(PIP) freeze > requirements-lock.txt