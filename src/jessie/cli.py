"""Command-line interface for Jessie."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from jessie import __version__
from jessie.converter import DEFAULT_SIZES, convert_many, convert_to_ico
from jessie.exceptions import JessieError

# The package logger, not ``__name__``: --verbose must also reach ``jessie.converter``.
logger = logging.getLogger("jessie")


def parse_sizes(value: str) -> list[int]:
    """Parse a comma-separated list like ``16,32,48`` into ints."""
    try:
        return [int(part) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid sizes '{value}'; expected e.g. 16,32,48"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="jessie",
        description="Convert JPG, JPEG or PNG images into multi-resolution .ico files.",
    )
    parser.add_argument(
        "sources", nargs="+", type=Path, metavar="SOURCE", help="Source image(s) to convert."
    )
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument(
        "-o", "--output", type=Path, help="Icon path (single source image only)."
    )
    destination.add_argument("-d", "--output-dir", type=Path, help="Directory for the icons.")
    parser.add_argument(
        "-s",
        "--sizes",
        type=parse_sizes,
        default=list(DEFAULT_SIZES),
        help=f"Comma-separated sizes (default: {','.join(map(str, DEFAULT_SIZES))}).",
    )
    parser.add_argument(
        "--no-pad", action="store_true", help="Keep aspect ratio instead of padding."
    )
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing icons.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging.")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``jessie`` command.

    Prints the path of each icon written and logs each failure.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        Exit code: 0 if every source image converted, 1 if any failed.
        Invalid usage exits with code 2 via ``argparse``.

    """
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(format="%(levelname)s: %(message)s", stream=sys.stderr)
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    if args.output and len(args.sources) > 1:
        parser.error("--output needs a single source image; use --output-dir instead.")

    sizes, pad, overwrite = args.sizes, not args.no_pad, args.force
    try:
        if args.output:
            print(
                convert_to_ico(
                    args.sources[0], args.output, sizes=sizes, pad=pad, overwrite=overwrite
                )
            )
            return 0
        results = convert_many(
            args.sources, args.output_dir, sizes=sizes, pad=pad, overwrite=overwrite
        )
    except JessieError as exc:
        logger.error("%s", exc)
        return 1

    for result in results:
        if result.repeat:
            continue
        if result.ok:
            print(result.icon)
        else:
            logger.error("%s", result.error)

    return 0 if all(result.ok for result in results) else 1
