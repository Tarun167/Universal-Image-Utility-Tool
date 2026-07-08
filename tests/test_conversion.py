from __future__ import annotations

from pathlib import Path

from PIL import Image

from imgconvert.conversion import ConversionOptions, convert_image
from imgconvert.resizing import ResizeOptions


def test_convert_image_resizes_and_flattens_alpha(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    output = tmp_path / "output.jpg"
    Image.new("RGBA", (100, 50), (255, 0, 0, 128)).save(source)

    result = convert_image(
        source,
        ConversionOptions(
            output_format="jpeg",
            output_path=output,
            resize=ResizeOptions(width=50, height=50),
            overwrite=True,
        ),
    )

    assert result.backend == "pillow"
    assert result.output_path == output
    with Image.open(output) as converted:
        assert converted.mode == "RGB"
        assert converted.size == (50, 25)


def test_convert_image_strips_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    output = tmp_path / "output.jpg"
    Image.new("RGB", (20, 20), "green").save(source, icc_profile=b"profile")

    convert_image(
        source,
        ConversionOptions(
            output_format="jpeg",
            output_path=output,
            strip_metadata=True,
            overwrite=True,
        ),
    )

    with Image.open(output) as converted:
        assert "icc_profile" not in converted.info
