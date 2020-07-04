from typing import Dict, List, Optional

from backend.common.consts.media_type import (
    IMAGE_TYPES,
    MediaType,
    SOCIAL_SORT_ORDER,
    SOCIAL_TYPES,
)
from backend.common.models.media import Media


class MediaHelper(object):
    @classmethod
    def group_by_slugname(cls, medias: List[Media]) -> Dict[str, List[Media]]:
        medias_by_slugname: Dict[str, List[Media]] = {}
        for media in medias:
            slugname = media.slug_name
            if slugname in medias_by_slugname:
                medias_by_slugname[slugname].append(media)
            else:
                medias_by_slugname[slugname] = [media]
        return medias_by_slugname

    @classmethod
    def get_avatar(cls, medias: List[Media]) -> Optional[Media]:
        avatars = filter(lambda m: m.media_type_enum == MediaType.AVATAR, medias)
        return next(avatars, None)

    @classmethod
    def get_images(cls, medias: List[Media]) -> List[Media]:
        return list(filter(lambda m: m.media_type_enum in IMAGE_TYPES, medias))

    @classmethod
    def get_socials(cls, medias: List[Media]) -> List[Media]:
        return list(filter(lambda m: m.media_type_enum in SOCIAL_TYPES, medias))

    @classmethod
    def social_media_sorter(cls, media: Media) -> int:
        return SOCIAL_SORT_ORDER.get(media.media_type_enum, 1000)
