from unittest.mock import patch

import pytest
from google.appengine.ext import testbed

from backend.tasks_io.api.nexus_api import NexusAPI


@pytest.fixture(autouse=True)
def auto_add_urlfetch_stub(
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    pass


def test_init_no_secrets(ndb_stub) -> None:
    with pytest.raises(
        Exception, match="Missing Nexus API key. Setup nexus.secrets sitevar"
    ):
        NexusAPI()


def test_init_auth_token(ndb_stub) -> None:
    NexusAPI(auth_token="test")


def test_pit_status(ndb_stub) -> None:
    api = NexusAPI(auth_token="test")
    with patch.object(NexusAPI, "_get") as mock_get:
        api.pit_locations("2019casj")

    mock_get.assert_called_once_with("/event/2019casj/pits")


def test_event_queue_status(ndb_stub) -> None:
    api = NexusAPI(auth_token="test")
    with patch.object(NexusAPI, "_get") as mock_get:
        api.queue_status("2019casj")

    mock_get.assert_called_once_with("/event/2019casj")


def test_get(
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    api = NexusAPI(auth_token="test")

    expected_url = "https://frc.nexus/api/v1/event/2019casj"
    expected_headers = {
        "Accept": "application/json",
        "Cache-Control": "no-cache, max-age=10",
        "Pragma": "no-cache",
        "Nexus-Api-Key": "test",
    }

    with patch.object(urlfetch_stub, "_Dynamic_Fetch") as mock_fetch:
        api._get("/event/2019casj").get_result()

    assert mock_fetch.call_count == 1
    called_request = mock_fetch.call_args[0][0]
    assert called_request.Url == expected_url

    called_headers = {h.Key: h.Value for h in called_request.header}
    assert called_headers == expected_headers
