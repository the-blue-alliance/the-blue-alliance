from typing import Any, Dict, NamedTuple, Optional


class MatchAlliancePoints(NamedTuple):
    score: int
    breakdown: Optional[Dict[str, Any]]
    year: int


def get_total_points(match_alliance: MatchAlliancePoints) -> int:
    return match_alliance.score


def get_foul_points(match_alliance: MatchAlliancePoints) -> int:
    if match_alliance.breakdown is None:
        return 0
    return int(match_alliance.breakdown.get("foulPoints", 0))
