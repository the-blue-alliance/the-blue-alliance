from typing import List, Union

from backend.common.models.team import Team


class TeamHelper(object):
    @classmethod
    def sortTeams(cls, team_list: List[Union[Team, None]]) -> List[Team]:
        """
        Takes a list of Teams (not a Query object).
        """
        filtered = filter(None, team_list)
        sorted_list = sorted(filtered, key=lambda team: team.team_number)

        return list(sorted_list)
