from unittest.mock import patch

from backend.common.helpers.insights_helper_utils import LeaderboardInsightArguments
from backend.common.helpers.insights_leaderboard_event_helper import (
    InsightsLeaderboardEventHelper,
)
from backend.common.models.event import Event


def test_highest_median_score(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2022on305.json")
    test_data_importer.import_match_list(__file__, "data/2022on305_matches.json")

    test_data_importer.import_event(__file__, "data/2022on306.json")
    test_data_importer.import_match_list(__file__, "data/2022on306_matches.json")

    insight = InsightsLeaderboardEventHelper._highest_median_score(
        LeaderboardInsightArguments(
            events=[Event.get_by_id("2022on305"), Event.get_by_id("2022on306")],
            year=2022,
        )
    )

    assert insight is not None
    assert insight.data["rankings"] == [
        {"keys": ["2022on306"], "value": 41.5},
        {"keys": ["2022on305"], "value": 26.5},
    ]
    assert insight.data["key_type"] == "event"


def test_highest_median_score_overall_is_skipped(ndb_stub):
    assert (
        InsightsLeaderboardEventHelper._highest_median_score(
            LeaderboardInsightArguments(events=[], year=0)
        )
        is None
    )


def test_highest_median_score_needs_ten_scores(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2022on305.json")
    test_data_importer.import_match_list(__file__, "data/2022on305_matches.json")

    # Only keep a handful of matches, so the event has too few scores
    event = Event.get_by_id("2022on305")
    matches = event.matches[:3]
    with patch.object(LeaderboardInsightArguments, "matches", return_value=matches):
        insight = InsightsLeaderboardEventHelper._highest_median_score(
            LeaderboardInsightArguments(events=[event], year=2022)
        )

    assert insight is not None
    assert insight.data["rankings"] == []


def test_make_insights(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2022on305.json")
    test_data_importer.import_match_list(__file__, "data/2022on305_matches.json")

    insights = InsightsLeaderboardEventHelper.make_insights(2022)
    assert [i.year for i in insights] == [2022]
