from typing import List
from unittest.mock import ANY, Mock, patch
from urllib.parse import parse_qsl, quote, urlparse

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask.testing import FlaskClient

import backend
from backend.common import auth
from backend.common.consts.client_type import ClientType
from backend.common.consts.model_type import ModelType
from backend.common.helpers.account_deletion import AccountDeletionHelper
from backend.common.helpers.mytba import AttendanceStatsHelper
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.models.account import Account
from backend.common.models.mobile_client import MobileClient
from backend.web.handlers.conftest import CapturedTemplate
from backend.web.handlers.tests.helpers import get_page_title


def test_register_logged_out(web_client: FlaskClient) -> None:
    response = web_client.get("/account/register")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account/register"
    }


def test_register_unregistered(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    login_user.is_registered = False
    response = web_client.get("/account/register")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_register.html"
    assert get_page_title(response.data) == "Account Registration - The Blue Alliance"
    assert context["next"] is None


@pytest.mark.parametrize(
    "next_url, expected",
    [
        ("https://zachorr.com", None),
        ("ftp://localhost/account", None),
        ("localhost/account", "localhost/account"),
    ],
)
def test_register_unregistered_next(
    login_user,
    next_url: str,
    expected: str,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    login_user.is_registered = False
    response = web_client.get("/account/register?next={}".format(quote(next_url)))

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_register.html"
    assert get_page_title(response.data) == "Account Registration - The Blue Alliance"
    assert context["next"] == expected


@pytest.mark.parametrize(
    "next_url, expected",
    [
        ("", None),
        ("https://zachorr.com", None),
        ("ftp://localhost/mytba", None),
        ("http://localhost/mytba", "/mytba"),
        ("/mytba", "/mytba"),
    ],
)
def test_register_register(
    login_user, next_url: str, expected: str, web_client: FlaskClient
) -> None:
    response = web_client.get("/account/register?next={}".format(quote(next_url)))

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == (expected if expected else "/account")


def test_register_register_no_account_id(login_user, web_client: FlaskClient) -> None:
    login_user.is_registered = False

    response = web_client.post("/account/register", data={"display_name": "Zach"})

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/"


def test_register_register_no_display_name(login_user, web_client: FlaskClient) -> None:
    login_user.is_registered = False

    response = web_client.post("/account/register", data={"account_id": "abc"})

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/"


def test_register_register_account_id_mismatch(
    login_user, web_client: FlaskClient
) -> None:
    login_user.is_registered = False

    response = web_client.post(
        "/account/register", data={"account_id": "efg", "display_name": "Zach"}
    )

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/"


@pytest.mark.parametrize(
    "next_url, expected",
    [
        ("", None),
        ("https://zachorr.com", None),
        ("ftp://localhost/mytba", None),
        ("http://localhost/mytba", "/mytba"),
        ("/mytba", "/mytba"),
    ],
)
def test_register_register_account(
    login_user, next_url: str, expected: str, web_client: FlaskClient
) -> None:
    login_user.is_registered = False
    login_user.uid = "abc"

    with patch.object(login_user, "register") as mock_register:
        response = web_client.post(
            "/account/register?next={}".format(quote(next_url)),
            data={"account_id": login_user.uid, "display_name": "Zach"},
        )

    mock_register.assert_called_with("Zach")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == (expected if expected else "/account")


def test_edit_logged_out(web_client: FlaskClient) -> None:
    response = web_client.get("/account/edit")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account/edit"
    }


def test_edit_unregistered(login_user, web_client: FlaskClient) -> None:
    login_user.is_registered = False

    response = web_client.get("/account/edit")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/register"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account/edit"
    }


