from google.cloud import ndb
from werkzeug.test import Client

from backend.api.handlers.helpers.model_properties import simple_event_properties
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event


def validate_nominal_keys(team):
    assert set(team.keys()).difference(set(simple_event_properties)) != set()


def validate_simple_keys(team):
    assert set(team.keys()).difference(set(simple_event_properties)) == set()


def test_event(ndb_client: ndb.Client, api_client: Client) -> None:
    with ndb_client.context():
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

    # Nominal response
    resp = api_client.get(
        "/api/v3/event/2019casj", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "2019casj"
    validate_nominal_keys(resp.json)

    # Simple response
    resp = api_client.get(
        "/api/v3/event/2019casj/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "2019casj"
    validate_simple_keys(resp.json)

    # Keys response
    resp = api_client.get(
        "/api/v3/event/2019casj/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404
