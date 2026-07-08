from __future__ import annotations

from PIL import Image

from imgconvert.resizing import ResizeOptions, resize_image


def test_resize_contain_preserves_aspect_ratio() -> None:
    image = Image.new("RGB", (200, 100), "red")
    resized = resize_image(image, ResizeOptions(width=50, height=50, fit="contain"))
    assert resized.size == (50, 25)


def test_resize_cover_crops_to_exact_target() -> None:
    image = Image.new("RGB", (200, 100), "red")
    resized = resize_image(image, ResizeOptions(width=50, height=50, fit="cover"))
    assert resized.size == (50, 50)


def test_resize_scale() -> None:
    image = Image.new("RGB", (200, 100), "red")
    resized = resize_image(image, ResizeOptions(scale=0.25))
    assert resized.size == (50, 25)
