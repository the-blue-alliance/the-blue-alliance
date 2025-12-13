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
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_event_list_parser import (
    FMSAPIEventListParser,
)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_get_event_list() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/events",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "event_list", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPIEventListParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIEventListParser, "parse"
    ) as mock_parse:
        df.get_event_list(2020).get_result()

    mock_api.assert_called_once_with(2020)
    mock_init.assert_called_once_with(2020)
    mock_parse.assert_called_once_with(response.json())


def test_get_event_details() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/events?eventCode=MIKET",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "event_info", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPIEventListParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIEventListParser, "parse"
    ) as mock_parse:
        df.get_event_details("2020miket").get_result()

    mock_api.assert_called_once_with(2020, "miket")
    mock_init.assert_called_once_with(2020, short="miket")
    mock_parse.assert_called_once_with(response.json())


def test_get_event_details_cmp() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2014/events?eventCode=GALILEO",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "event_info", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPIEventListParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIEventListParser, "parse"
    ) as mock_parse:
        df.get_event_details("2014gal").get_result()

    mock_api.assert_called_once_with(2014, "galileo")
    mock_init.assert_called_once_with(2014, short="gal")
    mock_parse.assert_called_once_with(response.json())
