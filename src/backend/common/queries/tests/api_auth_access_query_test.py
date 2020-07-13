from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.queries.api_auth_access_query import ApiAuthAccessQuery


def test_no_auth_access() -> None:
    account = Account(id="uid")
    auths = ApiAuthAccessQuery(owner=account).fetch()
    assert auths == []


def test_auth_access() -> None:
    account = Account(id="uid")
    auth = ApiAuthAccess(owner=account.key)
    auth.put()
    auths = ApiAuthAccessQuery(owner=account).fetch()
    assert auths == [auth]
