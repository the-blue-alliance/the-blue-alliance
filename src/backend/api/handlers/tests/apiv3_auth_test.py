import json
from unittest.mock import patch

import pytest
from flask import g
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common import auth
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team


def test_not_authenticated(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    with api_client.application.test_request_context():  # pyre-ignore[16]
        assert g.get("auth_owner_id", None) is None

        resp = api_client.get("/api/v3/team/frc254")

        assert g.get("auth_owner_id", None) is None

    assert resp.status_code == 401
    assert "required" in resp.json["Error"]


def test_bad_auth(ndb_stub, api_client: Client) -> None:
    account = Account()
    ApiAuthAccess(
        id="test_auth_key", auth_types_enum=[AuthType.READ_API], owner=account.key
    ).put()
    Team(id="frc254", team_number=254).put()

    with api_client.application.test_request_context():  # pyre-ignore[16]
        assert g.get("auth_owner_id", None) is None

        resp = api_client.get(
            "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "bad_auth_key"}
        )

        assert g.get("auth_owner_id", None) is None

    assert resp.status_code == 401
    assert "invalid" in resp.json["Error"]


@pytest.mark.parametrize("account", [None, Account()])
def test_authenticated_header(ndb_stub, api_client: Client, account: Account) -> None:
    if account:
        account.put()
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
        owner=account.key if account else None,
    ).put()
    Team(id="frc254", team_number=254).put()

    with api_client.application.test_request_context():  # pyre-ignore[16]
        assert g.get("auth_owner_id", None) is None

        resp = api_client.get(
            "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
        )

        if account:
            assert g.auth_owner_id == account.key.id()

    assert resp.status_code == 200


@pytest.mark.parametrize("account", [None, Account()])
def test_authenticated_urlparam(ndb_stub, api_client: Client, account: Account) -> None:
    if account:
        account.put()
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
        owner=account.key if account else None,
    ).put()
    Team(id="frc254", team_number=254).put()

    with api_client.application.test_request_context():  # pyre-ignore[16]
        assert g.get("auth_owner_id", None) is None

        resp = api_client.get("/api/v3/team/frc254?X-TBA-Auth-Key=test_auth_key")

        if account:
            assert g.auth_owner_id == account.key.id()

    assert resp.status_code == 200


def test_authenticated_user(ndb_stub, api_client: Client) -> None:
    email = "zach@thebluealliance.com"
    account = Account(email=email)

    Team(id="frc254", team_number=254).put()
    account.put()

    with api_client.application.test_request_context():  # pyre-ignore[16]
        assert g.get("auth_owner_id", None) is None

        with patch.object(auth, "_decoded_claims", return_value={"email": email}):
            resp = api_client.get("/api/v3/team/frc254")

        assert g.auth_owner_id == account.key.id()

    assert resp.status_code == 200


def test_team_key_valid(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # Test model return
    resp = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200

    # Test different model return
    resp = api_client.get(
        "/api/v3/team/frc254/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200


def test_team_key_invalid(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # Test model return
    resp = api_client.get(
        "/api/v3/team/254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "254 is not a valid team key"

    # Test different model return
    resp = api_client.get(
        "/api/v3/team/254/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "254 is not a valid team key"


def test_team_key_does_not_exist(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # Test model return
    resp = api_client.get(
        "/api/v3/team/frc604", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "team key: frc604 does not exist"

    # Test different model return
    resp = api_client.get(
        "/api/v3/team/frc604/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "team key: frc604 does not exist"


def test_event_key_valid(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    # Test model return
    resp = api_client.get(
        "/api/v3/event/2019casj", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200

    # Test different model return
    resp = api_client.get(
        "/api/v3/event/2019casj/teams", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200


def test_event_key_invalid(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    # Test model return
    resp = api_client.get(
        "/api/v3/event/casj", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "casj is not a valid event key"

    # Test different model return
    resp = api_client.get(
        "/api/v3/event/casj/teams", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "casj is not a valid event key"


def test_event_key_does_not_exist(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    # Test model return
    resp = api_client.get(
        "/api/v3/event/2019casf", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "event key: 2019casf does not exist"

    # Test different model return
    resp = api_client.get(
        "/api/v3/event/2019casf/teams", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "event key: 2019casf does not exist"


def test_match_key_valid(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Match(
        id="2020casj_qm1",
        year=2020,
        event=ndb.Key("Event", "2020casj"),
        comp_level="qm",
        match_number=1,
        set_number=1,
        alliances_json=json.dumps(
            {
                "red": {"score": 0, "teams": []},
                "blue": {"score": 0, "teams": []},
            }
        ),
    ).put()
    resp = api_client.get(
        "/api/v3/match/2020casj_qm1", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200


def test_match_key_invalid(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Match(
        id="2020casj_qm1",
        year=2020,
        event=ndb.Key("Event", "2020casj"),
        comp_level="qm",
        match_number=1,
        set_number=1,
        alliances_json=json.dumps(
            {
                "red": {"score": 0, "teams": []},
                "blue": {"score": 0, "teams": []},
            }
        ),
    ).put()
    resp = api_client.get(
        "/api/v3/match/2020casj_qm", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "2020casj_qm is not a valid match key"


def test_match_key_does_not_exist(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Match(
        id="2020casj_qm1",
        year=2020,
        event=ndb.Key("Event", "2020casj"),
        comp_level="qm",
        match_number=1,
        set_number=1,
        alliances_json=json.dumps(
            {
                "red": {"score": 0, "teams": []},
                "blue": {"score": 0, "teams": []},
            }
        ),
    ).put()
    resp = api_client.get(
        "/api/v3/match/2020casj_qm2", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "match key: 2020casj_qm2 does not exist"


def test_district_key_valid(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    District(
        id="2020mar",
        year=2020,
        abbreviation="mar",
    ).put()

    # Test model return
    resp = api_client.get(
        "/api/v3/district/2020mar/rankings", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    # We allow both old/new keys
    resp = api_client.get(
        "/api/v3/district/2020fma/rankings", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200

    # Test different model return
    resp = api_client.get(
        "/api/v3/district/2020mar/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    # We allow both old/new keys
    resp = api_client.get(
        "/api/v3/district/2020fma/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200


def test_district_key_invalid(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    District(
        id="2020mar",
        year=2020,
        abbreviation="mar",
    ).put()

    # Test model return
    resp = api_client.get(
        "/api/v3/district/mar/rankings", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "mar is not a valid district key"

    # Test different model return
    resp = api_client.get(
        "/api/v3/district/mar/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "mar is not a valid district key"


def test_district_key_does_not_exist(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    District(
        id="2020mar",
        year=2020,
        abbreviation="mar",
    ).put()

    # Test model return
    resp = api_client.get(
        "/api/v3/district/2020tx/rankings", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "district key: 2020tx does not exist"

    # Test different model return
    resp = api_client.get(
        "/api/v3/district/2020tx/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
    assert resp.json["Error"] == "district key: 2020tx does not exist"
