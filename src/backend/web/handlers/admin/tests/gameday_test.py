from werkzeug.test import Client

from backend.common.consts.webcast_type import WebcastType
from backend.common.sitevars.gameday_special_webcasts import (
    GamedaySpecialWebcasts,
    WebcastType as TSpecialWebcast,
)


def test_gameday_dashboard(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/gameday")
    assert resp.status_code == 200


def test_add_special_webcast(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.post(
        "/admin/gameday",
        data={
            "action": "add",
            "item": "webcast",
            "webcast_type": "twitch",
            "webcast_channel": "tbagameday",
            "webcast_file": "file",
            "webcast_name": "TBA Gameday",
            "webcast_urlkey": "gameday",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/gameday"

    webcasts = GamedaySpecialWebcasts.webcasts()
    assert webcasts == [
        TSpecialWebcast(
            type=WebcastType.TWITCH,
            channel="tbagameday",
            name="TBA Gameday",
            key_name="gameday",
            file="file",
        )
    ]


def test_remove_special_webcast(web_client: Client, login_gae_admin, ndb_stub) -> None:
    GamedaySpecialWebcasts.add_special_webcast(
        TSpecialWebcast(
            type=WebcastType.TWITCH,
            channel="tbagameday",
            name="TBA Gameday",
            key_name="gameday",
            file="file",
        )
    )
    resp = web_client.post(
        "/admin/gameday",
        data={
            "action": "delete",
            "item": "webcast",
            "webcast_key": "gameday",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/gameday"

    webcasts = GamedaySpecialWebcasts.webcasts()
    assert webcasts == []


def test_add_alias(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.post(
        "/admin/gameday",
        data={
            "action": "add",
            "item": "alias",
            "alias_name": "cmp",
            "alias_args": "test_test",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/gameday"

    alias = GamedaySpecialWebcasts.get_alias("cmp")
    assert alias == "test_test"


def test_remove_alias(web_client: Client, login_gae_admin, ndb_stub) -> None:
    GamedaySpecialWebcasts.add_alias("cmp", "test_test")
    resp = web_client.post(
        "/admin/gameday",
        data={
            "action": "delete",
            "item": "alias",
            "alias_key": "cmp",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/gameday"

    alias = GamedaySpecialWebcasts.get_alias("cmp")
    assert alias is None


def test_set_default_chat(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.post(
        "/admin/gameday",
        data={"action": "defaultChat", "defaultChat": "tbagameday_chat"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/gameday"

    default_chat = GamedaySpecialWebcasts.default_chat()
    assert default_chat == "tbagameday_chat"
