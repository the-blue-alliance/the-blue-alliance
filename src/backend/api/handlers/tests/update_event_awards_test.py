import json
from typing import Dict, List, Optional

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/awards/update"


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
    setup_auth(access_types=[AuthType.EVENT_AWARDS])

    resp = api_client.post(
        "/api/trusted/v1/event/asdf/awards/update", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_AWARDS])

    resp = api_client.post(
        "/api/trusted/v1/event/2015casj/awards/update", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_auth_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.post(
        "/api/trusted/v1/event/2014casj/awards/update", data=json.dumps([])
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


def test_no_award_name(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_AWARDS])

    awards = [{"team_key": "frc254"}]  # missing name_str
    request_body = json.dumps(awards)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_bad_team_key(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_AWARDS])

    awards = [{"name_str": "Winner", "team_key": "abc"}]
    request_body = json.dumps(awards)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_bad_award_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_AWARDS])

    awards = [{"name_str": "blargh", "team_key": "frc254"}]
    request_body = json.dumps(awards)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_no_winner(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_AWARDS])

    awards = [{"name_str": "Winner"}]
    request_body = json.dumps(awards)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_awards_update(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_AWARDS])

    awards = [
        {"name_str": "Winner", "team_key": "frc254"},
        {"name_str": "Winner", "team_key": "frc604"},
        {"name_str": "Volunteer Blahblah", "team_key": "frc1", "awardee": "Bob Bobby"},
    ]
    request_body = json.dumps(awards)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    db_awards = Award.query(Award.event == event.key).fetch(None)
    assert len(db_awards) == 2
    assert "2014casj_1" in [a.key.id() for a in db_awards]
    assert "2014casj_5" in [a.key.id() for a in db_awards]


def test_awards_update_clears_old(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_AWARDS])
    Award(
        id=Award.render_key_name("2014casj", AwardType.CHAIRMANS),
        name_str="Chairmans",
        award_type_enum=AwardType.CHAIRMANS,
        year=2014,
        event=ndb.Key(Event, "2014casj"),
        event_type_enum=EventType.REGIONAL,
        team_list=[ndb.Key(Team, "frc148")],
    )

    awards = [
        {"name_str": "Winner", "team_key": "frc254"},
        {"name_str": "Winner", "team_key": "frc604"},
    ]
    request_body = json.dumps(awards)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    db_awards = Award.query(Award.event == event.key).fetch(None)
    assert len(db_awards) == 1
    assert "2014casj_1" in [a.key.id() for a in db_awards]


def test_awards_update_remapteams(api_client: Client) -> None:
    setup_event(remap_teams={"frc9000": "frc254B"})
    setup_auth(access_types=[AuthType.EVENT_AWARDS])

    awards = [
        {"name_str": "Winner", "team_key": "frc254"},
        {"name_str": "Winner", "team_key": "frc9000"},
    ]
    request_body = json.dumps(awards)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None
    db_awards: List[Award] = Award.query(Award.event == event.key).fetch()
    assert len(db_awards) == 1
    assert "2014casj_1" in [a.key.id() for a in db_awards]

    award = db_awards[0]
    assert [ndb.Key(Team, "frc254"), ndb.Key(Team, "frc254B")] == award.team_list
