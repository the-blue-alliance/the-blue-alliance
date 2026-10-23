from unittest.mock import patch

from firebase_admin import auth
from flask.testing import FlaskClient

from backend.web.signed_in_cookie import SIGNED_IN_COOKIE


def _signed_in_set_cookie(response) -> str:
    cookies = [
        c
        for c in response.headers.getlist("Set-Cookie")
        if c.startswith(f"{SIGNED_IN_COOKIE}=")
    ]
    assert len(cookies) <= 1
    return cookies[0] if cookies else ""


def test_anonymous_request_untouched(web_client: FlaskClient) -> None:
    resp = web_client.get("/contact")
    assert resp.status_code == 200
    assert "Set-Cookie" not in resp.headers


def test_login_sets_marker(web_client: FlaskClient) -> None:
    with patch.object(auth, "create_session_cookie", return_value="firebase-cookie"):
        resp = web_client.post("/account/login", data={"id_token": "abc"})
    assert resp.status_code == 200
    cookie = _signed_in_set_cookie(resp)
    assert cookie.startswith(f"{SIGNED_IN_COOKIE}=1;")
    assert "Max-Age=1209600" in cookie
    assert "Path=/" in cookie
    assert "SameSite=Lax" in cookie
    assert "HttpOnly" not in cookie


def test_existing_session_gets_marker(web_client: FlaskClient) -> None:
    with web_client.session_transaction() as session:
        session["session"] = "firebase-cookie"
    resp = web_client.get("/contact")
    assert _signed_in_set_cookie(resp).startswith(f"{SIGNED_IN_COOKIE}=1;")


def test_synced_marker_untouched(web_client: FlaskClient) -> None:
    with web_client.session_transaction() as session:
        session["session"] = "firebase-cookie"
    web_client.set_cookie(SIGNED_IN_COOKIE, "1")
    resp = web_client.get("/contact")
    assert _signed_in_set_cookie(resp) == ""


def test_marker_without_session_cleared(web_client: FlaskClient) -> None:
    web_client.set_cookie(SIGNED_IN_COOKIE, "1")
    resp = web_client.get("/contact")
    cookie = _signed_in_set_cookie(resp)
    assert cookie.startswith(f"{SIGNED_IN_COOKIE}=;")
    assert "Max-Age=0" in cookie


def test_logout_clears_marker(web_client: FlaskClient) -> None:
    with web_client.session_transaction() as session:
        session["session"] = "firebase-cookie"
    web_client.set_cookie(SIGNED_IN_COOKIE, "1")
    with (
        patch.object(auth, "verify_session_cookie", return_value={"sub": "uid"}),
        patch.object(auth, "revoke_refresh_tokens"),
    ):
        resp = web_client.get("/account/logout")
    assert resp.status_code == 302
    assert _signed_in_set_cookie(resp).startswith(f"{SIGNED_IN_COOKIE}=;")


def test_stale_session_clears_marker_and_session(web_client: FlaskClient) -> None:
    with web_client.session_transaction() as session:
        session["session"] = "firebase-cookie"
    web_client.set_cookie(SIGNED_IN_COOKIE, "1")
    with patch.object(
        auth,
        "verify_session_cookie",
        side_effect=auth.ExpiredSessionCookieError("expired", None),
    ):
        resp = web_client.get("/_/account/favorites/1")
    assert resp.status_code == 401
    assert _signed_in_set_cookie(resp).startswith(f"{SIGNED_IN_COOKIE}=;")
    with web_client.session_transaction() as session:
        assert "session" not in session

    # Not re-set on the next request
    resp = web_client.get("/contact")
    assert _signed_in_set_cookie(resp) == ""
