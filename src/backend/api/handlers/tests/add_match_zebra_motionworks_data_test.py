import copy
import json
from typing import Dict, List, Optional

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.zebra_motionworks import ZebraMotionWorks

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/zebra_motionworks/add"
REQUEST_DATA = [
    {
        "key": "2014casj_qm1",
        "times": [0.0, 0.5, 1.0, 1.5],
        "alliances": {
            "red": [
                {
                    "team_key": "frc254",
                    "xs": [None, 1.2, 1.3, 1.4],
                    "ys": [None, 0.1, 0.1, 0.1],
                },
                {
                    "team_key": "frc971",
                    "xs": [1.1, 1.2, 1.3, 1.4],
                    "ys": [0.1, 0.1, 0.1, 0.1],
                },
                {
                    "team_key": "frc604",
                    "xs": [1.1, 1.2, 1.3, 1.4],
                    "ys": [0.1, 0.1, 0.1, 0.1],
                },
            ],
            "blue": [
                {
                    "team_key": "frc1",
                    "xs": [None, 1.2, 1.3, 1.4],
                    "ys": [None, 0.1, 0.1, 0.1],
                },
                {
                    "team_key": "frc2",
                    "xs": [1.1, 1.2, 1.3, 1.4],
                    "ys": [0.1, 0.1, 0.1, 0.1],
                },
                {
                    "team_key": "frc3",
                    "xs": [1.1, 1.2, None, 1.4],
                    "ys": [0.1, 0.1, None, 0.1],
                },
            ],
        },
    }
]


def setup_event() -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        event_type_enum=EventType.OFFSEASON,
    ).put()


def setup_match() -> None:
    Match(
        id="2014casj_qm1",
        alliances_json="""{"blue": {"score": -1, "teams": ["frc1", "frc2", "frc3"]}, "red": {"score": -1, "teams": ["frc254", "frc971", "frc604"]}}""",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, "2014casj"),
        year=2014,
        set_number=1,
        match_number=1,
        team_key_names=["frc254", "frc971", "frc604", "frc1", "frc2", "frc3"],
        youtube_videos=["abcdef"],
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
    setup_auth(access_types=[AuthType.ZEBRA_MOTIONWORKS])

    resp = api_client.post(
        "/api/trusted/v1/event/asdf/zebra_motionworks/add", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.ZEBRA_MOTIONWORKS])

    resp = api_client.post(
        "/api/trusted/v1/event/2015casj/zebra_motionworks/add", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_auth_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.post(REQUEST_PATH, data=json.dumps([]))
    assert resp.status_code == 401


def test_no_auth(api_client: Client) -> None:
    setup_event()

    resp = api_client.post(REQUEST_PATH, data=json.dumps({}))
    assert resp.status_code == 401


def test_match_key_mismatch(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.ZEBRA_MOTIONWORKS])

    data = copy.deepcopy(REQUEST_DATA)
    data[0]["key"] = "2015casj_qm1"
    request_body = json.dumps(data)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_nonexistent_match(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.ZEBRA_MOTIONWORKS])

    request_body = json.dumps(REQUEST_DATA)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_teams_mismatch(api_client: Client) -> None:
    setup_event()
    setup_match()
    setup_auth(access_types=[AuthType.ZEBRA_MOTIONWORKS])

    data = copy.deepcopy(REQUEST_DATA)
    data[0]["alliances"]["red"][0]["team_key"] = "frc9000"
    request_body = json.dumps(data)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_add_data(api_client: Client) -> None:
    setup_event()
    setup_match()
    setup_auth(access_types=[AuthType.ZEBRA_MOTIONWORKS])

    request_body = json.dumps(REQUEST_DATA)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200, response.data

    match_data: Optional[ZebraMotionWorks] = ZebraMotionWorks.get_by_id("2014casj_qm1")
    assert match_data is not None
    assert match_data.data == REQUEST_DATA[0]
