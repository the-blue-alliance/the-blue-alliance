import datetime
from typing import List
from unittest.mock import Mock

import pytest

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.event_type import EventType
from backend.common.models.account import Account
from backend.common.models.event import Event
from backend.common.models.user import User


@pytest.fixture
def author(ndb_stub) -> Account:
    """The person who submitted a suggestion."""
    account = Account(
        id="author_uid",
        email="author@example.com",
        nickname="Author",
        display_name="Alice Author",
        registered=True,
    )
    account.put()
    return account


@pytest.fixture
def reviewer(ndb_stub) -> Account:
    """A moderator account, as recorded on a reviewed suggestion."""
    account = Account(
        id="reviewer_uid",
        email="mod@tba.com",
        display_name="Mod Erator",
        permissions=[AccountPermission.REVIEW_APIWRITE],
        registered=True,
    )
    account.put()
    return account


@pytest.fixture
def event(ndb_stub) -> Event:
    event = Event(
        id="2026cc",
        name="Chezy Champs",
        event_type_enum=EventType.OFFSEASON,
        short_name="Chezy",
        event_short="cc",
        year=2026,
        start_date=datetime.datetime(2026, 9, 25),
        end_date=datetime.datetime(2026, 9, 27),
    )
    event.put()
    return event


def make_user(permissions: List[AccountPermission], is_admin: bool = False) -> User:
    """A signed-in User backed by a real Account, for calling the reviewer."""
    account_key = Account(id="reviewer_uid", email="reviewer@tba.com").put()
    user = Mock(spec=User)
    user.is_admin = is_admin
    user.permissions = permissions
    user.account_key = account_key
    return user
