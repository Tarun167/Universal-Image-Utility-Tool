"""General utility helpers for paths, formats, and sizes."""

from __future__ import annotations

import glob
import re
import shutil
from pathlib import Path
from typing import Iterable, TypedDict

from imgconvert.exceptions import UnsupportedFormatError


class FormatInfo(TypedDict):
    """Registry information for a supported image format."""

    extensions: tuple[str, ...]
    pillow: str
    alpha: bool
    lossy: bool


BASE_FORMATS: dict[str, FormatInfo] = {
    "jpeg": {"extensions": (".jpg", ".jpeg"), "pillow": "JPEG", "alpha": False, "lossy": True},
    "png": {"extensions": (".png",), "pillow": "PNG", "alpha": True, "lossy": False},
    "webp": {"extensions": (".webp",), "pillow": "WEBP", "alpha": True, "lossy": True},
    "tiff": {"extensions": (".tif", ".tiff"), "pillow": "TIFF", "alpha": True, "lossy": False},
    "bmp": {"extensions": (".bmp",), "pillow": "BMP", "alpha": False, "lossy": False},
    "gif": {"extensions": (".gif",), "pillow": "GIF", "alpha": True, "lossy": False},
    "ico": {"extensions": (".ico",), "pillow": "ICO", "alpha": True, "lossy": False},
    "ppm": {"extensions": (".ppm", ".pnm"), "pillow": "PPM", "alpha": False, "lossy": False},
    "heic": {"extensions": (".heic", ".heif"), "pillow": "HEIF", "alpha": True, "lossy": True},
    "avif": {"extensions": (".avif",), "pillow": "AVIF", "alpha": True, "lossy": True},
}

SIZE_PATTERN = re.compile(r"^\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[kmgt]?b?)?\s*$", re.I)


def register_optional_plugins() -> None:
    """Register optional Pillow format plugins when they are installed."""

    try:
        from pillow_heif import register_heif_opener  # type: ignore[import-not-found]
    except ImportError:
        pass
    else:
        register_heif_opener()

    try:
        import pillow_avif  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        pass


def normalize_format(value: str) -> str:
    """Normalize a user-provided format name or extension."""

    cleaned = value.strip().lower().lstrip(".")
    aliases = {"jpg": "jpeg", "tif": "tiff", "pnm": "ppm", "heif": "heic"}
    cleaned = aliases.get(cleaned, cleaned)
    if cleaned not in BASE_FORMATS:
        raise UnsupportedFormatError(f"Unsupported format: {value}")
    return cleaned


def pillow_format(format_name: str) -> str:
    """Return the Pillow save format for a normalized format."""

    return str(BASE_FORMATS[normalize_format(format_name)]["pillow"])


def default_extension(format_name: str) -> str:
    """Return the preferred extension for a normalized format."""

    return str(BASE_FORMATS[normalize_format(format_name)]["extensions"][0])


def format_supports_alpha(format_name: str) -> bool:
    """Return whether a normalized format supports alpha."""

    return bool(BASE_FORMATS[normalize_format(format_name)]["alpha"])


def format_is_lossy(format_name: str) -> bool:
    """Return whether quality settings are meaningful for this output format."""

    return bool(BASE_FORMATS[normalize_format(format_name)]["lossy"])


def parse_size(value: str | None) -> int | None:
    """Parse byte-size strings such as ``500KB`` or ``1.5MB``."""

    if value is None:
        return None
    match = SIZE_PATTERN.match(value)
    if not match:
        raise ValueError(f"Invalid size value: {value}")
    amount = float(match.group("value"))
    unit = (match.group("unit") or "b").lower()
    multipliers = {
        "": 1,
        "b": 1,
        "k": 1024,
        "kb": 1024,
        "m": 1024**2,
        "mb": 1024**2,
        "g": 1024**3,
        "gb": 1024**3,
        "t": 1024**4,
        "tb": 1024**4,
    }
    if unit not in multipliers:
        raise ValueError(f"Invalid size unit: {unit}")
    return int(amount * multipliers[unit])


def imagemagick_binary() -> str | None:
    """Return an ImageMagick executable when available."""

    return shutil.which("magick") or shutil.which("convert")


def is_supported_input(path: Path) -> bool:
    """Return whether a path extension maps to a supported input format."""

    suffix = path.suffix.lower()
    return any(suffix in data["extensions"] for data in BASE_FORMATS.values())


def expand_inputs(inputs: Iterable[str], recursive: bool) -> list[Path]:
    """Expand files, directories, and glob patterns into candidate input files."""

    paths: list[Path] = []
    for raw in inputs:
        expanded = [Path(item) for item in glob.glob(raw, recursive=recursive)]
        candidates = expanded or [Path(raw)]
        for candidate in candidates:
            if candidate.is_dir():
                pattern = "**/*" if recursive else "*"
                paths.extend(path for path in candidate.glob(pattern) if path.is_file())
            elif candidate.is_file():
                paths.append(candidate)
    unique = dict.fromkeys(path.resolve() for path in paths if is_supported_input(path))
    return list(unique)


def build_output_path(
    input_path: Path,
    output_format: str,
    output: Path | None,
    output_dir: Path | None,
    suffix: str,
) -> Path:
    """Compute an output path for a single input."""

    extension = default_extension(output_format)
    if output is not None:
        return output
    directory = output_dir if output_dir is not None else input_path.parent
    return directory / f"{input_path.stem}{suffix}{extension}"


def ensure_parent(path: Path) -> None:
    """Create the parent directory for an output path."""

    path.parent.mkdir(parents=True, exist_ok=True)
