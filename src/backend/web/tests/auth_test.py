import datetime
from unittest.mock import ANY, Mock, patch

from firebase_admin import auth
from flask import session

import backend.web.auth as backend_auth
from backend.web.auth import (
    _decoded_claims,
    _user_context_processor,
    create_session_cookie,
    current_user,
    revoke_session_cookie,
)
from backend.web.models.user import User


def test_create_session_cookie() -> None:
    id_token = "abc"
    expires_in = datetime.timedelta(seconds=1)

    from backend.web.main import app

    app.secret_key = "test_secret_key"

    with app.test_request_context("/"):
        assert session.get("session") is None

        with patch.object(auth, "create_session_cookie") as mock_create_session_cookie:
            create_session_cookie(id_token, expires_in)
        mock_create_session_cookie.assert_called_with(
            "abc", expires_in=expires_in, app=ANY
        )

        assert session["session"] is not None


def test_revoke_session_cookie_no_claims() -> None:
    from backend.web.main import app

    app.secret_key = "test_secret_key"

    with app.test_request_context("/"):
        session["session"] = "abc"

        with patch.object(
            backend_auth, "_decoded_claims", return_value=None
        ), patch.object(auth, "revoke_refresh_tokens") as mock_revoke_refresh_tokens:
            revoke_session_cookie()
        mock_revoke_refresh_tokens.assert_not_called()

        assert session.get("session") is None


def test_revoke_session_cookie() -> None:
    sub = "sub"

    from backend.web.main import app

    app.secret_key = "test_secret_key"

    with app.test_request_context("/"):
        session["session"] = "abc"

        with patch.object(
            backend_auth, "_decoded_claims", return_value={"sub": sub}
        ), patch.object(auth, "revoke_refresh_tokens") as mock_revoke_refresh_tokens:
            revoke_session_cookie()
        mock_revoke_refresh_tokens.assert_called_with(sub, app=ANY)

        assert session.get("session") is None


def test_decoded_claims_no_session() -> None:
    from backend.web.main import app

    app.secret_key = "test_secret_key"

    with app.test_request_context("/"):
        assert session.get("session") is None
        assert _decoded_claims() is None


def test_decoded_claims_throw_error() -> None:
    from backend.web.main import app

    app.secret_key = "test_secret_key"

    with app.test_request_context("/"):
        session["session"] = "abc"

        error_mock = Mock()
        error_mock.side_effect = auth.InvalidSessionCookieError(
            message="Some error here"
        )

        with patch.object(
            auth, "verify_session_cookie", error_mock
        ) as mock_verify_session_cookie:
            assert _decoded_claims() is None
        mock_verify_session_cookie.assert_called_once()


def test_decoded_claims() -> None:
    from backend.web.main import app

    app.secret_key = "test_secret_key"

    with app.test_request_context("/"):
        session["session"] = "abc"

        mock_decoded_claims = {"email": "zach@thebluealliance.com"}

        with patch.object(
            auth, "verify_session_cookie", return_value=mock_decoded_claims
        ) as mock_verify_session_cookie:
            decoded_claims = _decoded_claims()
        mock_verify_session_cookie.assert_called_once()
        assert mock_decoded_claims == decoded_claims


def test_current_user_no_claims() -> None:
    with patch.object(backend_auth, "_decoded_claims", return_value=None):
        user = current_user()
    assert user is None


def test_current_user() -> None:
    with patch.object(backend_auth, "_decoded_claims", return_value={"abc": "abc"}):
        user = current_user()
    assert user is not None


def test_user_context_processor_no_claims() -> None:
    with patch.object(backend_auth, "_decoded_claims", return_value=None):
        user_context = _user_context_processor()
    assert user_context == {"user": None}


def test_user_context_processor() -> None:
    with patch.object(backend_auth, "_decoded_claims", return_value={"abc": "abc"}):
        user_context = _user_context_processor()
    assert type(user_context["user"]) is User
