from unittest.mock import call, patch

import pytest

from backend.common.frc_api import FRCAPI
from backend.common.futures import InstantFuture
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_district_list_parser import (
    FMSAPIDistrictListParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_district_rankings_parser import (
    FMSAPIDistrictRankingsParser,
    TParsedDistrictAdvancement,
)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_get_district_list() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/teams?eventCode=MIKET&page=1",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "district_list", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPIDistrictListParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIDistrictListParser, "parse"
    ) as mock_parse:
        df.get_district_list(2020).get_result()

    mock_api.assert_called_once_with(2020)
    mock_init.assert_called_once_with(2020)
    mock_parse.assert_called_once_with(response.json())


def test_get_district_rankings() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/teams?eventCode=MIKET&page=1",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "district_rankings", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPIDistrictRankingsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIDistrictRankingsParser, "parse"
    ) as mock_parse:
        mock_parse.side_effect = ({}, False)
        df.get_district_rankings("2020ne").get_result()

    mock_api.assert_called_once_with(2020, "ne", 1)
    mock_init.assert_called_once_with()
    mock_parse.assert_called_once_with(response.json())


def test_get_district_rankings_paginated() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/teams?eventCode=MIKET&page=1",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "district_rankings", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPIDistrictRankingsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIDistrictRankingsParser, "parse"
    ) as mock_parse:
        mock_parse.side_effect = [
            (TParsedDistrictAdvancement(advancement={}, adjustments={}), True),
            (TParsedDistrictAdvancement(advancement={}, adjustments={}), False),
        ]
        df.get_district_rankings("2020ne").get_result()

    mock_api.assert_has_calls([call(2020, "ne", 1), call(2020, "ne", 2)])
    mock_init.assert_called_once_with()
    mock_parse.assert_has_calls([call(response.json()), call(response.json())])
