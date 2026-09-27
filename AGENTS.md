# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

**Jessie** converts JPG/JPEG/PNG images into multi-resolution Windows `.ico` files using Pillow.
It ships both a library (`jessie.convert_to_ico` for one image, `jessie.convert_many` for batches) and a CLI (`jessie`, also `python -m jessie`).

- Python `>=3.10` (local default `3.12`, see `.python-version`); CI tests 3.10 and 3.12 on Linux, macOS and Windows.
- Managed with [uv](https://docs.astral.sh/uv/). Always run tools through `uv run`; never `pip install` into the venv.
- Only runtime dependency is `pillow`. Do not add new runtime dependencies without a clear reason.

## Layout

```
src/jessie/
  __init__.py     # public API: convert_to_ico, convert_many, ConversionResult, errors, __version__
  __main__.py     # `python -m jessie` entry point
  cli.py          # argparse + logging; -o -> convert_to_ico, else convert_many; reports results
  converter.py    # pure library logic: batch icon planning, validate, prepare, save
  exceptions.py   # JessieError and its subclasses
tests/
  conftest.py     # `make_image` fixture generates images into tmp_path
  test_batch.py   # convert_many: naming, clashes, repeats, partial failure
  test_cli.py     # calls main(argv) in-process
  test_converter.py  # convert_to_ico: formats, frames, errors
docs/             # architecture, usage, development, testing, contributing, changelog
CONTEXT.md        # domain glossary: source image, icon, frame, batch, clash
```

Keep the split: `converter.py` must not import from `cli.py`, print, or call `sys.exit`.
Every failure the library raises must be a `JessieError` subclass: wrap filesystem and Pillow errors, never let a raw `OSError` escape.
Batch behaviour (where icons go, clashes, repeated sources) belongs in `convert_many`, not the CLI.

## Commands

`make` targets exist but `make` may not be installed (e.g. on Windows), so the `uv` equivalents are listed.

| Task | Command |
|---|---|
| Install | `uv sync` |
| Format | `uv run ruff format .` then `uv run ruff check --fix .` |
| Lint | `uv run ruff check .` |
| Type-check | `uv run mypy src` |
| Test | `uv run pytest` |
| Build | `uv build` (outputs to `dist/`) |
| Full CI check | `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy src`, `uv run pytest` |

Run the full CI check before calling a change done.

## Conventions

- **Style:** ruff, line length 100, double quotes. Lint rules include pydocstyle (`D`), so every public module, class and function in `src/` needs a docstring (Google style, as in `converter.py`). Tests are exempt from `D`.
- **Typing:** mypy `strict` on `src/`. Annotate everything; use `from __future__ import annotations`, and import abstract types from `collections.abc`.
- **Logging:** use module loggers (`logging.getLogger(__name__)`), not `print`, in library code. The one exception is `cli.py`, which configures the package logger `"jessie"` so `--verbose` reaches every module.
- **Paths:** accept `str | Path` at public boundaries and convert to `Path` internally.

## Testing

- Coverage gate is **90%** (`--cov-fail-under=90`) and currently sits at 100%. Don't lower it.
- **Test through the public functions** (`convert_to_ico`, `convert_many`, `cli.main`). Helpers prefixed `_` are private; don't import them in tests.
- **No binary fixtures.** Generate images with the `make_image` fixture into `tmp_path`; read frames back with `ico_sizes()` / `ico_pixel()` from `conftest.py`. `.ico` files are gitignored.
- Verify outputs by re-opening the `.ico` with Pillow and checking the embedded frame sizes.
- CLI tests call `jessie.cli.main(argv)` in-process and assert on exit codes, output and logs.
- Every bug fix needs a regression test.

## Changes and commits

- Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat: ...`, `fix: ...`, `docs: ...`).
- When behaviour changes, update the relevant page in `docs/` and add an entry to `docs/changelog.md` (Keep a Changelog format).
- Pre-commit hooks (`.pre-commit-config.yaml`) run ruff and mypy. Don't bypass them with `--no-verify`.
