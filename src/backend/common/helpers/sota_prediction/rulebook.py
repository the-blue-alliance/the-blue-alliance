"""Rulebook tables: per-robot point attribution by season.

Each FRC game awards some points to a single robot and records the achievement
per driver station in the TBA score breakdown. Station N in the breakdown maps to
the Nth team key of the alliance. The tables below give the point value of each
recorded per-robot state, taken from the game manuals.

Points that depend on an alliance-level state (for example the 2023 charge
station "engaged" bonus) use the alliance field to pick the value.
Alliance-level achievements that the breakdown assigns to one station but that
no robot performs alone (2018 Levitate) are excluded and stay in the shared part.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

# (field template, {value: points}); "{n}" is the 1-based station number.
_SIMPLE: Dict[int, List[tuple]] = {
    2016: [("robot{n}Auto", {"Reached": 2, "Crossed": 10})],
    2017: [("robot{n}Auto", {"Mobility": 5})],
    2018: [
        ("autoRobot{n}", {"AutoRun": 5}),
        ("endgameRobot{n}", {"Parking": 5, "Climbing": 30}),
    ],
    2019: [("endgameRobot{n}", {"HabLevel1": 3, "HabLevel2": 6, "HabLevel3": 12})],
    2020: [
        ("initLineRobot{n}", {"Exited": 5}),
        ("endgameRobot{n}", {"Park": 5, "Hang": 25}),
    ],
    2022: [
        ("taxiRobot{n}", {"Yes": 2}),
        ("endgameRobot{n}", {"Low": 4, "Mid": 6, "High": 10, "Traversal": 15}),
    ],
    2023: [("mobilityRobot{n}", {"Yes": 3})],
    2024: [
        ("autoLineRobot{n}", {"Yes": 2}),
        (
            "endGameRobot{n}",
            {"Parked": 1, "StageLeft": 3, "StageRight": 3, "CenterStage": 3},
        ),
    ],
    2025: [
        ("autoLineRobot{n}", {"Yes": 3}),
        ("endGameRobot{n}", {"Parked": 2, "ShallowCage": 6, "DeepCage": 12}),
    ],
    # 2026 REBUILT, Game Manual TU22 Table 6-4.
    2026: [
        ("autoTowerRobot{n}", {"Level1": 15}),
        ("endGameTowerRobot{n}", {"Level1": 10, "Level2": 20, "Level3": 30}),
    ],
}

SUPPORTED_SEASONS = frozenset(_SIMPLE)


def _points_2019_sandstorm(b: Mapping[str, Any], n: int) -> Optional[float]:
    line = b.get(f"habLineRobot{n}")
    lvl = b.get(f"preMatchLevelRobot{n}")
    if line is None or lvl is None:
        return None
    if line != "CrossedHabLineInSandstorm":
        return 0.0
    return {"HabLevel1": 3.0, "HabLevel2": 6.0}.get(str(lvl), 0.0)


def _points_2023_charge(b: Mapping[str, Any], n: int) -> Optional[float]:
    a = b.get(f"autoChargeStationRobot{n}")
    e = b.get(f"endGameChargeStationRobot{n}")
    if a is None or e is None:
        return None
    pts = 0.0
    if a == "Docked":
        pts += 12.0 if b.get("autoBridgeState") == "Level" else 8.0
    if e == "Docked":
        pts += 10.0 if b.get("endGameBridgeState") == "Level" else 6.0
    elif e == "Park":
        pts += 2.0
    return pts


def robot_points(
    season: int, alliance_breakdown: Optional[Mapping[str, Any]], n_robots: int
) -> Optional[List[float]]:
    """Return per-station robot points, or None if the season or data is unsupported."""
    if season not in _SIMPLE or not alliance_breakdown:
        return None
    b = alliance_breakdown
    out: List[float] = []
    for n in range(1, n_robots + 1):
        pts = 0.0
        for tmpl, table in _SIMPLE[season]:
            v = b.get(tmpl.format(n=n))
            if v is None:
                return None
            pts += float(table.get(str(v), 0))
        if season == 2019:
            extra = _points_2019_sandstorm(b, n)
            if extra is None:
                return None
            pts += extra
        if season == 2023:
            extra = _points_2023_charge(b, n)
            if extra is None:
                return None
            pts += extra
        out.append(pts)
    return out


def foul_points(alliance_breakdown: Optional[Mapping[str, Any]]) -> Optional[float]:
    """Points this alliance received from opponent fouls."""
    if not alliance_breakdown:
        return None
    v = alliance_breakdown.get("foulPoints", alliance_breakdown.get("foul_points"))
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def playoff_bonus_points(
    season: Optional[int],
    alliance_breakdown: Optional[Mapping[str, Any]],
    is_qm: bool = False,
) -> float:
    """Points awarded only for playoff threshold bonuses in 2016 and 2017."""
    if is_qm or not alliance_breakdown or season not in (2016, 2017):
        return 0.0
    if season == 2016:
        return float(
            (alliance_breakdown.get("breachPoints") or 0.0)
            + (alliance_breakdown.get("capturePoints") or 0.0)
        )
    if season == 2017:
        return float(
            (alliance_breakdown.get("kPaBonusPoints") or 0.0)
            + (alliance_breakdown.get("rotorBonusPoints") or 0.0)
        )
    return 0.0
