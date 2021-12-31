#!/usr/bin/env python3

import base64
import os
import pickle
import subprocess
import time
from typing import List, Tuple

from artifact_data import ARTIFACT_FILENAME, ArtifactData


CAPTURE_URLS = [
    ("Homepage", "http://localhost:8080"),
    ("GameDay", "http://localhost:8080/gameday"),
]  # (name, url)
GITHUB_REF = os.environ.get("GITHUB_REF", "")
GITHUB_PULL_REQUEST_NUMBER = (
    int(GITHUB_REF.split("/")[2]) if "refs/pull/" in GITHUB_REF else None
)


def capture_screenshots(urls: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
    screenshots = []  # (name, filename, base64encode image)
    for name, url in urls:
        print(f"Screenshotting {name}: {url}")
        try:
            cmd = [
                "capture-website",
                url,
                "--width",
                "1920",
                "--height",
                "1080",
                "--scale-factor",
                "1",
            ]
            image_data = subprocess.check_output(cmd)
            image = base64.b64encode(image_data).decode("utf-8")
            filename = (
                f"pr-{GITHUB_PULL_REQUEST_NUMBER}-{url}-{int(time.time())}.png".replace(
                    "/", "-"
                ).replace(" ", "")
            )
            screenshots.append((name, filename, image))
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
    return screenshots


if __name__ == "__main__":
    if os.environ.get("CI"):
        screenshots = capture_screenshots(CAPTURE_URLS)
        pickle.dump(
            ArtifactData(screenshots=screenshots, pr=GITHUB_PULL_REQUEST_NUMBER),
            open(ARTIFACT_FILENAME, "wb"),
        )
    else:
        print("Only runnable in CI.")
