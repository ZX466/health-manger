.PHONY: test coverage lint install clean

install:
	pip install -r requirements.txt

test:
	pytest --tb=short -q

test-verbose:
	pytest --tb=short -v

coverage:
	pytest --cov=. --cov-report=term-missing --cov-report=html -q

lint:
	ruff check .
	ruff format --check .

lint-fix:
	ruff check --fix .
	ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml
