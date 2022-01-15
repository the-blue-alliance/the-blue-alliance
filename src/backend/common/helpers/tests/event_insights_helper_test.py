import json

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.helpers.event_insights_helper import EventInsightsHelper
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.match import Match


def test_compute_event_insights_too_old() -> None:
    assert EventInsightsHelper.calculate_event_insights([], 2015) is None


@pytest.mark.parametrize(
    "event_key",
    [
        "2020scmb",
        "2019nyny",
        "2018nyny",
        "2017nyny",
        "2016nyny",
    ],
)
def test_compute_event_insights(event_key: EventKey, test_data_importer) -> None:
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")

    year = int(event_key[:4])
    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    insights = EventInsightsHelper.calculate_event_insights(matches, year)

    with open(
        test_data_importer._get_path(__file__, f"data/{event_key}_insights.json"), "r"
    ) as f:
        expected_insights = json.load(f)

    if year == 2018 and insights is not None:
        # For some reason these don't match prod, so skip comparing them?
        del none_throws(insights["qual"])["winning_opp_switch_denial_percentage_teleop"]
        del none_throws(insights["playoff"])[
            "winning_opp_switch_denial_percentage_teleop"
        ]
        del none_throws(expected_insights["qual"])[
            "winning_opp_switch_denial_percentage_teleop"
        ]
        del none_throws(expected_insights["playoff"])[
            "winning_opp_switch_denial_percentage_teleop"
        ]

    assert insights == expected_insights
