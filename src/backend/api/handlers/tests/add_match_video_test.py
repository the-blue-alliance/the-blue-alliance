import json
from typing import Dict, List

from google.cloud import ndb
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
REQUEST_PATH = "/api/trusted/v1/event/2014casj/match_videos/add"


def setup_event() -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
    ).put()


def setup_matches() -> None:
    Match(
        id="2014casj_qm1",
        alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, "2014casj"),
        year=2014,
        set_number=1,
        match_number=1,
        team_key_names=["frc69", "frc571", "frc176", "frc3464", "frc20", "frc1073"],
        youtube_videos=["abcdef"],
    ).put()
    Match(
        id="2014casj_sf1m1",
        alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level=CompLevel.SF,
        event=ndb.Key(Event, "2014casj"),
        year=2014,
        set_number=1,
        match_number=1,
        team_key_names=["frc69", "frc571", "frc176", "frc3464", "frc20", "frc1073"],
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


def test_no_auth(ndb_client: ndb.Client, api_client: Client) -> None:
    with ndb_client.context():
        setup_event()

    resp = api_client.post(REQUEST_PATH, data=json.dumps({}))
    assert resp.status_code == 401


def test_set_video(ndb_client: ndb.Client, api_client: Client) -> None:
    with ndb_client.context():
        setup_event()
        setup_auth(access_types=[AuthType.MATCH_VIDEO])
        setup_matches()

    request_body = json.dumps({"qm1": "aFZy8iibMD0", "sf1m1": "RpSgUrsghv4"})

    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    with ndb_client.context():
        assert set(Match.get_by_id("2014casj_qm1").youtube_videos) == {
            "abcdef",
            "aFZy8iibMD0",
        }
        assert set(Match.get_by_id("2014casj_sf1m1").youtube_videos) == {"RpSgUrsghv4"}


def test_bad_match_id(ndb_client: ndb.Client, api_client: Client) -> None:
    with ndb_client.context():
        setup_event()
        setup_auth(access_types=[AuthType.MATCH_VIDEO])
        setup_matches()

    request_body = json.dumps({"qm1": "aFZy8iibMD0", "qm2": "abc123"})

    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 404

    # make sure the valid match is unchnaged
    with ndb_client.context():
        assert set(Match.get_by_id("2014casj_qm1").youtube_videos) == {"abcdef"}


def test_malformed_match_id(ndb_client: ndb.Client, api_client: Client) -> None:
    with ndb_client.context():
        setup_event()
        setup_auth(access_types=[AuthType.MATCH_VIDEO])
        setup_matches()

    request_body = json.dumps({"qm1": "aFZy8iibMD0", "zzz": "abc123"})

    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400, response.data
    assert response.json["Error"] == "Invalid match IDs provided: ['zzz']"

    # make sure the valid match is unchnaged
    with ndb_client.context():
        assert set(Match.get_by_id("2014casj_qm1").youtube_videos) == {"abcdef"}
