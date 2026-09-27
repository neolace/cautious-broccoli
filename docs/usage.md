# Usage

## CLI

```
jessie [-h] [-o OUTPUT | -d OUTPUT_DIR] [-s SIZES] [--no-pad] [-f] [-v] [-V] SOURCE [SOURCE ...]
```

| Option | Description | Default |
|---|---|---|
| `SOURCE` | One or more source images: `.jpg`, `.jpeg`, `.png` (case-insensitive) | — |
| `-o, --output` | Icon path. Single source image only. Suffix is forced to `.ico`. | `<source>.ico` |
| `-d, --output-dir` | Directory for the icons (created if missing) | next to each source |
| `-s, --sizes` | Comma-separated square sizes, 1–256 | `16,24,32,48,64,128,256` |
| `--no-pad` | Don't pad non-square images; frames keep the source aspect ratio (200×100 → 64×32) | padding on |
| `-f, --force` | Overwrite existing icons | off |
| `-v, --verbose` | Debug logging | off |
| `-V, --version` | Print version | — |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Every source image converted |
| 1 | One or more source images failed (the others are still converted), or a size outside 1–256 |
| 2 | Invalid command-line usage, e.g. `-o` with several source images or a non-numeric `-s` |

### Batch naming

Each icon is named after its source image (`logo.png` → `logo.ico`). If two sources in one run would produce the same icon, for example `logo.png` and `logo.jpg`, or `a/logo.png` and `b/logo.png` with `-d`, every icon in the clash is named after its full source name instead, and a warning is logged:

| Sources | Icons |
|---|---|
| `logo.png logo.jpg banner.png` | `logo.png.ico`, `logo.jpg.ico`, `banner.ico` |
| `a/logo.png b/logo.png -d out` | `out/logo.png.ico`, `out/logo.png-2.ico` |

- If a renamed icon would take a name another icon in the run already uses, a counter is added (`logo.png-2.ico`).
- Missing or unsupported sources fail on their own; they never cause another icon to be renamed.
- Names that differ only in case (`Logo.png`, `logo.jpg`) count as a clash on every platform.
- A source listed more than once is converted once and printed once.
- `--force` only replaces icons left over from earlier runs; it never lets one source overwrite another in the same run.

### Examples

```bash
uv run jessie favicon.png -s 16,32,48 -o public/favicon.ico
uv run jessie assets/*.png -d dist/icons --force
```

## Library API

### One image

```python
from jessie import convert_to_ico, JessieError

try:
    path = convert_to_ico("logo.jpg", sizes=[32, 256], pad=True, overwrite=False)
except JessieError as err:
    print(f"Conversion failed: {err}")
```

`convert_to_ico(input_path, output_path=None, *, sizes=DEFAULT_SIZES, pad=True, overwrite=False) -> Path`

### A batch

```python
from jessie import convert_many

for result in convert_many(["logo.png", "logo.jpg"], "build/icons"):
    if result.ok:
        print(result.icon, "(renamed)" if result.renamed else "")
    else:
        print(f"{result.source}: {result.error}")
```

`convert_many(sources, output_dir=None, *, sizes=DEFAULT_SIZES, pad=True, overwrite=False) -> list[ConversionResult]`

Returns one `ConversionResult(source, icon, error, renamed, repeat)` per entry in `sources`, in the same order, with an `ok` property. A failing source never stops the batch: its result carries the error. `repeat` is `True` when an earlier entry already named the same source image; its result is a copy, so skip it when reporting per source. Icon names follow the [batch naming](#batch-naming) rules. Only invalid `sizes` (`InvalidSizeError`) or an empty `sources` (`EmptyBatchError`) raise, before anything is converted.

### Errors

Every failure is a `JessieError`:

| Error | When | Also a |
|---|---|---|
| `SourceNotFoundError` | Source image doesn't exist | `FileNotFoundError` |
| `UnsupportedFormatError` | Wrong extension, unreadable/truncated image data, or an image too large for Pillow to open safely | |
| `InvalidSizeError` | A size outside 1–256, or no sizes | |
| `OutputExistsError` | Icon exists and `overwrite` is off | |
| `IconWriteError` | Icon folder or icon can't be written | `OSError` |
| `EmptyBatchError` | `convert_many` was given no sources | `ValueError` |
