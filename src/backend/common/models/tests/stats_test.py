from backend.common.models.stats import EventMatchStats, StatType


def test_stat_type_values() -> None:
    assert StatType.OPR == "oprs"
    assert StatType.DPR == "dprs"
    assert StatType.CCWM == "ccwms"


def test_event_match_stats() -> None:
    stats: EventMatchStats = {StatType.OPR: {"254": 12.5}}
    assert stats[StatType.OPR]["254"] == 12.5
