#!/usr/bin/env python3
"""Screenshot the dev server for a PR's Before | After | Diff comment.

    python ops/pr_screenshots/capture_screenshots.py           # on the PR head
    python ops/pr_screenshots/capture_screenshots.py --before  # on the PR base

The head run writes the artifact; the base run adds `before_screenshots` to
it. The comment workflow pairs them up by name and renders the diff.
"""

import base64
import os
import pickle
import re
import subprocess
import sys
import time
from typing import Callable

from artifact_data import ARTIFACT_FILENAME, ArtifactData, Screenshot

CAPTURE_URLS = [
    ("Homepage", "http://localhost:8080"),
    ("GameDay", "http://localhost:8080/gameday"),
]  # (name, url)

GITHUB_REF = os.environ.get("GITHUB_REF", "")
GITHUB_PULL_REQUEST_NUMBER = (
    int(GITHUB_REF.split("/")[2]) if "refs/pull/" in GITHUB_REF else None
)


def screenshot_filename(pr: int | None, name: str, phase: str, timestamp: int) -> str:
    """`pr-123-gameday-after-1790000000.png`; the phase lets the comment
    workflow derive the diff's filename from the after's."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"pr-{pr}-{slug}-{phase}-{timestamp}.png"


def _capture_website(url: str) -> bytes:
    return subprocess.check_output(
        [
            "capture-website",
            url,
            "--width",
            "1920",
            "--height",
            "1080",
            "--scale-factor",
            "1",
        ]
    )


def capture_screenshots(
    urls: list[tuple[str, str]],
    phase: str,
    pr: int | None,
    capture: Callable[[str], bytes] | None = None,
    now: Callable[[], float] = time.time,
) -> list[Screenshot]:
    # Resolved at call time so tests can swap the real capture out.
    capture = capture or _capture_website
    screenshots: list[Screenshot] = []
    for name, url in urls:
        print(f"Screenshotting {name} ({phase}): {url}")
        try:
            image = base64.b64encode(capture(url)).decode("utf-8")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            continue
        screenshots.append(
            (name, screenshot_filename(pr, name, phase, int(now())), image)
        )
    return screenshots


def with_before_screenshots(
    artifact: ArtifactData, before: list[Screenshot]
) -> ArtifactData:
    """The base capture runs second and must not disturb what the head wrote."""
    return ArtifactData(
        pr=artifact["pr"],
        screenshots=artifact["screenshots"],
        before_screenshots=before,
    )


def main(argv: list[str]) -> int:
    if not os.environ.get("CI"):
        print("Only runnable in CI.")
        return 0
    if "--before" in argv:
        with open(ARTIFACT_FILENAME, "rb") as f:
            artifact = ArtifactData(pickle.load(f))
        artifact = with_before_screenshots(
            artifact,
            capture_screenshots(CAPTURE_URLS, "before", GITHUB_PULL_REQUEST_NUMBER),
        )
    else:
        artifact = ArtifactData(
            pr=GITHUB_PULL_REQUEST_NUMBER,
            screenshots=capture_screenshots(
                CAPTURE_URLS, "after", GITHUB_PULL_REQUEST_NUMBER
            ),
        )
    with open(ARTIFACT_FILENAME, "wb") as f:
        pickle.dump(artifact, f)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
