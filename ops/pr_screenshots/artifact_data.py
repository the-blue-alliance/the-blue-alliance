from typing import TypedDict

ARTIFACT_FILENAME = "ci_screenshots.pickle"


class ArtifactData(TypedDict):
    pr: int | None
    screenshots: list[tuple[str, str, str]]  # (name, filename, base64encode image)
