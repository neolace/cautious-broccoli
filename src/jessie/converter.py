"""Core image-to-ICO conversion logic (pure library, no CLI concerns)."""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from PIL import Image

from jessie.exceptions import (
    EmptyBatchError,
    IconWriteError,
    InvalidSizeError,
    JessieError,
    OutputExistsError,
    SourceNotFoundError,
    UnsupportedFormatError,
)

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png"})
DEFAULT_SIZES: tuple[int, ...] = (16, 24, 32, 48, 64, 128, 256)
MAX_ICO_SIZE = 256


@dataclass(frozen=True)
class ConversionResult:
    """Outcome of converting one source image in a batch.

    Attributes:
        source: The source image, as passed to :func:`convert_many`.
        icon: Path of the written icon, or ``None`` if conversion failed.
        error: Why conversion failed, or ``None`` on success.
        renamed: ``True`` if the icon was named after its full source name to avoid a clash.
        repeat: ``True`` if an earlier entry already named this source image; the result
            is a copy of that entry's, so callers reporting per source can skip it.

    """

    source: Path
    icon: Path | None = None
    error: JessieError | None = None
    renamed: bool = False
    repeat: bool = False

    @property
    def ok(self) -> bool:
        """Whether the icon was written."""
        return self.error is None


class _PlannedIcon(NamedTuple):
    """Where a source image's icon will be written, and whether it was renamed."""

    icon: Path
    renamed: bool


def _validate_sizes(sizes: Iterable[int]) -> tuple[int, ...]:
    """Return sorted, de-duplicated sizes, raising if any are out of range."""
    unique = sorted(set(sizes))
    if not unique:
        raise InvalidSizeError("At least one icon size is required.")
    bad = [s for s in unique if not 1 <= s <= MAX_ICO_SIZE]
    if bad:
        raise InvalidSizeError(f"Icon sizes must be between 1 and {MAX_ICO_SIZE}, got {bad}.")
    return tuple(unique)


def _validate_source(path: Path) -> None:
    """Ensure the source image at *path* exists and has a supported extension."""
    if not path.is_file():
        raise SourceNotFoundError(f"Source image not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedFormatError(
            f"Unsupported file type '{path.suffix}'. Use one of: {allowed}"
        )


