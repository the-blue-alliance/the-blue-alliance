from typing import Dict, List, TypedDict

from backend.common.models.keys import EventKey, TeamKey


class _TeamAtEventDistrictPointsOptional(TypedDict, total=False):
    """
    DistrictHelper's calulation code does not set these, they're added
    in elsewhere.
    """

    event_key: EventKey
    district_cmp: bool


class TeamAtEventDistrictPoints(_TeamAtEventDistrictPointsOptional):
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
