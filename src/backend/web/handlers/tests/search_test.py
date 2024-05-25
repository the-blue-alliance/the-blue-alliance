from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.team import Team


def test_team_number(ndb_stub, web_client: Client) -> None:
    Team(
        id="frc1124",
        team_number=1124,
    ).put()

    resp = web_client.get("/search", query_string={"q": "1124"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/team/1124"


def test_team_number_doest_exist(ndb_stub, web_client: Client) -> None:
    resp = web_client.get("/search", query_string={"q": "99999"})
    assert resp.status_code == 200


def test_team_key(ndb_stub, web_client: Client) -> None:
    Team(
        id="frc1124",
        team_number=1124,
    ).put()

    resp = web_client.get("/search", query_string={"q": "frc1124"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/team/1124"


def test_team_key_doest_exist(ndb_stub, web_client: Client) -> None:
    resp = web_client.get("/search", query_string={"q": "frc9999"})
    assert resp.status_code == 200


def test_event_key(ndb_stub, web_client: Client) -> None:
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    resp = web_client.get("/search", query_string={"q": "2019casj"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/event/2019casj"


def test_event_key_doesnt_exist(ndb_stub, web_client: Client) -> None:
    resp = web_client.get("/search", query_string={"q": "2019casj"})
    assert resp.status_code == 200


@freeze_time("2019-04-01")
def test_event_code(ndb_stub, web_client: Client) -> None:
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    resp = web_client.get("/search", query_string={"q": "casj"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/event/2019casj"


@freeze_time("2019-04-01")
def test_event_code_doesnt_exist(ndb_stub, web_client: Client) -> None:
    resp = web_client.get("/search", query_string={"q": "casj"})
    assert resp.status_code == 200


def test_random_query_string(ndb_stub, web_client: Client) -> None:
    resp = web_client.get("/search", query_string={"q": "2@sdf"})
    assert resp.status_code == 200
