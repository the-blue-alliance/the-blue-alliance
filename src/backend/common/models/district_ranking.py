from typing import List

from typing_extensions import TypedDict

from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.common.models.keys import TeamKey


class DistrictRanking(TypedDict):
    rank: int
    team_key: TeamKey
    point_toal: int
    rookie_bonus: int
    event_points: List[TeamAtEventDistrictPoints]
