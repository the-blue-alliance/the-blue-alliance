from unittest.mock import Mock

import pytest
from werkzeug.test import Client

from backend.api.client_api_auth_helper import ClientApiAuthHelper
from backend.common.models.account import Account
from backend.common.models.user import User


@pytest.fixture
def api_client(gae_testbed, ndb_stub, memcache_stub, taskqueue_stub) -> Client:
    from backend.api.main import app

    return app.test_client()


@pytest.fixture
def mock_clientapi_auth(ndb_stub, monkeypatch: pytest.MonkeyPatch) -> User:
    account = Account(
        email="test@tba.com",
        registered=True,
    )
    account_key = account.put()

    mock_user = Mock(spec=User)
    mock_user.is_registered = True
    mock_user.is_admin = False
    mock_user.api_read_keys = []
    mock_user.api_write_keys = []
    mock_user.mobile_clients = []
    mock_user.permissions = []
    mock_user.account_key = account_key
    mock_user.uid = account_key.id()

    def mock_current_user():
        return mock_user

    monkeypatch.setattr(ClientApiAuthHelper, "get_current_user", mock_current_user)
    return mock_user