def test_edit(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    response = web_client.get("/account/edit")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_edit.html"
    assert get_page_title(response.data) == "Edit Profile - The Blue Alliance"
    assert context["status"] is None


def test_edit_no_account_id(login_user, web_client: FlaskClient) -> None:
    with web_client:
        response = web_client.post("/account/edit", data={})

    with web_client.session_transaction() as session:
        assert session.get("account_edit_status") == "account_edit_failure"

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/edit"


def test_edit_no_account_id_follow_redirect(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    with web_client:
        response = web_client.post("/account/edit", follow_redirects=True, data={})
    with web_client.session_transaction() as session:
        assert session.get("account_edit_status") is None

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_edit.html"
    assert context["status"] == "account_edit_failure"


def test_edit_mismatch_account_id(login_user, web_client: FlaskClient) -> None:
    with web_client:
        response = web_client.post("/account/edit", data={"account_id": "def"})
    with web_client.session_transaction() as session:
        assert session.get("account_edit_status") == "account_edit_failure"

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/edit"


def test_edit_mismatch_account_id_follow_redirect(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    with web_client:
        response = web_client.post(
            "/account/edit", follow_redirects=True, data={"account_id": "def"}
        )
    with web_client.session_transaction() as session:
        assert session.get("account_edit_status") is None

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_edit.html"
    assert context["status"] == "account_edit_failure"


def test_edit_no_display_name(login_user, web_client: FlaskClient) -> None:
    login_user.uid = "abc"

    with web_client:
        response = web_client.post("/account/edit", data={"account_id": login_user.uid})
    with web_client.session_transaction() as session:
        assert session.get("account_edit_status") == "account_edit_failure_name"

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/edit"


def test_edit_no_display_name_follow_redirect(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    login_user.uid = "abc"

    with web_client:
        response = web_client.post(
            "/account/edit", follow_redirects=True, data={"account_id": login_user.uid}
        )
    with web_client.session_transaction() as session:
        assert session.get("account_edit_status") is None

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_edit.html"
    assert context["status"] == "account_edit_failure_name"


def test_edit_success(login_user, web_client: FlaskClient) -> None:
    login_user.uid = "abc"

    with web_client, patch.object(
        login_user, "update_display_name"
    ) as mock_update_display_name:
        response = web_client.post(
            "/account/edit", data={"account_id": login_user.uid, "display_name": "Zach"}
        )
    with web_client.session_transaction() as session:
        assert session.get("account_edit_status") is None
        assert session.get("account_status") == "account_edit_success"

    mock_update_display_name.assert_called_with("Zach")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_logout_logged_out(web_client: FlaskClient) -> None:
    response = web_client.get("/account/logout")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account/logout"
    }


@pytest.mark.parametrize(
    "next_url, expected",
    [
        ("", None),
        ("https://zachorr.com", None),
        ("ftp://localhost/mytba", None),
        ("http://localhost/mytba", "/mytba"),
        ("/mytba", "/mytba"),
    ],
)
def test_logout_unregistered(
    login_user, next_url: str, expected: str, web_client: FlaskClient
) -> None:
    login_user.is_registered = False

    with patch.object(
        backend.web.handlers.account, "revoke_session_cookie"
    ) as mock_revoke_session_cookie:
        response = web_client.get("/account/logout?next={}".format(quote(next_url)))

    assert mock_revoke_session_cookie.called

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == (expected if expected else "/")


@pytest.mark.parametrize(
    "next_url, expected",
    [
        ("", None),
        ("https://zachorr.com", None),
        ("ftp://localhost/mytba", None),
        ("http://localhost/mytba", "/mytba"),
        ("/mytba", "/mytba"),
    ],
)
def test_logout(
    login_user, next_url: str, expected: str, web_client: FlaskClient
) -> None:
    with patch.object(
        backend.web.handlers.account, "revoke_session_cookie"
    ) as mock_revoke_session_cookie:
        response = web_client.get("/account/logout?next={}".format(quote(next_url)))

    assert mock_revoke_session_cookie.called

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == (expected if expected else "/")


def test_login_logged_in(login_user, web_client: FlaskClient) -> None:
    response = web_client.get("/account/login")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


@pytest.mark.parametrize(
    "auth_emulator_host",
    [
        None,
        "",
        "localhost:9099",
    ],
)
def test_login(
    auth_emulator_host,
    monkeypatch: MonkeyPatch,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    if auth_emulator_host is not None:
        monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", auth_emulator_host)

    response = web_client.get("/account/login")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    # context = captured_templates[0][1]
    assert template.name == "account_login_required.html"
    assert get_page_title(response.data) == "The Blue Alliance - Login Required"

    # NOTE: Google App Engine is dropping our monkeypatch'd variable during
    # our request context. It's really unclear why. Going to comment this out
    # and attempt to fix this test at some other point - especially since
    # the auth_emulator_host is just for testing in dev.
    # ~Zach
    # assert context["auth_emulator_host"] == auth_emulator_host


def test_login_no_id_token(web_client: FlaskClient) -> None:
    response = web_client.post("/account/login")
    assert response.status_code == 400


def test_login_success(web_client: FlaskClient) -> None:
    with patch.object(
        backend.web.handlers.account, "create_session_cookie"
    ) as mock_create_session_cookie:
        response = web_client.post("/account/login", data={"id_token": "abc"})

    mock_create_session_cookie.assert_called_with("abc", ANY)

    assert response.status_code == 200
    assert response.get_json() == {"status": "success"}


def test_read_key_add_no_description(login_user, web_client: FlaskClient) -> None:
    with patch.object(
        login_user, "add_api_read_key"
    ) as mock_add_api_read_key, web_client:
        response = web_client.post("/account/api/read_key_add")
    with web_client.session_transaction() as session:
        assert session.get("account_status") == "read_key_add_no_description"

    mock_add_api_read_key.assert_not_called()
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_add_no_api_key(login_user, web_client: FlaskClient) -> None:
    with patch.object(
        login_user, "add_api_read_key", side_effect=Exception()
    ) as mock_add_api_read_key, web_client:
        response = web_client.post(
            "/account/api/read_key_add", data={"description": "Testing"}
        )
    with web_client.session_transaction() as session:
        assert session.get("account_status") == "read_key_add_failure"

    mock_add_api_read_key.assert_called_with("Testing")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_add(login_user, web_client: FlaskClient) -> None:
    with patch.object(
        login_user, "add_api_read_key"
    ) as mock_add_api_read_key, web_client:
        response = web_client.post(
            "/account/api/read_key_add", data={"description": "Testing"}
        )
    with web_client.session_transaction() as session:
        assert session.get("account_status") == "read_key_add_success"

    mock_add_api_read_key.assert_called_with("Testing")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_delete_no_key_id(login_user, web_client: FlaskClient) -> None:
    with patch.object(login_user, "delete_api_key") as mock_delete_api_key, web_client:
        response = web_client.post("/account/api/read_key_delete")
    with web_client.session_transaction() as session:
        assert session.get("account_status") == "read_key_delete_failure"

    mock_delete_api_key.assert_not_called()
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_delete_no_api_key(login_user, web_client: FlaskClient) -> None:
    with patch.object(
        login_user, "delete_api_key"
    ) as mock_delete_api_key, patch.object(
        login_user, "api_read_key", return_value=None
    ), web_client:
        response = web_client.post(
            "/account/api/read_key_delete", data={"key_id": "abcd"}
        )
    with web_client.session_transaction() as session:
        assert session.get("account_status") == "read_key_delete_failure"

    mock_delete_api_key.assert_not_called()
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_delete(login_user, web_client: FlaskClient) -> None:
    mock_api_key = Mock()
    with patch.object(
        login_user, "delete_api_key"
    ) as mock_delete_api_key, patch.object(
        login_user, "api_read_key", return_value=mock_api_key
    ), web_client:
        response = web_client.post(
            "/account/api/read_key_delete", data={"key_id": "abcd"}
        )
    with web_client.session_transaction() as session:
        assert session.get("account_status") == "read_key_delete_success"

    mock_delete_api_key.assert_called_with(mock_api_key)
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_mytba(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock_mytba = Mock()

    mock_event = Mock()
    mock_event_sorted = Mock()
    mock_events = [mock_event]
    mock_mytba.events = mock_events

    mock_team = Mock()
    mock_mytba.teams = [mock_team]

    mock_event_key = Mock()
    mock_event_key.configure_mock(**{"get.return_value": mock_event})
    mock_event_sorted.key = mock_event_key

    mock_match = Mock()
    mock_match_sorted = Mock()
    mock_matches = [mock_match]
    mock_event_matches = {mock_event_key: mock_matches}
    mock_mytba.event_matches = mock_event_matches

    login_user.myTBA = mock_mytba

    mock_event_favorite = Mock()
    mock_event_subscription = Mock()
    mock_event_subscription.notification_names = []
    mock_team_favorite = Mock()
    mock_team_subscription = Mock()
    mock_team_subscription.notification_names = []
    mock_match_favorite = Mock()
    mock_match_subscription = Mock()
    mock_match_subscription.notification_names = []
    mock_eventteam_favorite = Mock()

    def mock_favorite(model_type, key):
        if model_type == ModelType.EVENT:
            return mock_event_favorite
        elif model_type == ModelType.TEAM:
            return mock_team_favorite
        elif model_type == ModelType.EVENT_TEAM:
            return mock_eventteam_favorite
        return mock_match_favorite

    def mock_subscription(model_type, key):
        if model_type == ModelType.EVENT:
            return mock_event_subscription
        elif model_type == ModelType.TEAM:
            return mock_team_subscription
        return mock_match_subscription

    mock_mytba.favorite.side_effect = mock_favorite
    mock_mytba.subscription.side_effect = mock_subscription
    mock_mytba.attendance_stats_helper = AttendanceStatsHelper(
        event_teams=[], events=[], teams=[], matches={}
    )

    mock_year = 2012

    with patch.object(
        backend.common.helpers.event_helper.EventHelper,
        "sorted_events",
        return_value=[mock_event_sorted],
    ) as mock_sorted_events, patch.object(
        backend.common.helpers.match_helper.MatchHelper,
        "natural_sorted_matches",
        return_value=[mock_match_sorted],
    ) as mock_natural_sorted_matches, patch.object(
        backend.common.helpers.season_helper.SeasonHelper,
        "effective_season_year",
        return_value=mock_year,
    ) as mock_effective_season_year:
        response = web_client.get("/account/mytba")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "mytba.html"

    mock_sorted_events.assert_called_with(mock_events)
    mock_natural_sorted_matches.assert_called_with(mock_matches)
    mock_effective_season_year.assert_called()

    assert context["event_fav_sub"] == [
        (mock_event_sorted, mock_event_favorite, mock_event_subscription)
    ]
    assert context["team_fav_sub"] == [
        (mock_team, mock_team_favorite, mock_team_subscription)
    ]
    assert context["event_match_fav_sub"] == [
        (
            mock_event_sorted,
            [(mock_match_sorted, mock_match_favorite, mock_match_subscription)],
        )
    ]
    assert context["year"] == mock_year


@pytest.mark.parametrize(
    "ping_sent, expected", [((True, True), "1"), ((False, True), "0")]
)
def test_ping_client(
    ping_sent,
    expected,
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
):
    c1 = MobileClient(
        parent=login_user.account_key,
        user_id=str(login_user.account_key.id()),
        messaging_id="token_1",
        client_type=ClientType.OS_IOS,
    )
    c1.put()

    with web_client, patch.object(
        TBANSHelper, "ping", return_value=ping_sent
    ) as mock_ping:
        response = web_client.post(
            "/account/ping", data={"mobile_client_id": c1.key.id()}
        )

    mock_ping.assert_called_with(c1)

    with web_client.session_transaction() as session:
        assert session.get("ping_sent") == expected

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_ping_not_our_client(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
):
    # Insert two mobile clients - one for our user, and one for another user
    # Make sure we can only ping the one for our user - not the other user
    other_account = Account(
        email="some_other_account@tba.com",
        registered=True,
    )
    other_account.put()

    c1 = MobileClient(
        parent=other_account.key,
        user_id=str(other_account.key.id()),
        messaging_id="token_1",
        client_type=ClientType.OS_IOS,
    )
    c1.put()

    with web_client, patch.object(
        TBANSHelper, "ping", return_value=(True, True)
    ) as mock_ping:
        response = web_client.post(
            "/account/ping", data={"mobile_client_id": c1.key.id()}
        )

    mock_ping.assert_not_called()

    with web_client.session_transaction() as session:
        assert session.get("ping_sent") == "0"

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_delete_confirmation(login_user, web_client: FlaskClient) -> None:
    response = web_client.get("/account/delete")
    assert response.status_code == 200


def test_delete_post(login_user, web_client: FlaskClient) -> None:
    with patch.object(
        backend.web.handlers.account, "revoke_session_cookie"
    ) as mock_revoke_session_cookie, patch.object(
        AccountDeletionHelper, "delete_account"
    ) as mock_delete_account, patch.object(
        auth, "_delete_user"
    ) as mock_delete_user:
        response = web_client.post("/account/delete")

    # make sure we log out the current user and that we call the deletion function
    assert mock_revoke_session_cookie.called
    assert mock_delete_account.called
    assert mock_delete_user.called

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/"
