#!/usr/bin/env python3

import os
import shutil
import subprocess
from typing import List, Tuple


CAPTURE_URLS = [
    ("Homepage", "https://www.thebluealliance.com"),
    ("GameDay", "https://www.thebluealliance.com/gameday"),
]  # (name, url)
SAVE_DIR = "ci_screenshots"
MESSAGE_FILENAME = "message.md"


def reset_directory() -> None:
    if os.path.isdir(SAVE_DIR):
        shutil.rmtree(SAVE_DIR)
    os.mkdir(SAVE_DIR)


def capture_screenshots(urls: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    screenshots = []
    for i, (name, url) in enumerate(urls):
        print(f"Screenshotting {name}: {url}")
        file_name = f"{SAVE_DIR}/out_{i}.png"
        try:
            cmd = [
                "capture-website",
                url,
                "--width",
                "1920",
                "--height",
                "1080",
                "--output",
                file_name,
            ]
            subprocess.check_output(cmd)
            screenshots.append((name, file_name))
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
    return screenshots


def generate_message(screenshots: List[Tuple[str, str]]):
    print("Generating message")
    message = "## Screenshots"
    for name, filename in screenshots:
        message += f"\n\n### {name}"
    with open(f"{SAVE_DIR}/{MESSAGE_FILENAME}", "w") as file:
        file.write(message)


if __name__ == "__main__":
    reset_directory()
    screenshots = capture_screenshots(CAPTURE_URLS)
    generate_message(screenshots)
