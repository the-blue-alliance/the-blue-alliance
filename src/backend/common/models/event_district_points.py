from typing import Dict, List

from typing_extensions import TypedDict

from backend.common.models.keys import TeamKey


class TeamAtEventDistrictPoints(TypedDict):
    qual_points: int
    elim_points: int
    alliance_points: int
    award_points: int
    total: int


class TeamAtEventDistrictPointTiebreakers(TypedDict):
    qual_wins: int
    highest_qual_scores: List[int]


class EventDistrictPoints(TypedDict):
    points: Dict[TeamKey, TeamAtEventDistrictPoints]
    tiebreakers: Dict[TeamKey, TeamAtEventDistrictPointTiebreakers]
