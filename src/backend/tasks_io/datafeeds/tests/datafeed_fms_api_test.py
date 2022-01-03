import json
from unittest.mock import Mock, patch

import pytest
from requests import Response

from backend.common.frc_api import FRCAPI
from backend.common.models.event import Event
from backend.common.sitevars.apistatus_fmsapi_down import ApiStatusFMSApiDown
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.storage.clients.in_memory_client import InMemoryClient
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


@pytest.fixture(autouse=True)
def reset_gcs_client():
    yield
    InMemoryClient.CLIENT = None


@pytest.fixture()
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_init(ndb_stub):
    with pytest.raises(
        Exception, match="Missing FRC API auth token. Setup fmsapi.secrets sitevar."
    ):
        DatafeedFMSAPI(save_response=True)


@pytest.mark.parametrize(
    "event_code, expected",
    list(DatafeedFMSAPI.EVENT_SHORT_EXCEPTIONS.items()) + [("miket", "miket")],
)
def test_get_event_short_event_first_code_none(event_code, expected):
    event = Mock(spec=Event)
    event.first_code = None
    assert DatafeedFMSAPI._get_event_short(event_code, event) == expected


def test_get_event_short_event_first_code():
    event = Mock(spec=Event)
    event.first_code = "MIKET"
    assert DatafeedFMSAPI._get_event_short("2020miket", event) == event.first_code


def test_get_event_short_event_cmp():
    assert DatafeedFMSAPI._get_event_short("arc") == "archimedes"


def test_get_root(fms_api_secrets):
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }
    response = Mock(spec=Response)
    response.status_code = 200
    response.url = "https://frc-api.firstinspires.org/v3.0/"
    response.json.return_value = content
    response.content = json.dumps(content).encode()

    df = DatafeedFMSAPI(save_response=True)
    with patch.object(FRCAPI, "root", return_value=response) as mock_root:
        df.get_root_info() is None

    mock_root.assert_called_once_with()


def test_get_root_failure(fms_api_secrets):
    content = {}
    response = Mock(spec=Response)
    response.status_code = 500
    response.url = "https://frc-api.firstinspires.org/v3.0/"
    response.json.return_value = content
    response.content = json.dumps(content).encode()

    df = DatafeedFMSAPI(save_response=True)
    with patch.object(FRCAPI, "root", return_value=response) as mock_root:
        assert df.get_root_info() is None

    mock_root.assert_called_once_with()


def test_mark_api_down(fms_api_secrets):
    response1 = Mock(spec=Response)
    response1.status_code = 500
    response1.url = "https://frc-api.firstinspires.org/v3.0/"

    response2 = Mock(spec=Response)
    response2.status_code = 200
    response2.url = "https://frc-api.firstinspires.org/v3.0/"
    response2.json.return_value = {}
    response2.content = b"{}"

    df = DatafeedFMSAPI(save_response=True)
    with patch.object(FRCAPI, "root", return_value=response1):
        assert df.get_root_info() is None
        assert ApiStatusFMSApiDown.get() is True

    with patch.object(FRCAPI, "root", return_value=response2):
        assert df.get_root_info() == {}
        assert ApiStatusFMSApiDown.get() is False


def test_save_response(fms_api_secrets, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }
    response = Mock(spec=Response)
    response.status_code = 200
    response.url = "https://frc-api.firstinspires.org/v3.0/root"
    response.json.return_value = content
    response.content = json.dumps(content).encode()

    df = DatafeedFMSAPI(save_response=True)
    with patch.object(FRCAPI, "root", return_value=response):
        df.get_root_info()

    client = InMemoryClient.get()
    files = client.get_files()
    assert len(files) == 1

    f = client.read(files[0])
    assert f is not None
    assert f == response.content.decode()


def test_save_response_unchanged(fms_api_secrets, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }
    response = Mock(spec=Response)
    response.status_code = 200
    response.url = "https://frc-api.firstinspires.org/v3.0/root"
    response.json.return_value = content
    response.content = json.dumps(content).encode()

    df = DatafeedFMSAPI(save_response=True)
    with patch.object(FRCAPI, "root", return_value=response):
        df.get_root_info()

    client = InMemoryClient.get()
    files = client.get_files()
    assert len(files) == 1
    f_name = files[0]

    with patch.object(FRCAPI, "root", return_value=response):
        df.get_root_info()

    # Since the content didn't change, we shouldn't have written another
    assert client.get_files() == [f_name]


def test_save_response_updated(fms_api_secrets, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }
    response = Mock(spec=Response)
    response.status_code = 200
    response.url = "https://frc-api.firstinspires.org/v3.0/root"
    response.json.return_value = content
    response.content = json.dumps(content).encode()

    df = DatafeedFMSAPI(save_response=True)
    with patch.object(FRCAPI, "root", return_value=response):
        df.get_root_info()

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
    response2 = Mock(spec=Response)
    response2.status_code = 200
    response2.url = "https://frc-api.firstinspires.org/v3.0/root"
    response2.json.return_value = content2
    response2.content = json.dumps(content2).encode()
    with patch.object(FRCAPI, "root", return_value=response2):
        df.get_root_info()

    # Since the content is different, we should have two items
    files = client.get_files()
    assert len(files) == 2

    f = client.read(files[0])
    assert f is not None
    assert f == response.content.decode()

    f2 = client.read(files[1])
    assert f2 is not None
    assert f2 == response2.content.decode()
