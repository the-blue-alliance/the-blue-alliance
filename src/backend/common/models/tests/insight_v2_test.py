from backend.common.models.insight_v2 import InsightCategory, InsightV2


def test_render_key_name_with_year() -> None:
    assert (
        InsightV2.render_key_name(2026, InsightCategory.LEADERBOARD, "blue_banners")
        == "2026_v2_leaderboard_blue_banners"
    )


def test_render_key_name_all_time() -> None:
    assert (
        InsightV2.render_key_name(0, InsightCategory.LEADERBOARD, "blue_banners")
        == "0_v2_leaderboard_blue_banners"
    )


def test_render_key_name_with_district() -> None:
    assert (
        InsightV2.render_key_name(
            2026, InsightCategory.LEADERBOARD, "blue_banners", "ne"
        )
        == "2026_v2_leaderboard_blue_banners_ne"
    )


def test_key_name_property(ndb_stub) -> None:
    insight = InsightV2(
        id=InsightV2.render_key_name(2026, InsightCategory.LEADERBOARD, "blue_banners"),
        name="blue_banners",
        display_name="Total Blue Banners",
        year=2026,
        category=InsightCategory.LEADERBOARD,
        data_json={"rankings": [], "key_type": "team"},
    )
    assert insight.key_name == "2026_v2_leaderboard_blue_banners"


def test_data_property(ndb_stub) -> None:
    insight = InsightV2(
        id=InsightV2.render_key_name(2026, InsightCategory.LEADERBOARD, "blue_banners"),
        name="blue_banners",
        display_name="Total Blue Banners",
        year=2026,
        category=InsightCategory.LEADERBOARD,
        data_json={"rankings": [{"keys": ["frc1"], "value": 5}], "key_type": "team"},
    )
    assert insight.data["rankings"] == [{"keys": ["frc1"], "value": 5}]
    assert insight.data["key_type"] == "team"
