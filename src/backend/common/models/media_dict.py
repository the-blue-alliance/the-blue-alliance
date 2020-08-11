from typing_extensions import TypedDict

from backend.common.consts.media_type import MediaType


class _MediaDictOptional(TypedDict, total=False):
    profile_url: str
    media_type: MediaType
    is_social: bool
    foreign_key: str
    site_name: str
    details_json: str


class MediaDict(_MediaDictOptional):
    media_type_enum: MediaType
