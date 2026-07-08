from __future__ import annotations

from pathlib import Path

from PIL import Image

from imgconvert.batch import BatchOptions, run_batch


def test_run_batch_converts_multiple_files(tmp_path: Path) -> None:
    for index in range(3):
        Image.new("RGB", (20, 20), "red").save(tmp_path / f"image-{index}.png")
    output_dir = tmp_path / "out"

    report = run_batch(
        [str(tmp_path)],
        BatchOptions(
            output_format="webp",
            output_dir=output_dir,
            workers=2,
            overwrite=True,
        ),
    )

    assert report.ok
    assert len(report.results) == 3
    assert len(list(output_dir.glob("*.webp"))) == 3


def test_run_batch_records_failures(tmp_path: Path) -> None:
    bad = tmp_path / "bad.png"
    bad.write_text("not an image")

    report = run_batch(
        [str(bad)],
        BatchOptions(output_format="jpeg", output_dir=tmp_path / "out", overwrite=True),
    )

    assert not report.ok
    assert len(report.failures) == 1
