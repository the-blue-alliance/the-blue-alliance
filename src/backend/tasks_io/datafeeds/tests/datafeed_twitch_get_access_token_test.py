import json
import time
from typing import Any, Dict
from unittest import mock

import pytest

from backend.common.futures import InstantFuture
from backend.common.sitevars.twitch_secrets import (
    ContentType as TwitchSecretsContent,
    TwitchSecrets,
)
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_twitch import TwitchGetAccessToken


@pytest.fixture
def twitch_secrets(ndb_stub) -> None:
    TwitchSecrets.put(TwitchSecretsContent(client_id="test", client_secret="test"))


def test_init_requires_secrets(ndb_stub) -> None:
    with pytest.raises(
        ValueError,
        match="Missing twitch client ID & secret! Configure TwitchSecrets sitevar",
    ):
        TwitchGetAccessToken(refresh_token=None)


@mock.patch.object(TwitchGetAccessToken, "_fetch")
def test_request_token(api_mock: mock.Mock, twitch_secrets) -> None:
    api_data = {
        "access_token": "rfx2uswqe8l4g1mkagrvg5tv0ks3",
        "expires_in": 14124,
        "refresh_token": "5b93chm6hdve3mycz05zfzatkfdenfspp1h1ar2xxdalen01",
        "scope": [],
        "token_type": "bearer",
    }
    api_response = URLFetchResult.mock_for_content(
        "https://id.twitch.tv/oauth2/token", 200, json.dumps(api_data)
    )
    api_mock.return_value = InstantFuture(api_response)

    df = TwitchGetAccessToken(refresh_token=None)
    assert df.payload()["grant_type"] == "client_credentials"

    result = df.fetch_async().get_result()
    expected: Dict[str, Any] = {
        "client_id": "test",
        "expires_at": int(time.time()) + 14124,
    }
    expected.update(api_data)
    assert result == expected


@mock.patch.object(TwitchGetAccessToken, "_fetch")
def test_refresh_token(api_mock: mock.Mock, twitch_secrets) -> None:
    api_data = {
        "access_token": "rfx2uswqe8l4g1mkagrvg5tv0ks3",
        "expires_in": 14124,
        "refresh_token": "5b93chm6hdve3mycz05zfzatkfdenfspp1h1ar2xxdalen01",
        "scope": [],
        "token_type": "bearer",
    }
    api_response = URLFetchResult.mock_for_content(
        "https://id.twitch.tv/oauth2/token", 200, json.dumps(api_data)
    )
    api_mock.return_value = InstantFuture(api_response)

    df = TwitchGetAccessToken(refresh_token="old_refresh_token")
    assert df.payload()["grant_type"] == "refresh_token"
    assert df.payload()["refresh_token"] == "old_refresh_token"

    result = df.fetch_async().get_result()

    result = df.fetch_async().get_result()
    expected: Dict[str, Any] = {
        "client_id": "test",
        "expires_at": int(time.time()) + 14124,
    }
    expected.update(api_data)
    assert result == expected
