from __future__ import annotations

from PIL import Image

from imgconvert.metadata import extract_metadata, metadata_save_options


def test_extract_metadata_can_strip() -> None:
    image = Image.new("RGB", (10, 10), "red")
    image.info["icc_profile"] = b"profile"
    metadata = extract_metadata(image, preserve=False)
    assert metadata.icc_profile is None


def test_metadata_save_options_limits_exif_formats() -> None:
    image = Image.new("RGB", (10, 10), "red")
    image.info["exif"] = b"Exif\x00\x00"
    image.info["icc_profile"] = b"profile"
    metadata = extract_metadata(image, preserve=True)
    assert "exif" in metadata_save_options(metadata, "jpeg")
    assert "exif" not in metadata_save_options(metadata, "png")
    assert "icc_profile" in metadata_save_options(metadata, "png")
