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


@pytest.mark.parametrize("cache_enabled", [True, False])
def test_apiv3_404_returns_404_not_304_when_etag_matches(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch, cache_enabled: bool
) -> None:
    """
    Ensure that 404 responses in APIv3 always return 404, not 304,
    even when the client sends an If-None-Match header matching the 404 ETag.
    Tests both with flask_response_cache enabled and disabled.
    """
    from backend.common.environment import Environment

    monkeypatch.setattr(
        Environment, "flask_response_cache_enabled", lambda: cache_enabled
    )

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    # 1. Non-existent team key: returns 404 with ETag
    resp1 = api_client.get(
        "/api/v3/team/frc9999999", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 404
    etag = resp1.headers.get("ETag")
    assert etag is not None

    # Subsequent request with matching If-None-Match must STILL return 404, not 304
    resp2 = api_client.get(
        "/api/v3/team/frc9999999",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp2.status_code == 404
    assert resp2.headers.get("ETag") == etag
    assert "Error" in resp2.json

    # 2. Invalid key format: returns 404 with ETag
    resp3 = api_client.get(
        "/api/v3/team/not_a_valid_team_key",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp3.status_code == 404
    bad_format_etag = resp3.headers.get("ETag")
    assert bad_format_etag is not None

    resp4 = api_client.get(
        "/api/v3/team/not_a_valid_team_key",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": bad_format_etag},
    )
    assert resp4.status_code == 404
    assert resp4.headers.get("ETag") == bad_format_etag
    assert "Error" in resp4.json


def test_apiv3_query_params_ignored_for_caching(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Ensure that APIv3 memcache keys ignore URL query parameters so that
    requests with query params (such as ?X-TBA-Auth-Key=... or ?foo=bar) hit
    the same cached response.
    """
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # 1. Warm cache with header authentication
    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None

    # Track calls to Team.get_by_id_async to ensure cache hits bypass handler/validate_keys
    original_get_by_id_async = Team.get_by_id_async
    mock_get_by_id_async = MagicMock(side_effect=original_get_by_id_async)
    monkeypatch.setattr(Team, "get_by_id_async", mock_get_by_id_async)

    # 2. Request with query param auth: ?X-TBA-Auth-Key=test_auth_key
    resp2 = api_client.get("/api/v3/team/frc254?X-TBA-Auth-Key=test_auth_key")
    assert resp2.status_code == 200
    assert resp2.json["key"] == "frc254"
    mock_get_by_id_async.assert_not_called()

    # 3. Request with arbitrary query parameters: ?foo=bar&baz=qux
    resp3 = api_client.get(
        "/api/v3/team/frc254?foo=bar&baz=qux",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp3.status_code == 200
    assert resp3.json["key"] == "frc254"
    mock_get_by_id_async.assert_not_called()

    # 4. Request with query params and If-None-Match
    resp4 = api_client.get(
        "/api/v3/team/frc254?timestamp=123456789",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp4.status_code == 304
    mock_get_by_id_async.assert_not_called()
