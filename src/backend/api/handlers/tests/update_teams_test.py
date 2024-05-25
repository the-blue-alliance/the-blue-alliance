import json
from typing import Dict, List

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import TeamKey
from backend.common.models.team import Team

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/team_list/update"


def setup_event() -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
    ).put()


def setup_eventteams(team_keys: List[TeamKey]) -> None:
    eventteams = [
        EventTeam(
            id=f"2014casj_{team_key}",
            year=2014,
            event=ndb.Key(Event, "2014casj"),
            team=ndb.Key(Team, team_key),
        )
        for team_key in team_keys
    ]
    ndb.put_multi(eventteams)


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


def setup_teams() -> None:
    # Insert teams into db, otherwise they won't get added (see 072058b)
    Team(id="frc254", team_number=254).put()
    Team(id="frc971", team_number=971).put()
    Team(id="frc604", team_number=604).put()
    Team(id="frc100", team_number=100).put()


def test_no_auth(ndb_stub, api_client: Client) -> None:
    setup_event()
    resp = api_client.post(REQUEST_PATH, data=json.dumps([]))
    assert resp.status_code == 401


def test_set_teams(ndb_stub, api_client: Client, taskqueue_stub) -> None:
    setup_event()
    setup_teams()
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    request_body = json.dumps(["frc254", "frc971", "frc604"])

    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200, response.data
    assert "Success" in response.json

    db_eventteams = EventTeam.query(
        EventTeam.event == ndb.Key(Event, "2014casj")
    ).fetch(keys_only=True)

    assert db_eventteams == [
        ndb.Key(EventTeam, "2014casj_frc254"),
        ndb.Key(EventTeam, "2014casj_frc604"),
        ndb.Key(EventTeam, "2014casj_frc971"),
    ]


def test_remove_teams(ndb_stub, api_client: Client, taskqueue_stub) -> None:
    setup_event()
    setup_teams()
    setup_eventteams(["frc254", "frc971", "frc604"])
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    request_body = json.dumps([])

    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200, response.data
    assert "Success" in response.json

    db_eventteams = EventTeam.query(
        EventTeam.event == ndb.Key(Event, "2014casj")
    ).fetch(keys_only=True)

    assert db_eventteams == []


def test_update_teams(ndb_stub, api_client: Client, taskqueue_stub) -> None:
    setup_event()
    setup_teams()
    setup_eventteams(["frc254", "frc971", "frc604"])
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    request_body = json.dumps(["frc254", "frc100"])

    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200, response.data
    assert "Success" in response.json

    db_eventteams = EventTeam.query(
        EventTeam.event == ndb.Key(Event, "2014casj")
    ).fetch(keys_only=True)

    assert db_eventteams == [
        ndb.Key(EventTeam, "2014casj_frc100"),
        ndb.Key(EventTeam, "2014casj_frc254"),
    ]


def test_unknown_teams_skipped(ndb_stub, api_client: Client, taskqueue_stub) -> None:
    setup_event()
    setup_teams()
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    request_body = json.dumps(["frc254", "frc971", "frc148"])

    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200, response.data
    assert "Success" in response.json

    db_eventteams = EventTeam.query(
        EventTeam.event == ndb.Key(Event, "2014casj")
    ).fetch(keys_only=True)

    assert db_eventteams == [
        ndb.Key(EventTeam, "2014casj_frc254"),
        ndb.Key(EventTeam, "2014casj_frc971"),
    ]


def test_bad_team_key(ndb_stub, api_client: Client) -> None:
    setup_event()
    setup_teams()
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    request_body = json.dumps(["frc254", "asdf"])

    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400, response.data
    assert response.json["Error"] == "Invalid team keys provided: ['asdf']"

    db_eventteams = EventTeam.query(
        EventTeam.event == ndb.Key(Event, "2014casj")
    ).fetch(keys_only=True)

    assert db_eventteams == []


def test_bad_body_format(ndb_stub, api_client: Client) -> None:
    setup_event()
    setup_teams()
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    request_body = "[254]"

    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400, response.data
    assert response.json["Error"].startswith("`254` is not a <class 'str'>")
