#!/usr/bin/env python3

import base64
import os
import subprocess
import sys
import time
from typing import List, Optional, Tuple

import requests


CAPTURE_URLS = [
    ("Homepage", "http://localhost:8080"),
    ("GameDay", "http://localhost:8080/gameday"),
]  # (name, url)
MESSAGE_FILENAME = "ci_screenshots_message.md"
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


def upload_screenshots(
    screenshots: List[Tuple[str, str, str]], GITHUB_TOKEN: str
) -> List[Tuple[str, Optional[str]]]:
    GITHUB_API_URL = "https://api.github.com"
    GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
    BRANCH_NAME = "ci-screenshots"
    AUTHOR_NAME = "github-actions[bot]"
    AUTHOR_EMAIL = "github-actions[bot]@users.noreply.github.com"

    subprocess.run(["git", "config", "user.name", AUTHOR_NAME])
    subprocess.run(["git", "config", "user.email", AUTHOR_EMAIL])
    subprocess.run(
        ["git", "fetch", "origin", "--prune", "--unshallow"],
    )
    remote_branches = subprocess.check_output(
        ["git", "branch", "-r"],
    )

    # Create branch if it does not yet exist
    if BRANCH_NAME not in str(remote_branches):
        subprocess.run(["git", "checkout", "--orphan", BRANCH_NAME])
        subprocess.run(["git", "reset"])
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial commit on empty branch"]
        )
        subprocess.run(["git", "push", "-u", "origin", BRANCH_NAME])
    else:
        print(f'Branch "{BRANCH_NAME}" Already Exists')

    def upload_single_screenshot(filename: str, image: str) -> Optional[str]:
        url = f"{GITHUB_API_URL}/repos/{GITHUB_REPOSITORY}/contents/{filename}"
        data = {
            "message": f"[CI] Added Screenshots for PR #{GITHUB_PULL_REQUEST_NUMBER}",
            "content": image,
            "branch": BRANCH_NAME,
            "author": {"name": AUTHOR_NAME, "email": AUTHOR_EMAIL},
            "committer": {"name": AUTHOR_NAME, "email": AUTHOR_EMAIL},
        }
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "authorization": f"Bearer {GITHUB_TOKEN}",
        }
        response = requests.put(url, headers=headers, json=data)

        if response.status_code in {200, 201}:
            link = (
                f"https://github.com/{GITHUB_REPOSITORY}/raw/{BRANCH_NAME}/{filename}"
            )
            print(f'Image "{filename}" Uploaded to "{link}"')
            return link
        else:
            print(f'Error uploading "{filename}"')
            print(response.content)
            return None

    image_urls = []  # (name, image_url)
    for name, filename, image in screenshots:
        image_url = upload_single_screenshot(filename, image)
        image_urls.append((name, image_url))
    return image_urls


def generate_message(image_urls: List[Tuple[str, Optional[str]]]):
    print("Generating message")
    message = "## Screenshots"
    for name, image_url in image_urls:
        if image_url is None:
            continue
        message += f"\n\n### {name}"
        message += f"\n![{name}]({image_url})"
    with open(MESSAGE_FILENAME, "w") as file:
        file.write(message)


if __name__ == "__main__":
    if os.environ.get("CI"):
        screenshots = capture_screenshots(CAPTURE_URLS)
        image_urls = upload_screenshots(screenshots, sys.argv[1])
        generate_message(image_urls)
    else:
        print("Only runnable in CI.")
