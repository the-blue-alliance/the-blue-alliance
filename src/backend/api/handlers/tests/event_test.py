from werkzeug.test import Client

from backend.api.handlers.helpers.model_properties import simple_event_properties
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event


def validate_nominal_event_keys(team):
    assert set(team.keys()).difference(set(simple_event_properties)) != set()


def validate_simple_event_keys(team):
    assert set(team.keys()).difference(set(simple_event_properties)) == set()


def test_event(ndb_stub, api_client: Client) -> None:
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
    validate_nominal_event_keys(resp.json)

    # Simple response
    resp = api_client.get(
        "/api/v3/event/2019casj/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "2019casj"
    validate_simple_event_keys(resp.json)

    # Keys response
    resp = api_client.get(
        "/api/v3/event/2019casj/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404


def test_event_list_all(ndb_stub, api_client: Client) -> None:
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
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/events/all", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_nominal_event_keys(event)
    keys = set([event["key"] for event in resp.json])
    assert "2019casj" in keys
    assert "2020casj" in keys

    # Simple response
    resp = api_client.get(
        "/api/v3/events/all/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_simple_event_keys(event)
    keys = set([event["key"] for event in resp.json])
    assert "2019casj" in keys
    assert "2020casj" in keys

    # Keys response
    resp = api_client.get(
        "/api/v3/events/all/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert len(resp.json) == 2
    assert "2019casj" in resp.json
    assert "2020casj" in resp.json


def test_event_list_year(ndb_stub, api_client: Client) -> None:
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
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020casf",
        year=2020,
        event_short="casf",
        event_type_enum=EventType.REGIONAL,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/events/2019", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for event in resp.json:
        validate_nominal_event_keys(event)
    assert resp.json[0]["key"] == "2019casj"

    resp = api_client.get(
        "/api/v3/events/2020", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_nominal_event_keys(event)
    keys = set([event["key"] for event in resp.json])
    assert "2020casf" in keys
    assert "2020casj" in keys

    # Simple response
    resp = api_client.get(
        "/api/v3/events/2019/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for event in resp.json:
        validate_simple_event_keys(event)
    assert resp.json[0]["key"] == "2019casj"

    resp = api_client.get(
        "/api/v3/events/2020/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_simple_event_keys(event)
    keys = set([event["key"] for event in resp.json])
    assert "2020casf" in keys
    assert "2020casj" in keys

    # Keys response
    resp = api_client.get(
        "/api/v3/events/2019/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert "2019casj" in resp.json

    resp = api_client.get(
        "/api/v3/events/2020/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert "2020casf" in resp.json
    assert "2020casj" in resp.json
