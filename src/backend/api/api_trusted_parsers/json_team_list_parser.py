from typing import AnyStr, List

from pyre_extensions import safe_json

from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.models.keys import TeamKey
from backend.common.models.team import Team


class JSONTeamListParser:
    """
    Take a json-formatted list of team keys
    """

    @staticmethod
    def parse(team_list_json: AnyStr) -> List[TeamKey]:
        team_keys = safe_json.loads(team_list_json, List[str])
        bad_team_keys = list(
            filter(lambda team_key: not Team.validate_key_name(team_key), team_keys)
        )
        if bad_team_keys:
            raise ParserInputException(f"Invalid team keys provided: {bad_team_keys}")

        return team_keys
