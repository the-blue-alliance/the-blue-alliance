import datetime
import json
from typing import Any, Dict, List, Optional

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.match import Match

AUTH_ID = "tEsT_id_0"
AUTH_SECRET = "321tEsTsEcReT"
REQUEST_PATH = "/api/trusted/v1/event/2014casj/matches/update"


def setup_event(
    remap_teams: Optional[Dict[str, str]] = None,
    timezone_id: Optional[str] = "America/Los_Angeles",
) -> None:
    Event(
        id="2014casj",
        year=2014,
        event_short="casj",
        timezone_id=timezone_id,
        start_date=datetime.datetime(2014, 4, 1),
        end_date=datetime.datetime(2014, 4, 3),
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
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.post(
        "/api/trusted/v1/event/asdf/matches/update", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_event(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    resp = api_client.post(
        "/api/trusted/v1/event/2015casj/matches/update", data=json.dumps([])
    )
    assert resp.status_code == 404


def test_bad_auth_type(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_INFO])

    resp = api_client.post(
        "/api/trusted/v1/event/2014casj/matches/update", data=json.dumps([])
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


@pytest.mark.parametrize(
    "request_data",
    [
        "",
        "not_json",
        ["is_not_dict"],
        [{}],
        [{"comp_level": "meow"}],
        [{"comp_level": "qf", "set_number": "abc"}],
        [{"comp_level": "qf", "set_number": 1, "match_number": "abc"}],
        [{"comp_level": "qf", "set_number": 1, "match_number": 1, "alliances": "abc"}],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {"green": {}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {"red": {}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {"red": {"teams": []}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {"red": {"score": 0, "teams": ["bad_team"]}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {"red": {"teams": [], "score": "abc"}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {
                    "red": {"teams": [], "score": 0, "surrogates": ["bad_team"]}
                },
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {"red": {"teams": [], "score": 0, "surrogates": ["frc1"]}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {"red": {"teams": [], "score": 0, "dqs": ["bad_team"]}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {"red": {"teams": [], "score": 0, "dqs": ["frc1"]}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {},
                "score_breakdown": "blah",
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {},
                "score_breakdown": {"green": {}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {},
                "score_breakdown": {"red": {"bad_key": 0}},
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {},
                "time_utc": "foo",
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {},
                "actual_start_time_utc": "foo",
            }
        ],
        [
            {
                "comp_level": "qf",
                "set_number": 1,
                "match_number": 1,
                "alliances": {},
                "post_results_time_utc": "foo",
            }
        ],
    ],
)
def test_bad_json(api_client: Client, request_data: Any) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    request_body = json.dumps(request_data)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 400


def test_matches_update(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    # add one match
    matches = [
        {
            "comp_level": "qm",
            "set_number": 1,
            "match_number": 1,
            "alliances": {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 25},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 26},
            },
            "time_string": "9:00 AM",
            "time_utc": "2014-08-31T16:00:00",
        }
    ]
    request_body = json.dumps(matches)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event = none_throws(Event.get_by_id("2014casj"))
    db_matches = Match.query(Match.event == event.key).fetch()
    assert len(db_matches) == 1
    assert "2014casj_qm1" in [m.key.id() for m in db_matches]

    # add another match
    matches = [
        {
            "comp_level": "f",
            "set_number": 1,
            "match_number": 1,
            "alliances": {
                "red": {
                    "teams": ["frc1", "frc2", "frc3"],
                    "score": 250,
                    "surrogates": ["frc1"],
                    "dqs": ["frc2"],
                },
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 260},
            },
            "score_breakdown": {
                "red": {
                    "auto": 20,
                    "assist": 40,
                    "truss+catch": 20,
                    "teleop_goal+foul": 20,
                },
                "blue": {
                    "auto": 40,
                    "assist": 60,
                    "truss+catch": 10,
                    "teleop_goal+foul": 40,
                },
            },
            "time_string": "10:00 AM",
            "time_utc": "2014-08-31T17:00:00",
            "actual_start_time_utc": "2014-08-31T17:01:00",
            "post_results_time_utc": "2014-08-31T17:05:00",
        }
    ]
    request_body = json.dumps(matches)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    db_matches = Match.query(Match.event == event.key).fetch()
    assert len(db_matches) == 2
    assert "2014casj_qm1" in [m.key.id() for m in db_matches]
    assert "2014casj_f1m1" in [m.key.id() for m in db_matches]

    # verify match data
    match = Match.get_by_id("2014casj_f1m1")
    assert match is not None
    assert match.time == datetime.datetime(2014, 8, 31, 17, 0)
    assert match.time_string == "10:00 AM"
    assert match.actual_time == datetime.datetime(2014, 8, 31, 17, 1)
    assert match.post_result_time == datetime.datetime(2014, 8, 31, 17, 5)
    assert match.alliances[AllianceColor.RED]["teams"] == ["frc1", "frc2", "frc3"]
    assert match.alliances[AllianceColor.RED]["score"] == 250
    assert match.alliances[AllianceColor.RED]["surrogates"] == ["frc1"]
    assert match.alliances[AllianceColor.RED]["dqs"] == ["frc1", "frc2", "frc3"]

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["truss+catch"] == 20

    assert match.alliances[AllianceColor.BLUE]["teams"] == ["frc4", "frc5", "frc6"]
    assert match.alliances[AllianceColor.BLUE]["score"] == 260
    assert match.alliances[AllianceColor.BLUE]["surrogates"] == []
    assert match.alliances[AllianceColor.BLUE]["dqs"] == []


def test_calculate_match_time(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    matches = [
        # day 1
        {
            "comp_level": "qm",
            "set_number": 1,
            "match_number": 1,
            "alliances": {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 25},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 26},
            },
            "time_string": "9:00 AM",
        },
        {
            "comp_level": "qm",
            "set_number": 1,
            "match_number": 2,
            "alliances": {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 25},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 26},
            },
            "time_string": "12:00 PM",
        },
        {
            "comp_level": "qm",
            "set_number": 1,
            "match_number": 3,
            "alliances": {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 25},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 26},
            },
            "time_string": "4:00 PM",
        },
        # day 2
        {
            "comp_level": "qm",
            "set_number": 1,
            "match_number": 4,
            "alliances": {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 25},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 26},
            },
            "time_string": "9:00 AM",
        },
    ]
    request_body = json.dumps(matches)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event = none_throws(Event.get_by_id("2014casj"))
    db_matches = Match.query(Match.event == event.key).fetch()
    assert len(db_matches) == 4

    # verify match data
    match = Match.get_by_id("2014casj_qm1")
    assert match is not None
    assert match.time == datetime.datetime(2014, 4, 2, 16, 0)

    match = Match.get_by_id("2014casj_qm2")
    assert match is not None
    assert match.time == datetime.datetime(2014, 4, 2, 19, 0)

    match = Match.get_by_id("2014casj_qm3")
    assert match is not None
    assert match.time == datetime.datetime(2014, 4, 2, 23, 0)

    match = Match.get_by_id("2014casj_qm4")
    assert match is not None
    assert match.time == datetime.datetime(2014, 4, 3, 16, 0)


def test_calculate_match_time_bad_time(api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    matches = [
        {
            "comp_level": "qm",
            "set_number": 1,
            "match_number": 1,
            "alliances": {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 25},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 26},
            },
            "time_string": "blahhh",
        },
    ]
    request_body = json.dumps(matches)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event = none_throws(Event.get_by_id("2014casj"))
    db_matches = Match.query(Match.event == event.key).fetch()
    assert len(db_matches) == 1

    # verify match data - we should have skipped over the time
    match = Match.get_by_id("2014casj_qm1")
    assert match is not None
    assert match.time is None


