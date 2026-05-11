from backend.common.helpers.insights_v2.leaderboards.highest_endgame_score import (
    HighestEndgameScoreV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year


def test_highest_endgame_score_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestEndgameScoreV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "highest_endgame_score"
    assert insight.display_name == "Highest Endgame Score"
    assert insight.key_name == "2024_v2_leaderboard_highest_endgame_score"


def test_highest_endgame_score_context_type(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestEndgameScoreV2Calculator()])

    assert insights[0].data["context_type"] == "match_alliance"
    assert insights[0].data["key_type"] == "match"


def test_highest_endgame_score_top_entry(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestEndgameScoreV2Calculator()])

    # sf11m1: red endGameTotalStagePoints=15
    top = insights[0].data["rankings"][0]
    assert top["value"] == 15
    assert top["keys"] == ["2024nytr_sf11m1"]
    ctx = top["contexts"][0]
    assert ctx["match_key"] == "2024nytr_sf11m1"
    assert set(ctx["alliance"]) == {"frc9624", "frc1796", "frc1591"}


def test_highest_endgame_score_no_insight_without_breakdown_year(
    ndb_stub, test_data_importer
) -> None:
    # 2015 has no endgame points field in the score breakdown — no insight should be generated
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2015, [HighestEndgameScoreV2Calculator()])

    assert insights == []


def test_highest_endgame_score_skips_year_zero(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(0, [HighestEndgameScoreV2Calculator()])

    assert insights == []


def test_highest_endgame_score_rankings_descending(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestEndgameScoreV2Calculator()])

    values = [r["value"] for r in insights[0].data["rankings"]]
    assert values == sorted(values, reverse=True)
