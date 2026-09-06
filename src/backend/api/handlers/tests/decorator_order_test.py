from unittest.mock import MagicMock

import pytest
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.team import Team


def test_decorator_order_cache_hit_bypasses_validate_keys(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Ensure that when an endpoint response is cached, @cached_public serves it
    without executing @validate_keys (preventing redundant Datastore/Memcache lookups).
    """
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # 1. First request: cache miss, executes validate_keys and handler, caches response
    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200
    assert resp1.json["key"] == "frc254"
    etag = resp1.headers.get("ETag")
    assert etag is not None

    # Track calls to Team.get_by_id_async (which is called by validate_keys)
    original_get_by_id_async = Team.get_by_id_async
    mock_get_by_id_async = MagicMock(side_effect=original_get_by_id_async)
    monkeypatch.setattr(Team, "get_by_id_async", mock_get_by_id_async)

    # 2. Second request: cache hit, should bypass validate_keys completely
    resp2 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp2.status_code == 200
    assert resp2.json["key"] == "frc254"
    # Team.get_by_id_async should NOT have been called because validate_keys was bypassed
    mock_get_by_id_async.assert_not_called()

    # 3. Third request with If-None-Match: should return 304 directly from cache
    resp3 = api_client.get(
        "/api/v3/team/frc254",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp3.status_code == 304
    mock_get_by_id_async.assert_not_called()


def test_decorator_order_unauthenticated_request_rejected_first(
    ndb_stub, api_client: Client
) -> None:
    """
    Ensure that unauthenticated requests are rejected by @api_authenticated with 401
    without serving cached responses.
    """
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # Seed the cache with a valid request
    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200

    # Request without auth key should return 401 despite cached data being present
    resp_unauth = api_client.get("/api/v3/team/frc254")
    assert resp_unauth.status_code == 401

    # Request with invalid auth key should return 401
    resp_invalid_key = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "invalid_key"}
    )
    assert resp_invalid_key.status_code == 401


def test_decorator_order_invalid_keys_return_404_on_cache_miss(
    ndb_stub, api_client: Client
) -> None:
    """
    Ensure that @validate_keys still correctly rejects invalid format or non-existent keys.
    """
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    # Invalid key format
    resp_bad_format = api_client.get(
        "/api/v3/team/not_a_valid_team_key",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp_bad_format.status_code == 404

    # Non-existent team key
    resp_nonexistent = api_client.get(
        "/api/v3/team/frc9999999", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp_nonexistent.status_code == 404
