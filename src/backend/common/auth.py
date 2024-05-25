import datetime
from typing import Any, Dict, Optional

from firebase_admin import auth
from flask import session
from google.auth import exceptions

from backend.common.firebase import app
from backend.common.models.user import User


_SESSION_KEY = "session"


# Code from https://firebase.google.com/docs/auth/admin/manage-cookies


def _verify_id_token(id_token: str) -> Optional[dict]:
    try:
        return auth.verify_id_token(id_token, check_revoked=True, app=app())
    except Exception:
        return None


def verify_id_token(id_token: str) -> Optional[dict]:
    return _verify_id_token(id_token)


def create_session_cookie(id_token: str, expires_in: datetime.timedelta) -> None:
    session_cookie = auth.create_session_cookie(
        id_token, expires_in=expires_in, app=app()
    )
    session[_SESSION_KEY] = session_cookie


def revoke_session_cookie() -> None:
    session_claims = _decoded_claims()
    if session_claims:
        auth.revoke_refresh_tokens(session_claims["sub"], app=app())
    session.pop(_SESSION_KEY, None)


def _decoded_claims() -> Optional[Dict[str, Any]]:
    session_cookie = session.get(_SESSION_KEY)
    if not session_cookie:
        return None

    # Verify the session cookie. In this case an additional check is added to detect
    # if the user's Firebase session was revoked, user deleted/disabled, etc.
    try:
        return auth.verify_session_cookie(session_cookie, check_revoked=True, app=app())
    except (auth.InvalidSessionCookieError, exceptions.DefaultCredentialsError):
        # Session cookie is invalid, expired or revoked. Force user to login.
        return None


def _current_user() -> Optional[User]:
    session_claims = _decoded_claims()
    if not session_claims:
        return None
    return User(session_claims)


def current_user() -> Optional[User]:
    return _current_user()


def _delete_user(uid: str) -> None:
    auth.delete_user(uid, app=app())


def delete_user(uid: str) -> None:
    _delete_user(uid)


def _user_context_processor() -> Dict[str, Optional[User]]:
    return dict(user=current_user())
