#!/usr/bin/env python3

import os
import shutil
import subprocess
from typing import List


CAPTURE_URLS = [
    # "http://localhost:8080",
    # "http://localhost:8080/gameday",
    "https://www.thebluealliance.com/gameday",
]
SAVE_DIR = "ci_screenshots"
MESSAGE_FILENAME = "message.md"


def reset_directory() -> None:
    shutil.rmtree(SAVE_DIR)
    os.mkdir(SAVE_DIR)


def capture_screenshots(urls: List[str]) -> List[str]:
    file_names = []
    for i, url in enumerate(urls):
        print(f"Screenshotting: {url}")
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
            file_names.append(file_name)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
    return file_names


def generate_message(file_names: List[str]):
    print("Generating message")
    with open(f"{SAVE_DIR}/{MESSAGE_FILENAME}", "w") as file:
        file.write("HELLO THIS IS A TEST")


if __name__ == "__main__":
    reset_directory()
    files = capture_screenshots(CAPTURE_URLS)
    generate_message(files)
