from pyre_extensions import safe_json

from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.models.keys import TeamKey
from backend.common.models.team import Team


class JSONTeamListParser:
    """
    Take a json-formatted list of team keys
    """

    @staticmethod
    def parse[T: (str, bytes)](team_list_json: T) -> list[TeamKey]:
        team_keys = safe_json.loads(team_list_json, list[str])
        bad_team_keys = [key for key in team_keys if not Team.validate_key_name(key)]
        if bad_team_keys:
            raise ParserInputException(f"Invalid team keys provided: {bad_team_keys}")

        return team_keys
