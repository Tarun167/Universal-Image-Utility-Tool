"""Custom exceptions used by imgconvert."""

from __future__ import annotations


class ImgConvertError(Exception):
    """Base exception for expected imgconvert failures."""


class UnsupportedFormatError(ImgConvertError):
    """Raised when an input or output format is unsupported."""


class ConversionError(ImgConvertError):
    """Raised when a conversion fails."""


class OptimizationError(ImgConvertError):
    """Raised when an output cannot satisfy the requested optimization target."""
