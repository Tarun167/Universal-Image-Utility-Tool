"""Single-image conversion pipeline."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from imgconvert.exceptions import ConversionError, UnsupportedFormatError
from imgconvert.metadata import extract_metadata, metadata_save_options
from imgconvert.optimization import OptimizationResult, optimize_to_size
from imgconvert.resizing import ResizeOptions, resize_image
from imgconvert.utils import (
    ensure_parent,
    format_supports_alpha,
    imagemagick_binary,
    normalize_format,
    register_optional_plugins,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConversionOptions:
    """Options for converting a single image."""

    output_format: str
    output_path: Path
    resize: ResizeOptions = ResizeOptions()
    quality: int = 90
    max_size: int | None = None
    preserve_metadata: bool = True
    strip_metadata: bool = False
    background: str = "#ffffff"
    overwrite: bool = False
    use_imagemagick: bool = True


@dataclass(frozen=True)
class ConversionResult:
    """Successful conversion result."""

    input_path: Path
    output_path: Path
    output_format: str
    size: int
    quality: int | None
    backend: str


def convert_image(input_path: Path, options: ConversionOptions) -> ConversionResult:
    """Convert one image using Pillow, falling back to ImageMagick when necessary."""

    output_format = normalize_format(options.output_format)
    if options.output_path.exists() and not options.overwrite:
        raise ConversionError(f"Output already exists: {options.output_path}")
    ensure_parent(options.output_path)

    try:
        result = _convert_with_pillow(input_path, options, output_format)
    except (UnidentifiedImageError, OSError, UnsupportedFormatError) as exc:
        if not options.use_imagemagick:
            raise ConversionError(str(exc)) from exc
        LOGGER.debug("Pillow conversion failed, trying ImageMagick", exc_info=exc)
        result = _convert_with_imagemagick(input_path, options, output_format)

    LOGGER.info(
        "converted image",
        extra={
            "input": str(result.input_path),
            "output": str(result.output_path),
            "format": result.output_format,
            "size": result.size,
            "quality": result.quality,
            "backend": result.backend,
        },
    )
    return result


def _convert_with_pillow(
    input_path: Path, options: ConversionOptions, output_format: str
) -> ConversionResult:
    register_optional_plugins()
    preserve_metadata = options.preserve_metadata and not options.strip_metadata
    with Image.open(input_path) as source:
        image = ImageOps.exif_transpose(source)
        metadata = extract_metadata(source, preserve_metadata)
        image = resize_image(image, options.resize)
        image = _prepare_for_output(image, output_format, options.background)
        save_options = metadata_save_options(metadata, output_format)
        optimized = optimize_to_size(
            image=image,
            output_format=output_format,
            max_size=options.max_size,
            quality=options.quality,
            save_options=save_options,
        )
    options.output_path.write_bytes(optimized.data)
    return _result(input_path, options.output_path, output_format, optimized, "pillow")


def _prepare_for_output(image: Image.Image, output_format: str, background: str) -> Image.Image:
    if image.mode in {"P", "LA"}:
        image = image.convert("RGBA")

    has_alpha = image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    )
    if has_alpha and not format_supports_alpha(output_format):
        canvas = Image.new("RGBA", image.size, background)
        canvas.alpha_composite(image.convert("RGBA"))
        return canvas.convert("RGB")

    if output_format in {"jpeg", "ppm"} and image.mode != "RGB":
        return image.convert("RGB")
    return image


def _convert_with_imagemagick(
    input_path: Path, options: ConversionOptions, output_format: str
) -> ConversionResult:
    binary = imagemagick_binary()
    if binary is None:
        raise ConversionError("Pillow failed and ImageMagick is not installed")

    command = _imagemagick_command(binary, input_path, options, output_format)
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise ConversionError(f"ImageMagick failed for {input_path}: {stderr}")
    size = options.output_path.stat().st_size
    return ConversionResult(
        input_path=input_path,
        output_path=options.output_path,
        output_format=output_format,
        size=size,
        quality=options.quality,
        backend="imagemagick",
    )


def _imagemagick_command(
    binary: str, input_path: Path, options: ConversionOptions, output_format: str
) -> list[str]:
    command = [binary, str(input_path), "-auto-orient"]
    if options.resize.scale is not None:
        percent = max(1, round(options.resize.scale * 100))
        command.extend(["-resize", f"{percent}%"])
    elif options.resize.width or options.resize.height:
        width = "" if options.resize.width is None else str(options.resize.width)
        height = "" if options.resize.height is None else str(options.resize.height)
        modifier = "!" if options.resize.fit == "stretch" else "^" if options.resize.fit == "cover" else ""
        command.extend(["-resize", f"{width}x{height}{modifier}"])
    if not format_supports_alpha(output_format):
        command.extend(["-background", options.background, "-alpha", "remove", "-alpha", "off"])
    if options.strip_metadata:
        command.append("-strip")
    if output_format in {"jpeg", "webp", "avif", "heic"}:
        command.extend(["-quality", str(options.quality)])
    command.append(str(options.output_path))
    return command


def _result(
    input_path: Path,
    output_path: Path,
    output_format: str,
    optimized: OptimizationResult,
    backend: str,
) -> ConversionResult:
    return ConversionResult(
        input_path=input_path,
        output_path=output_path,
        output_format=output_format,
        size=optimized.size,
        quality=optimized.quality,
        backend=backend,
    )
