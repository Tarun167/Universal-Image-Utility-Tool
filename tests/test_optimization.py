from __future__ import annotations

import pytest
from PIL import Image

from imgconvert.exceptions import OptimizationError
from imgconvert.optimization import optimize_to_size


def test_optimize_to_size_finds_smaller_jpeg() -> None:
    image = Image.effect_noise((300, 300), 80).convert("RGB")
    large = optimize_to_size(image, "jpeg", None, 95, {})
    small = optimize_to_size(image, "jpeg", large.size // 2, 95, {})
    assert small.size <= large.size // 2
    assert small.quality is not None
    assert small.quality < 95


def test_optimize_to_size_rejects_unreachable_png_target() -> None:
    image = Image.new("RGB", (100, 100), "blue")
    with pytest.raises(OptimizationError):
        optimize_to_size(image, "png", 10, 90, {})
