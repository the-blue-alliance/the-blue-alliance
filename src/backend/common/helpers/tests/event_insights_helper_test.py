import json

from google.appengine.ext import ndb

from backend.common.helpers.event_insights_helper import EventInsightsHelper
from backend.common.models.event import Event
from backend.common.models.match import Match


def test_compute_event_insights_too_old() -> None:
    assert EventInsightsHelper.calculate_event_insights([], 2015) is None


def test_compute_event_insights_delegates(test_data_importer) -> None:
    """Verify EventInsightsHelper delegates to get_game().calculate_event_insights()."""
    event_key = "2019nyny"
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")

    year = int(event_key[:4])
    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    insights = EventInsightsHelper.calculate_event_insights(matches, year)

    with open(
        test_data_importer._get_path(__file__, f"data/{event_key}_insights.json"), "r"
    ) as f:
        expected_insights = json.load(f)

    assert insights == expected_insights
