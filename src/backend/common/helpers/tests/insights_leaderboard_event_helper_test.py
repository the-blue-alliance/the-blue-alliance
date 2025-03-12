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
