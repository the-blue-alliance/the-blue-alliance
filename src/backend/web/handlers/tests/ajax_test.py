import datetime
import json
from collections.abc import Generator

import pytest
from flask.testing import FlaskClient
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.consts.model_type import ModelType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
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


def test_apiwrite_events_not_logged_in(web_client: Client) -> None:
    resp = web_client.get("/_/account/apiwrite_events")
    assert resp.status_code == 401


def test_apiwrite_events(login_user, web_client: Client) -> None:
    Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        name="New York City Regional",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020ctha",
        year=2020,
        event_short="ctha",
        name="Hartford",
        event_type_enum=EventType.DISTRICT,
    ).put()
    ApiAuthAccess(
        id="active",
        owner=login_user.account_key,
        event_list=[ndb.Key(Event, "2020nyny")],
    ).put()
    ApiAuthAccess(
        id="expired",
        owner=login_user.account_key,
        event_list=[ndb.Key(Event, "2020ctha")],
        expiration=datetime.datetime(2000, 1, 1),
    ).put()

    resp = web_client.get("/_/account/apiwrite_events")
    assert resp.status_code == 200
    assert resp.json == [
        {"value": "2020nyny", "label": "2020 New York City Regional"},
    ]


def test_remap_teams_no_event(web_client: Client) -> None:
    resp = web_client.get("/_/remap_teams/2020nyny")
    assert resp.status_code == 200
    assert resp.json is None


def test_remap_teams(web_client: Client) -> None:
    Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
        remap_teams={"frc9000": "frc254B"},
    ).put()
    resp = web_client.get("/_/remap_teams/2020nyny")
    assert resp.status_code == 200
    assert resp.json == {"frc9000": "frc254B"}


def test_playoff_types(web_client: Client) -> None:
    resp = web_client.get("/_/playoff_types")
    assert resp.status_code == 200
    assert {"value": 0, "label": "Elimination Bracket (8 Alliances)"} in resp.json
