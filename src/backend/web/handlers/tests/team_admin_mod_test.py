import datetime
from urllib.parse import urlparse

import pytest
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.models.team import Team
from backend.common.models.team_admin_access import TeamAdminAccess

TEAM_NUMBER = 1124
YEAR = datetime.datetime.now().year


@pytest.fixture(autouse=True)
def store_team(ndb_stub):
    team = Team(
        id=f"frc{TEAM_NUMBER}",
        team_number=TEAM_NUMBER,
    )
    team.put()


@pytest.fixture
def login_user_with_permission(login_user):
    """User with the REVIEW_MEDIA account permission."""
    login_user.has_permission.return_value = True
    login_user.permissions = [AccountPermission.REVIEW_MEDIA]
    return login_user


@pytest.fixture
def login_user_no_access(login_user):
    """Regular user with no special permissions and no TeamAdminAccess."""
    login_user.has_permission.return_value = False
    return login_user


def add_team_admin_access(account, team_number=TEAM_NUMBER, year=None):
    if not year:
        year = datetime.datetime.now().year
    access = TeamAdminAccess(
        id=f"test_access_{year}",
        access_code="abc123",
        team_number=team_number,
        year=year,
        expiration=datetime.datetime.now() + datetime.timedelta(days=1),
        account=account,
    )
    return access.put()


# ---- GET /mod ----


def test_get_login_redirect(web_client: Client) -> None:
    resp = web_client.get("/mod")

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/account/login"


def test_get_no_access_redirects_to_redeem(
    login_user_no_access, web_client: Client
) -> None:
    resp = web_client.get("/mod")

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/mod/redeem"


def test_get_with_team_admin_access_can_view(
    login_user_no_access, web_client: Client
) -> None:
    add_team_admin_access(account=login_user_no_access.account_key)

    resp = web_client.get("/mod")

    assert resp.status_code == 200


def test_get_admin_can_view_with_forced_team_year(
    login_admin, web_client: Client
) -> None:
    resp = web_client.get(f"/mod?team={TEAM_NUMBER}&year={YEAR}")

    assert resp.status_code == 200


def test_get_review_media_permission_can_view_with_forced_team_year(
    login_user_with_permission, web_client: Client
) -> None:
    resp = web_client.get(f"/mod?team={TEAM_NUMBER}&year={YEAR}")

    assert resp.status_code == 200


# ---- POST /mod ----


def test_post_login_redirect(web_client: Client) -> None:
    resp = web_client.post(
        "/mod",
        data={
            "team_number": str(TEAM_NUMBER),
            "action": "set_team_info",
            "robot_name": "",
        },
    )

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/account/login"


def test_post_no_access_returns_403(login_user_no_access, web_client: Client) -> None:
    resp = web_client.post(
        "/mod",
        data={
            "team_number": str(TEAM_NUMBER),
            "action": "set_team_info",
            "robot_name": "",
        },
    )

    assert resp.status_code == 403


def test_post_with_team_admin_access_succeeds(
    login_user_no_access, web_client: Client
) -> None:
    add_team_admin_access(account=login_user_no_access.account_key)

    resp = web_client.post(
        "/mod",
        data={
            "team_number": str(TEAM_NUMBER),
            "action": "set_team_info",
            "robot_name": "",
        },
    )

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/mod"


def test_post_admin_can_perform_action(login_admin, web_client: Client) -> None:
    resp = web_client.post(
        "/mod",
        data={
            "team_number": str(TEAM_NUMBER),
            "action": "set_team_info",
            "robot_name": "",
        },
    )

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/mod"


def test_post_review_media_permission_can_perform_action(
    login_user_with_permission, web_client: Client
) -> None:
    resp = web_client.post(
        "/mod",
        data={
            "team_number": str(TEAM_NUMBER),
            "action": "set_team_info",
            "robot_name": "",
        },
    )

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/mod"
