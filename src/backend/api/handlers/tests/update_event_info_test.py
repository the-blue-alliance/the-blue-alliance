import json

import pytest
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_sync_type import EventSyncType
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/info/update"


def setup_event(
    official: bool | None = None,
    playoff_type: PlayoffType | None = None,
    manual_attrs: list[str] | None = None,
) -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
        official=official,
        playoff_type=playoff_type,
        manual_attrs=manual_attrs if manual_attrs is not None else [],
    ).put()


def setup_auth(access_types: list[AuthType]) -> None:
    ApiAuthAccess(
        id=AUTH_ID,
        secret=AUTH_SECRET,
        event_list=[ndb.Key(Event, "2014casj")],
        auth_types_enum=access_types,
    ).put()


def get_auth_headers(request_path: str, request_body) -> dict[str, str]:
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
            {"url": "https://youtu.be/abc12312312"},
            {"type": "youtube", "channel": "cde456", "date": "2024-01-03"},
        ],
        "remap_teams": {
            "frc9323": "frc1323B",
            "frc9254": "frc254B",
            "frc8254": "frc254C",
            "frc9000": "frc6000",
        },
        "timezone": "America/New_York",
        "disable_sync": {
            "event_playoff_matches": True,
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

    event: Event | None = Event.get_by_id("2014casj")
    assert event is not None
    assert event.first_code == "abc123"
    assert event.official is True
    assert event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM
    assert event.timezone_id == "America/New_York"

    webcasts = event.webcast
    assert len(webcasts) == 2

    webcast = webcasts[0]
    assert webcast["type"] == "youtube"
    assert webcast["channel"] == "abc12312312"
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

    assert event.is_sync_enabled(EventSyncType.EVENT_PLAYOFF_MATCHES) is False

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

    event: Event | None = Event.get_by_id("2014casj")
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

    event: Event | None = Event.get_by_id("2014casj")
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
    event: Event | None = Event.get_by_id("2014casj")
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
    event: Event | None = Event.get_by_id("2014casj")
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
    event: Event | None = Event.get_by_id("2014casj")
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
    event: Event | None = Event.get_by_id("2014casj")
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
    event: Event | None = Event.get_by_id("2014casj")
    assert event is not None
    assert event.remap_teams is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_bad_playoff_type(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {"playoff_type": "DoubleElim"}
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 400
    event: Event | None = Event.get_by_id("2014casj")
    assert event is not None
    assert event.timezone_id is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_playoff_type_sets_manual_attr(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "first_event_code": "TEST",
        "playoff_type": int(PlayoffType.ROUND_ROBIN_6_TEAM),
    }
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 200
    event: Event | None = Event.get_by_id("2014casj")
    assert event is not None
    assert event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM
    assert event.official is True
    assert event.manual_attrs == ["playoff_type"]
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_playoff_type_sets_manual_attr_dedup(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event(manual_attrs=["playoff_type"])
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {
        "first_event_code": "TEST",
        "playoff_type": int(PlayoffType.ROUND_ROBIN_6_TEAM),
    }
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 200
    event: Event | None = Event.get_by_id("2014casj")
    assert event is not None
    assert event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM
    assert event.official is True
    assert event.manual_attrs == ["playoff_type"]
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_playoff_type_None_clears_manual_attr(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event(
        official=True,
        playoff_type=PlayoffType.ROUND_ROBIN_6_TEAM,
        manual_attrs=["playoff_type"],
    )
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {"playoff_type": None}
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 200
    event: Event | None = Event.get_by_id("2014casj")
    assert event is not None
    assert event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM
    assert event.official is True
    assert event.manual_attrs == []
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_invalid_event_timezone(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {"timezone": "Not/Real_Timezone"}
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 400
    event: Event | None = Event.get_by_id("2014casj")
    assert event is not None
    assert event.timezone_id is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_invalid_sync_disable_flags(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {"disable_sync": True}
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 400
    event: Event | None = Event.get_by_id("2014casj")
    assert event is not None
    assert event.disable_sync_flags is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0


def test_invalid_sync_disable_flags_key(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub, api_client: Client
) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    request = {"disable_sync": {"invalid_sync_type": True}}
    request_body = json.dumps(request)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )

    assert response.status_code == 400
    event: Event | None = Event.get_by_id("2014casj")
    assert event is not None
    assert event.disable_sync_flags is None
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="admin")) == 0
