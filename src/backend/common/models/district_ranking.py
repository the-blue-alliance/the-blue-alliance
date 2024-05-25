from typing import List, TypedDict

from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.common.models.keys import TeamKey


class _DistrictRankingOptional(TypedDict, total=False):
    other_bonus: int


class DistrictRanking(_DistrictRankingOptional):
    rank: int
    team_key: TeamKey
    point_total: int
    rookie_bonus: int
    event_points: List[TeamAtEventDistrictPoints]
