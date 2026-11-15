.PHONY: test coverage lint install clean

install:
	uv pip install -r requirements.txt

test:
	uv run pytest --tb=short -q

test-verbose:
	uv run pytest --tb=short -v

coverage:
	uv run pytest --cov=. --cov-report=term-missing --cov-report=html -q

lint:
	uv run ruff check .
	uv run ruff format --check .

lint-fix:
	uv run ruff check --fix .
	uv run ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml
