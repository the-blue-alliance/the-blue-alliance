from typing import Any, Dict, List, NamedTuple, Optional


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


def get_auto_points(match_alliance: MatchAlliancePoints) -> Optional[int]:
    if match_alliance.breakdown is None:
        return None
    bd = match_alliance.breakdown
    if "autoPoints" in bd:
        return int(bd["autoPoints"])
    if "totalAutoPoints" in bd:
        return int(bd["totalAutoPoints"])
    return None


def get_teleop_points(match_alliance: MatchAlliancePoints) -> Optional[int]:
    if match_alliance.breakdown is None:
        return None
    bd = match_alliance.breakdown
    if "teleopPoints" in bd:
        return int(bd["teleopPoints"])
    if "totalTeleopPoints" in bd:
        return int(bd["totalTeleopPoints"])
    return None


_ENDGAME_KEYS: Dict[int, List[str]] = {
    2016: ["teleopChallengePoints", "teleopScalePoints"],
    2017: ["teleopTakeoffPoints"],
    2018: ["endgamePoints"],
    2019: ["habClimbPoints"],
    2020: ["endgamePoints"],
    2021: ["endgamePoints"],
    2022: ["endgamePoints"],
    2023: ["endGameChargeStationPoints", "endGameParkPoints"],
    2024: ["endGameTotalStagePoints"],
    2025: ["endGameBargePoints"],
    2026: ["endGameTowerPoints"],
}


def get_coral_count(match_alliance: MatchAlliancePoints) -> Optional[int]:
    if match_alliance.breakdown is None or match_alliance.year != 2025:
        return None
    bd = match_alliance.breakdown
    auto = bd.get("autoCoralCount")
    teleop = bd.get("teleopCoralCount")
    if auto is None or teleop is None:
        return None
    return int(auto) + int(teleop)


def get_fuel_count(match_alliance: MatchAlliancePoints) -> Optional[int]:
    if match_alliance.breakdown is None or match_alliance.year != 2026:
        return None
    hub = match_alliance.breakdown.get("hubScore")
    if hub is None:
        return None
    total = hub.get("totalCount")
    if total is None:
        return None
    return int(total)


def get_endgame_points(match_alliance: MatchAlliancePoints) -> Optional[int]:
    if match_alliance.breakdown is None:
        return None
    keys = _ENDGAME_KEYS.get(match_alliance.year)
    if keys is None:
        return None
    return sum(int(match_alliance.breakdown.get(k, 0)) for k in keys)
