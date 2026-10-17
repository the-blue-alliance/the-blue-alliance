from flask import current_app, g, request, Response

from backend.common.auth import (
    is_signed_in_session,
    SESSION_AUTH_CHANGED,
    SESSION_COOKIE_LIFETIME,
)

# JS-readable hint that this browser has a signed-in session, so pages can skip
# fetching account data for signed-out visitors. Not a credential: the session
# cookie is still what authenticates every account request.
SIGNED_IN_COOKIE = "tba-signed-in"


def sync_signed_in_cookie(response: Response) -> Response:
    has_session_cookie = current_app.config["SESSION_COOKIE_NAME"] in request.cookies
    if has_session_cookie or g.get(SESSION_AUTH_CHANGED, False):
        signed_in = is_signed_in_session()
    else:
        # Don't touch the session for anonymous traffic; reading it adds Vary: Cookie
        signed_in = False

    has_marker = SIGNED_IN_COOKIE in request.cookies
    if signed_in and not has_marker:
        response.set_cookie(
            SIGNED_IN_COOKIE,
            "1",
            max_age=SESSION_COOKIE_LIFETIME,
            path="/",
            secure=current_app.config["SESSION_COOKIE_SECURE"],
            httponly=False,
            samesite="Lax",
        )
    elif not signed_in and has_marker:
        response.delete_cookie(SIGNED_IN_COOKIE, path="/")
    return response
