from typing import List
from unittest.mock import ANY, Mock, patch
from urllib.parse import parse_qsl, quote, urlparse

import pytest
from flask import session
from flask.testing import FlaskClient

import backend
from backend.web.handlers.tests.conftest import CapturedTemplate
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
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account/register?next={}".format(quote(next_url)))

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == (expected if expected else "/account")


def test_register_register_no_account_id(web_client: FlaskClient) -> None:
    mock = user_mock(registered=False)
    mock.uid = "abc"

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.post("/account/register", data={"display_name": "Zach"})

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/"


def test_register_register_no_display_name(web_client: FlaskClient) -> None:
    mock = user_mock(registered=False)
    mock.uid = "abc"

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.post("/account/register", data={"account_id": "abc"})

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/"


def test_register_register_account_id_mismatch(web_client: FlaskClient) -> None:
    mock = user_mock(registered=False)
    mock.uid = "abc"

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account/edit")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_edit.html"
    assert get_page_title(response.data) == "Edit Profile - The Blue Alliance"
    assert context["status"] is None


def test_edit_no_account_id(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
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


def test_edit_mismatch_account_id(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock = user_mock()
    mock.uid = "abc"

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
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


def test_edit_no_display_name(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock = user_mock()
    mock.uid = "abc"

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
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


def test_edit_success(
    captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    mock = user_mock()
    mock.uid = "abc"

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), web_client, patch.object(
        mock, "update_display_name"
    ) as mock_update_display_name:
        response = web_client.post(
            "/account/edit", data={"account_id": "abc", "display_name": "Zach"}
        )
        assert session.get("account_edit_status") is None

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
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
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
        backend.web.handlers.decorators, "current_user", return_value=mock
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
