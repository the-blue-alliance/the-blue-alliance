"""Per-season scoring rules read from the TBA score breakdown, taken from the game manuals.

* Robot points: points that one robot earns alone (auto mobility, endgame climb or park).
  The breakdown records them per driver station, and station N is the Nth team of the
  alliance.
* Score components: the breakdown fields that add up to the alliance score, with the point
  step of each field (the gcd of the point values the field can hold). A component that only
  scores in playoffs is marked ``playoff_only``.

Seasons without an entry run without that part of the model. Add the entries for each new
game at kickoff (see docs/Developing/Predictions-v2.md).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from backend.common.helpers.predictions_v2.model.types import AllianceBreakdown
from backend.common.models.keys import Year

# (field template, {value: points}). "{n}" is the 1-based station number.
_ROBOT_POINTS: Dict[Year, List[Tuple[str, Dict[str, int]]]] = {
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
    2026: [
        ("autoTowerRobot{n}", {"Level1": 15}),
        ("endGameTowerRobot{n}", {"Level1": 10, "Level2": 20, "Level3": 30}),
    ],
}

ROBOT_POINT_SEASONS = frozenset(_ROBOT_POINTS)


@dataclass(frozen=True)
class ScoreComponent:
    # Breakdown field. A dotted name reads a nested field ("hubScore.totalPoints").
    field: str
    step: int
    playoff_only: bool = False


SCORE_COMPONENTS: Dict[Year, Tuple[ScoreComponent, ...]] = {
    2016: (
        ScoreComponent("autoReachPoints", 2),
        ScoreComponent("autoCrossingPoints", 10),
        ScoreComponent("autoBoulderPoints", 5),  # low 5, high 10
        ScoreComponent("teleopCrossingPoints", 5),
        ScoreComponent("teleopBoulderPoints", 1),  # low 2, high 5
        ScoreComponent("teleopChallengePoints", 5),
        ScoreComponent("teleopScalePoints", 15),
        ScoreComponent("breachPoints", 20, playoff_only=True),
        ScoreComponent("capturePoints", 25, playoff_only=True),
        ScoreComponent("foulPoints", 5),
    ),
    2017: (
        ScoreComponent("autoMobilityPoints", 5),
        ScoreComponent("autoFuelPoints", 1),
        ScoreComponent("autoRotorPoints", 60),
        ScoreComponent("teleopFuelPoints", 1),
        ScoreComponent("teleopRotorPoints", 40),
        ScoreComponent("teleopTakeoffPoints", 50),
        ScoreComponent("kPaBonusPoints", 20, playoff_only=True),
        ScoreComponent("rotorBonusPoints", 100, playoff_only=True),
        ScoreComponent("foulPoints", 5),
    ),
    2018: (
        ScoreComponent("autoRunPoints", 5),
        ScoreComponent("autoOwnershipPoints", 2),
        ScoreComponent("teleopOwnershipPoints", 1),
        ScoreComponent("vaultPoints", 5),
        ScoreComponent("endgamePoints", 5),  # park 5, climb 30
        ScoreComponent("foulPoints", 5),
    ),
    2019: (
        ScoreComponent("sandStormBonusPoints", 3),  # level 1: 3, level 2: 6
        ScoreComponent("hatchPanelPoints", 2),
        ScoreComponent("cargoPoints", 3),
        ScoreComponent("habClimbPoints", 3),  # 3, 6, 12
        ScoreComponent("foulPoints", 1),  # foul 3, tech foul 10
    ),
    2020: (
        ScoreComponent("autoInitLinePoints", 5),
        ScoreComponent("autoCellPoints", 2),  # bottom 2, outer 4, inner 6
        ScoreComponent("teleopCellPoints", 1),  # bottom 1, outer 2, inner 3
        ScoreComponent("controlPanelPoints", 10),  # rotation 10, position 20
        ScoreComponent("endgamePoints", 5),  # park 5, hang 25, level 15
        ScoreComponent("foulPoints", 3),  # foul 3, tech foul 15
    ),
    2022: (
        ScoreComponent("autoTaxiPoints", 2),
        ScoreComponent("autoCargoPoints", 2),  # lower 2, upper 4
        ScoreComponent("teleopCargoPoints", 1),  # lower 1, upper 2
        ScoreComponent("endgamePoints", 1),  # 4, 6, 10, 15
        ScoreComponent("foulPoints", 4),  # foul 4, tech foul 8
    ),
    2023: (
        ScoreComponent("autoMobilityPoints", 3),
        ScoreComponent("autoGamePiecePoints", 1),  # 3, 4, 6
        ScoreComponent("autoChargeStationPoints", 4),  # docked 8, engaged 12
        ScoreComponent("teleopGamePiecePoints", 1),  # 2, 3, 5
        ScoreComponent("linkPoints", 5),
        ScoreComponent("endGameChargeStationPoints", 2),  # docked 6, engaged 10
        ScoreComponent("endGameParkPoints", 2),
        ScoreComponent("foulPoints", 1),  # foul 5, tech foul 12
    ),
    2024: (
        ScoreComponent("autoLeavePoints", 2),
        ScoreComponent("autoAmpNotePoints", 2),
        ScoreComponent("autoSpeakerNotePoints", 5),
        ScoreComponent("teleopAmpNotePoints", 1),
        ScoreComponent("teleopSpeakerNotePoints", 2),
        ScoreComponent("teleopSpeakerNoteAmplifiedPoints", 5),
        ScoreComponent("endGameParkPoints", 1),
        ScoreComponent("endGameOnStagePoints", 3),
        ScoreComponent("endGameSpotLightBonusPoints", 1),
        ScoreComponent("endGameHarmonyPoints", 2),
        ScoreComponent("endGameNoteInTrapPoints", 5),
        ScoreComponent("foulPoints", 1),  # foul 2, tech foul 5
    ),
    2025: (
        ScoreComponent("autoMobilityPoints", 3),
        ScoreComponent("autoCoralPoints", 1),  # 3, 4, 6, 7
        ScoreComponent("teleopCoralPoints", 1),  # 2, 3, 4, 5
        ScoreComponent("algaePoints", 2),  # processor 6, net 4
        ScoreComponent("endGameBargePoints", 2),  # park 2, shallow 6, deep 12
        ScoreComponent("foulPoints", 2),  # minor 2, major 6
    ),
    2026: (
        ScoreComponent("hubScore.totalPoints", 1),
        ScoreComponent("autoTowerPoints", 15),
        ScoreComponent("endGameTowerPoints", 10),  # 10, 20, 30
        ScoreComponent("foulPoints", 5),  # minor 5, major 15
    ),
}


def component_value(breakdown: AllianceBreakdown, name: str) -> Any:
    """The value of a (possibly dotted) breakdown field, or None if it is missing."""
    value: Any = breakdown
    for part in name.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _points_2019_sandstorm(b: AllianceBreakdown, n: int) -> Optional[float]:
    line = b.get(f"habLineRobot{n}")
    lvl = b.get(f"preMatchLevelRobot{n}")
    if line is None or lvl is None:
        return None
    if line != "CrossedHabLineInSandstorm":
        return 0.0
    return {"HabLevel1": 3.0, "HabLevel2": 6.0}.get(str(lvl), 0.0)


def first_auto_docked_2023(b: AllianceBreakdown) -> Optional[int]:
    """The station credited with the 2023 auto charge station points.

    FMS awards the auto DOCKED/ENGAGED points once per alliance, even when more than one
    robot docks, so they go to the first docked station.
    """
    for n in (1, 2, 3):
        if b.get(f"autoChargeStationRobot{n}") == "Docked":
            return n
    return None


def _points_2023_charge(b: AllianceBreakdown, n: int) -> Optional[float]:
    a = b.get(f"autoChargeStationRobot{n}")
    e = b.get(f"endGameChargeStationRobot{n}")
    if a is None or e is None:
        return None
    pts = 0.0
    if a == "Docked" and first_auto_docked_2023(b) == n:
        pts += 12.0 if b.get("autoBridgeState") == "Level" else 8.0
    if e == "Docked":
        pts += 10.0 if b.get("endGameBridgeState") == "Level" else 6.0
    elif e == "Park":
        pts += 2.0
    return pts


def robot_points(
    season: Year, breakdown: Optional[AllianceBreakdown], n_robots: int
) -> Optional[List[float]]:
    """Points per station, or None if the season or the data is not supported."""
    if season not in _ROBOT_POINTS or not breakdown:
        return None
    out: List[float] = []
    for n in range(1, n_robots + 1):
        pts = 0.0
        for tmpl, table in _ROBOT_POINTS[season]:
            v = breakdown.get(tmpl.format(n=n))
            if v is None:
                return None
            pts += float(table.get(str(v), 0))
        if season == 2019:
            extra = _points_2019_sandstorm(breakdown, n)
            if extra is None:
                return None
            pts += extra
        if season == 2023:
            extra = _points_2023_charge(breakdown, n)
            if extra is None:
                return None
            pts += extra
        out.append(pts)
    return out


def foul_points(breakdown: Optional[AllianceBreakdown]) -> Optional[float]:
    """Points this alliance received from opponent fouls."""
    if not breakdown:
        return None
    v = breakdown.get("foulPoints", breakdown.get("foul_points"))
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def playoff_bonus_points(
    season: Optional[Year], breakdown: Optional[AllianceBreakdown], is_qual: bool
) -> float:
    """Points awarded only for the 2016 and 2017 playoff threshold bonuses."""
    if is_qual or not breakdown or season not in (2016, 2017):
        return 0.0
    if season == 2016:
        return float(
            (breakdown.get("breachPoints") or 0.0)
            + (breakdown.get("capturePoints") or 0.0)
        )
    return float(
        (breakdown.get("kPaBonusPoints") or 0.0)
        + (breakdown.get("rotorBonusPoints") or 0.0)
    )
