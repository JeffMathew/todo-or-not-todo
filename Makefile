.PHONY: test lint clean run

test:
	uv run pytest

lint:
	uv run black --check .
	uv run ruff check .
	uv run pyright

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache

run:
	uv run uvicorn app.main:app --reload
