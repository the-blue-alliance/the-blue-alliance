import copy
import json
from typing import List

from dateutil import tz
from google.appengine.ext import testbed
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.match_time_prediction_helper import (
    MatchTimePredictionHelper,
)
from backend.common.models.match import Match


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
