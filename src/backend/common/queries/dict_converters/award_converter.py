from typing import Dict, List

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.award import Award
from backend.common.queries.dict_converters.converter_base import ConverterBase


class AwardConverter(ConverterBase):
    # SUBVERSIONS = {  # Increment every time a change to the dict is made
    #     3: 3,
    # }
    # TODO use for cache clearing

    @classmethod
    def _convert_list(cls, awards: List[Award], version: ApiMajorVersion) -> List[Dict]:
        AWARD_CONVERTERS = {
            ApiMajorVersion.API_V3: cls.awardsConverter_v3,
        }
        return AWARD_CONVERTERS[version](awards)

    @classmethod
    def awardsConverter_v3(cls, awards: List[Award]) -> List[Dict]:
        return list(map(cls.awardConverter_v3, awards))

    @classmethod
    def awardConverter_v3(cls, award: Award) -> Dict:
        recipient_list_fixed = []
        for recipient in award.recipient_list:
            recipient_list_fixed.append(
                {
                    "awardee": recipient["awardee"],
                    "team_key": "frc{}".format(recipient["team_number"])
                    if recipient["team_number"]
                    else None,
                }
            )
        return {
            "name": award.name_str,
            "award_type": award.award_type_enum,
            "year": award.year,
            "event_key": award.event.id(),
            "recipient_list": recipient_list_fixed,
        }
