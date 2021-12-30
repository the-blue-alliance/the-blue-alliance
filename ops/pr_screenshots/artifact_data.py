from typing import List, Tuple, TypedDict


ARTIFACT_FILENAME = "ci_screenshots.pickle"


class ArtifactData(TypedDict):
    pr: int
    screenshots: List[Tuple[str, str, str]]  # (name, filename, base64encode image)
