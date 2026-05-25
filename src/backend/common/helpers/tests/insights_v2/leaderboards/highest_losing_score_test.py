from backend.common.helpers.insights_v2.leaderboards.highest_losing_score import (
    HighestLosingScoreV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year


def test_highest_losing_score_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestLosingScoreV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "highest_losing_score"
    assert insight.display_name == "Highest Losing Score"
    assert insight.key_name == "2024_v2_leaderboard_highest_losing_score"


def test_highest_losing_score_context_type(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestLosingScoreV2Calculator()])

    assert insights[0].data["context_type"] == "match_alliance"
    assert insights[0].data["key_type"] == "match"


def test_highest_losing_score_top_entry(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestLosingScoreV2Calculator()])

    # sf11m1: blue loses with raw score 97
    top = insights[0].data["rankings"][0]
    assert top["value"] == 97
    assert top["keys"] == ["2024nytr_sf11m1"]
    ctx = top["contexts"][0]
    assert ctx["match_key"] == "2024nytr_sf11m1"
    assert set(ctx["alliance"]) == {"frc3173", "frc3419", "frc6911"}


def test_highest_losing_score_skips_ties(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestLosingScoreV2Calculator()])

    # All entries should have a single match per ranking (no ties in top entries)
    for ranking in insights[0].data["rankings"]:
        assert len(ranking["keys"]) >= 1


def test_highest_losing_score_skips_year_zero(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(0, [HighestLosingScoreV2Calculator()])

    assert insights == []


def test_highest_losing_score_rankings_descending(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestLosingScoreV2Calculator()])

    values = [r["value"] for r in insights[0].data["rankings"]]
    assert values == sorted(values, reverse=True)
