from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from jessie import (
    EmptyBatchError,
    InvalidSizeError,
    OutputExistsError,
    SourceNotFoundError,
    UnsupportedFormatError,
    convert_many,
)
from tests.conftest import BLUE, MakeImage, ico_pixel, ico_sizes


def make_jpg(make_image: MakeImage, name: str, **kwargs: object) -> Path:
    return make_image(name, mode="RGB", fmt="JPEG", **kwargs)


def test_distinct_names_keep_plain_icons(make_image: MakeImage, tmp_path: Path) -> None:
    a, b = make_image("a.png"), make_jpg(make_image, "b.jpg")
    icon_dir = tmp_path / "icons"
    results = convert_many([a, b], icon_dir, sizes=[16])
    assert [r.icon for r in results] == [icon_dir / "a.ico", icon_dir / "b.ico"]
    assert all(ico_sizes(icon_dir / name) == {(16, 16)} for name in ("a.ico", "b.ico"))
    assert not any(r.renamed or r.repeat for r in results)


def test_clash_renames_every_member_and_keeps_both(
    make_image: MakeImage, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # Regression: logo.jpg used to silently overwrite logo.png's icon with overwrite=True.
    png = make_image("logo.png")
    jpg = make_jpg(make_image, "logo.jpg", color=BLUE)
    banner = make_image("banner.png")
    icon_dir = tmp_path / "icons"

    results = convert_many([png, jpg, banner], icon_dir, sizes=[16], overwrite=True)

    assert [(r.icon, r.renamed) for r in results] == [
        (icon_dir / "logo.png.ico", True),
        (icon_dir / "logo.jpg.ico", True),
        (icon_dir / "banner.ico", False),
    ]
    assert ico_pixel(icon_dir / "logo.png.ico", (0, 0))[0] > 150  # red survived
    assert ico_pixel(icon_dir / "logo.jpg.ico", (0, 0))[2] > 150  # blue survived
    assert "all map to" in caplog.text


def test_clash_without_output_dir(make_image: MakeImage, tmp_path: Path) -> None:
    png = make_image("logo.png")
    jpg = make_jpg(make_image, "logo.jpg")
    results = convert_many([jpg, png], sizes=[16])
    assert [r.icon for r in results] == [tmp_path / "logo.jpg.ico", tmp_path / "logo.png.ico"]


def test_same_name_from_different_folders_gets_counter(
    make_image: MakeImage, tmp_path: Path
) -> None:
    first = make_image("a/logo.png")
    second = make_image("b/logo.png")
    icon_dir = tmp_path / "icons"
    results = convert_many([first, second], icon_dir, sizes=[16])
    assert [r.icon for r in results] == [icon_dir / "logo.png.ico", icon_dir / "logo.png-2.ico"]


def test_rename_avoids_other_plain_icons(make_image: MakeImage, tmp_path: Path) -> None:
    # "logo.png.png" already claims logo.png.ico, so the renamed logo.png takes a counter.
    taken = make_image("logo.png.png")
    png = make_image("logo.png")
    jpg = make_jpg(make_image, "logo.jpg")
    results = convert_many([taken, png, jpg], sizes=[16])
    assert [r.icon for r in results] == [
        tmp_path / "logo.png.ico",
        tmp_path / "logo.png-2.ico",
        tmp_path / "logo.jpg.ico",
    ]


def test_names_differing_only_in_case_clash(make_image: MakeImage, tmp_path: Path) -> None:
    upper = make_image("Logo.png")
    lower = make_jpg(make_image, "logo.jpg")
    results = convert_many([upper, lower], tmp_path / "icons", sizes=[16])
    assert all(r.renamed for r in results)
    assert [r.icon.name for r in results if r.icon] == ["Logo.png.ico", "logo.jpg.ico"]


def test_invalid_sources_never_cause_a_rename(make_image: MakeImage, tmp_path: Path) -> None:
    png = make_image("logo.png")
    missing = tmp_path / "logo.jpg"
    unsupported = make_image("logo.bmp", fmt="BMP")
    results = convert_many([png, missing, unsupported], sizes=[16])
    assert results[0].icon == tmp_path / "logo.ico"
    assert isinstance(results[1].error, SourceNotFoundError)
    assert isinstance(results[2].error, UnsupportedFormatError)
    assert not any(r.renamed for r in results)


def test_repeated_source_is_converted_once(
    make_image: MakeImage, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = make_image("logo.png")
    monkeypatch.chdir(tmp_path)
    entries = [src, Path("logo.png"), src]
    results = convert_many(entries, sizes=[16])
    assert [r.source for r in results] == entries
    assert [r.repeat for r in results] == [False, True, True]
    assert {r.icon for r in results} == {tmp_path / "logo.ico"}
    assert all(r.ok and not r.renamed for r in results)


def test_failures_do_not_stop_the_batch(
    make_image: MakeImage, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    good = make_image("good.png", size=(20, 20))
    missing = tmp_path / "missing.png"
    existing = make_image("existing.png", size=(20, 20))
    existing.with_suffix(".ico").write_bytes(b"old")
    huge = make_image("huge.png")  # 300x300 > 2 * MAX_IMAGE_PIXELS below
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1000)

    results = convert_many([missing, good, existing, huge], sizes=[16])

    assert [r.ok for r in results] == [False, True, False, False]
    assert isinstance(results[0].error, SourceNotFoundError)
    assert results[0].icon is None
    assert isinstance(results[2].error, OutputExistsError)
    assert isinstance(results[3].error, UnsupportedFormatError)


def test_invalid_sizes_raise_before_any_work(make_image: MakeImage) -> None:
    src = make_image()
    with pytest.raises(InvalidSizeError):
        convert_many([src], sizes=[300])
    assert not src.with_suffix(".ico").exists()


def test_empty_batch_raises() -> None:
    with pytest.raises(EmptyBatchError):
        convert_many([])
