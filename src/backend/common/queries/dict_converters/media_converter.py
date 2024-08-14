import json
from typing import Dict, List, NewType, Optional

from google.appengine.ext import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.media_type import SLUG_NAME_TO_TYPE
from backend.common.models.keys import TeamKey
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.dict_converters.converter_base import ConverterBase

MediaDict = NewType("MediaDict", Dict)


class MediaConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        ApiMajorVersion.API_V3: 5,
    }

    @classmethod
    def _convert_list(
        cls, model_list: List[Media], version: ApiMajorVersion
    ) -> List[MediaDict]:
        MEDIA_CONVERTERS = {
            ApiMajorVersion.API_V3: cls.mediasConverter_v3,
        }
        return MEDIA_CONVERTERS[version](model_list)

    @classmethod
    def mediasConverter_v3(cls, medias: List[Media]) -> List[MediaDict]:
        return list(map(cls.mediaConverter_v3, medias))

    @classmethod
    def mediaConverter_v3(cls, media: Media) -> MediaDict:
        dict = {
            "type": media.slug_name,
            "foreign_key": media.foreign_key,
            "details": media.details if media.details else {},
            "preferred": True if media.preferred_references != [] else False,
            "view_url": None,
            "direct_url": None,
        }
        if media.slug_name == "youtube":
            dict["direct_url"] = "https://img.youtube.com/vi/{}/hqdefault.jpg".format(
                media.foreign_key
            )
            dict["view_url"] = media.youtube_url_link
        else:
            dict["direct_url"] = media.image_direct_url
            dict["view_url"] = media.view_image_url
        return MediaDict(dict)

    @staticmethod
    def dictToModel_v3(
        data: Dict, year: Optional[int], team_key: Optional[TeamKey]
    ) -> Media:
        media_type = SLUG_NAME_TO_TYPE[data["type"]]
        foreign_key = data["foreign_key"]
        media = Media(
            id=Media.render_key_name(media_type, foreign_key),
            media_type_enum=media_type,
            foreign_key=foreign_key,
            details_json=json.dumps(data["details"]),
            references=[ndb.Key(Team, team_key)] if team_key else [],
            preferred_references=(
                [ndb.Key(Team, team_key)] if team_key and data["preferred"] else []
            ),
            year=year,
        )
        return media
