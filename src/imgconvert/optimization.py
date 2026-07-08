"""Output optimization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from PIL import Image

from imgconvert.exceptions import OptimizationError
from imgconvert.utils import format_is_lossy, pillow_format


@dataclass(frozen=True)
class OptimizationResult:
    """Bytes produced by an optimization run."""

    data: bytes
    quality: int | None
    size: int


def base_save_options(output_format: str, quality: int | None = None) -> dict[str, Any]:
    """Build sensible Pillow save options for a format."""

    options: dict[str, Any] = {}
    if output_format in {"jpeg", "webp", "avif", "heic"} and quality is not None:
        options["quality"] = quality
    if output_format == "jpeg":
        options.update(optimize=True, progressive=True)
    elif output_format == "png":
        options.update(optimize=True, compress_level=9)
    elif output_format == "webp":
        options.update(method=6)
    elif output_format == "tiff":
        options.update(compression="tiff_deflate")
    return options


def save_to_bytes(
    image: Image.Image,
    output_format: str,
    save_options: dict[str, Any],
    quality: int | None = None,
) -> bytes:
    """Save an image to bytes using Pillow."""

    buffer = BytesIO()
    options = base_save_options(output_format, quality)
    options.update(save_options)
    image.save(buffer, format=pillow_format(output_format), **options)
    return buffer.getvalue()


def optimize_to_size(
    image: Image.Image,
    output_format: str,
    max_size: int | None,
    quality: int,
    save_options: dict[str, Any],
) -> OptimizationResult:
    """Save an image, binary-searching quality when a maximum size is requested."""

    if max_size is None:
        data = save_to_bytes(image, output_format, save_options, quality)
        return OptimizationResult(data=data, quality=quality, size=len(data))

    if not format_is_lossy(output_format):
        data = save_to_bytes(image, output_format, save_options, None)
        if len(data) > max_size:
            raise OptimizationError(
                f"{output_format.upper()} output is {len(data)} bytes, above target {max_size}"
            )
        return OptimizationResult(data=data, quality=None, size=len(data))

    low = 1
    high = max(1, min(quality, 100))
    best: OptimizationResult | None = None
    while low <= high:
        mid = (low + high) // 2
        data = save_to_bytes(image, output_format, save_options, mid)
        size = len(data)
        if size <= max_size:
            best = OptimizationResult(data=data, quality=mid, size=size)
            low = mid + 1
        else:
            high = mid - 1

    if best is None:
        raise OptimizationError(f"Could not reach target size {max_size} bytes")
    return best
