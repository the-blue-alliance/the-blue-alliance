from backend.common.helpers.insights_v2.leaderboards.highest_match_clean_combined_score import (
    HighestMatchCleanCombinedScoreV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year


def test_highest_match_clean_combined_score_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        2024, [HighestMatchCleanCombinedScoreV2Calculator()]
    )

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "highest_match_clean_combined_score"
    assert insight.display_name == "Highest Combined Clean Score"
    assert insight.key_name == "2024_v2_leaderboard_highest_match_clean_combined_score"


def test_highest_match_clean_combined_score_context_type(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        2024, [HighestMatchCleanCombinedScoreV2Calculator()]
    )

    assert insights[0].data["context_type"] == "match_alliance"
    assert insights[0].data["key_type"] == "match"


def test_highest_match_clean_combined_score_top_entry(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        2024, [HighestMatchCleanCombinedScoreV2Calculator()]
    )

    top = insights[0].data["rankings"][0]
    assert top["value"] == 204
    assert top["keys"] == ["2024nytr_sf7m1"]
    ctx = top["contexts"][0]
    assert ctx["match_key"] == "2024nytr_sf7m1"
    assert set(ctx["alliance"]) == {
        "frc9624",
        "frc1796",
        "frc1591",
        "frc3550",
        "frc7605",
        "frc3799",
    }


def test_highest_match_clean_combined_score_includes_both_alliances(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        2024, [HighestMatchCleanCombinedScoreV2Calculator()]
    )

    # Every context should include 6 teams (both alliances)
    for ranking in insights[0].data["rankings"]:
        for ctx in ranking["contexts"]:
            assert len(ctx["alliance"]) == 6


def test_highest_match_clean_combined_score_skips_year_zero(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        0, [HighestMatchCleanCombinedScoreV2Calculator()]
    )

    assert insights == []


def test_highest_match_clean_combined_score_rankings_descending(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        2024, [HighestMatchCleanCombinedScoreV2Calculator()]
    )

    values = [r["value"] for r in insights[0].data["rankings"]]
    assert values == sorted(values, reverse=True)
