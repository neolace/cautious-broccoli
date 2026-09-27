from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from jessie import (
    DEFAULT_SIZES,
    IconWriteError,
    InvalidSizeError,
    JessieError,
    OutputExistsError,
    SourceNotFoundError,
    UnsupportedFormatError,
    convert_to_ico,
)
from tests.conftest import MakeImage, ico_pixel, ico_sizes

ALL_FRAMES = {(s, s) for s in DEFAULT_SIZES}


@pytest.mark.parametrize(
    ("name", "mode", "fmt"),
    [("a.png", "RGBA", "PNG"), ("b.jpg", "RGB", "JPEG"), ("c.jpeg", "RGB", "JPEG")],
)
def test_converts_supported_formats(make_image: MakeImage, name: str, mode: str, fmt: str) -> None:
    src = make_image(name, mode=mode, fmt=fmt)
    icon = convert_to_ico(src)
    assert icon == src.with_suffix(".ico")
    assert ico_sizes(icon) == ALL_FRAMES


def test_uppercase_extension(make_image: MakeImage) -> None:
    src = make_image("UP.PNG", fmt="PNG")
    assert ico_sizes(convert_to_ico(src)) == ALL_FRAMES


def test_custom_sizes_and_icon_path(make_image: MakeImage, tmp_path: Path) -> None:
    icon = convert_to_ico(make_image(), tmp_path / "nested" / "icon.ico", sizes=[32, 16, 32])
    assert ico_sizes(icon) == {(16, 16), (32, 32)}


def test_icon_suffix_forced_to_ico(make_image: MakeImage, tmp_path: Path) -> None:
    icon = convert_to_ico(make_image(), tmp_path / "icon.png", sizes=[16])
    assert icon.suffix == ".ico"
    assert ico_sizes(icon) == {(16, 16)}


def test_refuses_overwrite(make_image: MakeImage) -> None:
    src = make_image()
    convert_to_ico(src)
    with pytest.raises(OutputExistsError):
        convert_to_ico(src)
    assert convert_to_ico(src, overwrite=True).exists()


def test_missing_source(tmp_path: Path) -> None:
    with pytest.raises(SourceNotFoundError) as exc:
        convert_to_ico(tmp_path / "nope.png")
    assert isinstance(exc.value, FileNotFoundError)  # still caught by existing handlers


def test_unsupported_extension(make_image: MakeImage) -> None:
    src = make_image("x.bmp", fmt="BMP")
    with pytest.raises(UnsupportedFormatError):
        convert_to_ico(src)


def test_corrupt_image(tmp_path: Path) -> None:
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    with pytest.raises(UnsupportedFormatError):
        convert_to_ico(bad)


def test_truncated_image(make_image: MakeImage) -> None:
    src = make_image()
    data = src.read_bytes()
    src.write_bytes(data[: len(data) // 2])
    with pytest.raises(UnsupportedFormatError):
        convert_to_ico(src)


def test_oversized_image(make_image: MakeImage, monkeypatch: pytest.MonkeyPatch) -> None:
    # Pillow raises DecompressionBombError (not an OSError) above 2x MAX_IMAGE_PIXELS.
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1000)
    with pytest.raises(UnsupportedFormatError):
        convert_to_ico(make_image())


def test_write_failure(make_image: MakeImage, tmp_path: Path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where a directory is needed")
    with pytest.raises(IconWriteError) as exc:
        convert_to_ico(make_image(), blocker / "icon.ico")
    assert isinstance(exc.value, OSError)
    assert isinstance(exc.value, JessieError)


@pytest.mark.parametrize("sizes", [[], [0], [512], [16, 300]])
def test_invalid_sizes(make_image: MakeImage, sizes: list[int]) -> None:
    with pytest.raises(InvalidSizeError):
        convert_to_ico(make_image(), sizes=sizes)


def test_pad_makes_square_frames_with_transparent_bands(make_image: MakeImage) -> None:
    src = make_image("wide.png", size=(200, 100))
    icon = convert_to_ico(src, sizes=[64])
    assert ico_sizes(icon) == {(64, 64)}
    assert ico_pixel(icon, (0, 0))[3] == 0  # padding band
    assert ico_pixel(icon, (32, 32))[3] == 255  # image


def test_no_pad_keeps_aspect(make_image: MakeImage) -> None:
    src = make_image("wide.png", size=(200, 100))
    icon = convert_to_ico(src, sizes=[64], pad=False)
    assert ico_sizes(icon) == {(64, 32)}
    assert ico_pixel(icon, (0, 0))[3] == 255


def test_small_image_is_upscaled(make_image: MakeImage, caplog: pytest.LogCaptureFixture) -> None:
    icon = convert_to_ico(make_image("tiny.png", size=(20, 20)))
    assert ico_sizes(icon) == ALL_FRAMES
    assert "upscaling" in caplog.text
