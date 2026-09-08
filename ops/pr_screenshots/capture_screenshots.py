#!/usr/bin/env python3

import json
import os
import pickle
import subprocess

from artifact_data import ARTIFACT_FILENAME, ArtifactData

GITHUB_REF = os.environ.get("GITHUB_REF", "")
GITHUB_PULL_REQUEST_NUMBER = (
    int(GITHUB_REF.split("/")[2]) if "refs/pull/" in GITHUB_REF else None
)


def capture_screenshots() -> list[tuple[str, str, str]]:
    script_path = os.path.join(os.path.dirname(__file__), "capture_screenshots.js")
    env = os.environ.copy()
    if GITHUB_PULL_REQUEST_NUMBER is not None:
        env["GITHUB_PULL_REQUEST_NUMBER"] = str(GITHUB_PULL_REQUEST_NUMBER)
    output = subprocess.check_output(
        ["node", script_path],
        env=env,
        text=True,
    )
    raw_results: list[list[str]] = json.loads(output)
    return [(item[0], item[1], item[2]) for item in raw_results]


if __name__ == "__main__":
    if os.environ.get("CI"):
        screenshots = capture_screenshots()
        pickle.dump(
            ArtifactData(screenshots=screenshots, pr=GITHUB_PULL_REQUEST_NUMBER),
            open(ARTIFACT_FILENAME, "wb"),
        )
    else:
        print("Only runnable in CI.")
