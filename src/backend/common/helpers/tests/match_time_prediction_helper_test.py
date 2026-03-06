import copy
import datetime
import json
from typing import List

import pytest
from dateutil import tz
from google.appengine.ext import testbed
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.nexus_match_status import NexusMatchStatus
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.match_time_prediction_helper import (
    MatchTimePredictionHelper,
)
from backend.common.models.event_queue_status import EventQueueStatus, NexusMatch
from backend.common.models.match import Match


@pytest.fixture(autouse=True)
def auto_use_gcs_stub(gcs_stub):
    pass


def _mark_match_unplayed(match: Match) -> None:
    alliances = match.alliances
    alliances[AllianceColor.RED]["score"] = -1
    alliances[AllianceColor.BLUE]["score"] = -1
    match.alliances_json = json.dumps(alliances)
    match._alliances = None
    match.predicted_time = None
    match.actual_time = None


def _mark_match_played(
    test_matches: List[Match], original_matches: List[Match], i: int
) -> None:
    test_matches[i].alliances_json = original_matches[i].alliances_json
    test_matches[i]._alliances = None
    test_matches[i].actual_time = original_matches[i].actual_time


def test_predict_times(
    test_data_importer, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    original_matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    original_matches = MatchHelper.play_order_sorted_matches(original_matches)
    matches = copy.deepcopy(original_matches)

    # First, mark all matches except the first as unplayed
    [_mark_match_unplayed(m) for m in matches[1:]]

    timezone = none_throws(tz.gettz("America/New_York"))
    for i in range(1, len(matches)):
        played = matches[:i]
        unplayed = matches[i:]
        MatchTimePredictionHelper.predict_future_matches(
            "2019nyny", played, unplayed, timezone, False, None
        )

        _mark_match_played(matches, original_matches, i)


def test_nexus_prediction_ignored_when_no_matches_played_today(
    test_data_importer, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    """
    Test that nexus predictions are NOT used when no matches have been played
    on the current day. This ensures we don't predict unreliably early times
    from nexus when we have no actual match data to calibrate against.
    """
    original_matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    original_matches = MatchHelper.play_order_sorted_matches(original_matches)
    matches = copy.deepcopy(original_matches)

    # Mark all matches as unplayed (simulating the start of the event)
    [_mark_match_unplayed(m) for m in matches]

    timezone = none_throws(tz.gettz("America/New_York"))

    # Create a nexus queue info with an early prediction for the first match
    # This prediction should be ignored because no matches have been played yet
    first_match = matches[0]
    scheduled_time_local = none_throws(
        MatchTimePredictionHelper.as_local(first_match.time, timezone)
    )
    early_time = scheduled_time_local - datetime.timedelta(minutes=30)
    nexus_predicted_time_ms = int(
        MatchTimePredictionHelper.timestamp(early_time) * 1000
    )

    nexus_match: NexusMatch = {
        "label": first_match.key_name,
        "status": NexusMatchStatus.QUEUING_SOON,
        "played": False,
        "times": {
            "estimated_queue_time_ms": None,
            "estimated_start_time_ms": nexus_predicted_time_ms,
        },
    }

    nexus_queue_info: EventQueueStatus = {
        "data_as_of_ms": int(datetime.datetime.now().timestamp() * 1000),
        "now_queueing": None,
        "matches": {first_match.key_name: nexus_match},
    }

    # Predict times with no matches played yet
    MatchTimePredictionHelper.predict_future_matches(
        "2019nyny", [], matches, timezone, False, nexus_queue_info
    )

    # The predicted time should equal the scheduled time (or very close to it),
    # not the early nexus prediction
    predicted = none_throws(
        MatchTimePredictionHelper.as_local(
            none_throws(matches[0].predicted_time), timezone
        )
    )
    scheduled = none_throws(
        MatchTimePredictionHelper.as_local(matches[0].time, timezone)
    )

    # Allow a small tolerance for timing differences (e.g., a few seconds)
    time_diff = abs((predicted - scheduled).total_seconds())
    assert (
        time_diff < 60
    ), f"Predicted time {predicted} should be close to scheduled time {scheduled}, but diff is {time_diff} seconds"
