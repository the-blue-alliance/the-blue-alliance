import json

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award import Award
from backend.common.models.award_recipient import AwardRecipient
from backend.common.models.event import Event
from backend.common.models.team import Team


def test_award_dashboard(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.get("/admin/awards")
    assert resp.status_code == 200


def test_award_delete(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    a = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
    )
    a.put()

    resp = web_client.post("/admin/award/delete", data={"award_key": a.key_name})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/awards"

    assert Award.get_by_id(a.key_name) is None


def test_award_delete_not_found(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post("/admin/award/delete", data={"award_key": "2010ct_3"})
    assert resp.status_code == 404


def test_award_edit_get(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    a = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
    )
    a.put()

    resp = web_client.get(f"/admin/award/edit/{a.key_name}")
    assert resp.status_code == 200


def test_award_edit_get_bad_key(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.get("/admin/award/edit/2010ct_1")
    assert resp.status_code == 404


def test_award_edit_post(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    a = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
        recipient_json_list=[
            json.dumps(
                AwardRecipient(
                    team_number=1124,
                    awardee=None,
                )
            )
        ],
        team_list=[ndb.Key(Team, "frc1124")],
    )
    a.put()

    resp = web_client.post(
        f"/admin/award/edit/{a.key_name}",
        data={
            "award_type_enum": AwardType.WINNER.value,
            "event_key_name": "2010ct",
            "event_type_enum": EventType.REGIONAL.value,
            "name_str": "Winner",
            "recipient_list_json": json.dumps(
                [
                    AwardRecipient(
                        team_number=1124,
                        awardee=None,
                    ),
                    AwardRecipient(
                        team_number=177,
                        awardee=None,
                    ),
                ]
            ),
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2010ct"

    a = Award.get_by_id(a.key_name)
    assert a is not None
    assert a.name_str == "Winner"
    assert a.award_type_enum == AwardType.WINNER
    assert a.event_type_enum == EventType.REGIONAL
    assert a.event == ndb.Key(Event, "2010ct")
    assert a.year == 2010
    assert a.recipient_list == [
        AwardRecipient(
            team_number=1124,
            awardee=None,
        ),
        AwardRecipient(
            team_number=177,
            awardee=None,
        ),
    ]
    assert a.team_list == [
        ndb.Key(Team, "frc1124"),
        ndb.Key(Team, "frc177"),
    ]


def test_award_edit_bad_key(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    a = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
        recipient_json_list=[
            json.dumps(
                AwardRecipient(
                    team_number=1124,
                    awardee=None,
                )
            )
        ],
        team_list=[ndb.Key(Team, "frc1124")],
    )
    a.put()

    resp = web_client.post(
        f"/admin/award/edit/{a.key_name}",
        data={
            "award_type_enum": AwardType.CHAIRMANS.value,
            "event_key_name": "2010ct",
            "event_type_enum": EventType.REGIONAL.value,
            "name_str": "Winner",
            "recipient_list_json": json.dumps(
                [
                    AwardRecipient(
                        team_number=1124,
                        awardee=None,
                    ),
                    AwardRecipient(
                        team_number=177,
                        awardee=None,
                    ),
                ]
            ),
        },
    )
    assert resp.status_code == 400
