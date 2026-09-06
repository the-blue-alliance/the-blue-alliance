import json
from collections.abc import Generator

import pytest
from flask.testing import FlaskClient
from werkzeug.test import Client

from backend.common.consts.model_type import ModelType
from backend.common.models.favorite import Favorite
from backend.common.models.typeahead_entry import TypeaheadEntry


def test_typeahead_empty(web_client: Client) -> None:
    resp = web_client.get("/_/typeahead/teams-all")
    assert resp.status_code == 200
    assert resp.json == []


def test_typeahead_empty_cached(web_client: Client) -> None:
    resp = web_client.get("/_/typeahead/teams-all")
    assert resp.status_code == 200
    assert resp.json == []


def test_typeahead_content(web_client: Client) -> None:
    data = ["254 | The Cheesy Poofs"]
    entry = TypeaheadEntry(id=TypeaheadEntry.ALL_TEAMS_KEY, data_json=json.dumps(data))
    entry.put()

    resp = web_client.get("/_/typeahead/teams-all")
    assert resp.status_code == 200
    assert resp.json == data


def test_typeahead_content_cached(web_client: Client) -> None:
    data = ["254 | The Cheesy Poofs"]
    entry = TypeaheadEntry(id=TypeaheadEntry.ALL_TEAMS_KEY, data_json=json.dumps(data))
    entry.put()

    resp = web_client.get("/_/typeahead/teams-all")
    assert resp.status_code == 200
    assert resp.json == data

    resp2 = web_client.get(
        "/_/typeahead/teams-all",
        headers={"If-Modified-Since": resp.headers["Last-Modified"]},
    )
    assert resp2.status_code == 304


def test_favorites_not_logged_in(web_client: Client) -> None:
    resp = web_client.get("/_/account/favorites/1")
    assert resp.status_code == 401


def test_favorites_bad_type(login_user, web_client: Client) -> None:
    resp = web_client.get("/_/account/favorites/999")
    assert resp.status_code == 400


def test_favorites_empty(login_user, web_client: Client) -> None:
    resp = web_client.get("/_/account/favorites/1")
    assert resp.status_code == 200
    assert resp.json == []


def test_favorites(login_user, web_client: Client) -> None:
    account = login_user.account_key.get()
    favorite = Favorite(
        parent=account.key,
        model_type=ModelType.TEAM,
        model_key="frc254",
        user_id=account.email,
    )
    favorite.put()

    resp = web_client.get("/_/account/favorites/1")
    assert resp.status_code == 200
    assert resp.json == [favorite.to_json()]


def test_favorites_add_not_logged_in(web_client: Client) -> None:
    resp = web_client.post("/_/account/favorites/add")
    assert resp.status_code == 401


def test_favorites_add(login_user, web_client: Client) -> None:
    resp = web_client.post(
        "/_/account/favorites/add",
        data={"model_type": ModelType.TEAM, "model_key": "frc254"},
    )
    assert resp.status_code == 200

    favorites = Favorite.query(ancestor=login_user.account_key).fetch()
    assert len(favorites) == 1
    assert favorites[0].model_type == ModelType.TEAM
    assert favorites[0].model_key == "frc254"


def test_favorites_delete_not_logged_in(web_client: Client) -> None:
    resp = web_client.post("/_/account/favorites/delete")
    assert resp.status_code == 401


def test_favorites_delete(login_user, web_client: Client) -> None:
    Favorite(
        parent=login_user.account_key,
        model_type=ModelType.TEAM,
        model_key="frc254",
        user_id=str(login_user.account_key.id()),
    ).put()
    resp = web_client.post(
        "/_/account/favorites/delete",
        data={"model_type": ModelType.TEAM, "model_key": "frc254"},
    )
    assert resp.status_code == 200

    favorites = Favorite.query(ancestor=login_user.account_key).fetch()
    assert len(favorites) == 0


@pytest.fixture
def csrf_enforced(web_client: FlaskClient) -> Generator[FlaskClient, None, None]:
    """Re-enables the CSRF checking that the `web_client` fixture disables."""
    from backend.web.main import app

    previous = app.config["WTF_CSRF_CHECK_DEFAULT"]
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True
    try:
        yield web_client
    finally:
        app.config["WTF_CSRF_CHECK_DEFAULT"] = previous


def test_account_info_not_logged_in(web_client: Client) -> None:
    resp = web_client.get("/_/account/info")
    assert resp.json is not None
    assert resp.json["logged_in"] is False
    assert resp.json["user_id"] is None


def test_account_info_logged_in(login_user, web_client: Client) -> None:
    resp = web_client.get("/_/account/info")
    assert resp.json is not None
    assert resp.json["logged_in"] is True
    assert resp.json["user_id"] == str(login_user.uid)


def test_account_info_returns_csrf_token(web_client: Client) -> None:
    resp = web_client.get("/_/account/info")
    assert resp.status_code == 200
    assert resp.json is not None
    assert resp.json["csrf_token"]


def test_account_info_is_not_shared_cacheable(web_client: Client) -> None:
    # The response carries a per-session CSRF token, so no shared cache (the
    # Google Frontend, a proxy, ...) may store it.
    # See https://github.com/the-blue-alliance/the-blue-alliance/issues/10495
    resp = web_client.get("/_/account/info")
    assert "no-store" in resp.headers["Cache-Control"]


def test_account_info_csrf_token_is_accepted(
    login_user, csrf_enforced: FlaskClient
) -> None:
    token = csrf_enforced.get("/_/account/info").json["csrf_token"]

    resp = csrf_enforced.post(
        "/_/account/favorites/add",
        data={"model_type": ModelType.TEAM, "model_key": "frc254"},
        headers={"X-CSRFToken": token},
    )
    assert resp.status_code == 200

    favorites = Favorite.query(ancestor=login_user.account_key).fetch()
    assert len(favorites) == 1


def test_account_info_csrf_token_from_another_session_is_rejected(
    login_user, csrf_enforced: FlaskClient
) -> None:
    # This is the failure mode of issue #10495: a token minted for someone
    # else's session must not be usable, which is exactly why the token can't
    # be baked into a publicly cached page.
    from backend.web.main import app

    other_session_token = app.test_client().get("/_/account/info").json["csrf_token"]

    resp = csrf_enforced.post(
        "/_/account/favorites/add",
        data={"model_type": ModelType.TEAM, "model_key": "frc254"},
        headers={"X-CSRFToken": other_session_token},
    )
    assert resp.status_code == 400
    assert Favorite.query(ancestor=login_user.account_key).fetch() == []
