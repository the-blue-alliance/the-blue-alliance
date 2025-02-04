from typing import List, TypedDict

from backend.common.models.event_district_points import TeamAtEventDistrictPoints


class RegionalPoolRanking(TypedDict):
    point_total: int
    rookie_bonus: int
    event_points: List[TeamAtEventDistrictPoints]
