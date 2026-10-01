import json

from google.appengine.ext import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.queries.dict_converters.award_converter import AwardConverter


def _award() -> Award:
    return Award(
        id="2019nyny_1",
        year=2019,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2019nyny"),
        name_str="Regional Winners",
        recipient_json_list=[
            json.dumps({"team_number": 254, "awardee": None}),
            json.dumps({"team_number": "7332B", "awardee": None}),
            json.dumps({"team_number": None, "awardee": "Dean Kamen"}),
        ],
        team_list=[ndb.Key(Team, "frc254"), ndb.Key(Team, "frc7332B")],
    )


def test_awardConverter_v3(ndb_context) -> None:
    converted = AwardConverter.awardConverter_v3(_award())
    assert converted == {
        "name": "Regional Winners",
        "award_type": AwardType.WINNER,
        "year": 2019,
        "event_key": "2019nyny",
        "recipient_list": [
            {"awardee": None, "team_key": "frc254"},
            {"awardee": None, "team_key": "frc7332B"},
            {"awardee": "Dean Kamen", "team_key": None},
        ],
    }


def test_awardConverter_v3_no_recipients(ndb_context) -> None:
    award = _award()
    award.recipient_json_list = []
    converted = AwardConverter.awardConverter_v3(award)
    assert converted["recipient_list"] == []


def test_convert_list(ndb_context) -> None:
    converted = AwardConverter([_award()]).convert(ApiMajorVersion.API_V3)
    assert converted == [AwardConverter.awardConverter_v3(_award())]


def test_dictToModel_v3_round_trip(ndb_context) -> None:
    award = _award()
    event = Event(id="2019nyny", event_type_enum=EventType.REGIONAL)
    converted = AwardConverter.awardConverter_v3(award)

    model = AwardConverter.dictToModel_v3(converted, event)

    assert model.key.id() == "2019nyny_1"
    assert model.event == ndb.Key(Event, "2019nyny")
    assert model.award_type_enum == AwardType.WINNER
    assert model.event_type_enum == EventType.REGIONAL
    assert model.year == 2019
    assert model.name_str == "Regional Winners"
    assert model.team_list == [ndb.Key(Team, "frc254"), ndb.Key(Team, "frc7332B")]
    # Team numbers come back as strings, since they are sliced off the team key
    assert model.recipient_list == [
        {"team_number": "254", "awardee": None},
        {"team_number": "7332B", "awardee": None},
        {"team_number": None, "awardee": "Dean Kamen"},
    ]
