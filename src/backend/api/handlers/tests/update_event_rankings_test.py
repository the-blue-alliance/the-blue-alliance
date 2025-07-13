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
REQUEST_PATH = "/api/trusted/v1/event/2014casj/rankings/update"


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
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    resp = api_client.post(
        "/api/trusted/v1/event/asdf/rankings/update", data=json.dumps({})
    )
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    resp = api_client.post(
        "/api/trusted/v1/event/2015casj/rankings/update", data=json.dumps({})
    )
    assert resp.status_code == 404


def test_bad_auth_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.post(
        "/api/trusted/v1/event/2014casj/rankings/update", data=json.dumps({})
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


def test_bad_json(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    request_body = "abcd"
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_bad_payload_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    request_body = json.dumps([])
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_bad_breakdowns(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    request_body = json.dumps({"breakdowns": "foo", "rankings": []})
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_bad_rankings(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    request_body = json.dumps({"breakdowns": [], "rankings": "foo"})
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_bad_ranking_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    request_body = json.dumps({"breakdowns": [], "rankings": ["foo"]})
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_bad_team_key(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    request_body = json.dumps({"breakdowns": [], "rankings": [{"team_key": "foo"}]})
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_bad_rank(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    request_body = json.dumps(
        {"breakdowns": [], "rankings": [{"team_key": "frc254", "rank": "foo"}]}
    )
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_rankings_update(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    rankings = {
        "breakdowns": ["QS", "Auton", "Teleop", "T&C"],
        "rankings": [
            {
                "team_key": "frc254",
                "rank": 1,
                "played": 10,
                "dqs": 0,
                "QS": 20,
                "Auton": 500,
                "Teleop": 500,
                "T&C": 200,
            },
            {
                "team_key": "frc971",
                "rank": 2,
                "played": 10,
                "dqs": 0,
                "QS": 20,
                "Auton": 500,
                "Teleop": 500,
                "T&C": 200,
            },
        ],
    }
    request_body = json.dumps(rankings)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None

    event_rankings = event.rankings
    assert event_rankings is not None
    assert event_rankings[0] == {
        "rank": 1,
        "team_key": "frc254",
        "record": {"wins": 0, "losses": 0, "ties": 0},
        "qual_average": None,
        "matches_played": 10,
        "dq": 0,
        "sort_orders": [20.0, 500.0, 500.0, 200.0],
    }


def test_rankings_wlt_update(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    rankings = {
        "breakdowns": ["QS", "Auton", "Teleop", "T&C", "wins", "losses", "ties"],
        "rankings": [
            {
                "team_key": "frc254",
                "rank": 1,
                "wins": 10,
                "losses": 0,
                "ties": 0,
                "played": 10,
                "dqs": 0,
                "QS": 20,
                "Auton": 500,
                "Teleop": 500,
                "T&C": 200,
            },
            {
                "team_key": "frc971",
                "rank": 2,
                "wins": 10,
                "losses": 0,
                "ties": 0,
                "played": 10,
                "dqs": 0,
                "QS": 20,
                "Auton": 500,
                "Teleop": 500,
                "T&C": 200,
            },
        ],
    }
    request_body = json.dumps(rankings)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None

    event_rankings = event.rankings
    assert event_rankings is not None
    assert event_rankings[0] == {
        "rank": 1,
        "team_key": "frc254",
        "record": {"wins": 10, "losses": 0, "ties": 0},
        "qual_average": None,
        "matches_played": 10,
        "dq": 0,
        "sort_orders": [20.0, 500.0, 500.0, 200.0],
    }


def test_rankings_update_remapteams(api_client: Client) -> None:
    setup_event(remap_teams={"frc9000": "frc254B"})
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    rankings = {
        "breakdowns": ["QS", "Auton", "Teleop", "T&C"],
        "rankings": [
            {
                "team_key": "frc254",
                "rank": 1,
                "played": 10,
                "dqs": 0,
                "QS": 20,
                "Auton": 500,
                "Teleop": 500,
                "T&C": 200,
            },
            {
                "team_key": "frc9000",
                "rank": 2,
                "played": 10,
                "dqs": 0,
                "QS": 20,
                "Auton": 500,
                "Teleop": 500,
                "T&C": 200,
            },
        ],
    }
    request_body = json.dumps(rankings)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None

    event_rankings = event.rankings
    assert event_rankings is not None
    assert event_rankings[1] == {
        "rank": 2,
        "team_key": "frc254B",
        "record": {"wins": 0, "losses": 0, "ties": 0},
        "qual_average": None,
        "matches_played": 10,
        "dq": 0,
        "sort_orders": [20.0, 500.0, 500.0, 200.0],
    }


def test_rankings_generic_update(api_client: Client) -> None:
    """
    This mirrors posting results as the "generic" format, as stored
    by FMS, to ensure that we properly remap the values back onto their
    "real" keys server-side
    """
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_RANKINGS])

    rankings = {
        "breakdowns": ["sort1", "sort2", "sort3", "sort4", "sort5", "sort6"],
        "rankings": [
            {
                "team_key": "frc254",
                "rank": 1,
                "wins": 10,
                "losses": 0,
                "ties": 0,
                "played": 10,
                "dqs": 0,
                "sort1": 1,
                "sort2": 2,
                "sort3": 3,
                "sort4": 4,
                "sort5": 5,
                "sort6": 6,
            },
            {
                "team_key": "frc971",
                "rank": 2,
                "wins": 10,
                "losses": 0,
                "ties": 0,
                "played": 10,
                "dqs": 0,
                "sort1": 11,
                "sort2": 12,
                "sort3": 13,
                "sort4": 14,
                "sort5": 15,
                "sort6": 16,
            },
        ],
    }
    request_body = json.dumps(rankings)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event: Optional[Event] = Event.get_by_id("2014casj")
    assert event is not None

    event_rankings = event.rankings
    assert event_rankings is not None
    assert event_rankings[0] == {
        "rank": 1,
        "team_key": "frc254",
        "record": {"wins": 10, "losses": 0, "ties": 0},
        "qual_average": None,
        "matches_played": 10,
        "dq": 0,
        "sort_orders": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    }
