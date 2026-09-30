from typing import TypedDict

ARTIFACT_FILENAME = "ci_screenshots.pickle"

# (name, filename on the ci-screenshots branch, base64-encoded PNG)
Screenshot = tuple[str, str, str]


class _RequiredArtifactData(TypedDict):
    pr: int | None
    # Captured on the PR head. The key and tuple shape are load-bearing: the
    # comment workflow runs main's copy of generate_screenshots_message.py,
    # which reads exactly this until a change to it lands on main.
    screenshots: list[Screenshot]


class ArtifactData(_RequiredArtifactData, total=False):
    # Captured on the PR base, same names as `screenshots`. Absent when the
    # base capture did not run or failed, in which case the comment shows the
    # head screenshots alone.
    before_screenshots: list[Screenshot]
