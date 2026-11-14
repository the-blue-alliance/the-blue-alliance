import datetime
from typing import Any, Dict, Optional

from flask import g, session

from backend.common.firebase import app
from backend.common.models.user import User

_SESSION_KEY = "session"

# Set on flask.g whenever this request signs the user in or out, so the
# signed-in hint cookie can be resynced without inspecting every session
SESSION_AUTH_CHANGED = "session_auth_changed"

# 14 days is Firebase Admin's max (MAX_SESSION_COOKIE_DURATION_SECONDS) and
# drives both the Firebase session cookie TTL and the Flask cookie's Max-Age.
SESSION_COOKIE_LIFETIME = datetime.timedelta(days=14)


# Code from https://firebase.google.com/docs/auth/admin/manage-cookies


def _verify_id_token(id_token: str) -> Optional[dict]:
    from firebase_admin import auth

    try:
        return auth.verify_id_token(id_token, check_revoked=True, app=app())
    except Exception:
        return None


def verify_id_token(id_token: str) -> Optional[dict]:
    return _verify_id_token(id_token)


def create_session_cookie(id_token: str, expires_in: datetime.timedelta) -> None:
    from firebase_admin import auth

    session_cookie = auth.create_session_cookie(
        id_token, expires_in=expires_in, app=app()
    )
    session.permanent = True
    session[_SESSION_KEY] = session_cookie
    setattr(g, SESSION_AUTH_CHANGED, True)


def revoke_session_cookie() -> None:
    session_claims = _decoded_claims()
    if session_claims:
        from firebase_admin import auth

        auth.revoke_refresh_tokens(session_claims["sub"], app=app())
    session.pop(_SESSION_KEY, None)
    setattr(g, SESSION_AUTH_CHANGED, True)


def is_signed_in_session() -> bool:
    """
    Whether this request's session holds a Firebase session cookie. Doesn't
    verify it; _decoded_claims drops cookies that fail verification.
    """
    return _SESSION_KEY in session


def _decoded_claims() -> Optional[Dict[str, Any]]:
    session_cookie = session.get(_SESSION_KEY)
    if not session_cookie:
        return None

    # Verify the session cookie. In this case an additional check is added to detect
    # if the user's Firebase session was revoked, user deleted/disabled, etc.
    try:
        from firebase_admin import auth

        return auth.verify_session_cookie(session_cookie, check_revoked=True, app=app())
    except (
        auth.InvalidSessionCookieError,
        auth.UserDisabledError,
        auth.UserNotFoundError,
    ):
        # Session cookie is invalid, expired or revoked, and never will be valid
        # again. Drop it so the user is treated as signed out from now on.
        session.pop(_SESSION_KEY, None)
        setattr(g, SESSION_AUTH_CHANGED, True)
        return None
    except Exception:
        # Possibly transient (e.g. fetching Firebase certs). Force user to login.
        return None


def _current_user() -> Optional[User]:
    session_claims = _decoded_claims()
    if not session_claims:
        return None
    return User(session_claims)


def current_user() -> Optional[User]:
    return _current_user()


def _delete_user(uid: str) -> None:
    from firebase_admin import auth

    auth.delete_user(uid, app=app())


def delete_user(uid: str) -> None:
    _delete_user(uid)


def _user_context_processor() -> Dict[str, Optional[User]]:
    return dict(user=current_user())
