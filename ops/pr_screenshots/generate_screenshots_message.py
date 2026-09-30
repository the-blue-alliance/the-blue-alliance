#!/usr/bin/env python3
# /// script
# dependencies = ["requests", "pillow"]
# ///
"""Turn the screenshot artifact into a Before | After | Diff PR comment.

Runs in the comment workflow (on main's copy of this file), after the PR
workflow has uploaded `ci_screenshots.pickle`. Uploads every image to the
`ci-screenshots` branch and writes the comment markdown to a file.
"""

import base64
import io
import os
import pickle
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable

import requests
from artifact_data import ARTIFACT_FILENAME, ArtifactData, Screenshot
from diff_screenshots import diff_images
from PIL import Image

MESSAGE_FILENAME = "ci_screenshots_message.md"


@dataclass(frozen=True)
class ScreenshotPair:
    name: str
    after: Screenshot
    before: Screenshot | None


@dataclass(frozen=True)
class DiffImage:
    filename: str
    image: str  # base64-encoded PNG
    changed_fraction: float


@dataclass(frozen=True)
class CommentRow:
    name: str
    after_url: str | None
    before_url: str | None = None
    diff_url: str | None = None
    changed_fraction: float | None = None


def pair_screenshots(artifact: ArtifactData) -> list[ScreenshotPair]:
    """Match base captures to head captures by page name. Head captures with
    no base counterpart (new page, or the base capture failed) pair with None."""
    before_by_name = {shot[0]: shot for shot in artifact.get("before_screenshots", [])}
    return [
        ScreenshotPair(
            name=name, after=(name, filename, image), before=before_by_name.get(name)
        )
        for name, filename, image in artifact["screenshots"]
    ]


def sibling_filename(after_filename: str, phase: str) -> str:
    """`pr-1-gameday-after-2.png` -> `pr-1-gameday-diff-2.png`; older filenames
    without a phase get the phase appended before the extension."""
    stem, _, ext = after_filename.rpartition(".")
    if "-after-" in stem:
        return f"{stem.replace('-after-', f'-{phase}-', 1)}.{ext}"
    return f"{stem}-{phase}.{ext}"


def diff_pair(pair: ScreenshotPair) -> DiffImage | None:
    if pair.before is None:
        return None
    before = Image.open(io.BytesIO(base64.b64decode(pair.before[2])))
    after = Image.open(io.BytesIO(base64.b64decode(pair.after[2])))
    result = diff_images(before, after)
    buffer = io.BytesIO()
    result.image.save(buffer, format="PNG")
    return DiffImage(
        filename=sibling_filename(pair.after[1], "diff"),
        image=base64.b64encode(buffer.getvalue()).decode("utf-8"),
        changed_fraction=result.changed_fraction,
    )


def build_rows(
    pairs: list[ScreenshotPair],
    upload: Callable[[str, str], str | None],
) -> list[CommentRow]:
    """Diff and upload each pair. `upload(filename, base64_png)` returns the
    raw URL or None on failure."""
    rows = []
    for pair in pairs:
        after_url = upload(pair.after[1], pair.after[2])
        diff = diff_pair(pair)
        if pair.before is None or diff is None:
            rows.append(CommentRow(name=pair.name, after_url=after_url))
            continue
        rows.append(
            CommentRow(
                name=pair.name,
                after_url=after_url,
                before_url=upload(pair.before[1], pair.before[2]),
                diff_url=upload(diff.filename, diff.image),
                changed_fraction=diff.changed_fraction,
            )
        )
    return rows


def generate_message(rows: list[CommentRow]) -> str:
    lines = ["## Screenshots", "", "| | Before | After | Diff |", "|---|---|---|---|"]
    missing_before = 0
    for row in rows:
        if row.after_url is None:
            continue
        after = f"![{row.name} after]({row.after_url})"
        if row.before_url is None or row.diff_url is None:
            missing_before += 1
            lines.append(f"| {row.name} | _no base capture_ | {after} | _n/a_ |")
            continue
        assert row.changed_fraction is not None
        lines.append(
            f"| {row.name} | ![{row.name} before]({row.before_url}) | {after} "
            f"| ![{row.name} diff]({row.diff_url})<br>{row.changed_fraction:.2%} "
            "of pixels changed |"
        )
    if missing_before:
        lines += [
            "",
            f"The base-branch capture is missing for {missing_before} page(s), "
            "so only the PR's screenshots are shown for those.",
        ]
    return "\n".join(lines) + "\n"


def _ensure_branch(branch: str, author_name: str, author_email: str) -> None:
    subprocess.run(["git", "config", "user.name", author_name])
    subprocess.run(["git", "config", "user.email", author_email])
    subprocess.run(["git", "fetch", "origin", "--prune", "--unshallow"])
    remote_branches = subprocess.check_output(["git", "branch", "-r"])
    if branch in str(remote_branches):
        print(f'Branch "{branch}" Already Exists')
        return
    subprocess.run(["git", "checkout", "--orphan", branch])
    subprocess.run(["git", "reset"])
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit on empty branch"]
    )
    subprocess.run(["git", "push", "-u", "origin", branch])


def make_uploader(
    pr: int | None, github_token: str
) -> Callable[[str, str], str | None]:
    GITHUB_API_URL = "https://api.github.com"
    GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
    BRANCH_NAME = "ci-screenshots"
    AUTHOR_NAME = "github-actions[bot]"
    AUTHOR_EMAIL = "github-actions[bot]@users.noreply.github.com"
    _ensure_branch(BRANCH_NAME, AUTHOR_NAME, AUTHOR_EMAIL)

    def upload(filename: str, image: str) -> str | None:
        url = f"{GITHUB_API_URL}/repos/{GITHUB_REPOSITORY}/contents/{filename}"
        data = {
            "message": f"[CI] Added Screenshots for PR #{pr}",
            "content": image,
            "branch": BRANCH_NAME,
            "author": {"name": AUTHOR_NAME, "email": AUTHOR_EMAIL},
            "committer": {"name": AUTHOR_NAME, "email": AUTHOR_EMAIL},
        }
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "authorization": f"Bearer {github_token}",
        }
        response = requests.put(url, headers=headers, json=data)
        if response.status_code in {200, 201}:
            link = (
                f"https://github.com/{GITHUB_REPOSITORY}/raw/{BRANCH_NAME}/{filename}"
            )
            print(f'Image "{filename}" Uploaded to "{link}"')
            return link
        print(f'Error uploading "{filename}"')
        print(response.content)
        return None

    return upload


def main(argv: list[str]) -> int:
    if not os.environ.get("CI"):
        print("Only runnable in CI.")
        return 0
    if not os.path.exists(ARTIFACT_FILENAME):
        print(f"{ARTIFACT_FILENAME} not found.")
        return 0
    with open(ARTIFACT_FILENAME, "rb") as f:
        artifact = ArtifactData(pickle.load(f))
    rows = build_rows(
        pair_screenshots(artifact), make_uploader(artifact["pr"], argv[1])
    )
    with open(MESSAGE_FILENAME, "w") as f:
        f.write(generate_message(rows))
    # Set PR number as output
    subprocess.run(["echo", f"::set-output name=pr::{artifact['pr']}"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
