from typing import AnyStr, List

from pyre_extensions import safe_json

from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.models.alliance import EventAlliance
from backend.common.models.keys import TeamKey
from backend.common.models.team import Team


class JSONAllianceSelectionsParser:
    @staticmethod
    def parse(alliances_json: AnyStr) -> List[EventAlliance]:
        """
        Parse JSON that contains team_keys
        Format is as follows:
        [[captain1, pick1-1, pick1-2(, ...)],
        ['frc254', 'frc971', 'frc604'],
        ...
        [captain8, pick8-1, pick8-2(, ...)]]
        """
        alliances = safe_json.loads(alliances_json, List[List[TeamKey]])

        alliance_selections: List[EventAlliance] = []
        for alliance in alliances:
            is_empty = True
            selection: EventAlliance = {"picks": [], "declines": []}
            for team_key in alliance:
                if not Team.validate_key_name(team_key):
                    raise ParserInputException(
                        "Bad team_key: '{}'. Must follow format: 'frcXXX'".format(
                            team_key
                        )
                    )
                else:
                    selection["picks"].append(team_key)
                    is_empty = False
            if not is_empty:
                alliance_selections.append(selection)
        return alliance_selections
