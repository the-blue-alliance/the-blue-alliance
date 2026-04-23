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


def test_district_insight_created(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2022on305.json")
    test_data_importer.import_award_list(__file__, "../data/2022on305_awards.json")

    insights = compute_insights_for_year(2022, [BlueBannersV2Calculator()])

    # global insight + one district insight
    assert len(insights) == 2
    district_insight = next(i for i in insights if i.district_abbreviation == "ont")
    assert district_insight.year == 2022
    assert district_insight.name == "blue_banners"
    assert district_insight.category == InsightCategory.LEADERBOARD
    assert district_insight.key_name == "2022_v2_leaderboard_blue_banners_ont"
    rankings = district_insight.data["rankings"]
    assert len(rankings) > 0
    # all winner team keys should appear in the district rankings
    winner_keys = {"frc2200", "frc610", "frc4015"}
    ranked_keys = {k for r in rankings for k in r["keys"]}
    assert winner_keys <= ranked_keys


def test_district_insight_excludes_non_district_event_teams(
    ndb_stub, test_data_importer
) -> None:
    # 2024nytr is a regional (no district); 2022on305 is Ontario district
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")
    test_data_importer.import_event(__file__, "../data/2022on305.json")
    test_data_importer.import_award_list(__file__, "../data/2022on305_awards.json")

    insights_2024 = compute_insights_for_year(2024, [BlueBannersV2Calculator()])
    # 2024nytr has no district — only the global insight
    assert all(i.district_abbreviation is None for i in insights_2024)

    insights_2022 = compute_insights_for_year(2022, [BlueBannersV2Calculator()])
    district_insights = [
        i for i in insights_2022 if i.district_abbreviation is not None
    ]
    assert len(district_insights) == 1
    assert district_insights[0].district_abbreviation == "ont"


def test_district_key_name(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2022on305.json")
    test_data_importer.import_award_list(__file__, "../data/2022on305_awards.json")

    insights = compute_insights_for_year(2022, [BlueBannersV2Calculator()])
    key_names = {i.key_name for i in insights}
    assert "2022_v2_leaderboard_blue_banners" in key_names
    assert "2022_v2_leaderboard_blue_banners_ont" in key_names
