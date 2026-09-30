#!/usr/bin/env python3
"""Render a pixel diff of two screenshots for a PR's Before | After | Diff table.

    uv run --group dev python3 ops/pr_screenshots/diff_screenshots.py before.png after.png diff.png
    uv run --group dev python3 ops/pr_screenshots/diff_screenshots.py --dir before/ after/ diff/

Pixels that differ are painted red on a faded grayscale copy of the "after" image, so
unchanged areas stay legible for orientation. Screenshots of different sizes
are padded (bottom/right) to the larger of the two before comparing, and the
padding counts as changed. Prints the changed-pixel percentage, which belongs
in the table cell next to the image.
"""

import json
import os
import sys
from dataclasses import dataclass

from PIL import Image, ImageChops

# Per-channel difference below this is treated as identical, so anti-aliasing
# and JPEG-ish noise from the browser don't light up the whole diff.
THRESHOLD = 16
HIGHLIGHT = (255, 0, 0, 255)
FADE = (
    0.45  # how much of the (grayscale) "after" image shows through the white backdrop
)


@dataclass(frozen=True)
class DiffResult:
    image: Image.Image
    changed_pixels: int
    total_pixels: int

    @property
    def changed_fraction(self) -> float:
        return self.changed_pixels / self.total_pixels if self.total_pixels else 0.0


def _pad_to(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Bottom/right-pad `image` with transparent pixels to `size`."""
    if image.size == size:
        return image
    padded = Image.new("RGBA", size, (0, 0, 0, 0))
    padded.paste(image, (0, 0))
    return padded


def diff_images(before: Image.Image, after: Image.Image) -> DiffResult:
    size = (max(before.width, after.width), max(before.height, after.height))
    before = _pad_to(before.convert("RGBA"), size)
    after = _pad_to(after.convert("RGBA"), size)

    # Any channel (including alpha, so padding counts) differing past the
    # threshold marks the pixel as changed.
    delta = ImageChops.difference(before, after)
    changed_mask = delta.convert("L").point(lambda v: 255 if v > THRESHOLD else 0)
    for band in delta.split():
        changed_mask = ImageChops.lighter(
            changed_mask, band.point(lambda v: 255 if v > THRESHOLD else 0)
        )

    # Unchanged areas stay visible in faded grayscale so the red reads as "the
    # change" rather than competing with the page's own colors.
    grayscale = after.convert("LA").convert("RGBA")
    faded = Image.blend(Image.new("RGBA", size, (255, 255, 255, 255)), grayscale, FADE)
    highlight = Image.new("RGBA", size, HIGHLIGHT)
    output = Image.composite(highlight, faded, changed_mask)

    histogram = changed_mask.histogram()
    return DiffResult(
        image=output,
        changed_pixels=histogram[255],
        total_pixels=size[0] * size[1],
    )


SUMMARY_FILENAME = "summary.json"


def _diff_files(before_path: str, after_path: str, out_path: str) -> DiffResult:
    result = diff_images(Image.open(before_path), Image.open(after_path))
    result.image.save(out_path)
    print(
        f"{out_path}: {result.changed_pixels} of {result.total_pixels} pixels "
        f"changed ({result.changed_fraction:.2%})"
    )
    return result


def diff_directories(
    before_dir: str, after_dir: str, out_dir: str
) -> dict[str, dict[str, float]]:
    """Diff every PNG in `after_dir` that has a same-named file in `before_dir`,
    writing each diff to `out_dir` plus a `summary.json` of the counts keyed by
    filename, which is what the comment scripts read."""
    os.makedirs(out_dir, exist_ok=True)
    summary: dict[str, dict[str, float]] = {}
    for filename in sorted(os.listdir(after_dir)):
        before_path = os.path.join(before_dir, filename)
        if not filename.endswith(".png") or not os.path.exists(before_path):
            continue
        result = _diff_files(
            before_path,
            os.path.join(after_dir, filename),
            os.path.join(out_dir, filename),
        )
        summary[filename] = {
            "changed_pixels": result.changed_pixels,
            "total_pixels": result.total_pixels,
            "changed_fraction": result.changed_fraction,
        }
    with open(os.path.join(out_dir, SUMMARY_FILENAME), "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main(argv: list[str]) -> int:
    if len(argv) == 5 and argv[1] == "--dir":
        diff_directories(*argv[2:])
        return 0
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    _diff_files(*argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
