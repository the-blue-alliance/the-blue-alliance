from backend.common.helpers.insights_v2.blue_banners import BlueBannersV2Calculator
from backend.common.helpers.insights_v2.compute import compute_insights_for_year
from backend.common.models.insight_v2 import InsightCategory


def test_no_events_returns_empty(ndb_stub) -> None:
    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])
    assert insights == []


def test_blue_banners_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "blue_banners"
    assert insight.display_name == "Total Blue Banners"
    assert insight.year == 2024
    assert insight.category == InsightCategory.LEADERBOARD
    assert insight.data["key_type"] == "team"
    rankings = insight.data["rankings"]
    assert len(rankings) > 0
    # All values should be positive integers
    for r in rankings:
        assert r["value"] > 0
        assert len(r["keys"]) > 0


def test_blue_banners_overall(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "../data/2019nyny_awards.json")

    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(0, [BlueBannersV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.year == 0
    # frc1796 wins at both 2019nyny and 2024nytr so should have 2 banners overall
    rankings = insight.data["rankings"]
    top = rankings[0]
    assert top["value"] == 2
    assert "frc1796" in top["keys"]


def test_blue_banners_rankings_sorted_descending(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "../data/2019nyny_awards.json")

    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(0, [BlueBannersV2Calculator()])
    rankings = insights[0].data["rankings"]

    values = [r["value"] for r in rankings]
    assert values == sorted(values, reverse=True)


def test_blue_banners_team_keys_sorted_numerically(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])
    rankings = insights[0].data["rankings"]

    for ranking in rankings:
        keys = ranking["keys"]
        nums = [int(k[3:]) for k in keys]
        assert nums == sorted(nums)


def test_key_name(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])
    assert insights[0].key_name == "2024_v2_leaderboard_blue_banners"
