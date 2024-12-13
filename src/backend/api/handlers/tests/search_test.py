from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.team import Team


def test_search_index(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(
        id="frc604", team_number=604, name="Quixilver/Long Name", nickname="Quixilver"
    ).put()
    Team(id="frc5254", team_number=5254, name="HYPE/Long Name", nickname="HYPE").put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
        name="Silicon Valley Regional",
        short_name="Silicon Valley",
    ).put()

    Event(
        id="2024mil",
        year=2024,
        event_short="mil",
        event_type_enum=EventType.CMP_DIVISION,
        name="Milstein Division",
        short_name="Milstein",
    ).put()

    resp = api_client.get(
        "/api/v3/search_index", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200

    assert len(resp.json["events"]) == 2
    assert len(resp.json["teams"]) == 2

    assert resp.json["events"][0] == {
        "key": "2019casj",
        "name": "Silicon Valley Regional",
    }
    assert resp.json["events"][1] == {
        "key": "2024mil",
        "name": "Milstein Division",
    }

    assert resp.json["teams"][0] == {
        "key": "frc604",
        "nickname": "Quixilver",
    }
    assert resp.json["teams"][1] == {
        "key": "frc5254",
        "nickname": "HYPE",
    }
