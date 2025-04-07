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
            events=[Event.get_by_id("2019nyny")],
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
            events=[Event.get_by_id("2019nyny")],
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
    test_data_importer.import_event(__file__, "data/2025oncmp2.json")
    test_data_importer.import_match_list(__file__, "data/2025oncmp2_matches.json")

    insight = InsightsLeaderboardMatchHelper._2025_most_coral_scored(
        LeaderboardInsightArguments(
            events=[Event.get_by_id("2025isde1"), Event.get_by_id("2025oncmp2")],
            year=2025,
        )
    )

    assert insight is not None
    assert insight.data["rankings"][:5] == [
        {"keys": ["2025oncmp2_f1m1", "2025oncmp2_sf7m1"], "value": 48},
        {"keys": ["2025oncmp2_qm95", "2025oncmp2_sf11m1"], "value": 47},
        {"keys": ["2025oncmp2_sf3m1"], "value": 46},
        {"keys": ["2025oncmp2_f1m2", "2025oncmp2_qm56"], "value": 45},
        {"keys": ["2025oncmp2_qm74"], "value": 44},
    ]
    assert insight.data["key_type"] == "match"


def test_only_year_are_computed(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "data/2025isde1_matches.json")
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insights = InsightsLeaderboardMatchHelper.make_insights(2025)
    assert len(insights) == 3

    insights_2025 = [i for i in insights if i.year == 2025]
    assert len(insights_2025) == 3


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

    clean_score_2019 = next(i for i in clean_score_insights if i.year == 2019)

    assert clean_score_2019 is not None
    assert clean_score_2019.year == 2019
    assert clean_score_2019.data["rankings"][:5] == [
        {"keys": ["2019nyny_f1m1", "2019nyny_qf1m1"], "value": 91},
        {"keys": ["2019nyny_qf1m2"], "value": 89},
        {"keys": ["2019nyny_sf1m1"], "value": 83},
        {"keys": ["2019nyny_f1m2", "2019nyny_qm57"], "value": 77},
        {"keys": ["2019nyny_qm15"], "value": 76},
    ]
