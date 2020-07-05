import json
from typing import Dict, List

from google.cloud import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team
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

    @staticmethod
    def dictToModel_v3(data: Dict, event: Event) -> Award:
        award = Award(id=Award.render_key_name(data["event_key"], data["award_type"]))
        award.event = ndb.Key(Event, data["event_key"])
        award.award_type_enum = data["award_type"]
        award.year = data["year"]
        award.name_str = data["name"]
        award.event_type_enum = event.event_type_enum

        recipient_list_fixed = []
        team_keys = []
        for recipient in data["recipient_list"]:
            if recipient["team_key"]:
                team_keys.append(ndb.Key(Team, recipient["team_key"]))
            recipient_list_fixed.append(
                json.dumps(
                    {
                        "awardee": recipient["awardee"],
                        "team_number": recipient["team_key"][3:]
                        if recipient["team_key"]
                        else None,
                    }
                )
            )
        award.recipient_json_list = recipient_list_fixed
        award.team_list = team_keys
        return award
