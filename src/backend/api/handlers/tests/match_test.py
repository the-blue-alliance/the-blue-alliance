import json

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.handlers.tests.helpers import (
    validate_nominal_match_keys,
    validate_simple_match_keys,
)
from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.match import Match


def test_match(ndb_stub, api_client: Client) -> None:
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

    # Nominal response
    resp = api_client.get(
        "/api/v3/match/2020casj_qm1", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "2020casj_qm1"
    validate_nominal_match_keys(resp.json)

    # Simple response
    resp = api_client.get(
        "/api/v3/match/2020casj_qm1/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "2020casj_qm1"
    validate_simple_match_keys(resp.json)

    # Keys response
    resp = api_client.get(
        "/api/v3/match/2020casj_qm1/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
