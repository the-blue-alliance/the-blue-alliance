import re

from werkzeug.test import Client

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.account import Account
from backend.common.models.suggestion import Suggestion


def test_not_logged_in_no_user(web_client: Client) -> None:
    resp = web_client.get("/admin/tasks")
    assert resp.status_code == 401


def test_not_logged_in_not_admin(web_client: Client, login_gae_user) -> None:
    resp = web_client.get("/admin/tasks")
    assert resp.status_code == 401


def test_not_logged_in_admin(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/tasks")
    assert resp.status_code == 200


def test_admin_home_not_logged_in(web_client: Client) -> None:
    resp = web_client.get("/admin/")
    assert resp.status_code == 401


def test_admin_home_logged_in_admin(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/")
    assert resp.status_code == 200
    assert b"Pending Suggestions" in resp.data


def test_admin_home_shows_pending_suggestions_count(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    # Create an author for the suggestions
    author_key = Account(id="author", email="author@example.com").put()

    # Create some pending suggestions
    Suggestion(
        author=author_key,
        target_key="frc254",
        target_model="media",
        review_state=SuggestionState.REVIEW_PENDING,
    ).put()
    Suggestion(
        author=author_key,
        target_key="frc1678",
        target_model="media",
        review_state=SuggestionState.REVIEW_PENDING,
    ).put()
    # Create an accepted suggestion (should not be counted)
    Suggestion(
        author=author_key,
        target_key="frc971",
        target_model="media",
        review_state=SuggestionState.REVIEW_ACCEPTED,
    ).put()

    resp = web_client.get("/admin/")
    assert resp.status_code == 200
    # Check that the suggestions badge shows the correct count
    # The template renders: <span class="badge pull-right">{{suggestions_count}}</span>
    match = re.search(
        rb'<span class="badge pull-right">(\d+)</span>\s*Pending Suggestions',
        resp.data,
    )
    assert match is not None, "Could not find pending suggestions badge"
    assert match.group(1) == b"2", f"Expected 2 pending suggestions, got {match.group(1)}"


def test_admin_home_shows_recent_users(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    # Create some users
    Account(id="user1", email="user1@example.com", display_name="User One").put()
    Account(id="user2", email="user2@example.com", display_name="User Two").put()

    resp = web_client.get("/admin/")
    assert resp.status_code == 200
    assert b"User One" in resp.data
    assert b"User Two" in resp.data
