from typing import Dict, List

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.team import Team
from backend.common.queries.dict_converters.converter_base import ConverterBase


class TeamConverter(ConverterBase):
    # SUBVERSIONS = {  # Increment every time a change to the dict is made
    #     3: 4,
    # }  # TODO: used for cache clearing

    def _convert_list(
        self, model_list: List[Team], version: ApiMajorVersion
    ) -> List[Dict]:
        CONVERTERS = {
            ApiMajorVersion.API_V3: self.teamsConverter_v3,
        }
        return CONVERTERS[version](model_list)

    def teamsConverter_v3(self, teams: List[Team]) -> List[Dict]:
        return list(map(self.teamConverter_v3, teams))

    def teamConverter_v3(self, team: Team) -> Dict:
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

    @staticmethod
    def dictToModel_v3(data: Dict) -> Team:
        team = Team(id=data["key"])
        team.team_number = data["team_number"]
        team.nickname = data["nickname"]
        team.name = data["name"]
        team.website = data["website"]
        team.rookie_year = data["rookie_year"]
        team.motto = data["motto"]
        team.city = data["city"]
        team.state_prov = data["state_prov"]
        team.country = data["country"]
        team.school_name = data["school_name"]
        return team
