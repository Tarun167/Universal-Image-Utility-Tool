"""Metadata extraction and save-option helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PIL import Image


@dataclass(frozen=True)
class ImageMetadata:
    """Metadata that can be safely passed back to Pillow on save."""

    exif: bytes | None = None
    icc_profile: bytes | None = None


def extract_metadata(image: Image.Image, preserve: bool) -> ImageMetadata:
    """Extract EXIF and ICC profile data from a Pillow image."""

    if not preserve:
        return ImageMetadata()
    exif = image.info.get("exif")
    icc_profile = image.info.get("icc_profile")
    return ImageMetadata(
        exif=exif if isinstance(exif, bytes) else None,
        icc_profile=icc_profile if isinstance(icc_profile, bytes) else None,
    )


def metadata_save_options(metadata: ImageMetadata, output_format: str) -> dict[str, Any]:
    """Return Pillow save options for metadata supported by the output format."""

    options: dict[str, Any] = {}
    if metadata.icc_profile:
        options["icc_profile"] = metadata.icc_profile
    if metadata.exif and output_format in {"jpeg", "tiff", "webp"}:
        options["exif"] = metadata.exif
    return options
