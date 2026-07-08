"""Command-line interface for imgconvert."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from imgconvert import __version__
from imgconvert.batch import BatchOptions, run_batch
from imgconvert.exceptions import ImgConvertError
from imgconvert.log_config import configure_logging
from imgconvert.resizing import ResizeOptions
from imgconvert.utils import BASE_FORMATS, normalize_format


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser."""

    parser = argparse.ArgumentParser(
        prog="imgconvert",
        description="Convert, resize, optimize, and batch-process images.",
    )
    parser.add_argument("inputs", nargs="+", help="Input files, directories, or glob patterns.")
    parser.add_argument("-f", "--format", required=True, help="Output format.")
    parser.add_argument("-o", "--output", type=Path, help="Output path for a single input.")
    parser.add_argument("--output-dir", type=Path, help="Output directory for batch conversion.")
    parser.add_argument("--suffix", default="", help="Suffix added to batch output filenames.")
    parser.add_argument("--quality", type=_quality, default=90, help="Lossy quality, 1-100.")
    parser.add_argument("--max-size", help="Maximum output size, e.g. 500KB or 1.5MB.")
    parser.add_argument("--width", type=_positive_int, help="Target width in pixels.")
    parser.add_argument("--height", type=_positive_int, help="Target height in pixels.")
    parser.add_argument("--scale", type=_positive_float, help="Scale factor, e.g. 0.5.")
    parser.add_argument("--fit", choices=("contain", "cover", "stretch"), default="contain")
    metadata = parser.add_mutually_exclusive_group()
    metadata.add_argument(
        "--preserve-metadata",
        action="store_true",
        default=True,
        help="Preserve EXIF and ICC metadata where supported.",
    )
    metadata.add_argument("--strip-metadata", action="store_true", help="Strip metadata.")
    parser.add_argument("--background", default="#ffffff", help="Flattening background color.")
    parser.add_argument("--recursive", action="store_true", help="Recurse through directories.")
    parser.add_argument("--workers", type=_positive_int, default=4, help="Batch worker count.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs.")
    parser.add_argument("--progress", action="store_true", help="Print progress to stderr.")
    parser.add_argument("--log-level", default="WARNING", help="Python logging level.")
    parser.add_argument("--log-format", choices=("text", "json"), default="text")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line application."""

    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level, args.log_format)

    try:
        output_format = normalize_format(args.format)
        if args.scale is not None and (args.width is not None or args.height is not None):
            parser.error("--scale cannot be combined with --width or --height")
        options = BatchOptions(
            output_format=output_format,
            output=args.output,
            output_dir=args.output_dir,
            suffix=args.suffix,
            resize=ResizeOptions(width=args.width, height=args.height, scale=args.scale, fit=args.fit),
            quality=args.quality,
            max_size=args.max_size,
            preserve_metadata=not args.strip_metadata,
            strip_metadata=args.strip_metadata,
            background=args.background,
            overwrite=args.overwrite,
            recursive=args.recursive,
            workers=args.workers,
            progress=args.progress,
        )
        report = run_batch(args.inputs, options)
    except ImgConvertError as exc:
        print(f"imgconvert: error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"imgconvert: error: {exc}", file=sys.stderr)
        return 2

    if report.failures:
        print(
            f"imgconvert: converted {len(report.results)} image(s), "
            f"failed {len(report.failures)} image(s)",
            file=sys.stderr,
        )
        return 1
    print(f"imgconvert: converted {len(report.results)} image(s)")
    return 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _quality(value: str) -> int:
    parsed = int(value)
    if parsed < 1 or parsed > 100:
        raise argparse.ArgumentTypeError("must be between 1 and 100")
    return parsed


def supported_formats() -> tuple[str, ...]:
    """Return CLI-visible supported format names."""

    return tuple(sorted(BASE_FORMATS))
