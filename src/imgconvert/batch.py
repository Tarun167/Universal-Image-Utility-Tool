"""Batch conversion with multithreaded execution."""

from __future__ import annotations

import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Callable

from imgconvert.conversion import ConversionOptions, ConversionResult, convert_image
from imgconvert.exceptions import ImgConvertError
from imgconvert.resizing import ResizeOptions
from imgconvert.utils import build_output_path, expand_inputs, parse_size

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class BatchOptions:
    """Options shared by a batch conversion run."""

    output_format: str
    output: Path | None = None
    output_dir: Path | None = None
    suffix: str = ""
    resize: ResizeOptions = ResizeOptions()
    quality: int = 90
    max_size: str | None = None
    preserve_metadata: bool = True
    strip_metadata: bool = False
    background: str = "#ffffff"
    overwrite: bool = False
    recursive: bool = False
    workers: int = 4
    progress: bool = False


@dataclass(frozen=True)
class BatchFailure:
    """A per-file failure that did not abort the full batch."""

    input_path: Path
    error: str


@dataclass(frozen=True)
class BatchReport:
    """Batch conversion summary."""

    results: tuple[ConversionResult, ...]
    failures: tuple[BatchFailure, ...]

    @property
    def ok(self) -> bool:
        return not self.failures


ProgressCallback = Callable[[int, int, Path, bool], None]


def run_batch(inputs: list[str], options: BatchOptions) -> BatchReport:
    """Discover and convert all inputs concurrently."""

    input_paths = expand_inputs(inputs, options.recursive)
    if not input_paths:
        raise ImgConvertError("No supported input images found")
    if options.output is not None and len(input_paths) != 1:
        raise ImgConvertError("--output can only be used with a single input image")

    callback = _stderr_progress if options.progress else None
    max_size = parse_size(options.max_size)
    total = len(input_paths)
    completed = 0
    lock = Lock()
    results: list[ConversionResult] = []
    failures: list[BatchFailure] = []

    def convert_one(path: Path) -> ConversionResult:
        output_path = build_output_path(
            input_path=path,
            output_format=options.output_format,
            output=options.output,
            output_dir=options.output_dir,
            suffix=options.suffix,
        )
        conversion_options = ConversionOptions(
            output_format=options.output_format,
            output_path=output_path,
            resize=options.resize,
            quality=options.quality,
            max_size=max_size,
            preserve_metadata=options.preserve_metadata,
            strip_metadata=options.strip_metadata,
            background=options.background,
            overwrite=options.overwrite,
        )
        return convert_image(path, conversion_options)

    with ThreadPoolExecutor(max_workers=max(1, options.workers)) as executor:
        future_to_path = {executor.submit(convert_one, path): path for path in input_paths}
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            success = False
            try:
                results.append(future.result())
                success = True
            except Exception as exc:  # noqa: BLE001 - isolate batch failures per file
                LOGGER.error("failed to convert image", extra={"input": str(path), "error": str(exc)})
                failures.append(BatchFailure(path, str(exc)))
            finally:
                with lock:
                    completed += 1
                    if callback is not None:
                        callback(completed, total, path, success)

    return BatchReport(results=tuple(results), failures=tuple(failures))


def _stderr_progress(done: int, total: int, path: Path, success: bool) -> None:
    status = "ok" if success else "failed"
    print(f"[{done}/{total}] {status}: {path}", file=sys.stderr)
