from datetime import datetime
from typing import List, Optional

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.event import Event


def test_api_auth_add(login_gae_admin, web_client: Client) -> None:
    resp = web_client.get("/admin/api_auth/add")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert 'name="event_list_str"' in content
    assert 'name="event_list_str" placeholder="2014cc,2014mttd" value=""' in content


def test_api_auth_add_with_event_key(login_gae_admin, web_client: Client) -> None:
    resp = web_client.get("/admin/api_auth/add?event_key=2020nyny")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert 'value="2020nyny"' in content


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _store_write_auth(
    auth_id: str = "writekey",
    auth_types: Optional[List[AuthType]] = None,
    expiration: Optional[datetime] = None,
    **kwargs,
) -> ApiAuthAccess:
    auth = ApiAuthAccess(
        id=auth_id,
        description=f"{auth_id} description",
        secret="secret",
        auth_types_enum=(
            auth_types if auth_types is not None else [AuthType.EVENT_MATCHES]
        ),
        expiration=expiration,
        **kwargs,
    )
    auth.put()
    return auth


# ---------------------------------------------------------------------------
# /admin/api_auth/delete/<auth_id>
# ---------------------------------------------------------------------------


def test_api_auth_delete_get_not_found(login_gae_admin, web_client: Client) -> None:
    resp = web_client.get("/admin/api_auth/delete/nope")
    assert resp.status_code == 404


def test_api_auth_delete_get(login_gae_admin, web_client: Client) -> None:
    _store_write_auth("writekey")
    resp = web_client.get("/admin/api_auth/delete/writekey")
    assert resp.status_code == 200
    assert b"writekey" in resp.data


def test_api_auth_delete_post_not_found(login_gae_admin, web_client: Client) -> None:
    resp = web_client.post("/admin/api_auth/delete/nope")
    assert resp.status_code == 404


def test_api_auth_delete_post(login_gae_admin, web_client: Client) -> None:
    _store_write_auth("writekey")
    resp = web_client.post("/admin/api_auth/delete/writekey")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/api_auth/manage"
    assert ApiAuthAccess.get_by_id("writekey") is None


# ---------------------------------------------------------------------------
# /admin/api_auth/edit/<auth_id>  (GET)
# ---------------------------------------------------------------------------


def test_api_auth_edit_get_not_found(login_gae_admin, web_client: Client) -> None:
    resp = web_client.get("/admin/api_auth/edit/nope")
    assert resp.status_code == 404


def test_api_auth_edit_get(login_gae_admin, web_client: Client) -> None:
    owner_key = Account(id="owner", email="owner@example.com").put()
    _store_write_auth(
        "writekey",
        owner=owner_key,
        expiration=datetime(2030, 6, 30),
        event_list=[ndb.Key(Event, "2020nyny")],
        district_list=[ndb.Key(District, "2020ne")],
        offseason_webcast_channels=["chan1", "chan2"],
    )
    resp = web_client.get("/admin/api_auth/edit/writekey")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert 'value="owner@example.com"' in content
    assert 'value="2030-06-30"' in content
    assert 'value="2020nyny"' in content
    assert 'value="2020ne"' in content
    assert 'value="chan1,chan2"' in content


# ---------------------------------------------------------------------------
# /admin/api_auth/edit/<auth_id>  (POST)
# ---------------------------------------------------------------------------


def test_api_auth_edit_post_creates_new_key_with_defaults(
    login_gae_admin, web_client: Client
) -> None:
    resp = web_client.post("/admin/api_auth/edit/newkey", data={})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/api_auth/manage"

    auth = ApiAuthAccess.get_by_id("newkey")
    assert auth is not None
    assert auth.description == ""
    assert auth.owner is None
    assert auth.expiration is None
    assert auth.allow_admin is False
    assert auth.secret is not None
    assert len(auth.secret) == 64
    assert auth.district_list == []
    assert auth.event_list == []
    assert auth.offseason_webcast_channels == []
    assert auth.all_official_events is False
    assert auth.auth_types_enum == []


