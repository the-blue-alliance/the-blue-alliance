import json
from typing import Dict, List

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.match import Match


AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/matches/delete"


def setup_event() -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
    ).put()


def setup_matches(n: int = 5) -> None:
    ndb.put_multi(
        [
            Match(
                id=Match.render_key_name("2014casj", CompLevel.QM, 1, i),
                comp_level=CompLevel.QM,
                set_number=1,
                match_number=i,
                event=ndb.Key(Event, "2014casj"),
                year=2014,
                alliances_json="",
            )
            for i in range(1, n + 1)
        ]
    )


def setup_auth(access_types: List[AuthType]) -> None:
    ApiAuthAccess(
        id=AUTH_ID,
        secret=AUTH_SECRET,
        event_list=[ndb.Key(Event, "2014casj")],
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
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.post(
        "/api/trusted/v1/event/asdf/matches/delete", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.post(
        "/api/trusted/v1/event/2015casj/matches/delete", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_auth_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.post(
        "/api/trusted/v1/event/2014casj/matches/delete", data=json.dumps([])
    )
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


def test_delete_match_bad_json(api_client: Client) -> None:
    setup_event()
    setup_matches(n=3)
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    keys_to_delete = {
        "qm1": "delete",
        "qm2": "me",
    }
    request_body = json.dumps(keys_to_delete)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400

    db_matches = Match.query(Match.event == ndb.Key(Event, "2014casj")).fetch(
        keys_only=True
    )
    assert len(db_matches) == 3


def test_delete_match(api_client: Client) -> None:
    setup_event()
    setup_matches(n=5)
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    keys_to_delete = ["qm1", "qm2"]
    request_body = json.dumps(keys_to_delete)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    db_matches = Match.query(Match.event == ndb.Key(Event, "2014casj")).fetch(
        keys_only=True
    )
    assert len(db_matches) == 3
    assert db_matches == [
        ndb.Key(Match, "2014casj_qm3"),
        ndb.Key(Match, "2014casj_qm4"),
        ndb.Key(Match, "2014casj_qm5"),
    ]


def test_delete_match_skips_invalid(api_client: Client) -> None:
    setup_event()
    setup_matches(n=3)
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    keys_to_delete = ["qm1", "q2m4"]
    request_body = json.dumps(keys_to_delete)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    db_matches = Match.query(Match.event == ndb.Key(Event, "2014casj")).fetch(
        keys_only=True
    )
    assert len(db_matches) == 2
    assert db_matches == [
        ndb.Key(Match, "2014casj_qm2"),
        ndb.Key(Match, "2014casj_qm3"),
    ]
