"""High-quality resizing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from PIL import Image, ImageOps

FitMode = Literal["contain", "cover", "stretch"]


@dataclass(frozen=True)
class ResizeOptions:
    """Resize settings for conversion."""

    width: int | None = None
    height: int | None = None
    scale: float | None = None
    fit: FitMode = "contain"


def resize_image(image: Image.Image, options: ResizeOptions) -> Image.Image:
    """Resize an image using Lanczos filtering and the requested fit behavior."""

    if options.scale is not None:
        width = max(1, round(image.width * options.scale))
        height = max(1, round(image.height * options.scale))
        return image.resize((width, height), Image.Resampling.LANCZOS)

    if options.width is None and options.height is None:
        return image

    target_width = options.width or image.width
    target_height = options.height or image.height
    target_size = (target_width, target_height)

    if options.fit == "stretch":
        return image.resize(target_size, Image.Resampling.LANCZOS)
    if options.fit == "cover":
        return ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS)

    result = image.copy()
    result.thumbnail(target_size, Image.Resampling.LANCZOS)
    return result
