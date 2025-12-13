import json
from unittest.mock import patch

import pytest
from google.appengine.ext import testbed

from backend.common.frc_api import FRCAPI
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.storage.clients.in_memory_client import InMemoryClient


@pytest.fixture(autouse=True)
def auto_add_urlfetch_stub(
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    pass


@pytest.fixture(autouse=True)
def reset_gcs_client():
    yield
    InMemoryClient.CLIENT = None


def test_init_no_fmsapi_secrets(ndb_stub) -> None:
    with pytest.raises(
        Exception, match="Missing FRC API auth token. Setup fmsapi.secrets sitevar."
    ):
        FRCAPI()


def test_init_fmsapi_secrets(ndb_stub) -> None:
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))
    api = FRCAPI()
    assert api.auth_token == "emFjaDphdXRoa2V5"


def test_init_auth_token() -> None:
    api = FRCAPI("test")
    assert api.auth_token == "test"


def test_init_with_credentials() -> None:
    api = FRCAPI.with_credentials("zach", "authkey")
    assert api.auth_token == "emFjaDphdXRoa2V5"


def test_root() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.root()

    mock_get.assert_called_once_with("/")


def test_event_list() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_list(2020)
    mock_get.assert_called_once_with("/2020/events")


def test_event_info() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_info(2020, "MIKET")
    mock_get.assert_called_once_with("/2020/events?eventCode=MIKET")


def test_event_teams() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_teams(2020, "MIKET", 1)
    mock_get.assert_called_once_with("/2020/teams?eventCode=MIKET&page=1")


def test_event_team_avatars() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_team_avatars(2020, "MIKET", 1)
    mock_get.assert_called_once_with("/2020/avatars?eventCode=MIKET&page=1")


def test_event_alliances() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.alliances(2020, "MIKET")
    mock_get.assert_called_once_with("/2020/alliances/MIKET")


def test_event_rankings() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.rankings(2020, "MIKET")
    mock_get.assert_called_once_with("/2020/rankings/MIKET")


def test_event_schedule() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.match_schedule(2020, "MIKET", "qual")
    mock_get.assert_called_once_with("/2020/schedule/MIKET?tournamentLevel=qual")


def test_event_matches() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.matches(2020, "MIKET", "qual")
    mock_get.assert_called_once_with("/2020/matches/MIKET?tournamentLevel=qual")


def test_event_scores() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.match_scores(2020, "MIKET", "qual")
    mock_get.assert_called_once_with("/2020/scores/MIKET/qual")


def test_awards_no_event_code_no_team_number() -> None:
    api = FRCAPI("zach")
    with pytest.raises(
        FRCAPI.ValidationError,
        match="awards expects either an event_code, team_number, or both",
    ):
        api.awards(2020)


def test_awards_event_code() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.awards(2020, event_code="MIKET")

    mock_get.assert_called_once_with("/2020/awards/event/MIKET")


def test_awards_team_number() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.awards(2020, team_number=2337)

    mock_get.assert_called_once_with("/2020/awards/team/2337")


def test_awards_event_code_team_number() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.awards(2020, event_code="MIKET", team_number=2337)

    mock_get.assert_called_once_with("/2020/awards/eventteam/MIKET/2337")


def test_district_list() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.district_list(2020)
    mock_get.assert_called_once_with("/2020/districts")


def test_district_rankings() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.district_rankings(2020, "ne", 1)
    mock_get.assert_called_once_with("/2020/rankings/district?districtCode=ne&page=1")


def test_team_details() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.team_details(2020, 254)
    mock_get.assert_called_once_with("/2020/teams?teamNumber=254")


def test_team_avatars() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.team_avatar(2020, 254)
    mock_get.assert_called_once_with("/2020/avatars?teamNumber=254")


@pytest.mark.parametrize(
    "endpoint", ["/2020/awards/MIKET", "2020/awards/MIKET", "///2020/awards/MIKET"]
)
def test_get(
    endpoint: str, urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub
) -> None:
    api = FRCAPI("zach")

    expected_url = "https://frc-api.firstinspires.org/v3.0/2020/awards/MIKET"
    expected_headers = {
        "Accept": "application/json",
        "Authorization": "Basic zach",
        "Cache-Control": "no-cache, max-age=10",
        "Pragma": "no-cache",
    }

    with patch.object(urlfetch_stub, "_Dynamic_Fetch") as mock_fetch:
        api._get(endpoint).get_result()

    assert mock_fetch.call_count == 1
    called_request = mock_fetch.call_args[0][0]
    assert called_request.Url == expected_url

    called_headers = {h.Key: h.Value for h in called_request.header}
    assert called_headers == expected_headers


def test_save_response(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }

    def mock_fetch_fn(request, response):
        response.StatusCode = 200
        response.Content = json.dumps(content).encode()

    api = FRCAPI("zach", save_response=True)
    with patch.object(urlfetch_stub, "_Dynamic_Fetch") as mock_fetch:
        mock_fetch.side_effect = mock_fetch_fn
        api.root().get_result()

    client = InMemoryClient.get()
    files = client.get_files()
    assert len(files) == 1

    f = client.read(files[0])
    assert f is not None
    assert f == json.dumps(content).encode()


def test_save_response_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }

    def mock_fetch_fn(request, response):
        response.StatusCode = 200
        response.Content = json.dumps(content).encode()

    api = FRCAPI("zach", save_response=True)
    with patch.object(urlfetch_stub, "_Dynamic_Fetch") as mock_fetch:
        mock_fetch.side_effect = mock_fetch_fn
        api.root().get_result()

    client = InMemoryClient.get()
    files = client.get_files()
    assert len(files) == 1
    f_name = files[0]

    with patch.object(urlfetch_stub, "_Dynamic_Fetch") as mock_fetch:
        mock_fetch.side_effect = mock_fetch_fn
        api.root().get_result()

    # Since the content didn't change, we shouldn't have written another
    assert client.get_files() == [f_name]


def test_save_response_updated(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }

    def mock_fetch_fn(request, response):
        response.StatusCode = 200
        response.Content = json.dumps(content).encode()

    api = FRCAPI("zach", save_response=True)
    with patch.object(urlfetch_stub, "_Dynamic_Fetch") as mock_fetch:
        mock_fetch.side_effect = mock_fetch_fn
        api.root().get_result()

    client = InMemoryClient.get()
    files = client.get_files()
    assert len(files) == 1

    content2 = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "SECOND ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }

    def mock_fetch_fn2(request, response):
        response.StatusCode = 200
        response.Content = json.dumps(content2).encode()

    with patch.object(urlfetch_stub, "_Dynamic_Fetch") as mock_fetch:
        mock_fetch.side_effect = mock_fetch_fn2
        api.root().get_result()

    # Since the content is different, we should have two items
    files = client.get_files()
    assert len(files) == 2

    f = client.read(files[0])
    assert f is not None
    assert f == json.dumps(content).encode()

    f2 = client.read(files[1])
    assert f2 is not None
    assert f2 == json.dumps(content2).encode()
