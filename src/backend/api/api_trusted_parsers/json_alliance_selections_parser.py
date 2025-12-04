from pyre_extensions import safe_json

from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.models.alliance import EventAlliance
from backend.common.models.keys import TeamKey
from backend.common.models.team import Team


class JSONAllianceSelectionsParser:
    @staticmethod
    def parse[T: (str, bytes)](alliances_json: T) -> list[EventAlliance]:
        """
        Parse JSON that contains team_keys
        Format is as follows:
        [[captain1, pick1-1, pick1-2(, ...)],
        ['frc254', 'frc971', 'frc604'],
        ...
        [captain8, pick8-1, pick8-2(, ...)]]
        """
        alliances = safe_json.loads(alliances_json, list[list[TeamKey]])

        alliance_selections: list[EventAlliance] = []
        for alliance in alliances:
            if not alliance:
                continue

            for team_key in alliance:
                if not Team.validate_key_name(team_key):
                    raise ParserInputException(
                        f"Bad team_key: '{team_key}'. Must follow format: 'frcXXX'"
                    )

            alliance_selections.append({"picks": list(alliance), "declines": []})

        return alliance_selections
