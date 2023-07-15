import json

from werkzeug.test import Client

from backend.common.consts.client_type import ClientType
from backend.common.consts.model_type import ModelType
from backend.common.models.favorite import Favorite
from backend.common.models.mobile_client import MobileClient
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


def test_account_info_not_logged_in(web_client: Client) -> None:
    resp = web_client.get("/_/account/info")
    assert resp.json == {
        "logged_in": False,
        "user_id": None,
    }


def test_account_info_logged_in(login_user, web_client: Client) -> None:
    resp = web_client.get("/_/account/info")
    assert resp.json == {
        "logged_in": True,
        "user_id": str(login_user.uid),
    }


def test_register_fcm_not_logged_in(web_client: Client) -> None:
    resp = web_client.post("/_/account/register_fcm_token", data={})
    assert resp.status_code == 401


def test_register_fcm_token(login_user, web_client: Client) -> None:
    resp = web_client.post(
        "/_/account/register_fcm_token",
        data={
            "fcm_token": "abc123",
            "uuid": "device_test",
            "display_name": "Test Device",
        },
    )
    assert resp.status_code == 200

    clients = MobileClient.query(ancestor=login_user.account_key).fetch()
    assert len(clients) == 1
    assert clients[0].user_id == str(login_user.uid)
    assert clients[0].messaging_id == "abc123"
    assert clients[0].client_type == ClientType.WEB
    assert clients[0].device_uuid == "device_test"
    assert clients[0].display_name == "Test Device"


def test_register_fcm_token_update_existing(login_user, web_client: Client) -> None:
    MobileClient(
        parent=login_user.account_key,
        user_id=str(login_user.uid),
        messaging_id="abc123",
        client_type=ClientType.WEB,
        device_uuid="device_test",
        display_name="Test Device",
    ).put()

    resp = web_client.post(
        "/_/account/register_fcm_token",
        data={
            "fcm_token": "asdf456",
            "uuid": "device_test",
            "display_name": "Test Device 2",
        },
    )
    assert resp.status_code == 200

    clients = MobileClient.query(ancestor=login_user.account_key).fetch()
    assert len(clients) == 1
    assert clients[0].user_id == str(login_user.uid)
    assert clients[0].messaging_id == "asdf456"
    assert clients[0].client_type == ClientType.WEB
    assert clients[0].device_uuid == "device_test"
    assert clients[0].display_name == "Test Device 2"
