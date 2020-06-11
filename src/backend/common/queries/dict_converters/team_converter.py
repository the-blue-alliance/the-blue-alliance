from typing import List

from backend.common.models.team import Team
from backend.common.queries.dict_converters.converter_base import ConverterBase


class TeamConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 4,
    }

    def _convert_list(self, model_list: List[Team], version: int) -> List[dict]:
        CONVERTERS = {
            3: self.teamsConverter_v3,
        }
        return CONVERTERS[version](model_list)

    def teamsConverter_v3(self, teams: List[Team]) -> List[dict]:
        return list(map(self.teamConverter_v3, teams))

    def teamConverter_v3(self, team: Team) -> dict:
        default_name = "Team {}".format(team.team_number)
        team_dict = {
            "key": team.key.id(),
            "team_number": team.team_number,
            "nickname": team.nickname if team.nickname else default_name,
            "name": team.name if team.name else default_name,
            "website": team.website,
            "rookie_year": team.rookie_year,
            "motto": None,
            # "home_championship": team.championship_location,  # TODO: event not ported yet
            "school_name": team.school_name,
        }
        team_dict.update(self.constructLocation_v3(team))
        return team_dict