def test_api_auth_edit_post_creates_new_key_with_all_fields(
    login_gae_admin, web_client: Client
) -> None:
    owner_key = Account(id="owner", email="owner@example.com").put()
    Event(
        id="2020ctwat",
        event_short="ctwat",
        year=2020,
        event_type_enum=EventType.DISTRICT,
        district_key=ndb.Key(District, "2020ne"),
    ).put()
    Event(
        id="2020casj",
        event_short="casj",
        year=2020,
        event_type_enum=EventType.REGIONAL,
    ).put()

    resp = web_client.post(
        "/admin/api_auth/edit/newkey",
        data={
            "description": "A new key",
            "owner": "owner@example.com",
            "expiration": "2030-01-15",
            "allow_admin": "on",
            "event_list_str": "2020nyny, 2020casj,2020nyny",
            "district_list_str": "2020ne",
            "webcast_list_str": "chan1,chan2",
            "all_official_events": "on",
            "allow_edit_teams": "on",
            "allow_edit_matches": "on",
            "allow_edit_rankings": "on",
            "allow_edit_alliances": "on",
            "allow_edit_awards": "on",
            "allow_edit_match_video": "on",
            "allow_edit_info": "on",
            "allow_edit_zebra_motionworks": "on",
        },
    )
    assert resp.status_code == 302

    auth = ApiAuthAccess.get_by_id("newkey")
    assert auth is not None
    assert auth.description == "A new key"
    assert auth.owner == owner_key
    assert auth.expiration == datetime(2030, 1, 15)
    assert auth.allow_admin is True
    assert auth.district_list == [ndb.Key(District, "2020ne")]
    # Explicit events are deduplicated, and district events are resolved and added
    assert auth.event_list == [
        ndb.Key(Event, "2020casj"),
        ndb.Key(Event, "2020ctwat"),
        ndb.Key(Event, "2020nyny"),
    ]
    assert auth.offseason_webcast_channels == ["chan1", "chan2"]
    assert auth.all_official_events is True
    assert auth.auth_types_enum == [
        AuthType.EVENT_TEAMS,
        AuthType.EVENT_MATCHES,
        AuthType.EVENT_RANKINGS,
        AuthType.EVENT_ALLIANCES,
        AuthType.EVENT_AWARDS,
        AuthType.MATCH_VIDEO,
        AuthType.EVENT_INFO,
        AuthType.ZEBRA_MOTIONWORKS,
    ]


def test_api_auth_edit_post_unknown_owner_email(
    login_gae_admin, web_client: Client
) -> None:
    resp = web_client.post(
        "/admin/api_auth/edit/newkey",
        data={"owner": "nobody@example.com"},
    )
    assert resp.status_code == 302

    auth = ApiAuthAccess.get_by_id("newkey")
    assert auth is not None
    assert auth.owner is None


def test_api_auth_edit_post_updates_existing_key(
    login_gae_admin, web_client: Client
) -> None:
    owner_key = Account(id="owner", email="owner@example.com").put()
    _store_write_auth(
        "writekey",
        auth_types=[AuthType.EVENT_MATCHES, AuthType.EVENT_TEAMS],
        expiration=datetime(2020, 1, 1),
        allow_admin=True,
        all_official_events=True,
        event_list=[ndb.Key(Event, "2019nyny")],
        district_list=[ndb.Key(District, "2019ne")],
        offseason_webcast_channels=["oldchan"],
    )

    resp = web_client.post(
        "/admin/api_auth/edit/writekey",
        data={
            "description": "Updated",
            "owner": "owner@example.com",
            "event_list_str": "2020nyny",
            "allow_edit_awards": "on",
        },
    )
    assert resp.status_code == 302

    auth = ApiAuthAccess.get_by_id("writekey")
    assert auth is not None
    assert auth.description == "Updated"
    assert auth.secret == "secret"  # Secret is preserved on update
    assert auth.owner == owner_key
    assert auth.expiration is None
    assert auth.allow_admin is False
    assert auth.all_official_events is False
    assert auth.event_list == [ndb.Key(Event, "2020nyny")]
    assert auth.district_list == []
    assert auth.auth_types_enum == [AuthType.EVENT_AWARDS]


