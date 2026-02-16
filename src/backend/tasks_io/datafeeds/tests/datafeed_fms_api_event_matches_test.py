import datetime
import json
from unittest.mock import call, patch

import pytest

from backend.common.consts.event_sync_type import EventSyncType
from backend.common.consts.event_type import EventType
from backend.common.frc_api import FRCAPI
from backend.common.futures import InstantFuture
from backend.common.models.event import Event
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_match_parser import (
    FMSAPIHybridScheduleParser,
    FMSAPIMatchDetailsParser,
)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_get_event_matches() -> None:
    schedule_response = URLFetchResult.mock_for_content(
        "", 200, json.dumps({"Schedule": []})
    )
    score_response = URLFetchResult.mock_for_content("", 200, "")

    df = DatafeedFMSAPI()
    with (
        patch.object(
            FRCAPI, "hybrid_schedule", return_value=InstantFuture(schedule_response)
        ) as mock_hybrid_schedule_api,
        patch.object(
            FRCAPI, "match_scores", return_value=InstantFuture(score_response)
        ) as mock_match_scores_api,
        patch.object(FMSAPIHybridScheduleParser, "parse") as mock_schedule_parse,
        patch.object(FMSAPIMatchDetailsParser, "parse") as mock_match_detail_parser,
    ):
        mock_schedule_parse.side_effect = ([], [])
        mock_match_detail_parser.return_value = {}
        df.get_event_matches("2020miket").get_result()

    mock_hybrid_schedule_api.assert_has_calls(
        [call(2020, "miket", "qual"), call(2020, "miket", "playoff")]
    )
    mock_match_scores_api.assert_has_calls(
        [call(2020, "miket", "qual"), call(2020, "miket", "playoff")]
    )
    mock_schedule_parse.assert_has_calls(
        [call({"Schedule": []}), call({"Schedule": []})]
    )


def test_get_event_matches_cmp() -> None:
    schedule_response = URLFetchResult.mock_for_content(
        "", 200, json.dumps({"Schedule": []})
    )
    score_response = URLFetchResult.mock_for_content("", 200, "")

    df = DatafeedFMSAPI()
    with (
        patch.object(
            FRCAPI, "hybrid_schedule", return_value=InstantFuture(schedule_response)
        ) as mock_hybrid_schedule_api,
        patch.object(
            FRCAPI, "match_scores", return_value=InstantFuture(score_response)
        ) as mock_match_scores_api,
        patch.object(FMSAPIHybridScheduleParser, "parse") as mock_schedule_parse,
        patch.object(FMSAPIMatchDetailsParser, "parse") as mock_match_detail_parser,
    ):
        mock_schedule_parse.side_effect = ([], [])
        mock_match_detail_parser.return_value = {}
        df.get_event_matches("2014gal").get_result()

    mock_hybrid_schedule_api.assert_has_calls(
        [call(2014, "galileo", "qual"), call(2014, "galileo", "playoff")]
    )
    mock_match_scores_api.assert_has_calls(
        [call(2014, "galileo", "qual"), call(2014, "galileo", "playoff")]
    )
    mock_schedule_parse.assert_has_calls(
        [call({"Schedule": []}), call({"Schedule": []})]
    )


def test_get_event_matches_qual_sync_disabled() -> None:
    e = Event(
        id="2025casj",
        year=2025,
        event_short="casj",
        start_date=datetime.datetime(2025, 4, 1),
        end_date=datetime.datetime(2025, 4, 3),
        event_type_enum=EventType.OFFSEASON,
        official=True,
        disable_sync_flags=(0 | EventSyncType.EVENT_QUAL_MATCHES),
    )
    e.put()

    schedule_response = URLFetchResult.mock_for_content(
        "", 200, json.dumps({"Schedule": []})
    )
    score_response = URLFetchResult.mock_for_content("", 200, "")

    df = DatafeedFMSAPI()
    with (
        patch.object(
            FRCAPI, "hybrid_schedule", return_value=InstantFuture(schedule_response)
        ) as mock_hybrid_schedule_api,
        patch.object(
            FRCAPI, "match_scores", return_value=InstantFuture(score_response)
        ) as mock_match_scores_api,
        patch.object(FMSAPIHybridScheduleParser, "parse") as mock_schedule_parse,
        patch.object(FMSAPIMatchDetailsParser, "parse") as mock_match_detail_parser,
    ):
        mock_schedule_parse.side_effect = ([], [])
        mock_match_detail_parser.return_value = {}
        df.get_event_matches("2025casj").get_result()

    mock_hybrid_schedule_api.assert_has_calls([call(2025, "casj", "playoff")])
    mock_match_scores_api.assert_has_calls([call(2025, "casj", "playoff")])
    mock_schedule_parse.assert_has_calls(
        [call({"Schedule": []}), call({"Schedule": []})]
    )


