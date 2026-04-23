from backend.common.helpers.insights_v2.compute import compute_insights_for_year
from backend.common.helpers.insights_v2.most_matches_played import (
    MostMatchesPlayedV2Calculator,
)


def test_most_matches_played_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [MostMatchesPlayedV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "most_matches_played"
    assert insight.display_name == "Most Matches Played"
    assert len(insight.data["rankings"]) > 0


def test_most_matches_played_top_team(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [MostMatchesPlayedV2Calculator()])
    assert insights[0].data["rankings"][0] == {"value": 17, "keys": ["frc6911"]}


def test_key_name(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../data/2024nytr_matches.json")

    insights = compute_insights_for_year(2024, [MostMatchesPlayedV2Calculator()])
    assert insights[0].key_name == "2024_v2_leaderboard_most_matches_played"
