from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from jessie.cli import main
from tests.conftest import MakeImage, ico_sizes


def test_single_source(make_image: MakeImage, capsys: pytest.CaptureFixture[str]) -> None:
    src = make_image()
    assert main([str(src)]) == 0
    assert capsys.readouterr().out.strip() == str(src.with_suffix(".ico"))


def test_explicit_icon_path_and_sizes(make_image: MakeImage, tmp_path: Path) -> None:
    icon = tmp_path / "custom.ico"
    assert main([str(make_image()), "-o", str(icon), "-s", "16,32", "--no-pad", "-v"]) == 0
    assert ico_sizes(icon) == {(16, 16), (32, 32)}


def test_batch_output_dir(make_image: MakeImage, tmp_path: Path) -> None:
    a = make_image("a.png")
    b = make_image("b.jpg", mode="RGB", fmt="JPEG")
    icon_dir = tmp_path / "icons"
    assert main([str(a), str(b), "-d", str(icon_dir)]) == 0
    assert {p.name for p in icon_dir.iterdir()} == {"a.ico", "b.ico"}


def test_batch_clash_keeps_both_icons(
    make_image: MakeImage, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Regression: `jessie logo.png logo.jpg -d out --force` kept only the JPG's icon.
    png = make_image("logo.png")
    jpg = make_image("logo.jpg", mode="RGB", fmt="JPEG")
    icon_dir = tmp_path / "out"
    assert main([str(png), str(jpg), "-d", str(icon_dir), "--force", "-s", "16"]) == 0
    assert {p.name for p in icon_dir.iterdir()} == {"logo.png.ico", "logo.jpg.ico"}
    assert len(capsys.readouterr().out.split()) == 2


def test_repeated_source_printed_once(
    make_image: MakeImage, capsys: pytest.CaptureFixture[str]
) -> None:
    src = make_image()
    assert main([str(src), str(src), "-s", "16"]) == 0
    assert capsys.readouterr().out.split() == [str(src.with_suffix(".ico"))]


def test_invalid_size_value_returns_1(
    make_image: MakeImage, caplog: pytest.LogCaptureFixture
) -> None:
    assert main([str(make_image()), "-s", "300"]) == 1
    assert "between 1 and 256" in caplog.text


def test_explicit_icon_path_failure_returns_1(tmp_path: Path) -> None:
    assert main([str(tmp_path / "missing.png"), "-o", str(tmp_path / "x.ico")]) == 1


def test_icon_path_with_many_sources_is_usage_error(make_image: MakeImage, tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        main([str(make_image("a.png")), str(make_image("b.png")), "-o", str(tmp_path / "x.ico")])
    assert exc.value.code == 2


def test_bad_sizes_argument(make_image: MakeImage) -> None:
    with pytest.raises(SystemExit) as exc:
        main([str(make_image()), "-s", "16,abc"])
    assert exc.value.code == 2


def test_failure_returns_1(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    assert main([str(tmp_path / "missing.png")]) == 1
    assert "not found" in caplog.text


def test_existing_icon_then_force(make_image: MakeImage) -> None:
    src = make_image()
    assert main([str(src)]) == 0
    assert main([str(src)]) == 1
    assert main([str(src), "--force"]) == 0


def test_python_dash_m(make_image: MakeImage, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["jessie", str(make_image())])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("jessie", run_name="__main__")
    assert exc.value.code == 0
