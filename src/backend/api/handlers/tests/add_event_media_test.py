import json
from typing import Dict, List, Optional

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import MediaType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.media import Media

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/media/add"


def setup_event(remap_teams: Optional[Dict[str, str]] = None) -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
        remap_teams=remap_teams,
    ).put()


def setup_cmp() -> None:
    Event(
        id="2014cur",
        year=2014,
        event_short="cur",
        event_type_enum=EventType.CMP_DIVISION,
        official=True,
    ).put()


def setup_auth(access_types: List[AuthType], event_key: EventKey = "2014casj") -> None:
    ApiAuthAccess(
        id=AUTH_ID,
        secret=AUTH_SECRET,
        event_list=[ndb.Key(Event, event_key)],
        auth_types_enum=access_types,
    ).put()


def get_auth_headers(request_path: str, request_body) -> Dict[str, str]:
    return {
        "X-TBA-Auth-Id": AUTH_ID,
        "X-TBA-AUth-Sig": TrustedApiAuthHelper.compute_auth_signature(
            AUTH_SECRET, request_path, request_body
        ),
    }


def test_bad_event_key(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.MATCH_VIDEO])

    resp = api_client.post("/api/trusted/v1/event/asdf/media/add", data=json.dumps([]))
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.MATCH_VIDEO])

    resp = api_client.post(
        "/api/trusted/v1/event/2015casj/media/add", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_auth_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.post(REQUEST_PATH, data=json.dumps([]))
    assert resp.status_code == 401


def test_no_auth(api_client: Client) -> None:
    setup_event()

    request_body = json.dumps([])
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 401


def test_bad_json(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.MATCH_VIDEO])

    resp = api_client.post(REQUEST_PATH, data=json.dumps({"foo": "bar"}))
    assert resp.status_code == 401


def test_add_media(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.MATCH_VIDEO])

    request_body = json.dumps(["abc123"])
    resp = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert resp.status_code == 200

    medias: List[Media] = Media.query(
        Media.references == ndb.Key(Event, "2014casj")
    ).fetch()
    assert len(medias) == 1

    media = medias[0]
    assert media.foreign_key == "abc123"
    assert media.year == 2014
    assert media.media_type_enum == MediaType.YOUTUBE_VIDEO


def test_add_media_cmp_remap(api_client: Client) -> None:
    setup_cmp()
    setup_auth(access_types=[AuthType.MATCH_VIDEO], event_key="2014cur")

    path = "/api/trusted/v1/event/2014curie/media/add"
    request_body = json.dumps(["abc123"])
    resp = api_client.post(
        path,
        headers=get_auth_headers(path, request_body),
        data=request_body,
    )
    assert resp.status_code == 200

    medias: List[Media] = Media.query(
        Media.references == ndb.Key(Event, "2014cur")
    ).fetch()
    assert len(medias) == 1

    media = medias[0]
    assert media.foreign_key == "abc123"
    assert media.year == 2014
    assert media.media_type_enum == MediaType.YOUTUBE_VIDEO
