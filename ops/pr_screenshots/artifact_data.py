from typing import List, Optional, Tuple, TypedDict


ARTIFACT_FILENAME = "ci_screenshots.pickle"


class ArtifactData(TypedDict):
    pr: Optional[int]
    screenshots: List[Tuple[str, str, str]]  # (name, filename, base64encode image)
