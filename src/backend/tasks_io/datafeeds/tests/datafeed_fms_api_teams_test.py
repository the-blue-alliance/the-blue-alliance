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
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_team_avatar_parser import (
    FMSAPITeamAvatarParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_team_details_parser import (
    FMSAPITeamDetailsParser,
)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_get_team_details() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/teams?teamNumber=254",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "team_details", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPITeamDetailsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPITeamDetailsParser, "parse"
    ) as mock_parse:
        mock_parse.side_effect = [([], False)]
        df.get_team_details(2020, "frc254")

    mock_api.assert_called_once_with(2020, 254)
    mock_init.assert_called_once_with(2020)
    mock_parse.assert_called_once_with(response.json())


def test_get_team_avatar() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/avatars?teamNumber=254",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "team_avatar", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPITeamAvatarParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPITeamAvatarParser, "parse"
    ) as mock_parse:
        mock_parse.side_effect = [(([], []), False)]
        df.get_team_avatar(2020, "frc254")

    mock_api.assert_called_once_with(2020, 254)
    mock_init.assert_called_once_with(2020)
    mock_parse.assert_called_once_with(response.json())


def test_get_team_avatar_parser_failed() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/avatars?teamNumber=254",
        500,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "team_avatar", return_value=InstantFuture(response)
    ) as mock_api, patch.object(
        FMSAPITeamAvatarParser, "__init__", return_value=None
    ) as mock_init:
        assert df.get_team_avatar(2020, "frc254") == ([], set())

    mock_api.assert_called_once_with(2020, 254)
    mock_init.assert_called_once_with(2020)
