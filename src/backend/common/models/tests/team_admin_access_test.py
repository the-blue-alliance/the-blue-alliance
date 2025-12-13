from backend.common.models.account import Account
from backend.common.models.team_admin_access import TeamAdminAccess


def test_account_email() -> None:
    mod_code = TeamAdminAccess()
    assert mod_code.account is None
    assert mod_code.account_email is None
    account = Account(email="zach@thebluealliance.com").put()
    mod_code = TeamAdminAccess(account=account)
    assert mod_code.account is not None
    assert mod_code.account_email == "zach@thebluealliance.com"
