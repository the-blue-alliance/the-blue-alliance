import re
from typing import AnyStr, Dict, List, Optional, TypedDict

from pyre_extensions import safe_json

from backend.common.consts.playoff_type import PlayoffType
from backend.common.consts.webcast_type import WebcastType
from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.helpers.webcast_helper import WebcastParser
from backend.common.models.keys import TeamKey
from backend.common.models.webcast import Webcast


# We let users pass either a regular webcast model (type+channel),
# or a dict with 'url' as a key, which we can parse into a model
class _WebcastUrlDict(TypedDict, total=False):
    url: str
    type: WebcastType
    channel: str


class EventInfoInput(TypedDict, total=False):
    first_event_code: Optional[str]
    playoff_type: int
    webcasts: List[_WebcastUrlDict]
    remap_teams: Dict[str, str]


class EventInfoParsed(TypedDict, total=False):
    first_event_code: Optional[str]
    playoff_type: PlayoffType
    webcasts: List[Webcast]
    remap_teams: Dict[TeamKey, TeamKey]


class JSONEventInfoParser:
    @staticmethod
    def parse(info_json: AnyStr) -> EventInfoParsed:
        # pyre validation doesn't support non-total TypedDict
        info_dict = safe_json.loads(info_json, EventInfoInput, validate=False)

        parsed_info: EventInfoParsed = {}
        if "webcasts" in info_dict:
            webcast_list: List[Webcast] = []
            for webcast in info_dict["webcasts"]:
                if "url" in webcast:
                    parsed_webcast = WebcastParser.webcast_dict_from_url(webcast["url"])
                    if not parsed_webcast:
                        raise ParserInputException(
                            f"Unknown webcast url {webcast['url']}!"
                        )
                    webcast_list.append(parsed_webcast)
                elif "type" in webcast and "channel" in webcast:
                    webcast_list.append(
                        Webcast(
                            type=webcast["type"],
                            channel=webcast["channel"],
                        )
                    )
            parsed_info["webcasts"] = webcast_list

        if "remap_teams" in info_dict:
            for temp_team, remapped_team in info_dict["remap_teams"].items():
                temp_match = re.match(r"frc\d+", str(temp_team))
                remapped_match = re.match(r"frc\d+[B-Z]?", str(remapped_team))
                if not temp_match or (
                    temp_match and (temp_match.group(0) != str(temp_team))
                ):
                    raise ParserInputException(
                        "Bad team: '{}'. Must follow format 'frcXXX'.".format(temp_team)
                    )
                if not remapped_match or (
                    remapped_match and (remapped_match.group(0) != str(remapped_team))
                ):
                    raise ParserInputException(
                        "Bad team: '{}'. Must follow format 'frcXXX' or 'frcXXX[B-Z]'.".format(
                            remapped_team
                        )
                    )
            parsed_info["remap_teams"] = info_dict["remap_teams"]

        if "playoff_type" in info_dict:
            if info_dict["playoff_type"] not in PlayoffType._value2member_map_:
                raise ParserInputException(
                    f"Bad playoff type: {info_dict['playoff_type']}"
                )
            parsed_info["playoff_type"] = PlayoffType(info_dict["playoff_type"])

        if "first_event_code" in info_dict:
            parsed_info["first_event_code"] = info_dict["first_event_code"]

        return parsed_info
