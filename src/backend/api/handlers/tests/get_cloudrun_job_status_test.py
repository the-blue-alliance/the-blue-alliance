from typing import Dict, List
from unittest.mock import patch

from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.cloudrun.clients.cloudrun_client import JobStatus
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event

AUTH_ID = "cloudrun_auth_id"
AUTH_SECRET = "cloudrun_auth_secret"
REQUEST_PATH = "/api/_eventwizard/_cloudrun/status/2019nyny/tba-job/exec-123"


def setup_event() -> None:
    Event(
        id="2019nyny",
        year=2019,
        event_short="nyny",
        event_type_enum=EventType.OFFSEASON,
    ).put()


def setup_auth(access_types: List[AuthType]) -> None:
    ApiAuthAccess(
        id=AUTH_ID,
        secret=AUTH_SECRET,
        event_list=[ndb.Key(Event, "2019nyny")],
        auth_types_enum=access_types,
    ).put()


def get_auth_headers(request_path: str, request_body: str) -> Dict[str, str]:
    return {
        "X-TBA-Auth-Id": AUTH_ID,
        "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
            AUTH_SECRET, request_path, request_body
        ),
    }


def test_no_auth(ndb_stub, api_client: Client) -> None:
    setup_event()

    resp = api_client.post(REQUEST_PATH, data="")
    assert resp.status_code == 401


def test_wrong_permission(ndb_stub, api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.MATCH_VIDEO])

    resp = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, ""),
        data="",
    )

    assert resp.status_code == 401


def test_get_cloudrun_job_status_success(ndb_stub, api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    status = JobStatus(state="RUNNING", message="1/2 tasks running", is_complete=False)
    with patch(
        "backend.api.handlers.eventwizard_internal.get_job_status",
        return_value=status,
    ) as mock_get_job_status:
        resp = api_client.post(
            REQUEST_PATH,
            headers=get_auth_headers(REQUEST_PATH, ""),
            data="",
        )

    assert resp.status_code == 200
    assert resp.json == {"status": status}
    mock_get_job_status.assert_called_once_with("tba-job", "exec-123")


def test_get_cloudrun_job_status_not_found(ndb_stub, api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    with patch(
        "backend.api.handlers.eventwizard_internal.get_job_status",
        return_value=None,
    ):
        resp = api_client.post(
            REQUEST_PATH,
            headers=get_auth_headers(REQUEST_PATH, ""),
            data="",
        )

    assert resp.status_code == 404
    assert resp.json == {"Error": "Job execution not found"}


def test_get_cloudrun_job_status_failure(ndb_stub, api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    with patch(
        "backend.api.handlers.eventwizard_internal.get_job_status",
        side_effect=Exception("cloud run unavailable"),
    ):
        resp = api_client.post(
            REQUEST_PATH,
            headers=get_auth_headers(REQUEST_PATH, ""),
            data="",
        )

    assert resp.status_code == 500
    assert "Failed to fetch job status: cloud run unavailable" in none_throws(
        resp.json
    ).get("Error", "")
