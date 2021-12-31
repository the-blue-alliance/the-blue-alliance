from unittest.mock import call, Mock, patch

import pytest
from requests import Response

from backend.common.frc_api import FRCAPI
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_team_details_parser import (
    FMSAPITeamDetailsParser,
)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_get_event_teams() -> None:
    response = Mock(spec=Response)
    response.status_code = 200
    response.url = (
        "https://frc-api.firstinspires.org/v3.0/2020/teams?eventCode=MIKET&page=1"
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "event_teams", return_value=response
    ) as mock_api, patch.object(
        FMSAPITeamDetailsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPITeamDetailsParser, "parse"
    ) as mock_parse:
        mock_parse.side_effect = [([], False)]
        df.get_event_teams("2020miket")

    mock_api.assert_called_once_with(2020, "miket", 1)
    mock_init.assert_called_once_with(2020)
    mock_parse.assert_called_once_with(response.json())


def test_get_event_teams_paginated() -> None:
    response = Mock(spec=Response)
    response.status_code = 200
    response.url = (
        "https://frc-api.firstinspires.org/v3.0/2020/teams?eventCode=MIKET&page=1"
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "event_teams", return_value=response
    ) as mock_api, patch.object(
        FMSAPITeamDetailsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPITeamDetailsParser, "parse"
    ) as mock_parse:
        mock_parse.side_effect = [([], True), ([], False)]
        df.get_event_teams("2020miket")

    mock_api.assert_has_calls([call(2020, "miket", 1), call(2020, "miket", 2)])
    mock_init.assert_called_once_with(2020)
    assert mock_parse.call_count == 2


def test_get_event_teams_cmp() -> None:
    response = Mock(spec=Response)
    response.status_code = 200
    response.url = (
        "https://frc-api.firstinspires.org/v3.0/2014/teams?eventCode=GALILEO&page=1"
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "event_teams", return_value=response
    ) as mock_api, patch.object(
        FMSAPITeamDetailsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPITeamDetailsParser, "parse"
    ) as mock_parse:
        mock_parse.side_effect = [([], False)]
        df.get_event_teams("2014gal")

    mock_api.assert_called_once_with(2014, "galileo", 1)
    mock_init.assert_called_once_with(2014)
    mock_parse.assert_called_once_with(response.json())
