from typing import List, NotRequired, TypedDict

from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.common.models.keys import TeamKey


class RegionalPoolRanking(TypedDict):
    rank: int
    team_key: TeamKey
    point_total: int
    rookie_bonus: int
    single_event_bonus: int
    adjustments: NotRequired[int]
    event_points: List[TeamAtEventDistrictPoints]
