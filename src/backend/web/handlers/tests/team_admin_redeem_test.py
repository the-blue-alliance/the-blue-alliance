import datetime
from typing import List
from urllib.parse import urlparse

import pytest
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.models.account import Account
from backend.common.models.team import Team
from backend.common.models.team_admin_access import TeamAdminAccess
from backend.common.models.user import User
from backend.web.handlers.conftest import CapturedTemplate


@pytest.fixture(autouse=True)
def store_team(ndb_stub):
    team = Team(
        id="frc1124",
        team_number=1124,
    )
    team.put()


def add_team_admin_access(account, team_number=1124, year=None, access_code="abc123"):
    if not year:
        year = datetime.datetime.now().year
    access = TeamAdminAccess(
        id="test_access_{}".format(year),
        access_code=access_code,
        team_number=team_number,
        year=year,
        expiration=datetime.datetime.now() + datetime.timedelta(days=1),
        account=account,
    )
    return access.put()


def assert_template_status(
    captured_templates: List[CapturedTemplate], status: str
) -> None:
    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "team_admin_redeem.html"
    assert context["status"] == status


def test_login_redirect(web_client: Client):
    resp = web_client.get("/mod/redeem")

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/account/login"


def test_redeem_bad_code(login_user, web_client: Client, captured_templates):
    web_client.post("/mod/redeem", data={"auth_code": "abc123"}, follow_redirects=True)

    assert_template_status(captured_templates, "invalid_code")


def test_redeem_no_team(login_user, web_client: Client, captured_templates):
    add_team_admin_access(account=None)
    web_client.post("/mod/redeem", data={"auth_code": "abc123"}, follow_redirects=True)

    assert_template_status(captured_templates, "invalid_code")


def test_redeem_garbage_team(login_user, web_client: Client, captured_templates):
    add_team_admin_access(account=None)
    web_client.post(
        "/mod/redeem",
        data={"team_number": "meow", "auth_code": "abc123"},
        follow_redirects=True,
    )

    assert_template_status(captured_templates, "invalid_code")


def test_redeem_bad_team(login_user, web_client: Client, captured_templates):
    add_team_admin_access(account=None)
    web_client.post(
        "/mod/redeem",
        data={"team_number": "11245", "auth_code": "abc123"},
        follow_redirects=True,
    )

    assert_template_status(captured_templates, "invalid_code")


def test_redeem_code(login_user: User, web_client: Client, captured_templates):
    access_key = add_team_admin_access(account=None)
    web_client.post(
        "/mod/redeem",
        data={"team_number": "1124", "auth_code": "abc123"},
        follow_redirects=True,
    )

    assert_template_status(captured_templates, "success")

    access = access_key.get()
    assert login_user.account_key == access.account


def test_redeem_code_with_whitespace(
    login_user: User, web_client: Client, captured_templates
):
    access_key = add_team_admin_access(account=None)
    web_client.post(
        "/mod/redeem",
        data={"team_number": "1124", "auth_code": " abc123 "},
        follow_redirects=True,
    )

    assert_template_status(captured_templates, "success")

    access = access_key.get()
    assert login_user.account_key == access.account


def test_redeem_used_code(login_user: User, web_client: Client, captured_templates):
    add_team_admin_access(account=ndb.Key(Account, "other-user@example.com"))
    web_client.post(
        "/mod/redeem",
        data={"team_number": "1124", "auth_code": " abc123 "},
        follow_redirects=True,
    )

    assert_template_status(captured_templates, "code_used")


def test_redeem_code_after_redeeming_last_year(
    login_user: User, web_client: Client, captured_templates
):
    year = datetime.datetime.now().year

    add_team_admin_access(
        account=login_user.account_key, year=year - 1, access_code="abc123_old"
    )
    access_key = add_team_admin_access(account=None, year=year)

    web_client.post(
        "/mod/redeem",
        data={"team_number": "1124", "auth_code": "abc123"},
        follow_redirects=True,
    )

    assert_template_status(captured_templates, "success")

    access = access_key.get()
    assert login_user.account_key == access.account
