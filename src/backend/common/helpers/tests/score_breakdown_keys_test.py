from backend.common.helpers.score_breakdown_keys import ScoreBreakdownKeys


def test_get_valid_score_breakdown_keys_known_year() -> None:
    keys = ScoreBreakdownKeys.get_valid_score_breakdown_keys(2025)

    assert "totalPoints" in keys
    assert len(keys) > 0


def test_get_valid_score_breakdown_keys_unknown_year() -> None:
    assert ScoreBreakdownKeys.get_valid_score_breakdown_keys(1999) == set()
