from google.appengine.ext import ndb

from backend.common.models.account import Account
from backend.common.models.team import Team
from backend.common.models.team_admin_access import TeamAdminAccess


def test_account_email() -> None:
    mod_code = TeamAdminAccess()
    assert mod_code.account is None
    assert mod_code.account_email is None
    account = Account(email="zach@thebluealliance.com").put()
    mod_code = TeamAdminAccess(account=account)
    assert mod_code.account is not None
    assert mod_code.account_email == "zach@thebluealliance.com"


def test_key_name() -> None:
    mod_code = TeamAdminAccess(team_number=254, year=2020)
    assert TeamAdminAccess.render_key_name(254, 2020) == "frc254_2020"
    assert mod_code.key_name == "frc254_2020"
    assert mod_code.team_key == ndb.Key(Team, "frc254")


def test_account_email_missing_account() -> None:
    mod_code = TeamAdminAccess(account=ndb.Key(Account, "does_not_exist"))
    assert mod_code.account is not None
    assert mod_code.account_email is None
