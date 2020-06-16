from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event


def test_team(ndb_client: ndb.Client, api_client: Client) -> None:
    with ndb_client.context():
        Event(
            id="2019casj",
            year=2019,
            event_short="casj",
            event_type_enum=EventType.REGIONAL,
        ).put()
    resp = api_client.get("/api/v3/event/2019casj", headers={"X-TBA-Auth-Key": "test"})
    assert resp.status_code == 200
