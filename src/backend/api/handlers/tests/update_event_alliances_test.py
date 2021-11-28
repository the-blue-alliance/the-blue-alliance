import json
from typing import Dict, List, Optional

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/alliance_selections/update"


def setup_event(remap_teams: Optional[Dict[str, str]] = None) -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
        remap_teams=remap_teams,
    ).put()


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
    setup_auth(access_types=[AuthType.EVENT_ALLIANCES])

    resp = api_client.post(
        "/api/trusted/v1/event/asdf/alliance_selections/update", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_ALLIANCES])

    resp = api_client.post(
        "/api/trusted/v1/event/2015casj/alliance_selections/update", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_auth_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.post(
        "/api/trusted/v1/event/2014casj/alliance_selections/update", data=json.dumps([])
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


def test_bad_team_key(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_ALLIANCES])

    alliances = [
        ["frc971", "frc254", "frc1662"],
        ["254", "971", "abc"],
    ]
    request_body = json.dumps(alliances)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400, response.data


def test_alliance_selections_update(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_ALLIANCES])

    alliances = [
        ["frc971", "frc254", "frc1662"],
        ["frc1678", "frc368", "frc4171"],
        ["frc2035", "frc192", "frc4990"],
        ["frc1323", "frc846", "frc2135"],
        ["frc2144", "frc1388", "frc668"],
        ["frc1280", "frc604", "frc100"],
        ["frc114", "frc852", "frc841"],
        ["frc2473", "frc3256", "frc1868"],
    ]
    request_body = json.dumps(alliances)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200, response.data

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    event_alliances = event.alliance_selections
    assert event_alliances is not None
    assert len(event_alliances) == 8
    for i, selection in enumerate(event_alliances):
        assert alliances[i] == selection["picks"]


def test_empty_alliance_selections_update(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_ALLIANCES])

    alliances = [
        ["frc971", "frc254", "frc1662"],
        ["frc1678", "frc368", "frc4171"],
        ["frc2035", "frc192", "frc4990"],
        ["frc1323", "frc846", "frc2135"],
        [],
        [],
        [],
        [],
    ]
    request_body = json.dumps(alliances)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200, response.data

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    event_alliances = event.alliance_selections
    assert event_alliances is not None
    assert len(event_alliances) == 4
    for i, selection in enumerate(event_alliances):
        assert alliances[i] == selection["picks"]


def test_alliance_selections_remapteams(api_client: Client) -> None:
    setup_event(remap_teams={"frc9000": "frc254B"})
    setup_auth(access_types=[AuthType.EVENT_ALLIANCES])

    alliances = [
        ["frc971", "frc254", "frc9000"],
    ]
    request_body = json.dumps(alliances)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200, response.data

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    event_alliances = event.alliance_selections
    assert event_alliances is not None
    assert len(event_alliances) == 1
    assert event_alliances[0]["picks"] == ["frc971", "frc254", "frc254B"]
