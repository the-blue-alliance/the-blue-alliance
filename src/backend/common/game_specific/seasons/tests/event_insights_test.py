import json
import os

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.game_specific.registry import get_game
from backend.common.models.event import Event
from backend.common.models.match import Match

# Sentinel path: dirname(_HELPERS_TESTS) == .../helpers/tests/
_HELPERS_TESTS = os.path.join(os.path.dirname(__file__), "../../../helpers/tests/x")


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def test_compute_event_insights_unsupported() -> None:
    assert get_game(2015).calculate_event_insights([]) is None


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
def test_compute_event_insights(event_key: str, test_data_importer) -> None:
    test_data_importer.import_match_list(
        _HELPERS_TESTS, f"data/{event_key}_matches.json"
    )

    year = int(event_key[:4])
    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    insights = get_game(year).calculate_event_insights(matches)

    with open(
        test_data_importer._get_path(_HELPERS_TESTS, f"data/{event_key}_insights.json"),
        "r",
    ) as f:
        expected_insights = json.load(f)

    if year == 2018 and insights is not None:
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
