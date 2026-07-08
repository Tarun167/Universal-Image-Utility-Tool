from __future__ import annotations

from pathlib import Path

import pytest

from imgconvert.exceptions import UnsupportedFormatError
from imgconvert.utils import build_output_path, normalize_format, parse_size


def test_parse_size_units() -> None:
    assert parse_size("512") == 512
    assert parse_size("1KB") == 1024
    assert parse_size("1.5MB") == 1_572_864


def test_normalize_format_aliases() -> None:
    assert normalize_format("jpg") == "jpeg"
    assert normalize_format(".tif") == "tiff"
    assert normalize_format("heif") == "heic"


def test_normalize_format_rejects_unknown() -> None:
    with pytest.raises(UnsupportedFormatError):
        normalize_format("raw")


def test_build_output_path_uses_suffix_and_extension(tmp_path: Path) -> None:
    input_path = tmp_path / "photo.jpg"
    output = build_output_path(input_path, "webp", None, tmp_path / "out", "-small")
    assert output == tmp_path / "out" / "photo-small.webp"
