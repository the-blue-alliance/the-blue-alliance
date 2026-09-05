"""The Jinja suggestion-review pages point moderators at the PWA queue.

Suggestion review shipped in the PWA (/suggest/review). These pages remain
functional, but each one now carries a banner linking to the equivalent PWA
queue so moderators try the new tooling instead.
"""

from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission

BANNER = b'data-testid="pwa-review-banner"'
PWA = b"https://beta.thebluealliance.com"


def _as_reviewer(login_user, *permissions: AccountPermission) -> None:
    login_user.has_permission.return_value = True
    login_user.permissions = list(permissions)


def test_review_home_links_to_pwa_queue_index(login_user, web_client: Client) -> None:
    _as_reviewer(login_user, AccountPermission.REVIEW_MEDIA)

    resp = web_client.get("/suggest/review")

    assert resp.status_code == 200
    assert BANNER in resp.data
    assert PWA + b"/suggest/review" in resp.data


def test_apiwrite_review_links_to_its_pwa_queue(login_user, web_client: Client) -> None:
    _as_reviewer(login_user, AccountPermission.REVIEW_APIWRITE)

    resp = web_client.get("/suggest/apiwrite/review")

    assert resp.status_code == 200
    assert BANNER in resp.data
    # The link targets the matching queue, not just the index.
    assert PWA + b"/suggest/review/api_auth_access" in resp.data


def test_banner_is_not_on_public_suggest_forms(web_client: Client) -> None:
    """Only reviewer pages get the banner; the public submission forms do not."""
    resp = web_client.get("/suggest/event/webcast?event_key=2026casj")

    # Whatever the form's own status, it must not carry the moderator banner.
    assert BANNER not in resp.data
