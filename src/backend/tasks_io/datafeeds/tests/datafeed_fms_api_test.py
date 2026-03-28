import json
from typing import cast
from unittest.mock import patch

import pytest

from backend.common.frc_api import FRCAPI
from backend.common.frc_api.types import ApiIndexModelV2
from backend.common.futures import InstantFuture
from backend.common.memcache_models.event_sync_status_memcache import (
    EventSyncStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.sitevars.apistatus_fmsapi_down import ApiStatusFMSApiDown
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.urlfetch import TypedURLFetchResult, URLFetchResult
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_root_parser import (
    FMSAPIRootParser,
)


@pytest.fixture()
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_init(ndb_stub):
    with pytest.raises(
        Exception, match="Missing FRC API auth token. Setup fmsapi.secrets sitevar."
    ):
        DatafeedFMSAPI()


@pytest.mark.parametrize(
    "event_code, expected",
    list(Event.EVENT_SHORT_EXCEPTIONS.items()) + [("miket", "miket")],
)
def test_get_event_short_event_first_code_none(event_code, expected):
    event = Event(
        year=2022,
        event_short=event_code,
    )
    assert DatafeedFMSAPI._get_event_short(event.year, event_code, event) == expected


@pytest.mark.parametrize(
    "event_code, expected",
    list(Event.EVENT_SHORT_EXCEPTIONS_2023.items()),
)
def test_get_event_short_2023_event_first_code_none(event_code, expected):
    event = Event(
        year=2023,
        event_short=event_code,
    )
    assert DatafeedFMSAPI._get_event_short(event.year, event_code, event) == expected


def test_get_event_short_event_first_code():
    event = Event(
        year=2020,
        event_short="miket",
        first_code="miket",
    )
    assert (
        DatafeedFMSAPI._get_event_short(event.year, "miket", event) == event.first_code
    )


def test_get_event_short_event_cmp():
    event = Event(year=2022, event_short="arc")
    assert DatafeedFMSAPI._get_event_short(event.year, "arc", event) == "archimedes"


def test_get_event_short_event_cmp_2023():
    event = Event(year=2023, event_short="arc")
    assert DatafeedFMSAPI._get_event_short(event.year, "arc", event) == "arpky"


def test_get_root(fms_api_secrets):
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/",
        200,
        json.dumps(content),
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "root", return_value=InstantFuture(response)
    ) as mock_root:
        df.get_root_info().get_result() is None

    mock_root.assert_called_once_with()


def test_get_root_failure(fms_api_secrets):
    content = {}
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/",
        500,
        json.dumps(content),
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "root", return_value=InstantFuture(response)
    ) as mock_root:
        assert df.get_root_info().get_result() is None

    mock_root.assert_called_once_with()


def test_mark_api_down(fms_api_secrets):
    response1 = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/",
        500,
        "",
    )

    response2 = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/",
        200,
        "{}",
    )

    df = DatafeedFMSAPI()
    with patch.object(FRCAPI, "root", return_value=InstantFuture(response1)):
        assert df.get_root_info().get_result() is None
        assert ApiStatusFMSApiDown.get() is True

    with patch.object(FRCAPI, "root", return_value=InstantFuture(response2)):
        assert df.get_root_info().get_result() == {}
        assert ApiStatusFMSApiDown.get() is False


def test_parse_records_event_sync_success(fms_api_secrets, ndb_stub) -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/",
        200,
        json.dumps({"apiVersion": "3.0"}),
    )

    df = DatafeedFMSAPI()
    with patch.object(
        DatafeedFMSAPI,
        "_request_endpoint",
        return_value="tasks.get.fmsapi_matches",
    ):
        df._parse(
            cast(TypedURLFetchResult[ApiIndexModelV2], response),
            FMSAPIRootParser(),
            event_key="2025casj",
        )

    status = EventSyncStatusMemcache("2025casj").get()
    assert status is not None
    assert "tasks.get.fmsapi_matches" in status
    assert status["tasks.get.fmsapi_matches"]["num_consecutive_failures"] == 0
    assert status["tasks.get.fmsapi_matches"]["last_success_time"] is not None


def test_parse_records_event_sync_failure(fms_api_secrets, ndb_stub) -> None:
    cache = EventSyncStatusMemcache("2025casj")
    with patch.object(
        DatafeedFMSAPI,
        "_request_endpoint",
        return_value="tasks.get.fmsapi_matches",
    ):
        cache.record_success("tasks.get.fmsapi_matches")

        response = URLFetchResult.mock_for_content(
            "https://frc-api.firstinspires.org/v3.0/",
            500,
            json.dumps({}),
        )

        df = DatafeedFMSAPI()
        df._parse(
            cast(TypedURLFetchResult[ApiIndexModelV2], response),
            FMSAPIRootParser(),
            event_key="2025casj",
        )

    status = cache.get()
    assert status is not None
    assert status["tasks.get.fmsapi_matches"]["num_consecutive_failures"] == 1
