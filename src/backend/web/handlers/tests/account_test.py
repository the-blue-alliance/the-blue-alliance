from typing import List
from unittest.mock import ANY, Mock, patch
from urllib.parse import parse_qsl, quote, urlparse

import pytest
from flask import session
from flask.testing import FlaskClient

import backend
from backend.common.consts.model_type import ModelType
from backend.web.handlers.conftest import CapturedTemplate
from backend.web.handlers.tests.helpers import get_page_title


def user_mock(registered: bool = True) -> Mock:
    mock = Mock()
    mock.is_registered = registered
    return mock


def test_register_logged_out(web_client: FlaskClient) -> None:
    response = web_client.get("/account/register")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account/register"
    }


def test_register_unregistered(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock = user_mock(registered=False)
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
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
    next_url: str,
    expected: str,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    mock = user_mock(registered=False)
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
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
    next_url: str, expected: str, web_client: FlaskClient
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account/register?next={}".format(quote(next_url)))

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == (expected if expected else "/account")


def test_register_register_no_account_id(web_client: FlaskClient) -> None:
    mock = user_mock(registered=False)
    mock.uid = "abc"

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.post("/account/register", data={"display_name": "Zach"})

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/"


def test_register_register_no_display_name(web_client: FlaskClient) -> None:
    mock = user_mock(registered=False)
    mock.uid = "abc"

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.post("/account/register", data={"account_id": "abc"})

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/"


def test_register_register_account_id_mismatch(web_client: FlaskClient) -> None:
    mock = user_mock(registered=False)
    mock.uid = "abc"

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
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
    next_url: str, expected: str, web_client: FlaskClient
) -> None:
    mock = user_mock(registered=False)
    mock.uid = "abc"

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        mock, "register"
    ) as mock_register:
        response = web_client.post(
            "/account/register?next={}".format(quote(next_url)),
            data={"account_id": "abc", "display_name": "Zach"},
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


def test_edit_unregistered(web_client: FlaskClient) -> None:
    mock = user_mock(registered=False)
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account/edit")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/register"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account/edit"
    }


def test_edit(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account/edit")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_edit.html"
    assert get_page_title(response.data) == "Edit Profile - The Blue Alliance"
    assert context["status"] is None


def test_edit_no_account_id(web_client: FlaskClient) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), web_client:
        response = web_client.post("/account/edit", data={})
        assert session.get("account_edit_status") == "account_edit_failure"

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/edit"


def test_edit_no_account_id_follow_redirect(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), web_client:
        response = web_client.post("/account/edit", follow_redirects=True, data={})
        assert session.get("account_edit_status") is None

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_edit.html"
    assert context["status"] == "account_edit_failure"


def test_edit_mismatch_account_id(web_client: FlaskClient) -> None:
    mock = user_mock()
    mock.uid = "abc"

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), web_client:
        response = web_client.post("/account/edit", data={"account_id": "def"})
        assert session.get("account_edit_status") == "account_edit_failure"

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/edit"


def test_edit_mismatch_account_id_follow_redirect(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock = user_mock()
    mock.uid = "abc"

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), web_client:
        response = web_client.post(
            "/account/edit", follow_redirects=True, data={"account_id": "def"}
        )
        assert session.get("account_edit_status") is None

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_edit.html"
    assert context["status"] == "account_edit_failure"


def test_edit_no_display_name(web_client: FlaskClient) -> None:
    mock = user_mock()
    mock.uid = "abc"

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), web_client:
        response = web_client.post("/account/edit", data={"account_id": "abc"})
        assert session.get("account_edit_status") == "account_edit_failure_name"

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/edit"


def test_edit_no_display_name_follow_redirect(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock = user_mock()
    mock.uid = "abc"

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), web_client:
        response = web_client.post(
            "/account/edit", follow_redirects=True, data={"account_id": "abc"}
        )
        assert session.get("account_edit_status") is None

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_edit.html"
    assert context["status"] == "account_edit_failure_name"


def test_edit_success(web_client: FlaskClient) -> None:
    mock = user_mock()
    mock.uid = "abc"

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), web_client, patch.object(
        mock, "update_display_name"
    ) as mock_update_display_name:
        response = web_client.post(
            "/account/edit", data={"account_id": "abc", "display_name": "Zach"}
        )
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
    next_url: str, expected: str, web_client: FlaskClient
) -> None:
    mock = user_mock(registered=False)
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
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
def test_logout(next_url: str, expected: str, web_client: FlaskClient) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "revoke_session_cookie"
    ) as mock_revoke_session_cookie:
        response = web_client.get("/account/logout?next={}".format(quote(next_url)))

    assert mock_revoke_session_cookie.called

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == (expected if expected else "/")


