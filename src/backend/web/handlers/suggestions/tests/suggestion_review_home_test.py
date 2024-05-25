from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from werkzeug.test import Client

from backend.common.consts.account_permission import (
    AccountPermission,
    SUGGESTION_PERMISSIONS,
)

PERMISSION_TO_SUGGESTION_ITEMS = {
    AccountPermission.REVIEW_MEDIA: [
        "match-video-suggestions",
        "event-webcast-suggestions",
        "team-media-suggestions",
        "team-social-media-suggestions",
    ],
    AccountPermission.REVIEW_EVENT_MEDIA: ["event-media-suggestions"],
    AccountPermission.REVIEW_DESIGNS: ["team-cad-suggestions"],
    AccountPermission.REVIEW_OFFSEASON_EVENTS: ["offseason-event-suggestions"],
    AccountPermission.REVIEW_APIWRITE: ["apiwrite-suggestions"],
}


@pytest.fixture(params=SUGGESTION_PERMISSIONS)
def suggestion_permissions(request):
    return request.param


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/review")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_missing_permissions(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/review")
    assert response.status_code == 401


def test_with_wrong_permission(login_user, web_client: Client) -> None:
    login_user.permissions = [AccountPermission.OFFSEASON_EVENTWIZARD]
    response = web_client.get("/suggest/review")
    assert response.status_code == 401


def test_shows_review_for_permissions(
    login_user, suggestion_permissions, web_client: Client
) -> None:
    login_user.permissions = [suggestion_permissions]
    response = web_client.get("/suggest/review")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    review_list = soup.find("ul", id="suggestion-review-list")
    assert review_list is not None

    expected_review_items = PERMISSION_TO_SUGGESTION_ITEMS[suggestion_permissions]
    review_items = review_list.find_all("li")
    assert review_items is not None
    assert set([i["id"] for i in review_items]) == set(expected_review_items)


def test_shows_all_reviews_for_admin(
    login_admin, suggestion_permissions, web_client: Client
) -> None:
    response = web_client.get("/suggest/review")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    review_list = soup.find("ul", id="suggestion-review-list")
    assert review_list is not None

    expected_review_items = PERMISSION_TO_SUGGESTION_ITEMS[suggestion_permissions]
    review_items = review_list.find_all("li")
    assert review_items is not None
    assert (
        set(expected_review_items).issubset(set([i["id"] for i in review_items]))
        is True
    )
