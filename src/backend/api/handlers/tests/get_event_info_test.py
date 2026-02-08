import json
from typing import Dict, List

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.api_trusted_parsers.json_event_info_parser import EventInfoParsed
from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/info"


def setup_event(
    official: bool | None = None,
    playoff_type: PlayoffType | None = None,
    manual_attrs: list[str] | None = None,
) -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
        official=official,
        playoff_type=playoff_type,
        timezone_id="America/New_York",
        manual_attrs=manual_attrs if manual_attrs is not None else [],
    ).put()


def setup_auth(access_types: List[AuthType]) -> None:
    ApiAuthAccess(
        id=AUTH_ID,
        secret=AUTH_SECRET,
        event_list=[ndb.Key(Event, "2014casj")],
        auth_types_enum=access_types,
    ).put()


def get_auth_headers(request_path: str) -> Dict[str, str]:
    return {
        "X-TBA-Auth-Id": AUTH_ID,
        "X-TBA-AUth-Sig": TrustedApiAuthHelper.compute_auth_signature(
            AUTH_SECRET, request_path, request_body=""
        ),
    }


def test_bad_event_key(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.get(
        "/api/trusted/v1/event/asdf/info",
    )
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.get(
        "/api/trusted/v1/event/2015casj/info",
    )
    assert resp.status_code == 404


def test_bad_auth_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.get(
        "/api/trusted/v1/event/2014casj/info",
    )
    assert resp.status_code == 401


def test_no_auth(api_client: Client) -> None:
    setup_event()

    response = api_client.get(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH),
    )
    assert response.status_code == 401


def test_get_event_info(api_client: Client) -> None:
    setup_event(official=True, playoff_type=PlayoffType.CUSTOM)
    setup_auth(access_types=[AuthType.EVENT_INFO])

    response = api_client.get(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH),
    )

    expected: EventInfoParsed = {
        "first_event_code": "casj",
        "playoff_type": PlayoffType.CUSTOM,
        "webcasts": [],
        "remap_teams": {},
        "timezone": "America/New_York",
        "sync_disabled_flags": 0,
    }
    assert response.status_code == 200, response.data
    assert json.loads(response.data) == expected
