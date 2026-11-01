import numpy as np

from backend.common.consts.event_type import EventType
from backend.common.helpers.predictions_v2.model.bonus import (
    rule_met,
    RuleBonusModel,
    tier_of,
)
from backend.common.helpers.predictions_v2.model.config import DEFAULT_CONFIG


def test_tier_of() -> None:
    assert tier_of("2024txhou", EventType.CMP_DIVISION) == "cmp"
    assert tier_of("2024cmptx", EventType.CMP_FINALS) == "cmp"
    assert tier_of("2024txcmp", EventType.DISTRICT_CMP) == "dcmp"
    assert tier_of("2024txcmp1", EventType.DISTRICT_CMP_DIVISION) == "dcmp"
    assert tier_of("2024casj", EventType.REGIONAL) == "reg"
    assert tier_of("2024cafr", EventType.DISTRICT) == "reg"
    assert tier_of("2024cmp", EventType.FOC) == "cmp"
    assert tier_of("2024foc", EventType.FOC) == "reg"


def test_rule_met_uses_the_tier_threshold() -> None:
    bd = {
        "autoAmpNoteCount": 2,
        "autoSpeakerNoteCount": 4,
        "teleopAmpNoteCount": 4,
        "teleopSpeakerNoteCount": 5,
        "teleopSpeakerNoteAmplifiedCount": 4,
        "coopertitionBonusAchieved": False,
        "endGameTotalStagePoints": 0,
    }
    assert rule_met(2024, "reg", bd, {})["rp_1"] == 1  # 19 notes >= 18
    assert rule_met(2024, "cmp", bd, {})["rp_1"] == 0  # 19 notes < 25
    assert (
        rule_met(2024, "cmp", {**bd, "coopertitionBonusAchieved": True}, {})["rp_1"]
        == 0
    )
    assert (
        rule_met(2024, "dcmp", {**bd, "coopertitionBonusAchieved": True}, {})["rp_1"]
        == 1
    )


def test_rule_probabilities_need_channel_data() -> None:
    m = RuleBonusModel(DEFAULT_CONFIG)
    m.reset_season(2017)
    assert m.supported()
    red, blue = ["frc1", "frc2", "frc3"], ["frc4", "frc5", "frc6"]
    extra = np.zeros(5)
    assert m.probs(["rp_1", "rp_2"], "reg", red, blue, extra, None) == {
        "rp_1": None,
        "rp_2": None,
    }

    bd = {
        "autoFuelPoints": 10,
        "teleopFuelPoints": 35,
        "rotor1Engaged": True,
        "rotor2Engaged": True,
    }
    for _ in range(5):
        m.update(
            "reg",
            red,
            blue,
            bd,
            bd,
            {"rp_1": 1, "rp_2": 0},
            {"rp_1": 1, "rp_2": 0},
            extra,
            extra,
            None,
        )
    probs = m.probs(["rp_1", "rp_2"], "reg", red, blue, extra, None)
    p1, p2 = probs["rp_1"], probs["rp_2"]
    assert p1 is not None and p2 is not None
    assert p1 > p2

    m.reset_season(2015)
    assert not m.supported()
