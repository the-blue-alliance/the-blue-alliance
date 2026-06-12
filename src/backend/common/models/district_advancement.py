from typing import Dict, TypedDict

from backend.common.models.keys import TeamKey


class TeamDistrictAdvancement(TypedDict):
    dcmp: bool
    cmp: bool


DistrictAdvancement = Dict[TeamKey, TeamDistrictAdvancement]


class AdvancementCounts(TypedDict):
    dcmp: int
    cmp: int


class ApiDistrictRankingTeamData(TypedDict):
    rank: int
    total_points: int
    team_age_points: int
    event1_code: str | None
    event1_points: int | None
    event2_code: str | None
    event2_points: int | None
    district_cmp_code: str | None
    district_cmp_points: int | None
