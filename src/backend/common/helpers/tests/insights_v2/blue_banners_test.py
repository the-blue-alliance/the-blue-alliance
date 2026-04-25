from backend.common.helpers.insights_v2.blue_banners import BlueBannersV2Calculator
from backend.common.helpers.insights_v2.compute import compute_insights_for_year


def test_blue_banners_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "blue_banners"
    assert insight.display_name == "Total Blue Banners"
    # A single event yields value=1 per team, which is filtered out by design
    assert insight.data["rankings"] == []


def test_blue_banners_overall(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "../data/2019nyny_awards.json")
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(0, [BlueBannersV2Calculator()])

    # frc1796 wins at both 2019nyny and 2024nytr so should have 2 banners overall
    assert insights[0].data["rankings"][0] == {"value": 2, "keys": ["frc1796"]}


def test_key_name(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])
    assert insights[0].key_name == "2024_v2_leaderboard_blue_banners"
