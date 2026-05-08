from backend.common.helpers.insights_v2.leaderboards.highest_match_clean_score import (
    HighestMatchCleanScoreV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year


def test_highest_match_clean_score_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestMatchCleanScoreV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "highest_match_clean_score"
    assert insight.display_name == "Highest Clean Score"
    assert insight.key_name == "2024_v2_leaderboard_highest_match_clean_score"


def test_highest_match_clean_score_context_type(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestMatchCleanScoreV2Calculator()])

    assert insights[0].data["context_type"] == "match_alliance"
    assert insights[0].data["key_type"] == "match"


def test_highest_match_clean_score_top_entry(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestMatchCleanScoreV2Calculator()])

    top = insights[0].data["rankings"][0]
    assert top["value"] == 131
    assert top["keys"] == ["2024nytr_sf7m1"]
    ctx = top["contexts"][0]
    assert ctx["match_key"] == "2024nytr_sf7m1"
    assert set(ctx["alliance"]) == {"frc9624", "frc1796", "frc1591"}


def test_highest_match_clean_score_subtracts_fouls(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestMatchCleanScoreV2Calculator()])

    # sf8m1: blue raw=131, foulPoints=10 → clean=121. Verify it appears below sf7m1.
    rankings = insights[0].data["rankings"]
    values = [r["value"] for r in rankings]
    assert values == sorted(values, reverse=True)
    assert 131 in values
    assert 121 in values
    assert values.index(131) < values.index(121)


def test_highest_match_clean_score_skips_year_zero(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(0, [HighestMatchCleanScoreV2Calculator()])

    assert insights == []


def test_highest_match_clean_score_rankings_descending(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [HighestMatchCleanScoreV2Calculator()])

    values = [r["value"] for r in insights[0].data["rankings"]]
    assert values == sorted(values, reverse=True)
