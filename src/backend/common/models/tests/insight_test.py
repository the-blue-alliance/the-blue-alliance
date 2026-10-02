import json

from backend.common.models.insight import Insight


def test_render_key_name() -> None:
    assert (
        Insight.render_key_name(2020, "matches_played") == "2020insights_matches_played"
    )
    assert Insight.render_key_name(0, "matches_played") == "insights_matches_played"
    assert (
        Insight.render_key_name(2020, "matches_played", "ne")
        == "2020insights_matches_played_ne"
    )


def test_key_name() -> None:
    insight = Insight(
        name="matches_played",
        year=2020,
        data_json=json.dumps({"count": 1}),
    )
    assert insight.key_name == "2020insights_matches_played"
    assert insight.data == {"count": 1}


def test_key_name_with_district() -> None:
    insight = Insight(
        name="matches_played",
        year=0,
        district_abbreviation="ne",
        data_json=json.dumps({}),
    )
    assert insight.key_name == "insights_matches_played_ne"