def test_api_auth_edit_post_preserves_read_api_type(
    login_gae_admin, web_client: Client
) -> None:
    _store_write_auth("readkey", auth_types=[AuthType.READ_API])

    resp = web_client.post(
        "/admin/api_auth/edit/readkey",
        data={"description": "Still a read key"},
    )
    assert resp.status_code == 302

    auth = ApiAuthAccess.get_by_id("readkey")
    assert auth is not None
    assert auth.description == "Still a read key"
    assert auth.auth_types_enum == [AuthType.READ_API]


# ---------------------------------------------------------------------------
# /admin/api_auth/manage[/<key_type>]
# ---------------------------------------------------------------------------


def test_api_auth_manage_no_type_redirects_to_write(
    login_gae_admin, web_client: Client
) -> None:
    resp = web_client.get("/admin/api_auth/manage")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/api_auth/manage/write"


def test_api_auth_manage_write(login_gae_admin, web_client: Client) -> None:
    _store_write_auth("writekey", auth_types=[AuthType.EVENT_MATCHES])
    _store_write_auth("readkey", auth_types=[AuthType.READ_API])
    _store_write_auth(
        "expiredwritekey",
        auth_types=[AuthType.EVENT_MATCHES],
        expiration=datetime(2000, 1, 1),
    )
    _store_write_auth(
        "futurewritekey",
        auth_types=[AuthType.EVENT_MATCHES],
        expiration=datetime(2100, 1, 1),
    )

    resp = web_client.get("/admin/api_auth/manage/write")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "writekey description" in content
    assert "futurewritekey description" in content
    assert "readkey description" not in content
    assert "expiredwritekey description" not in content


def test_api_auth_manage_write_include_expired(
    login_gae_admin, web_client: Client
) -> None:
    _store_write_auth("writekey", auth_types=[AuthType.EVENT_MATCHES])
    _store_write_auth(
        "expiredwritekey",
        auth_types=[AuthType.EVENT_MATCHES],
        expiration=datetime(2000, 1, 1),
    )

    resp = web_client.get("/admin/api_auth/manage/write?include_expired=true")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "writekey description" in content
    assert "expiredwritekey description" in content


def test_api_auth_manage_read(login_gae_admin, web_client: Client) -> None:
    _store_write_auth("writekey", auth_types=[AuthType.EVENT_MATCHES])
    _store_write_auth("readkey", auth_types=[AuthType.READ_API])

    resp = web_client.get("/admin/api_auth/manage/read")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "readkey description" in content
    assert "writekey description" not in content


def test_api_auth_manage_admin(
    login_gae_admin, web_client: Client, monkeypatch
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "tbatv-test")
    _store_write_auth("writekey", auth_types=[AuthType.EVENT_MATCHES])
    _store_write_auth("adminkey", auth_types=[AuthType.EVENT_MATCHES], allow_admin=True)
    _store_write_auth(
        "officialkey",
        auth_types=[AuthType.EVENT_MATCHES],
        all_official_events=True,
    )

    resp = web_client.get("/admin/api_auth/manage/admin")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "adminkey description" in content
    assert "officialkey description" in content
    assert "writekey description" not in content


def test_api_auth_manage_unknown_type_is_404(
    login_gae_admin, web_client: Client
) -> None:
    resp = web_client.get("/admin/api_auth/manage/bogus")
    assert resp.status_code == 404


def test_bug_5_api_auth_edit_updates_offseason_webcast_channels(
    login_gae_admin, web_client: Client
) -> None:
    """Bug #5: editing an existing key never saves offseason_webcast_channels.

    Today api_auth_edit_post only passes offseason_webcast_channels when
    creating a new key; the update branch ignores the submitted
    webcast_list_str, so the old channels stay. Correct: the channels become
    the submitted list.
    """
    _store_write_auth(
        "writekey",
        auth_types=[AuthType.EVENT_MATCHES],
        offseason_webcast_channels=["oldchan"],
    )

    resp = web_client.post(
        "/admin/api_auth/edit/writekey",
        data={
            "description": "Updated",
            "allow_edit_matches": "on",
            "webcast_list_str": "newchan1,newchan2",
        },
    )
    assert resp.status_code == 302

    auth = ApiAuthAccess.get_by_id("writekey")
    assert auth is not None
    assert auth.offseason_webcast_channels == ["newchan1", "newchan2"]
