import time
from typing import Dict, List

from backend.common.consts.alliance_color import ALLIANCE_COLORS
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.match import Match
from backend.common.queries.dict_converters.converter_base import ConverterBase


class MatchConverter(ConverterBase):
    # SUBVERSIONS = {  # Increment every time a change to the dict is made
    #     3: 6,
    # }
    # TODO: use for cache clearing

    @classmethod
    def _convert_list(
        cls, matches: List[Match], version: ApiMajorVersion
    ) -> List[Dict]:
        CONVERTERS = {
            ApiMajorVersion.API_V3: cls.matchesConverter_v3,
        }
        return CONVERTERS[version](matches)

    @classmethod
    def matchesConverter_v3(cls, matches: List[Match]) -> List[Dict]:
        return list(map(cls.matchConverter_v3, matches))

    @classmethod
    def matchConverter_v3(cls, match: Match) -> Dict:
        alliances = {}
        for alliance in ALLIANCE_COLORS:
            alliances[alliance] = {
                "team_keys": match.alliances[alliance]["teams"],
                "surrogate_team_keys": match.alliances[alliance]["surrogates"],
                "dq_team_keys": match.alliances[alliance]["dqs"]
                if "dqs" in match.alliances[alliance]
                else [],
            }

        match_dict = {
            "key": match.key.id(),
            "event_key": match.event.id(),
            "comp_level": match.comp_level,
            "set_number": match.set_number,
            "match_number": match.match_number,
            "alliances": match.alliances,
            "winning_alliance": match.winning_alliance,
            "score_breakdown": match.score_breakdown,
            "videos": match.videos,
        }
        if match.time is not None:
            match_dict["time"] = int(time.mktime(match.time.timetuple()))
        else:
            match_dict["time"] = None
        if match.actual_time is not None:
            match_dict["actual_time"] = int(time.mktime(match.actual_time.timetuple()))
        else:
            match_dict["actual_time"] = None
        if match.predicted_time is not None:
            match_dict["predicted_time"] = int(
                time.mktime(match.predicted_time.timetuple())
            )
        else:
            match_dict["predicted_time"] = None
        if match.post_result_time is not None:
            match_dict["post_result_time"] = int(
                time.mktime(match.post_result_time.timetuple())
            )
        else:
            match_dict["post_result_time"] = None

        return match_dict
