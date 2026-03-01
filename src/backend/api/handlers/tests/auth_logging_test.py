"""Tests that API authentication decorators add context to logging."""

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.logging import get_logging_context
from backend.common.models.api_auth_access import ApiAuthAccess


def test_api_authenticated_sets_logging_context(api_client: Client) -> None:
    """Test that api_authenticated decorator adds api_key to logging context."""
    from backend.common.models.team import Team

    # Create a team so the /status endpoint works
    Team(
        id="frc254",
        team_number=254,
    ).put()

    auth = ApiAuthAccess(
        id="test_auth_key",
        description="Test auth key",
        event_list=[],
    )
    auth.put()

    # Make a request with the auth key
    response = api_client.get(
        "/api/v3/status", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )

    # Verify the request was successful
    assert response.status_code == 200

    # Verify logging context was set
    context = get_logging_context()
    assert "api_auth_key" in context
    assert context["api_auth_key"] == "test_auth_key"


def test_api_authenticated_no_logging_context_on_invalid_key(
    api_client: Client,
) -> None:
    """Test that invalid auth key doesn't set logging context."""
    # Make a request with an invalid auth key
    response = api_client.get(
        "/api/v3/status", headers={"X-TBA-Auth-Key": "invalid_key"}
    )

    # Verify the request failed
    assert response.status_code == 401

    # Logging context should not have api_key since auth failed
    context = get_logging_context()
    # Context might be empty or not have api_auth_auth_key
    assert "api_auth_key" not in context


def test_require_write_auth_sets_logging_context(api_client: Client, ndb_stub) -> None:
    """Test that require_write_auth decorator adds api_auth_id to logging context."""
    from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
    from backend.common.models.event import Event

    # Set up an event
    Event(
        id="2024casj",
        year=2024,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    # Set up auth
    auth = ApiAuthAccess(
        id="test_auth_id",
        secret="test_secret",
        description="Test auth",
        event_list=[ndb.Key("Event", "2024casj")],
        auth_types_enum=[AuthType.EVENT_INFO],
    )
    auth.put()

    # Create request body and compute signature
    request_path = "/api/trusted/v1/event/2024casj/info/update"
    request_body = '{"timezone": "America/New_York"}'
    auth_sig = TrustedApiAuthHelper.compute_auth_signature(
        "test_secret", request_path, request_body
    )

    # Make a request
    response = api_client.post(
        request_path,
        data=request_body,
        headers={
            "X-TBA-Auth-Id": "test_auth_id",
            "X-TBA-Auth-Sig": auth_sig,
        },
        content_type="application/json",
    )

    # Verify the request was successful (or at least passed auth)
    # It might fail for other reasons, but should not be 401 Unauthorized
    assert response.status_code != 401

    # Verify logging context was set
    context = get_logging_context()
    assert "api_auth_key" in context
    assert context["api_auth_key"] == "test_auth_id"
