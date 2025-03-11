from backend.common.helpers.insights_leaderboard_team_helper import (
    InsightsLeaderboardTeamHelper,
    LeaderboardInsightArguments,
)
from backend.common.models.event import Event
from backend.common.models.insight import Insight


def test_most_blue_banners(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "data/2019nyny_awards.json")

    test_data_importer.import_event(__file__, "data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "data/2024nytr_awards.json")

    insight = InsightsLeaderboardTeamHelper._most_blue_banners(
        LeaderboardInsightArguments(
            matches=Event.get_by_id("2019nyny").matches
            + Event.get_by_id("2024nytr").matches,
            events=[Event.get_by_id("2019nyny"), Event.get_by_id("2024nytr")],
            awards=Event.get_by_id("2019nyny").awards
            + Event.get_by_id("2024nytr").awards,
            year=0,
        )
    )

    assert insight is not None
    assert insight.data["rankings"] == [
        {"keys": ["frc1796"], "value": 2},
        {
            "keys": [
                "frc250",
                "frc395",
                "frc694",
                "frc1591",
                "frc1660",
                "frc2265",
                "frc3181",
                "frc5993",
                "frc9624",
            ],
            "value": 1,
        },
    ]
    assert insight.data["key_type"] == "team"


def test_most_awards(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "data/2019nyny_awards.json")

    test_data_importer.import_event(__file__, "data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "data/2024nytr_awards.json")

    insight = InsightsLeaderboardTeamHelper._most_awards(
        LeaderboardInsightArguments(
            matches=Event.get_by_id("2019nyny").matches
            + Event.get_by_id("2024nytr").matches,
            events=[Event.get_by_id("2019nyny"), Event.get_by_id("2024nytr")],
            awards=Event.get_by_id("2019nyny").awards
            + Event.get_by_id("2024nytr").awards,
            year=0,
        )
    )

    assert insight is not None
    assert insight.data["rankings"][:3] == [
        {"keys": ["frc1796"], "value": 4},
        {"keys": ["frc3419", "frc4122"], "value": 3},
        {
            "keys": [
                "frc395",
                "frc694",
                "frc1155",
                "frc1591",
                "frc2265",
                "frc3173",
                "frc4571",
                "frc6621",
                "frc6911",
                "frc7522",
                "frc9624",
            ],
            "value": 2,
        },
    ]
    assert insight.data["key_type"] == "team"


def test_most_non_champs_event_wins(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "data/2019nyny_awards.json")

    test_data_importer.import_event(__file__, "data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "data/2024nytr_awards.json")

    test_data_importer.import_event(__file__, "data/2024mil.json")
    test_data_importer.import_award_list(__file__, "data/2024mil_awards.json")

    insight = InsightsLeaderboardTeamHelper._most_non_champs_event_wins(
        LeaderboardInsightArguments(
            matches=(
                Event.get_by_id("2019nyny").matches
                + Event.get_by_id("2024nytr").matches
                + Event.get_by_id("2024mil").matches
            ),
            events=[
                Event.get_by_id("2019nyny"),
                Event.get_by_id("2024nytr"),
                Event.get_by_id("2024mil"),
            ],
            awards=(
                Event.get_by_id("2019nyny").awards
                + Event.get_by_id("2024nytr").awards
                + Event.get_by_id("2024mil").awards
            ),
            year=2024,
        )
    )

    assert insight is not None
    assert insight.data["rankings"] == [
        {"keys": ["frc1796"], "value": 2},
        {"keys": ["frc694", "frc1591", "frc2265", "frc3181", "frc9624"], "value": 1},
    ]
    assert insight.data["key_type"] == "team"


def test_most_matches_played(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insight = InsightsLeaderboardTeamHelper._most_matches_played(
        LeaderboardInsightArguments(
            matches=Event.get_by_id("2019nyny").matches,
            events=[Event.get_by_id("2019nyny")],
            awards=[],
            year=2019,
        )
    )

    assert insight is not None
    assert insight.data["rankings"][:5] == [
        {"keys": ["frc1155", "frc2869"], "value": 17},
        {"keys": ["frc4122"], "value": 16},
        {"keys": ["frc694", "frc1796", "frc2265"], "value": 15},
        {
            "keys": ["frc333", "frc334", "frc354", "frc1880", "frc2579", "frc3419"],
            "value": 14,
        },
        {"keys": ["frc2344"], "value": 13},
    ]
    assert insight.data["key_type"] == "team"


def test_most_events_played_at(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    test_data_importer.import_event(__file__, "data/2024nytr.json")
    test_data_importer.import_match_list(__file__, "data/2024nytr_matches.json")

    insight = InsightsLeaderboardTeamHelper._most_events_played_at(
        LeaderboardInsightArguments(
            matches=(
                Event.get_by_id("2019nyny").matches
                + Event.get_by_id("2024nytr").matches
            ),
            events=[Event.get_by_id("2019nyny"), Event.get_by_id("2024nytr")],
            awards=[],
            year=0,
        )
    )

    assert insight is not None
    assert insight.data["rankings"][0] == {
        "keys": ["frc333", "frc1796", "frc1880", "frc3419", "frc4122", "frc6401"],
        "value": 2,
    }
    assert insight.data["key_type"] == "team"


def test_most_unique_teams_played_with_or_against(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insight = InsightsLeaderboardTeamHelper._most_unique_teams_played_with_or_against(
        LeaderboardInsightArguments(
            matches=Event.get_by_id("2019nyny").matches,
            events=[Event.get_by_id("2019nyny")],
            awards=[],
            year=2019,
        )
    )

    assert insight is not None
    assert insight.data["rankings"][:3] == [
        {"keys": ["frc1155"], "value": 46},
        {"keys": ["frc694", "frc4122", "frc7522"], "value": 43},
        {
            "keys": [
                "frc1796",
                "frc2344",
                "frc2869",
                "frc4383",
                "frc4571",
                "frc5298",
                "frc5599",
            ],
            "value": 42,
        },
    ]
    assert insight.data["key_type"] == "team"


def test_only_overall_and_year_are_computed(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "data/2025isde1_matches.json")
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insights = InsightsLeaderboardTeamHelper.make_insights(2025)
    assert len(insights) == 12

    overall_insights = [i for i in insights if i.year == 0]
    insights_2025 = [i for i in insights if i.year == 2025]

    assert len(overall_insights) == 6
    assert len(insights_2025) == 6
    assert len(overall_insights) + len(insights_2025) == len(insights)


def test_only_official_events_are_included(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019mttd.json")
    test_data_importer.import_match_list(__file__, "data/2019mttd_matches.json")
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insights = InsightsLeaderboardTeamHelper.make_insights(2019)
    most_matches_played_insights = [
        i
        for i in insights
        if i.name
        == Insight.INSIGHT_NAMES[Insight.TYPED_LEADERBOARD_MOST_MATCHES_PLAYED]
    ]

    most_matches_overall = next(i for i in most_matches_played_insights if i.year == 0)
    most_matches_2019 = next(i for i in most_matches_played_insights if i.year == 2019)

    assert most_matches_overall is not None
    assert most_matches_overall.year == 0
    assert most_matches_overall.data["rankings"][:5] == [
        {"keys": ["frc1155", "frc2869"], "value": 17},
        {"keys": ["frc4122"], "value": 16},
        {"keys": ["frc694", "frc1796", "frc2265"], "value": 15},
        {
            "keys": ["frc333", "frc334", "frc354", "frc1880", "frc2579", "frc3419"],
            "value": 14,
        },
        {"keys": ["frc2344"], "value": 13},
    ]

    assert most_matches_2019 is not None
    assert most_matches_2019.year == 2019
    assert most_matches_2019.data["rankings"][:5] == [
        {"keys": ["frc1155", "frc2869"], "value": 17},
        {"keys": ["frc4122"], "value": 16},
        {"keys": ["frc694", "frc1796", "frc2265"], "value": 15},
        {
            "keys": ["frc333", "frc334", "frc354", "frc1880", "frc2579", "frc3419"],
            "value": 14,
        },
        {"keys": ["frc2344"], "value": 13},
    ]
