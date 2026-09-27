# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/) and [SemVer](https://semver.org/).

## [Unreleased]

### Added
- `convert_many()` for batches, returning one `ConversionResult` per source.
- `SourceNotFoundError` and `IconWriteError`, so every failure is a `JessieError`.
- `EmptyBatchError`, raised by `convert_many([])`.
- `ConversionResult.repeat` marks entries that name a source image already listed.

### Changed
- When two sources in a batch would produce the same icon, every icon in the clash is renamed after its source (`logo.png.ico`, `logo.jpg.ico`) and a warning is logged.
- Sources listed more than once are converted once.
- Truncated image data raises `UnsupportedFormatError` instead of a raw `OSError`.
- Images too large for Pillow to open safely (`DecompressionBombError`) raise `UnsupportedFormatError` instead of crashing the batch and the CLI.
- Missing or unsupported sources in a batch no longer cause other icons to be renamed.
- Messages and the CLI say "source image" and "icon" (`SOURCE` in `--help`) instead of "input" and "output".
- CI and contributing docs target the `master` branch.
- `prepare_image`, `validate_sizes` and `validate_input` are now private (`_validate_input` is renamed `_validate_source`).

### Fixed
- `jessie logo.png logo.jpg -d out --force` no longer overwrites one icon with the other.

## [0.1.0] - 2026-09-27

### Added
- JPG/JPEG/PNG → ICO conversion with configurable sizes (16–256 px).
- Transparent square padding and automatic upscaling of small sources.
- `jessie` CLI with batch mode, `--output-dir`, `--force`, `--no-pad`.
- uv project, ruff lint/format, mypy strict, pytest with 90% coverage gate, pre-commit, GitHub Actions CI.
