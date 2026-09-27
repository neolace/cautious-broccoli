# Development

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) ≥ 0.4 (installs Python for you)
- `make` (optional; every target is a plain `uv run …` command)

## Setup

```bash
git clone https://github.com/neolace/cautious-broccoli.git && cd cautious-broccoli
uv sync                     # creates .venv, installs runtime + dev group
uv run pre-commit install   # run ruff + mypy on every commit
```

## Project layout

```
cautious-broccoli/
├── src/jessie/          # application package
│   ├── __init__.py      # public API: convert_to_ico, convert_many, ConversionResult, errors
│   ├── __main__.py      # python -m jessie
│   ├── cli.py           # argparse front-end; reports results
│   ├── converter.py     # core logic: batch icon planning, validate, prepare, save
│   └── exceptions.py    # JessieError hierarchy
├── tests/               # pytest suite (images generated in tmp dirs)
│   ├── conftest.py      # make_image fixture
│   ├── test_batch.py    # convert_many
│   ├── test_cli.py      # main(argv) in-process
│   └── test_converter.py  # convert_to_ico
├── docs/                # this documentation
├── .github/workflows/   # CI
├── AGENTS.md            # guidance for AI coding agents
├── CONTEXT.md           # domain glossary
├── pyproject.toml       # deps, entry point, ruff/mypy/pytest config
├── uv.lock              # locked dependencies
├── .python-version      # default local Python (3.12)
├── Makefile             # convenience targets
└── .pre-commit-config.yaml
```

## Tooling

| Tool | Purpose | Config |
|---|---|---|
| uv | env + dependency + lockfile management | `pyproject.toml`, `uv.lock` |
| ruff | linting (pycodestyle, pyflakes, isort, bugbear, pylint, pydocstyle…) and formatting | `[tool.ruff]` |
| mypy | strict static typing | `[tool.mypy]` |
| pytest + pytest-cov | tests, 90% coverage floor | `[tool.pytest.ini_options]` |
| pre-commit | runs ruff + mypy before commit | `.pre-commit-config.yaml` |

## Common tasks

```bash
uv add <pkg>             # runtime dependency
uv add --dev <pkg>       # dev dependency
uv lock --upgrade        # refresh lockfile
uv build                 # sdist + wheel into dist/
uv tool install .        # install `jessie` globally
```
