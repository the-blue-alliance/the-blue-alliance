from backend.common.helpers.insights_v2.leaderboards.highest_teleop_score import (
    HighestTeleopScoreV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year


def test_highest_teleop_score_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestTeleopScoreV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "highest_teleop_score"
    assert insight.display_name == "Highest Teleop Score"
    assert insight.key_name == "2024_v2_leaderboard_highest_teleop_score"


def test_highest_teleop_score_context_type(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestTeleopScoreV2Calculator()])

    assert insights[0].data["context_type"] == "match_alliance"
    assert insights[0].data["key_type"] == "match"


def test_highest_teleop_score_top_entry(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestTeleopScoreV2Calculator()])

    # sf8m1: blue teleopPoints=92
    top = insights[0].data["rankings"][0]
    assert top["value"] == 92
    assert top["keys"] == ["2024nytr_sf8m1"]
    ctx = top["contexts"][0]
    assert ctx["match_key"] == "2024nytr_sf8m1"
    assert set(ctx["alliance"]) == {"frc3173", "frc3419", "frc6911"}


def test_highest_teleop_score_skips_year_zero(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(0, [HighestTeleopScoreV2Calculator()])

    assert insights == []


def test_highest_teleop_score_rankings_descending(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestTeleopScoreV2Calculator()])

    values = [r["value"] for r in insights[0].data["rankings"]]
    assert values == sorted(values, reverse=True)
