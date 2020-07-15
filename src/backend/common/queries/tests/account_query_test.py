from backend.common.models.account import Account
from backend.common.queries.account_query import AccountQuery


def test_none_email() -> None:
    account = AccountQuery(email="").fetch()
    assert account is None


def test_no_account() -> None:
    account = AccountQuery(email="tba@tba.com").fetch()
    assert account is None


def test_account() -> None:
    acc = Account(email="tba@tba.com")
    acc.put()

    account = AccountQuery(email="tba@tba.com").fetch()
    assert account == acc
