from unittest.mock import call, Mock, patch

import pytest
from requests import Response

from backend.common.frc_api import FRCAPI
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_match_parser import (
    FMSAPIHybridScheduleParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.simple_json_parser import (
    FMSAPISimpleJsonParser,
)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_get_event_matches() -> None:
    response = Mock(spec=Response)
    response.status_code = 200
    response.url = ""

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "match_schedule", return_value=response
    ) as mock_schedule_api, patch.object(
        FRCAPI, "matches", return_value=response
    ) as mock_matches_api, patch.object(
        FMSAPIHybridScheduleParser, "parse"
    ) as mock_schedule_parse, patch.object(
        FMSAPISimpleJsonParser, "parse"
    ) as mock_json_parse:
        mock_schedule_parse.side_effect = ([], [])
        mock_json_parse.return_value = {"Schedule": [], "Matches": []}
        df.get_event_matches("2020miket")

    mock_schedule_api.assert_has_calls(
        [call(2020, "miket", "qual"), call(2020, "miket", "playoff")]
    )
    mock_matches_api.assert_has_calls(
        [call(2020, "miket", "qual"), call(2020, "miket", "playoff")]
    )
    mock_schedule_parse.assert_has_calls(
        [call({"Schedule": []}), call({"Schedule": []})]
    )


def test_get_event_matches_cmp() -> None:
    response = Mock(spec=Response)
    response.status_code = 200
    response.url = ""

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "match_schedule", return_value=response
    ) as mock_schedule_api, patch.object(
        FRCAPI, "matches", return_value=response
    ) as mock_matches_api, patch.object(
        FMSAPIHybridScheduleParser, "parse"
    ) as mock_schedule_parse, patch.object(
        FMSAPISimpleJsonParser, "parse"
    ) as mock_json_parse:
        mock_schedule_parse.side_effect = ([], [])
        mock_json_parse.return_value = {"Schedule": [], "Matches": []}
        df.get_event_matches("2014gal")

    mock_schedule_api.assert_has_calls(
        [call(2014, "galileo", "qual"), call(2014, "galileo", "playoff")]
    )
    mock_matches_api.assert_has_calls(
        [call(2014, "galileo", "qual"), call(2014, "galileo", "playoff")]
    )
    mock_schedule_parse.assert_has_calls(
        [call({"Schedule": []}), call({"Schedule": []})]
    )
