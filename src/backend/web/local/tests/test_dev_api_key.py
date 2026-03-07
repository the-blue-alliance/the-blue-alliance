import pytest
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.web.local.blueprint import DEV_AUTH_KEY, ensure_dev_api_key


def test_ensure_dev_api_key_creates_key(mock_dev_env) -> None:
    key = ensure_dev_api_key()
    assert key == DEV_AUTH_KEY

    auth = ApiAuthAccess.get_by_id(DEV_AUTH_KEY)
    assert auth is not None
    assert auth.auth_types_enum == [AuthType.READ_API]
    assert auth.is_read_key


def test_ensure_dev_api_key_idempotent(mock_dev_env) -> None:
    key1 = ensure_dev_api_key()
    key2 = ensure_dev_api_key()
    assert key1 == key2 == DEV_AUTH_KEY

    # Should still be exactly one entity
    auth = ApiAuthAccess.get_by_id(DEV_AUTH_KEY)
    assert auth is not None


def test_ensure_dev_api_key_raises_outside_dev() -> None:
    with pytest.raises(RuntimeError, match="must only be called in dev mode"):
        ensure_dev_api_key()


def test_bootstrap_shows_dev_key(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap")
    assert resp.status_code == 200
    assert DEV_AUTH_KEY.encode() in resp.data


def test_bootstrap_creates_key_in_datastore(local_client: Client) -> None:
    local_client.get("/local/bootstrap")

    auth = ApiAuthAccess.get_by_id(DEV_AUTH_KEY)
    assert auth is not None
    assert auth.is_read_key
