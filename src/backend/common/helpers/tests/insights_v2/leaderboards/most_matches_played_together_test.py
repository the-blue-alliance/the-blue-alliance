from backend.common.helpers.insights_v2.leaderboards.most_matches_played_together import (
    MostMatchesPlayedTogetherV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year


def test_most_matches_played_together_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        2024, [MostMatchesPlayedTogetherV2Calculator()]
    )

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "most_matches_played_together"
    assert insight.display_name == "Most Matches Played Together"
    assert insight.data["key_type"] == "team_pair"
    assert len(insight.data["rankings"]) > 0


def test_most_matches_played_together_top_pair(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        2024, [MostMatchesPlayedTogetherV2Calculator()]
    )
    assert insights[0].data["rankings"][0] == {
        "value": 8,
        "keys": [["frc3173", "frc3419"]],
    }


def test_key_format(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        2024, [MostMatchesPlayedTogetherV2Calculator()]
    )
    for ranking in insights[0].data["rankings"]:
        for pair in ranking["keys"]:
            team_a, team_b = pair
            assert team_a.startswith("frc")
            assert team_b.startswith("frc")
            assert int(team_a[3:]) < int(
                team_b[3:]
            ), "pair teams not in ascending order"


def test_key_name(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "../../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        2024, [MostMatchesPlayedTogetherV2Calculator()]
    )
    assert insights[0].key_name == "2024_v2_leaderboard_most_matches_played_together"


def test_no_unplayed_matches_counted(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2024nytr.json")

    insights = compute_insights_for_year(
        2024, [MostMatchesPlayedTogetherV2Calculator()]
    )
    assert insights == []
