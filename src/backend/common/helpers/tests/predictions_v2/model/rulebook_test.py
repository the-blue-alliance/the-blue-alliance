import glob
import json
import os
from typing import Any, Dict, List, Tuple

import pytest

from backend.common.helpers.predictions_v2.model.rulebook import (
    component_value,
    foul_points,
    playoff_bonus_points,
    robot_points,
    SCORE_COMPONENTS,
)
from backend.common.models.keys import Year

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _alliance_rows(year: Year) -> List[Tuple[str, Dict[str, Any], int]]:
    """(comp level, breakdown, score) of every played alliance in the year's real event
    fixtures (the synthetic "test" events are skipped)."""
    rows = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, f"{year}*_matches.json"))):
        if "test" in os.path.basename(path):
            continue
        with open(path) as f:
            for m in json.load(f):
                bd = m.get("score_breakdown")
                if not bd:
                    continue
                for color in ("red", "blue"):
                    score = m["alliances"][color]["score"]
                    if score >= 0 and bd.get(color):
                        rows.append((m["comp_level"], bd[color], score))
    return rows


@pytest.mark.parametrize("year", sorted(SCORE_COMPONENTS))
def test_score_components_add_up_to_the_score(year: Year) -> None:
    rows = _alliance_rows(year)
    assert rows, f"no {year} match fixtures"
    components = SCORE_COMPONENTS[year]
    exact = 0
    for comp_level, bd, score in rows:
        values = [component_value(bd, c.field) for c in components]
        assert all(isinstance(v, (int, float)) for v in values), (year, values)
        for c, v in zip(components, values):
            assert v % c.step == 0, (year, c.field, v)
            if c.playoff_only and comp_level == "qm":
                assert v == 0, (year, c.field)
        exact += sum(values) == score
    # Full-season data: 99.2% (2018) to 99.97% (2024) of alliances add up exactly. The
    # rest carry manual score adjustments.
    assert exact / len(rows) >= 0.98, (year, exact, len(rows))


def test_component_value_reads_nested_fields() -> None:
    bd = {"hubScore": {"totalPoints": 12}, "foulPoints": 5}
    assert component_value(bd, "hubScore.totalPoints") == 12
    assert component_value(bd, "foulPoints") == 5
    assert component_value(bd, "hubScore.missing") is None
    assert component_value(bd, "foulPoints.x") is None


def test_robot_points() -> None:
    bd = {
        "autoLineRobot1": "Yes",
        "autoLineRobot2": "No",
        "autoLineRobot3": "Yes",
        "endGameRobot1": "DeepCage",
        "endGameRobot2": "Parked",
        "endGameRobot3": "None",
    }
    assert robot_points(2025, bd, 3) == [15.0, 2.0, 3.0]
    assert robot_points(2025, {"autoLineRobot1": "Yes"}, 3) is None
    assert robot_points(2014, bd, 3) is None
    assert robot_points(2025, None, 3) is None


def test_foul_and_playoff_bonus_points() -> None:
    assert foul_points({"foulPoints": 6}) == 6.0
    assert foul_points({"foul_points": 4}) == 4.0
    assert foul_points({}) is None
    bd = {"breachPoints": 20, "capturePoints": 25}
    assert playoff_bonus_points(2016, bd, is_qual=False) == 45.0
    assert playoff_bonus_points(2016, bd, is_qual=True) == 0.0
    assert playoff_bonus_points(2018, bd, is_qual=False) == 0.0


def test_2023_auto_charge_points_are_credited_once() -> None:
    bd = {
        "mobilityRobot1": "Yes",
        "mobilityRobot2": "Yes",
        "mobilityRobot3": "No",
        "autoChargeStationRobot1": "None",
        "autoChargeStationRobot2": "Docked",
        "autoChargeStationRobot3": "Docked",
        "autoBridgeState": "Level",
        "endGameChargeStationRobot1": "Park",
        "endGameChargeStationRobot2": "Docked",
        "endGameChargeStationRobot3": "None",
        "endGameBridgeState": "NotLevel",
    }
    # Auto: one 12-point engage for the alliance, credited to station 2.
    assert robot_points(2023, bd, 3) == [3.0 + 2.0, 3.0 + 12.0 + 6.0, 0.0]