def test_get_event_matches_playoff_sync_disabled() -> None:
    e = Event(
        id="2025casj",
        year=2025,
        event_short="casj",
        start_date=datetime.datetime(2025, 4, 1),
        end_date=datetime.datetime(2025, 4, 3),
        event_type_enum=EventType.OFFSEASON,
        official=True,
        disable_sync_flags=(0 | EventSyncType.EVENT_PLAYOFF_MATCHES),
    )
    e.put()

    schedule_response = URLFetchResult.mock_for_content(
        "", 200, json.dumps({"Schedule": []})
    )
    score_response = URLFetchResult.mock_for_content("", 200, "")

    df = DatafeedFMSAPI()
    with (
        patch.object(
            FRCAPI, "hybrid_schedule", return_value=InstantFuture(schedule_response)
        ) as mock_hybrid_schedule_api,
        patch.object(
            FRCAPI, "match_scores", return_value=InstantFuture(score_response)
        ) as mock_match_scores_api,
        patch.object(FMSAPIHybridScheduleParser, "parse") as mock_schedule_parse,
        patch.object(FMSAPIMatchDetailsParser, "parse") as mock_match_detail_parser,
    ):
        mock_schedule_parse.side_effect = ([], [])
        mock_match_detail_parser.return_value = {}
        df.get_event_matches("2025casj").get_result()

    mock_hybrid_schedule_api.assert_has_calls([call(2025, "casj", "qual")])
    mock_match_scores_api.assert_has_calls([call(2025, "casj", "qual")])
    mock_schedule_parse.assert_has_calls(
        [call({"Schedule": []}), call({"Schedule": []})]
    )


def test_get_event_matches_both_sync_disabled() -> None:
    e = Event(
        id="2025casj",
        year=2025,
        event_short="casj",
        start_date=datetime.datetime(2025, 4, 1),
        end_date=datetime.datetime(2025, 4, 3),
        event_type_enum=EventType.OFFSEASON,
        official=True,
        disable_sync_flags=(
            0 | EventSyncType.EVENT_QUAL_MATCHES | EventSyncType.EVENT_PLAYOFF_MATCHES
        ),
    )
    e.put()

    schedule_response = URLFetchResult.mock_for_content(
        "", 200, json.dumps({"Schedule": []})
    )
    score_response = URLFetchResult.mock_for_content("", 200, "")

    df = DatafeedFMSAPI()
    with (
        patch.object(
            FRCAPI, "hybrid_schedule", return_value=InstantFuture(schedule_response)
        ) as mock_hybrid_schedule_api,
        patch.object(
            FRCAPI, "match_scores", return_value=InstantFuture(score_response)
        ) as mock_match_scores_api,
        patch.object(FMSAPIHybridScheduleParser, "parse") as mock_schedule_parse,
        patch.object(FMSAPIMatchDetailsParser, "parse") as mock_match_detail_parser,
    ):
        mock_schedule_parse.side_effect = ([], [])
        mock_match_detail_parser.return_value = {}
        df.get_event_matches("2025casj").get_result()

    mock_hybrid_schedule_api.assert_has_calls([])
    mock_match_scores_api.assert_has_calls([])
    mock_schedule_parse.assert_has_calls(
        [call({"Schedule": []}), call({"Schedule": []})]
    )
