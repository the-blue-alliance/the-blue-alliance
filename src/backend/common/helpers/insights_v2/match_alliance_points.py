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


def get_endgame_points(match_alliance: MatchAlliancePoints) -> Optional[int]:
    if match_alliance.breakdown is None:
        return None
    keys = _ENDGAME_KEYS.get(match_alliance.year)
    if keys is None:
        return None
    return sum(int(match_alliance.breakdown.get(k, 0)) for k in keys)


def _sum_required_keys(bd: Dict[str, Any], keys: List[str]) -> Optional[int]:
    # Returns None if any key is missing, so callers can treat that as "not
    # available for this match" rather than silently counting it as zero.
    total = 0
    for key in keys:
        value = bd.get(key)
        if value is None:
            return None
        total += int(value)
    return total


# Game piece breakdown fields, by year. Each entry sums to the number of game
# pieces scored by an alliance in a match (see docstring on get_game_piece_count).
_GAME_PIECE_KEYS: Dict[int, List[str]] = {
    2016: [
        "autoBouldersLow",
        "autoBouldersHigh",
        "teleopBouldersLow",
        "teleopBouldersHigh",
    ],
    2017: ["autoFuelLow", "autoFuelHigh", "teleopFuelLow", "teleopFuelHigh"],
    2020: [
        "autoCellsBottom",
        "autoCellsOuter",
        "autoCellsInner",
        "teleopCellsBottom",
        "teleopCellsOuter",
        "teleopCellsInner",
    ],
    2022: ["matchCargoTotal"],
    2023: ["autoGamePieceCount", "teleopGamePieceCount"],
    2024: [
        "autoAmpNoteCount",
        "autoSpeakerNoteCount",
        "teleopAmpNoteCount",
        "teleopSpeakerNoteCount",
        "teleopSpeakerNoteAmplifiedCount",
    ],
    2025: ["autoCoralCount", "teleopCoralCount"],
}

# 2019 (Deep Space) encodes game pieces as position strings rather than counts:
# each bay/rocket slot holds a string like "Panel", "Cargo", "PanelAndCargo", or
# "None" (as a JSON string, not null).
#
# Every cargo ship bay is preloaded before the match with a single piece: bays
# 1-3 and 6-8 are preloaded with either a Panel or Cargo, at the alliance's
# choice (see preMatchBay1, etc.); bays 4 and 5 are always preloaded with
# Cargo (no choice, and no corresponding preMatchBay field). A preloaded Panel
# isn't a game piece scored during the match, so it's excluded from the count;
# a preloaded Cargo IS counted as if newly scored (only Panels can be
# deliberately preloaded, so any other recorded preload reflects a piece
# added during the match, not a true preload). Rocket slots have no preload,
# so every piece present at the end of the match is counted directly.
#
# This means a bay that starts Cargo and ends PanelAndCargo scores 2 (both
# the Cargo and the Panel are counted), not 1 -- intentional, not a bug.
_2019_CHOSEN_PRELOAD_BAY_NUMBERS: List[int] = [1, 2, 3, 6, 7, 8]
_2019_ROCKET_KEYS: List[str] = [
    f"{level}{lr_side}Rocket{nf_side}"
    for level in ("low", "mid", "top")
    for lr_side in ("Left", "Right")
    for nf_side in ("Near", "Far")
]


def _count_2019_bay_pieces(bd: Dict[str, Any], bay_number: int) -> Optional[int]:
    value = bd.get(f"bay{bay_number}")
    if value is None:
        return None
    count = (1 if "Panel" in value else 0) + (1 if "Cargo" in value else 0)
    if bay_number in _2019_CHOSEN_PRELOAD_BAY_NUMBERS:
        preload = bd.get(f"preMatchBay{bay_number}")
        if preload is None:
            return None
    else:
        preload = "Cargo"  # bays 4 and 5 are always preloaded with Cargo
    if preload == "Panel":
        count -= 1
    return count


def _count_2019_pieces(bd: Dict[str, Any]) -> Optional[int]:
    total = 0
    for bay_number in range(1, 9):
        count = _count_2019_bay_pieces(bd, bay_number)
        if count is None:
            return None
        total += count
    for key in _2019_ROCKET_KEYS:
        value = bd.get(key)
        if value is None:
            return None
        total += (1 if "Panel" in value else 0) + (1 if "Cargo" in value else 0)
    return total


def _count_2026_fuel(bd: Dict[str, Any]) -> Optional[int]:
    # 2026-specific: fuel is a nested count, not a flat breakdown key.
    hub = bd.get("hubScore")
    if hub is None:
        return None
    total = hub.get("totalCount")
    if total is None:
        return None
    return int(total)


def get_game_piece_count(match_alliance: MatchAlliancePoints) -> Optional[int]:
    """
    Returns the number of "game pieces" (in whatever form that year's game
    defines them) scored by this alliance in this match, or None if the year
    isn't supported or the breakdown is missing required fields.
    """
    if match_alliance.breakdown is None:
        return None
    bd = match_alliance.breakdown
    year = match_alliance.year
    if year == 2019:
        return _count_2019_pieces(bd)
    if year == 2026:
        return _count_2026_fuel(bd)
    keys = _GAME_PIECE_KEYS.get(year)
    if keys is None:
        return None
    return _sum_required_keys(bd, keys)
