import enum
from typing import Dict, Optional, Set


@enum.unique
class MediaTag(enum.IntEnum):
    # ndb keys are based on these! Don't change!
    CHAIRMANS_VIDEO = 0
    CHAIRMANS_PRESENTATION = 1
    CHAIRMANS_ESSAY = 2


MEDIA_TAGS: Set[MediaTag] = {t for t in MediaTag}

TAG_NAMES: Dict[MediaTag, str] = {
    MediaTag.CHAIRMANS_VIDEO: "Chairman's Video",
    MediaTag.CHAIRMANS_PRESENTATION: "Chairman's Presentation",
    MediaTag.CHAIRMANS_ESSAY: "Chairman's Essay",
}

TAG_URL_NAMES: Dict[MediaTag, str] = {
    MediaTag.CHAIRMANS_VIDEO: "chairmans_video",
    MediaTag.CHAIRMANS_PRESENTATION: "chairmans_presentation",
    MediaTag.CHAIRMANS_ESSAY: "chairmans_essay",
}

CHAIRMANS_TAGS: Set[MediaTag] = {
    MediaTag.CHAIRMANS_VIDEO,
    MediaTag.CHAIRMANS_PRESENTATION,
    MediaTag.CHAIRMANS_ESSAY,
}


def get_enum_from_url(url_name: str) -> Optional[MediaTag]:
    inversed = {v: k for k, v in TAG_URL_NAMES.items()}
    if url_name in inversed:
        return inversed[url_name]
    else:
        return None
