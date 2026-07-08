# imgconvert

`imgconvert` is a Python 3.12 command-line utility for converting, resizing, optimizing, and batch-processing images. It uses Pillow by default and automatically falls back to ImageMagick when it is installed and Pillow cannot read or write a format.

## Features

- Convert JPEG, PNG, WebP, TIFF, BMP, GIF, ICO, and PPM.
- Optional HEIC and AVIF support when `pillow-heif` or `pillow-avif-plugin` is installed.
- Resize with high-quality Lanczos resampling.
- Optimize to a target file size with binary-search quality selection.
- Preserve or strip EXIF and ICC metadata.
- Flatten transparency for output formats that do not support alpha.
- Batch convert files, directories, and glob patterns with `ThreadPoolExecutor`.
- Progress reporting, structured JSON logging, and robust per-file error handling.
- Pip-installable package with a console entry point.

## Installation

```bash
python -m pip install .
```

For development:

```bash
python -m pip install -e ".[dev]"
```

Optional format plugins:

```bash
python -m pip install ".[heic,avif]"
```

ImageMagick is optional. If installed, `imgconvert` will use `magick` or `convert` as a fallback for files Pillow cannot handle.

## Usage

Convert one file:

```bash
imgconvert photo.png --format webp --output photo.webp --quality 85
```

Resize while converting:

```bash
imgconvert input.jpg --format png --width 1200 --height 800 --fit contain
```

Constrain output size:

```bash
imgconvert input.jpg --format jpeg --max-size 500KB --output compressed.jpg
```

Batch convert a directory:

```bash
imgconvert ./images --format webp --output-dir ./converted --workers 8 --recursive
```

Strip metadata:

```bash
imgconvert input.tif --format jpeg --strip-metadata
```

Structured logging:

```bash
imgconvert ./images --format webp --log-format json --log-level INFO
```

## CLI Reference

```text
imgconvert INPUT [INPUT ...] --format FORMAT [options]

Inputs may be files, directories, or glob patterns. Directories are processed as
batches. For a single file, use --output to control the exact destination.
For batches, use --output-dir and optionally --suffix.
```

Important options:

- `--format`: Output format. One of `jpeg`, `png`, `webp`, `tiff`, `bmp`, `gif`, `ico`, `ppm`, plus optional `heic` or `avif`.
- `--output`: Destination path for single-file conversion.
- `--output-dir`: Destination directory for batch conversion.
- `--quality`: Initial or fixed quality for lossy formats.
- `--max-size`: Target maximum size such as `250KB`, `1.5MB`, or raw bytes.
- `--width`, `--height`, `--scale`: Resize controls.
- `--fit`: `contain`, `cover`, or `stretch` resize behavior.
- `--preserve-metadata`, `--strip-metadata`: Metadata behavior.
- `--background`: Color used when flattening transparency for formats without alpha.
- `--recursive`: Recurse through directory inputs.
- `--workers`: Number of batch worker threads.
- `--overwrite`: Replace existing output files.
- `--progress`: Show conversion progress on stderr.

## Architecture

- `imgconvert.cli`: Argument parsing and command orchestration.
- `imgconvert.conversion`: Single-file conversion pipeline.
- `imgconvert.resizing`: Resize planning and Lanczos resizing.
- `imgconvert.optimization`: Quality binary search and byte-size targets.
- `imgconvert.metadata`: EXIF and ICC extraction and save parameter handling.
- `imgconvert.batch`: Input discovery and multithreaded batch conversion.
- `imgconvert.log_config`: Human and JSON logging setup.
- `imgconvert.utils`: Format, path, and size helpers.

## Testing

```bash
python -m pytest
```

The test suite creates images in temporary directories and covers format parsing, resizing behavior, optimization, metadata handling, conversion, and batch error handling.