def _prepare_image(image: Image.Image, target: int, *, pad: bool = True) -> Image.Image:
    """Convert to RGBA, optionally pad to a centred square, and upscale to *target* if needed."""
    rgba = image.convert("RGBA")
    if pad and rgba.width != rgba.height:
        side = max(rgba.size)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(rgba, ((side - rgba.width) // 2, (side - rgba.height) // 2))
        rgba = canvas
    if min(rgba.size) < target:
        logger.warning("Source is %sx%s; upscaling to %spx.", *rgba.size, target)
        scale = target / min(rgba.size)
        new_size = (round(rgba.width * scale), round(rgba.height * scale))
        rgba = rgba.resize(new_size, Image.Resampling.LANCZOS)
    return rgba


def convert_to_ico(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    sizes: Sequence[int] = DEFAULT_SIZES,
    pad: bool = True,
    overwrite: bool = False,
) -> Path:
    """Convert a JPG/JPEG/PNG source image to a multi-resolution icon.

    Args:
        input_path: Source image.
        output_path: Icon path; defaults to the source image path with an ``.ico`` suffix.
        sizes: Square frame sizes to embed (1-256).
        pad: Pad non-square images with transparency instead of keeping their aspect ratio.
        overwrite: Replace an existing icon.

    Returns:
        The path of the written icon.

    Raises:
        JessieError: Every failure is a subclass: :class:`SourceNotFoundError`,
            :class:`UnsupportedFormatError`, :class:`InvalidSizeError`,
            :class:`OutputExistsError` or :class:`IconWriteError`.

    """
    src = Path(input_path)
    _validate_source(src)
    valid_sizes = _validate_sizes(sizes)

    icon = Path(output_path) if output_path else src.with_suffix(".ico")
    if icon.suffix.lower() != ".ico":
        icon = icon.with_suffix(".ico")
    if icon.exists() and not overwrite:
        raise OutputExistsError(f"Icon already exists: {icon} (use overwrite=True / --force)")

    try:
        with Image.open(src) as img:
            prepared = _prepare_image(img, max(valid_sizes), pad=pad)
    except (OSError, Image.DecompressionBombError) as exc:
        # OSError covers unidentified and truncated data; DecompressionBombError is not one.
        raise UnsupportedFormatError(f"Could not read image data from {src}: {exc}") from exc

    try:
        icon.parent.mkdir(parents=True, exist_ok=True)
        prepared.save(icon, format="ICO", sizes=[(s, s) for s in valid_sizes])
    except OSError as exc:
        raise IconWriteError(f"Could not write {icon}: {exc}") from exc
    logger.info("Wrote %s (%s)", icon, ", ".join(f"{s}px" for s in valid_sizes))
    return icon


def _clash_key(path: Path) -> str:
    """Case-insensitive identity of an icon path, so clashes are the same on every platform."""
    return str(path.resolve()).casefold()


def _plan_icons(sources: Sequence[Path], icon_dir: Path | None) -> list[_PlannedIcon]:
    """Choose an icon path for each distinct, valid source image, renaming any that clash.

    Sources whose default icons clash are all renamed to ``<source name>.ico``
    (``logo.png.ico``). If that name is already taken, by another renamed icon or by a
    source's plain icon, a counter is appended in input order (``logo.png-2.ico``).
    Returns one plan per source, in the order of *sources*.
    """
    defaults = [(icon_dir or src.parent) / f"{src.stem}.ico" for src in sources]
    groups: dict[str, list[int]] = {}
    for i, icon in enumerate(defaults):
        groups.setdefault(_clash_key(icon), []).append(i)

    plan: dict[int, _PlannedIcon] = {}
    taken: set[str] = set()
    for key, members in groups.items():
        if len(members) == 1:
            plan[members[0]] = _PlannedIcon(defaults[members[0]], renamed=False)
            taken.add(key)

    for members in (m for m in groups.values() if len(m) > 1):
        renamed: list[Path] = []
        for i in members:
            parent, name = defaults[i].parent, sources[i].name
            icon, counter = parent / f"{name}.ico", 2
            while _clash_key(icon) in taken:
                icon, counter = parent / f"{name}-{counter}.ico", counter + 1
            taken.add(_clash_key(icon))
            plan[i] = _PlannedIcon(icon, renamed=True)
            renamed.append(icon)
        logger.warning(
            "%s all map to %s; writing %s",
            ", ".join(str(sources[i]) for i in members),
            defaults[members[0]],
            ", ".join(map(str, renamed)),
        )

    return [plan[i] for i in range(len(sources))]


def convert_many(
    sources: Iterable[str | Path],
    output_dir: str | Path | None = None,
    *,
    sizes: Sequence[int] = DEFAULT_SIZES,
    pad: bool = True,
    overwrite: bool = False,
) -> list[ConversionResult]:
    """Convert a batch of source images, one icon each.

    Icons go into *output_dir*, or next to each source image when it is ``None``. When
    two source images would produce the same icon (``logo.png`` and ``logo.jpg``), both
    are renamed after their source (``logo.png.ico``, ``logo.jpg.ico``) and a warning is
    logged. Missing or unsupported sources fail on their own and never cause a rename.
    Sources listed more than once are converted once.

    Args:
        sources: Source images.
        output_dir: Directory for the icons; created if missing.
        sizes: Square frame sizes to embed (1-256).
        pad: Pad non-square images with transparency instead of keeping their aspect ratio.
        overwrite: Replace icons that already exist on disk.

    Returns:
        One result per entry in *sources*, in the same order. A failing source never
        stops the batch; its result carries the error instead.

    Raises:
        InvalidSizeError: If *sizes* is invalid, before anything is converted.
        EmptyBatchError: If *sources* is empty.

    """
    valid_sizes = _validate_sizes(sizes)
    entries = [Path(s) for s in sources]
    if not entries:
        raise EmptyBatchError("At least one source image is required.")
    icon_dir = Path(output_dir) if output_dir is not None else None

    first_entry: dict[Path, Path] = {}  # resolved source -> first entry naming it
    for entry in entries:
        first_entry.setdefault(entry.resolve(), entry)

    results: dict[Path, ConversionResult] = {}
    convertible: list[Path] = []
    for src in first_entry.values():
        try:
            _validate_source(src)
            convertible.append(src)
        except JessieError as exc:
            results[src.resolve()] = ConversionResult(src, error=exc)

    for src, planned in zip(convertible, _plan_icons(convertible, icon_dir), strict=True):
        try:
            written = convert_to_ico(
                src, planned.icon, sizes=valid_sizes, pad=pad, overwrite=overwrite
            )
            result = ConversionResult(src, icon=written, renamed=planned.renamed)
        except JessieError as exc:
            result = ConversionResult(src, error=exc, renamed=planned.renamed)
        results[src.resolve()] = result

    batch: list[ConversionResult] = []
    seen: set[Path] = set()
    for entry in entries:
        key = entry.resolve()
        batch.append(dataclasses.replace(results[key], source=entry, repeat=key in seen))
        seen.add(key)
    return batch
