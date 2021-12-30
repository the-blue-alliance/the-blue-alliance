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
