"""Shared fixtures: generate sample images on the fly (no binary fixtures in git)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image

MakeImage = Callable[..., Path]

RED = (200, 30, 60)
BLUE = (30, 60, 200)


@pytest.fixture
def make_image(tmp_path: Path) -> MakeImage:
    """Return a factory that writes a solid-colour source image under tmp_path.

    *name* may include folders (``"a/logo.png"``); they are created as needed.
    """

    def _make(
        name: str = "sample.png",
        size: tuple[int, int] = (300, 300),
        mode: str = "RGBA",
        fmt: str | None = None,
        color: tuple[int, int, int] = RED,
    ) -> Path:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        fill = (*color, 255) if mode == "RGBA" else color
        Image.new(mode, size, fill).save(path, format=fmt)
        return path

    return _make


def ico_sizes(icon: Path) -> set[tuple[int, int]]:
    """Frame sizes embedded in *icon*."""
    with Image.open(icon) as ico:
        return set(ico.info["sizes"])


def ico_pixel(icon: Path, xy: tuple[int, int]) -> tuple[int, ...]:
    """RGBA pixel at *xy* in the largest frame of *icon*."""
    with Image.open(icon) as ico:
        pixel = ico.convert("RGBA").getpixel(xy)
    assert isinstance(pixel, tuple)
    return pixel