def test_calculate_match_time_skip_no_timezone(api_client: Client) -> None:
    setup_event(timezone_id=None)
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    matches = [
        {
            "comp_level": "qm",
            "set_number": 1,
            "match_number": 1,
            "alliances": {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 25},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 26},
            },
            "time_string": "9:00 AM",
        },
    ]
    request_body = json.dumps(matches)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event = none_throws(Event.get_by_id("2014casj"))
    db_matches = Match.query(Match.event == event.key).fetch()
    assert len(db_matches) == 1

    # verify match data - we should have skipped over the time
    match = Match.get_by_id("2014casj_qm1")
    assert match is not None
    assert match.time is None


def test_add_match_remapteams(api_client: Client) -> None:
    setup_event(remap_teams={"frc6": "frc254B"})
    setup_auth(access_types=[AuthType.EVENT_MATCHES])

    # add one match
    matches = [
        # day 1
        {
            "comp_level": "qm",
            "set_number": 1,
            "match_number": 1,
            "alliances": {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 25},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 26},
            },
            "time_string": "9:00 AM",
        },
    ]
    request_body = json.dumps(matches)
    response = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, request_body),
        data=request_body,
    )
    assert response.status_code == 200

    event = none_throws(Event.get_by_id("2014casj"))
    db_matches = Match.query(Match.event == event.key).fetch()
    assert len(db_matches) == 1

    # verify match data
    match = Match.get_by_id("2014casj_qm1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["teams"] == ["frc1", "frc2", "frc3"]
    assert match.alliances[AllianceColor.BLUE]["teams"] == ["frc4", "frc5", "frc254B"]
    assert match.team_key_names == ["frc1", "frc2", "frc3", "frc4", "frc5", "frc254B"]
