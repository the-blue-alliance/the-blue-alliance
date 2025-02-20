import json
from typing import Dict, List, Optional

import pytest
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/info/update"


def setup_event() -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
    ).put()


def setup_auth(access_types: List[AuthType]) -> None:
    ApiAuthAccess(
        id=AUTH_ID,
        secret=AUTH_SECRET,
        event_list=[ndb.Key(Event, "2014casj")],
        auth_types_enum=access_types,
    ).put()


def get_auth_headers(request_path: str, request_body) -> Dict[str, str]:
    return {
        "X-TBA-Auth-Id": AUTH_ID,
        "X-TBA-AUth-Sig": TrustedApiAuthHelper.compute_auth_signature(
            AUTH_SECRET, request_path, request_body
        ),
    }


def test_bad_event_key(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.post(
        "/api/trusted/v1/event/asdf/info/update", data=json.dumps({})
    )
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.post(
        "/api/trusted/v1/event/2015casj/info/update", data=json.dumps({})
    )
    assert resp.status_code == 404


def test_bad_auth_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.post(
        "/api/trusted/v1/event/2014casj/info/update", data=json.dumps({})
    )
    assert resp.status_code == 401


def test_no_auth(api_client: Client) -> None:
    setup_event()

    request_body = "{}"
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 401


def test_update_event_info(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "first_event_code": "abc123",
        "playoff_type": int(PlayoffType.ROUND_ROBIN_6_TEAM),
        "webcasts": [
            {"url": "https://youtu.be/abc123"},
            {"type": "youtube", "channel": "cde456", "date": "2024-01-03"},
        ],
        "remap_teams": {
            "frc9323": "frc1323B",
            "frc9254": "frc254B",
            "frc8254": "frc254C",
            "frc9000": "frc6000",
        },
        "someother": "randomstuff",  # This should be ignored
    }
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200, response.data

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    assert event.first_code == "abc123"
    assert event.official is True
    assert event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM

    webcasts = event.webcast
    assert len(webcasts) == 2

    webcast = webcasts[0]
    assert webcast["type"] == "youtube"
    assert webcast["channel"] == "abc123"
    assert "date" not in webcast

    webcast = webcasts[1]
    assert webcast["type"] == "youtube"
    assert webcast["channel"] == "cde456"
    assert webcast["date"] == "2024-01-03"

    assert event.remap_teams == {
        "frc9323": "frc1323B",
        "frc9254": "frc254B",
        "frc8254": "frc254C",
        "frc9000": "frc6000",
    }

    # We should have a job enqueued to remap data
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 1


@pytest.mark.parametrize(
    "invalid_webcast",
    [
        {"type": "youtube", "channel": "cde456", "date": "tomorrow"},
        {"type": "youtube", "channel": "cde456", "date": "2024-03-37"},
        {"robot": "robot"},
    ],
)
def test_invalid_webcasts_date(
    invalid_webcast: dict,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    api_client: Client,
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {"webcasts": [invalid_webcast]}
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    assert event.webcast == []
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_invalid_remap_teams_lowercase(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    # Test invalid remap_teams
    request = {
        "remap_teams": {
            "frc9323": "frc1323b",  # lower case
        }
    }
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    assert event.remap_teams is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_invalid_remap_teams_a_team(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "remap_teams": {
            "frc9323": "frc1323A",  # "A" team
        }
    }
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 400
    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    assert event.remap_teams is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_invalid_remap_teams_two_letters(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "remap_teams": {
            "frc9323": "frc1323BB",  # Two letters
        }
    }
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 400
    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    assert event.remap_teams is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_invalid_remap_teams_mapping_from_b_team(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "remap_teams": {
            "frc1323B": "frc1323",  # Mapping from B team
        }
    }

    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 400
    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    assert event.remap_teams is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_invalid_remap_teams_mapping_bad_start_format(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "remap_teams": {
            "1323": "frc1323B",  # Bad starting format
        }
    }
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 400
    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    assert event.remap_teams is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_invalid_remap_teams_mapping_bad_end_format(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "remap_teams": {
            "frc1323": "1323B",  # Bad ending format
        }
    }
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 400
    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    assert event.remap_teams is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0
