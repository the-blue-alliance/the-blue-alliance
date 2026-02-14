import json
from typing import Dict, List, Optional

import pytest
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH_PATCH = "/api/trusted/v1/event/2014casj/webcasts/update"
REQUEST_PATH_DELETE = "/api/trusted/v1/event/2014casj/webcasts/update"


def setup_event(
    webcast_json: Optional[str] = None,
) -> None:
    event = Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
    )
    if webcast_json:
        event.webcast_json = webcast_json
    event.put()


def setup_auth(access_types: List[AuthType]) -> None:
    ApiAuthAccess(
        id=AUTH_ID,
        secret=AUTH_SECRET,
        event_list=[ndb.Key(Event, "2014casj")],
        auth_types_enum=access_types,
    ).put()


def get_auth_headers(request_path: str, request_body: str) -> Dict[str, str]:
    return {
        "X-TBA-Auth-Id": AUTH_ID,
        "X-TBA-AUth-Sig": TrustedApiAuthHelper.compute_auth_signature(
            AUTH_SECRET, request_path, request_body
        ),
    }


def test_bad_event_key(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.patch(
        "/api/trusted/v1/event/asdf/webcasts/update",
        data=json.dumps({"webcasts": []}),
    )
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.patch(
        "/api/trusted/v1/event/2015casj/webcasts/update",
        data=json.dumps({"webcasts": []}),
    )
    assert resp.status_code == 404


def test_bad_auth_type_patch(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.patch(REQUEST_PATH_PATCH, data=json.dumps({"webcasts": []}))
    assert resp.status_code == 401


def test_bad_auth_type_delete(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.delete(REQUEST_PATH_DELETE, data=json.dumps({"webcasts": []}))
    assert resp.status_code == 401


def test_no_auth(api_client: Client) -> None:
    setup_event()

    request_body = json.dumps({"webcasts": []})
    response = api_client.patch(
        REQUEST_PATH_PATCH,
        headers=get_auth_headers(REQUEST_PATH_PATCH, request_body),
        data=request_body,
    )
    assert response.status_code == 401


def test_patch_add_single_webcast(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "webcasts": [
            {
                "type": "youtube",
                "channel": "abc123",
            },
        ]
    }
    request_body = json.dumps(request)
    response = api_client.patch(
        REQUEST_PATH_PATCH,
        headers=get_auth_headers(REQUEST_PATH_PATCH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    webcasts = event.webcast
    assert len(webcasts) == 1
    assert webcasts[0]["type"] == "youtube"
    assert webcasts[0]["channel"] == "abc123"


def test_patch_add_multiple_webcasts(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "webcasts": [
            {"type": "youtube", "channel": "abc123"},
            {"type": "twitch", "channel": "def456"},
        ]
    }
    request_body = json.dumps(request)
    response = api_client.patch(
        REQUEST_PATH_PATCH,
        headers=get_auth_headers(REQUEST_PATH_PATCH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    webcasts = event.webcast
    assert len(webcasts) == 2
    assert webcasts[0]["type"] == "youtube"
    assert webcasts[0]["channel"] == "abc123"
    assert webcasts[1]["type"] == "twitch"
    assert webcasts[1]["channel"] == "def456"


def test_patch_append_to_existing_webcasts(api_client: Client) -> None:
    existing_webcast = json.dumps(
        [
            {"type": "youtube", "channel": "existing123"},
        ]
    )
    setup_event(webcast_json=existing_webcast)
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "webcasts": [
            {"type": "twitch", "channel": "new456"},
        ]
    }
    request_body = json.dumps(request)
    response = api_client.patch(
        REQUEST_PATH_PATCH,
        headers=get_auth_headers(REQUEST_PATH_PATCH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    webcasts = event.webcast
    assert len(webcasts) == 2
    assert webcasts[0]["type"] == "youtube"
    assert webcasts[0]["channel"] == "existing123"
    assert webcasts[1]["type"] == "twitch"
    assert webcasts[1]["channel"] == "new456"


def test_patch_no_webcasts_provided(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request_body = json.dumps({})
    response = api_client.patch(
        REQUEST_PATH_PATCH,
        headers=get_auth_headers(REQUEST_PATH_PATCH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_delete_single_webcast(api_client: Client) -> None:
    existing_webcasts = json.dumps(
        [
            {"type": "youtube", "channel": "abc123"},
            {"type": "twitch", "channel": "def456"},
        ]
    )
    setup_event(webcast_json=existing_webcasts)
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "webcasts": [
            {"type": "youtube", "channel": "abc123"},
        ]
    }
    request_body = json.dumps(request)
    response = api_client.delete(
        REQUEST_PATH_DELETE,
        headers=get_auth_headers(REQUEST_PATH_DELETE, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    webcasts = event.webcast
    assert len(webcasts) == 1
    assert webcasts[0]["type"] == "twitch"
    assert webcasts[0]["channel"] == "def456"


def test_delete_multiple_webcasts(api_client: Client) -> None:
    existing_webcasts = json.dumps(
        [
            {"type": "youtube", "channel": "abc123"},
            {"type": "twitch", "channel": "def456"},
            {"type": "youtube", "channel": "ghi789"},
        ]
    )
    setup_event(webcast_json=existing_webcasts)
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "webcasts": [
            {"type": "youtube", "channel": "abc123"},
            {"type": "twitch", "channel": "def456"},
        ]
    }
    request_body = json.dumps(request)
    response = api_client.delete(
        REQUEST_PATH_DELETE,
        headers=get_auth_headers(REQUEST_PATH_DELETE, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    webcasts = event.webcast
    assert len(webcasts) == 1
    assert webcasts[0]["type"] == "youtube"
    assert webcasts[0]["channel"] == "ghi789"


def test_delete_non_existent_webcast(api_client: Client) -> None:
    existing_webcasts = json.dumps(
        [
            {"type": "youtube", "channel": "abc123"},
        ]
    )
    setup_event(webcast_json=existing_webcasts)
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "webcasts": [
            {"type": "twitch", "channel": "nonexistent"},
        ]
    }
    request_body = json.dumps(request)
    response = api_client.delete(
        REQUEST_PATH_DELETE,
        headers=get_auth_headers(REQUEST_PATH_DELETE, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    webcasts = event.webcast
    assert len(webcasts) == 1
    assert webcasts[0]["type"] == "youtube"
    assert webcasts[0]["channel"] == "abc123"


def test_delete_all_webcasts(api_client: Client) -> None:
    existing_webcasts = json.dumps(
        [
            {"type": "youtube", "channel": "abc123"},
            {"type": "twitch", "channel": "def456"},
        ]
    )
    setup_event(webcast_json=existing_webcasts)
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "webcasts": [
            {"type": "youtube", "channel": "abc123"},
            {"type": "twitch", "channel": "def456"},
        ]
    }
    request_body = json.dumps(request)
    response = api_client.delete(
        REQUEST_PATH_DELETE,
        headers=get_auth_headers(REQUEST_PATH_DELETE, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    webcasts = event.webcast
    assert len(webcasts) == 0


def test_delete_no_webcasts_provided(api_client: Client) -> None:
    existing_webcasts = json.dumps(
        [
            {"type": "youtube", "channel": "abc123"},
        ]
    )
    setup_event(webcast_json=existing_webcasts)
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request_body = json.dumps({})
    response = api_client.delete(
        REQUEST_PATH_DELETE,
        headers=get_auth_headers(REQUEST_PATH_DELETE, request_body),
        data=request_body,
    )
    assert response.status_code == 400
