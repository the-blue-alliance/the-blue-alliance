from datetime import datetime
from typing import List

from google.cloud import ndb
from pyre_extensions import safe_cast

from backend.common.consts.account_permission import AccountPermission


class Account(ndb.Model):
    """
    Accounts represent accounts people use on TBA.
    """

    # Set by login/registration
    # Not editable by the user
    email: str = ndb.StringProperty()
    nickname: str = ndb.StringProperty()
    registered: bool = ndb.BooleanProperty()
    permissions: List[AccountPermission] = safe_cast(
        List[AccountPermission],
        ndb.IntegerProperty(choices=list(AccountPermission), repeated=True),
    )
    shadow_banned: bool = ndb.BooleanProperty(default=False)
    created: datetime = ndb.DateTimeProperty(auto_now_add=True)
    updated: datetime = ndb.DateTimeProperty(auto_now=True, indexed=False)

    # These optional properties are editable by the user
    display_name: str = ndb.StringProperty()
