from unittest.mock import Mock

import pytest
from google.appengine.api import users
from google.appengine.ext import testbed


@pytest.fixture
def login_gae_user(
    gae_testbed: testbed.Testbed, monkeypatch: pytest.MonkeyPatch
) -> None:
    gae_testbed.init_user_stub()

    is_admin_mock = Mock(return_value=False)
    monkeypatch.setattr(users, "is_current_user_admin", is_admin_mock)
    """
    This doesn't seem to work...
    gae_testbed.setup_env(
        user_email="user@example.com",
        user_id="123",
        user_is_admin='0',
        overwrite=True)
    """


@pytest.fixture
def login_gae_admin(
    gae_testbed: testbed.Testbed, monkeypatch: pytest.MonkeyPatch
) -> None:
    gae_testbed.init_user_stub()

    is_admin_mock = Mock(return_value=True)
    monkeypatch.setattr(users, "is_current_user_admin", is_admin_mock)
    """
    gae_testbed.setup_env(
        user_email="user@example.com",
        user_id="123",
        user_is_admin='1',
        overwrite=True)
    """
