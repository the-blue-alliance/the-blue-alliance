import datetime
import json
from typing import Any
from unittest import mock

import pytest

from backend.common.consts.event_type import EventType
from backend.common.futures import InstantFuture
from backend.common.models.event import Event
from backend.common.sitevars.nexus_api_secret import (
    ContentType as NexusAPISecretsContentType,
)
from backend.common.sitevars.nexus_api_secret import NexusApiSecrets
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_nexus import (
    _DatafeedNexus,
    NexusEventQueueStatus,
    NexusPitLocations,
)
from backend.tasks_io.datafeeds.parsers.nexus_api.pit_location_parser import (
    NexusAPIPitLocationParser,
)
from backend.tasks_io.datafeeds.parsers.nexus_api.queue_status_parser import (
    NexusAPIQueueStatusParser,
)
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class DummyDatafeedNexus(_DatafeedNexus[Any]):

    def endpoint(self) -> str:
        return "/"

    def parser(self):
        class DummyParser(ParserBase[Any]):
            def parse(self, response):
                return response

        return DummyParser()


@pytest.fixture()
def nexus_api_secrets(ndb_stub) -> None:
    NexusApiSecrets.put(NexusAPISecretsContentType(api_secret="abc123"))


def create_event() -> Event:
    e = Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        start_date=datetime.datetime(2019, 4, 1),
        end_date=datetime.datetime(2019, 4, 3),
        event_type_enum=EventType.REGIONAL,
        official=True,
    )
    e.put()
    return e


def test_init_requires_secret(ndb_stub) -> None:
    with pytest.raises(
        Exception, match="Missing Nexus API key. Setup nexus.secrets sitevar"
    ):
        DummyDatafeedNexus()


def test_headers(ndb_stub, nexus_api_secrets) -> None:
    df = DummyDatafeedNexus()
    assert df.headers() == {
        "Accept": "application/json",
        "Cache-Control": "no-cache, max-age=10",
        "Nexus-Api-Key": "abc123",
        "Pragma": "no-cache",
    }


def test_versioned_url(ndb_stub, nexus_api_secrets) -> None:
    df = DummyDatafeedNexus()
    assert df.url() == "https://frc.nexus/api/v1/"


@mock.patch.object(_DatafeedNexus, "_fetch")
def test_request(api_mock: mock.Mock, ndb_stub, nexus_api_secrets) -> None:
    api_response = URLFetchResult.mock_for_content(
        "https://frc.nexus/api/v3/event/2025casj/pits",
        200,
        json.dumps(["test"]),
    )
    api_mock.return_value = InstantFuture(api_response)

    df = DummyDatafeedNexus()
    result = df.fetch_async().get_result()
    assert result == ["test"]


@mock.patch.object(NexusAPIPitLocationParser, "parse")
@mock.patch.object(_DatafeedNexus, "_urlfetch")
def test_get_pit_locations(
    api_mock: mock.Mock, parser_mock: mock.Mock, ndb_stub, nexus_api_secrets
) -> None:
    api_content = {
        "100": "A1",
    }
    api_response = URLFetchResult.mock_for_content(
        "https://frc.nexus/api/v3/event/2025casj/pits",
        200,
        json.dumps(api_content),
    )
    api_mock.return_value = InstantFuture(api_response)
    parser_mock.return_value = api_content

    response = NexusPitLocations("2019casj").fetch_async()
    assert response.get_result() == api_content


@mock.patch.object(NexusAPIPitLocationParser, "parse")
@mock.patch.object(_DatafeedNexus, "_urlfetch")
def test_get_pit_locations_missing(
    api_mock: mock.Mock, parser_mock: mock.Mock, ndb_stub, nexus_api_secrets
) -> None:
    api_content = "No pits"
    api_response = URLFetchResult.mock_for_content(
        "https://frc.nexus/api/v3/event/2025casj/pits",
        404,
        json.dumps(api_content),
    )
    api_mock.return_value = InstantFuture(api_response)

    response = NexusPitLocations("2019casj").fetch_async()
    assert response.get_result() is None
    parser_mock.assert_not_called()


@mock.patch.object(NexusAPIPitLocationParser, "parse")
@mock.patch.object(_DatafeedNexus, "_urlfetch")
def test_get_pit_locations_error(
    api_mock: mock.Mock, parser_mock: mock.Mock, ndb_stub, nexus_api_secrets
) -> None:
    api_content = ""
    api_response = URLFetchResult.mock_for_content(
        "https://frc.nexus/api/v3/event/2025casj/pits",
        500,
        json.dumps(api_content),
    )
    api_mock.return_value = InstantFuture(api_response)

    response = NexusPitLocations("2019casj").fetch_async()
    assert response.get_result() is None
    parser_mock.assert_not_called()


@mock.patch.object(NexusAPIQueueStatusParser, "parse")
@mock.patch.object(_DatafeedNexus, "_urlfetch")
def test_get_event_queue_status(
    api_mock: mock.Mock, parser_mock: mock.Mock, ndb_stub, nexus_api_secrets
) -> None:
    e = create_event()
    api_content = {}
    api_response = URLFetchResult.mock_for_content(
        "https://frc.nexus/api/v3/event/2025casj/",
        200,
        json.dumps(api_content),
    )
    api_mock.return_value = InstantFuture(api_response)
    parser_mock.return_value = api_content

    response = NexusEventQueueStatus(e).fetch_async()
    assert response.get_result() == api_content
