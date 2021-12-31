from unittest.mock import patch

import pytest

from backend.common.frc_api import FRCAPI
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets


def test_init_no_fmsapi_secrets(ndb_stub):
    with pytest.raises(
        Exception, match="Missing FRC API auth token. Setup fmsapi.secrets sitevar."
    ):
        FRCAPI()


def test_init_fmsapi_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))
    api = FRCAPI()

    assert api.session is not None

    auth_token = api.session.headers["Authorization"]
    assert auth_token == "Basic emFjaDphdXRoa2V5"


def test_init_auth_token():
    api = FRCAPI("test")

    assert api.session is not None

    auth_token = api.session.headers["Authorization"]
    assert auth_token == "Basic test"


def test_init_with_credentials():
    api = FRCAPI.with_credentials("zach", "authkey")

    assert api.session is not None

    auth_token = api.session.headers["Authorization"]
    assert auth_token == "Basic emFjaDphdXRoa2V5"


def test_root():
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.root()

    mock_get.assert_called_once_with("/")


def test_event_list():
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_list(2020)
    mock_get.assert_called_once_with("/2020/events")


def test_event_info():
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_info(2020, "MIKET")
    mock_get.assert_called_once_with("/2020/events?eventCode=MIKET")


def test_event_teams():
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_teams(2020, "MIKET", 1)
    mock_get.assert_called_once_with("/2020/teams?eventCode=MIKET&page=1")


def test_event_team_avatars():
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_team_avatars(2020, "MIKET", 1)
    mock_get.assert_called_once_with("/2020/avatars?eventCode=MIKET&page=1")


def test_awards_no_event_code_no_team_number():
    api = FRCAPI("zach")
    with pytest.raises(
        FRCAPI.ValidationError,
        match="awards expects either an event_code, team_number, or both",
    ):
        api.awards(2020)


def test_awards_event_code():
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.awards(2020, event_code="MIKET")

    mock_get.assert_called_once_with("/2020/awards/MIKET/0")


def test_awards_team_number():
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.awards(2020, team_number=2337)

    mock_get.assert_called_once_with("/2020/awards/2337")


def test_awards_event_code_team_number():
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.awards(2020, event_code="MIKET", team_number=2337)

    mock_get.assert_called_once_with("/2020/awards/MIKET/2337")


def test_district_list():
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.district_list(2020)
    mock_get.assert_called_once_with("/2020/districts")


@pytest.mark.parametrize(
    "endpoint", ["/2020/awards/MIKET", "2020/awards/MIKET", "///2020/awards/MIKET"]
)
def test_get(endpoint):
    api = FRCAPI("zach")

    expected_url = "https://frc-api.firstinspires.org/v3.0/2020/awards/MIKET"
    expected_headers = {
        "Accept": "application/json",
        "Cache-Control": "no-cache, max-age=10",
        "Pragma": "no-cache",
    }

    with patch.object(api.session, "get") as mock_get:
        api._get(endpoint)

    mock_get.assert_called_once_with(expected_url, headers=expected_headers)