def test_login_logged_in(web_client: FlaskClient) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account/login")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_login(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    response = web_client.get("/account/login")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_login_required.html"
    assert get_page_title(response.data) == "The Blue Alliance - Login Required"


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


def test_read_key_add_no_description(web_client: FlaskClient) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        mock, "add_api_read_key"
    ) as mock_add_api_read_key, web_client:
        response = web_client.post("/account/api/read_key_add")
        assert session.get("account_status") == "read_key_add_no_description"

    mock_add_api_read_key.assert_not_called()
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_add_no_api_key(web_client: FlaskClient) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        mock, "add_api_read_key", side_effect=Exception()
    ) as mock_add_api_read_key, web_client:
        response = web_client.post(
            "/account/api/read_key_add", data={"description": "Testing"}
        )
        assert session.get("account_status") == "read_key_add_failure"

    mock_add_api_read_key.assert_called_with("Testing")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_add(web_client: FlaskClient) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        mock, "add_api_read_key"
    ) as mock_add_api_read_key, web_client:
        response = web_client.post(
            "/account/api/read_key_add", data={"description": "Testing"}
        )
        assert session.get("account_status") == "read_key_add_success"

    mock_add_api_read_key.assert_called_with("Testing")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_delete_no_key_id(web_client: FlaskClient) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        mock, "delete_api_key"
    ) as mock_delete_api_key, web_client:
        response = web_client.post("/account/api/read_key_delete")
        assert session.get("account_status") == "read_key_delete_failure"

    mock_delete_api_key.assert_not_called()
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_delete_no_api_key(web_client: FlaskClient) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        mock, "delete_api_key"
    ) as mock_delete_api_key, patch.object(
        mock, "api_read_key", return_value=None
    ), web_client:
        response = web_client.post(
            "/account/api/read_key_delete", data={"key_id": "abcd"}
        )
        assert session.get("account_status") == "read_key_delete_failure"

    mock_delete_api_key.assert_not_called()
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_read_key_delete(web_client: FlaskClient) -> None:
    mock = user_mock()
    mock_api_key = Mock()
    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        mock, "delete_api_key"
    ) as mock_delete_api_key, patch.object(
        mock, "api_read_key", return_value=mock_api_key
    ), web_client:
        response = web_client.post(
            "/account/api/read_key_delete", data={"key_id": "abcd"}
        )
        assert session.get("account_status") == "read_key_delete_success"

    mock_delete_api_key.assert_called_with(mock_api_key)
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account"


def test_mytba(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
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

    mock = user_mock()
    mock.myTBA = mock_mytba

    mock_event_favorite = Mock()
    mock_event_subscription = Mock()
    mock_event_subscription.notification_names = []
    mock_team_favorite = Mock()
    mock_team_subscription = Mock()
    mock_team_subscription.notification_names = []
    mock_match_favorite = Mock()
    mock_match_subscription = Mock()
    mock_match_subscription.notification_names = []

    def mock_favorite(model_type, key):
        if model_type == ModelType.EVENT:
            return mock_event_favorite
        elif model_type == ModelType.TEAM:
            return mock_team_favorite
        return mock_match_favorite

    def mock_subscription(model_type, key):
        if model_type == ModelType.EVENT:
            return mock_event_subscription
        elif model_type == ModelType.TEAM:
            return mock_team_subscription
        return mock_match_subscription

    mock_mytba.favorite.side_effect = mock_favorite
    mock_mytba.subscription.side_effect = mock_subscription

    mock_year = 2012

    with patch.object(
        backend.web.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        backend.common.helpers.event_helper.EventHelper,
        "sorted_events",
        return_value=[mock_event_sorted],
    ) as mock_sorted_events, patch.object(
        backend.common.helpers.match_helper.MatchHelper,
        "natural_sort_matches",
        return_value=[mock_match_sorted],
    ) as mock_natural_sort_matches, patch.object(
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
    mock_natural_sort_matches.assert_called_with(mock_matches)
    mock_effective_season_year.assert_called()

    assert context["event_fav_sub"] == [
        (mock_event_sorted, mock_event_favorite, mock_event_subscription)
    ]
    assert context["team_fav_sub"] == [
        (mock_team, mock_team_favorite, mock_team_subscription)
    ]
    assert context["event_match_fav_sub"] == [
        (mock_event_sorted, [(mock_match_sorted, mock_match_favorite, mock_match_subscription)])
    ]
    assert context["year"] == mock_year
