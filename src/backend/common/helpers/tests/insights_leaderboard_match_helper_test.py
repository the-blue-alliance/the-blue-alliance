from backend.common.helpers.insights_leaderboard_match_helper import (
    InsightsLeaderboardMatchHelper,
    LeaderboardInsightArguments,
)
from backend.common.models.event import Event
from backend.common.models.insight import Insight


def test_highest_clean_score(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insight = InsightsLeaderboardMatchHelper._highest_match_clean_score(
        LeaderboardInsightArguments(
            matches=Event.get_by_id("2019nyny").matches,
            events=[Event.get_by_id("2019nyny")],
            awards=[],
            year=2019,
        )
    )

    assert insight is not None
    assert insight.data["rankings"][:5] == [
        {"keys": ["2019nyny_f1m1", "2019nyny_qf1m1"], "value": 91},
        {"keys": ["2019nyny_qf1m2"], "value": 89},
        {"keys": ["2019nyny_sf1m1"], "value": 83},
        {"keys": ["2019nyny_f1m2", "2019nyny_qm57"], "value": 77},
        {"keys": ["2019nyny_qm15"], "value": 76},
    ]
    assert insight.data["key_type"] == "match"


def test_highest_clean_combined_score(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insight = InsightsLeaderboardMatchHelper._highest_match_clean_combined_score(
        LeaderboardInsightArguments(
            matches=Event.get_by_id("2019nyny").matches,
            events=[Event.get_by_id("2019nyny")],
            awards=[],
            year=2019,
        )
    )

    assert insight is not None
    assert insight.data["rankings"][:5] == [
        {"keys": ["2019nyny_f1m1"], "value": 149},
        {"keys": ["2019nyny_sf1m1"], "value": 138},
        {"keys": ["2019nyny_qf1m2"], "value": 136},
        {"keys": ["2019nyny_qm57"], "value": 133},
        {"keys": ["2019nyny_qf1m1"], "value": 131},
    ]
    assert insight.data["key_type"] == "match"


def test_2025_most_coral_scored(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "data/2025isde1_matches.json")

    insight = InsightsLeaderboardMatchHelper._2025_most_coral_scored(
        LeaderboardInsightArguments(
            matches=Event.get_by_id("2025isde1").matches,
            events=[Event.get_by_id("2025isde1")],
            awards=[],
            year=2025,
        )
    )

    assert insight is not None

    assert insight.data["rankings"][:5] == [
        {"keys": ["2025isde1_sf1m1"], "value": 38},
        {"keys": ["2025isde1_f1m1"], "value": 37},
        {"keys": ["2025isde1_f1m2", "2025isde1_qm19"], "value": 33},
        {"keys": ["2025isde1_qm32", "2025isde1_qm33"], "value": 31},
        {"keys": ["2025isde1_qm36"], "value": 30},
    ]
    assert insight.data["key_type"] == "match"


def test_only_overall_and_year_are_computed(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "data/2025isde1_matches.json")
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insights = InsightsLeaderboardMatchHelper.make_insights(2025)
    assert len(insights) == 5

    overall_insights = [i for i in insights if i.year == 0]
    insights_2025 = [i for i in insights if i.year == 2025]

    assert len(overall_insights) == 2
    assert len(insights_2025) == 3
    assert len(overall_insights) + len(insights_2025) == len(insights)


def test_only_official_events_are_included(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019mttd.json")
    test_data_importer.import_match_list(__file__, "data/2019mttd_matches.json")
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insights = InsightsLeaderboardMatchHelper.make_insights(2019)
    clean_score_insights = [
        i
        for i in insights
        if i.name
        == Insight.INSIGHT_NAMES[Insight.TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_SCORE]
    ]

    clean_score_overall = next(i for i in clean_score_insights if i.year == 0)
    clean_score_2019 = next(i for i in clean_score_insights if i.year == 2019)

    assert clean_score_overall is not None
    assert clean_score_overall.year == 0
    assert clean_score_overall.data["rankings"][:5] == [
        {"keys": ["2019nyny_f1m1", "2019nyny_qf1m1"], "value": 91},
        {"keys": ["2019nyny_qf1m2"], "value": 89},
        {"keys": ["2019nyny_sf1m1"], "value": 83},
        {"keys": ["2019nyny_f1m2", "2019nyny_qm57"], "value": 77},
        {"keys": ["2019nyny_qm15"], "value": 76},
    ]

    assert clean_score_2019 is not None
    assert clean_score_2019.year == 2019
    assert clean_score_2019.data["rankings"][:5] == [
        {"keys": ["2019nyny_f1m1", "2019nyny_qf1m1"], "value": 91},
        {"keys": ["2019nyny_qf1m2"], "value": 89},
        {"keys": ["2019nyny_sf1m1"], "value": 83},
        {"keys": ["2019nyny_f1m2", "2019nyny_qm57"], "value": 77},
        {"keys": ["2019nyny_qm15"], "value": 76},
    ]
