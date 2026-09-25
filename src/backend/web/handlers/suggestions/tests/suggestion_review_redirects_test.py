import pytest
from werkzeug.test import Client

from backend.web.handlers.suggestions.suggestion_review_redirects import (
    LEGACY_REVIEW_PATHS,
)


@pytest.mark.parametrize(
    "legacy_path, expected_location",
    [
        ("/suggest/review", "https://beta.thebluealliance.com/suggest/review"),
        (
            "/suggest/apiwrite/review",
            "https://beta.thebluealliance.com/suggest/review/api_auth_access",
        ),
        (
            "/suggest/cad/review",
            "https://beta.thebluealliance.com/suggest/review/robot",
        ),
        (
            "/suggest/event/media/review",
            "https://beta.thebluealliance.com/suggest/review/event_media",
        ),
        (
            "/suggest/event/webcast/review",
            "https://beta.thebluealliance.com/suggest/review/event",
        ),
        (
            "/suggest/offseason/review",
            "https://beta.thebluealliance.com/suggest/review/offseason-event",
        ),
        (
            "/suggest/match/video/review",
            "https://beta.thebluealliance.com/suggest/review/match",
        ),
        (
            "/suggest/team/media/review",
            "https://beta.thebluealliance.com/suggest/review/media",
        ),
        (
            "/suggest/team/social/review",
            "https://beta.thebluealliance.com/suggest/review/social-media",
        ),
    ],
)
def test_legacy_review_url_redirects_to_beta(
    web_client: Client,
    legacy_path: str,
    expected_location: str,
) -> None:
    # monkeypatch.setenv is invisible inside requests (the WSGI wrapper
    # rebuilds os.environ per request), so set the env on the request itself
    resp = web_client.get(legacy_path, environ_overrides={"GAE_ENV": "standard"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == expected_location


def test_every_legacy_path_is_covered_by_a_test() -> None:
    # Keep the parametrized list above in sync with the blueprint
    covered = {
        path
        for path, _ in test_legacy_review_url_redirects_to_beta.pytestmark[0].args[1]
    }
    assert covered == set(LEGACY_REVIEW_PATHS)


def test_legacy_review_url_redirects_locally_in_dev(web_client: Client) -> None:
    resp = web_client.get(
        "/suggest/team/media/review", environ_overrides={"GAE_ENV": "localdev"}
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "http://localhost:5173/suggest/review/media"


def test_legacy_review_url_does_not_require_login(web_client: Client) -> None:
    # The PWA handles auth; the redirect itself is unconditional
    resp = web_client.get("/suggest/review")
    assert resp.status_code == 302


@pytest.mark.parametrize("legacy_path", list(LEGACY_REVIEW_PATHS.keys()))
def test_legacy_review_url_rejects_post(web_client: Client, legacy_path: str) -> None:
    # The old review forms POSTed here; there is nothing left to accept them
    resp = web_client.post(legacy_path, data={})
    assert resp.status_code == 405
