from unittest.mock import patch

import pytest

from backend.common.frc_api import FRCAPI
from backend.common.futures import InstantFuture
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_event_rankings_parser import (
    FMSAPIEventRankingsParser,
)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_get_event_rankings() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/rankings?eventCode=MIKET&page=1",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "rankings", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPIEventRankingsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIEventRankingsParser, "parse"
    ) as mock_parse:
        mock_parse.side_effect = [([], False)]
        df.get_event_rankings("2020miket").get_result()

    mock_api.assert_called_once_with(2020, "miket")
    mock_init.assert_called_once_with(2020)
    mock_parse.assert_called_once_with(response.json())


def test_get_event_rankings_cmp() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2014/teams?eventCode=GALILEO&page=1",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "rankings", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPIEventRankingsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIEventRankingsParser, "parse"
    ) as mock_parse:
        mock_parse.side_effect = [([], False)]
        df.get_event_rankings("2014gal").get_result()

    mock_api.assert_called_once_with(2014, "galileo")
    mock_init.assert_called_once_with(2014)
    mock_parse.assert_called_once_with(response.json())
