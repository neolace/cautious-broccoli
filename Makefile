.PHONY: install lint format typecheck test check clean

install:     ## Create venv and install all deps
	uv sync

lint:        ## Lint with ruff
	uv run ruff check .

format:      ## Auto-format with ruff
	uv run ruff format .
	uv run ruff check --fix .

typecheck:   ## Static type checking
	uv run mypy src

test:        ## Run unit tests with coverage
	uv run pytest

check: lint typecheck test  ## Everything CI runs
	uv run ruff format --check .

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist
