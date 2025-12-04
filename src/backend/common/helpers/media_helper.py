from backend.common.consts.media_type import (
    IMAGE_TYPES,
    MediaType,
    SOCIAL_SORT_ORDER,
    SOCIAL_TYPES,
)
from backend.common.models.media import Media


class MediaHelper(object):
    @classmethod
    def group_by_slugname(cls, medias: list[Media]) -> dict[str, list[Media]]:
        medias_by_slugname: dict[str, list[Media]] = {}
        for media in medias:
            slugname = media.slug_name
            if slugname in medias_by_slugname:
                medias_by_slugname[slugname].append(media)
            else:
                medias_by_slugname[slugname] = [media]
        return medias_by_slugname

    @classmethod
    def get_avatar(cls, medias: list[Media]) -> Media | None:
        avatars = filter(lambda m: m.media_type_enum == MediaType.AVATAR, medias)
        return next(avatars, None)

    @classmethod
    def get_images(cls, medias: list[Media]) -> list[Media]:
        return list(filter(lambda m: m.media_type_enum in IMAGE_TYPES, medias))

    @classmethod
    def get_socials(cls, medias: list[Media]) -> list[Media]:
        return list(filter(lambda m: m.media_type_enum in SOCIAL_TYPES, medias))

    @classmethod
    def social_media_sorter(cls, media: Media) -> int:
        return SOCIAL_SORT_ORDER.get(media.media_type_enum, 1000)
