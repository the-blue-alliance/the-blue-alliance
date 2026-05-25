from backend.common.helpers.insights_v2.leaderboards.most_coral_scored import (
    MostCoralScored2025V2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year


def test_most_coral_scored_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "../../data/2025isde1_matches.json")

    insights = compute_insights_for_year(2025, [MostCoralScored2025V2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "most_coral_scored"
    assert insight.display_name == "Most Coral Scored"
    assert insight.key_name == "2025_v2_leaderboard_most_coral_scored"


def test_most_coral_scored_context_type(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "../../data/2025isde1_matches.json")

    insights = compute_insights_for_year(2025, [MostCoralScored2025V2Calculator()])

    assert insights[0].data["context_type"] == "match_alliance"
    assert insights[0].data["key_type"] == "match"


def test_most_coral_scored_top_entry(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "../../data/2025isde1_matches.json")

    insights = compute_insights_for_year(2025, [MostCoralScored2025V2Calculator()])

    # sf1m1: red autoCoralCount=8 + teleopCoralCount=30 = 38
    top = insights[0].data["rankings"][0]
    assert top["value"] == 38
    assert top["keys"] == ["2025isde1_sf1m1"]
    ctx = top["contexts"][0]
    assert ctx["match_key"] == "2025isde1_sf1m1"
    assert set(ctx["alliance"]) == {"frc5928", "frc1690", "frc5614"}


def test_most_coral_scored_skips_year_zero(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "../../data/2025isde1_matches.json")

    insights = compute_insights_for_year(0, [MostCoralScored2025V2Calculator()])

    assert insights == []


def test_most_coral_scored_skips_other_years(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "../../data/2025isde1_matches.json")

    # 2024 matches have no coral breakdown fields
    insights = compute_insights_for_year(2024, [MostCoralScored2025V2Calculator()])

    assert insights == []


def test_most_coral_scored_rankings_descending(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "../../data/2025isde1_matches.json")

    insights = compute_insights_for_year(2025, [MostCoralScored2025V2Calculator()])

    values = [r["value"] for r in insights[0].data["rankings"]]
    assert values == sorted(values, reverse=True)
