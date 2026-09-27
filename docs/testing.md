# Testing

```bash
uv run pytest                      # full suite + coverage report
uv run pytest -k cli -v            # subset (also: -k batch, -k converter)
uv run pytest --cov-report=html    # browse htmlcov/index.html
```

## Strategy

- **No binary fixtures.** `tests/conftest.py` provides a `make_image` factory that writes solid-colour PNG/JPEG/BMP files into `tmp_path` (optionally in subfolders, in any colour), so tests are hermetic and the repo stays small. It also has `ico_sizes()` and `ico_pixel()` for reading frames back from an icon.
- **Library tests** (`test_converter.py`) cover every supported format, custom sizes, suffix normalisation, overwrite protection, missing/corrupt/truncated/unsupported files, write failures, size validation, and padding, no-padding and upscaling checked on the frames of the written icon.
- **Batch tests** (`test_batch.py`) cover `convert_many`: icon naming, clashes (including the `logo.png` + `logo.jpg` regression), the counter fallback, case-insensitive clashes, invalid sources never causing renames, repeated sources, partial failure (including oversized images) and the empty batch.
- **CLI tests** (`test_cli.py`) call `main(argv)` in-process and assert on exit codes, stdout and logs — including batch mode, usage errors and `python -m jessie`.
- Outputs are verified by re-opening the `.ico` with Pillow and checking the embedded frame sizes.

## Rules

- Coverage must stay **≥ 90%** (enforced by `--cov-fail-under`).
- Every bug fix ships with a regression test.
- Tests go through the public functions only; `_`-prefixed helpers are private. Check padding, upscaling and sizes on the frames of the icon actually written.
