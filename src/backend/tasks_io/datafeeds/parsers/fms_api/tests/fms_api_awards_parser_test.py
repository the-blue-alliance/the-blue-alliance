import json

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_awards_parser import (
    FMSAPIAwardsParser,
)


def test_parse_awards(test_data_importer, ndb_stub) -> None:
    path = test_data_importer._get_path(__file__, "data/2017cmpmo_awards.json")
    with open(path, "r") as f:
        data = json.load(f)

    event = Event(
        event_short="cmpmo",
        event_type_enum=EventType.CMP_FINALS,
        year=2017,
    )
    awards = FMSAPIAwardsParser(event).parse(data)

    assert awards is not None
    assert len(awards) == 6

    for award in awards:
        if award.key.string_id() == "2017cmpmo_0":
            assert award.name_str == "Chairman's Award"
            assert award.award_type_enum == 0
            assert not {"team_number": 2169, "awardee": None} in award.recipient_list
            assert not {"team_number": 1885, "awardee": None} in award.recipient_list
            assert {"team_number": 2614, "awardee": None} in award.recipient_list
        elif award.key.string_id() == "2017cmpmo_69":
            assert award.name_str == "Chairman's Award Finalist"
            assert award.award_type_enum == 69
            assert {"team_number": 2169, "awardee": None} in award.recipient_list
            assert {"team_number": 1885, "awardee": None} in award.recipient_list
            assert not {"team_number": 2614, "awardee": None} in award.recipient_list


def test_parse_awards_valid_team_nums(test_data_importer, ndb_stub) -> None:
    path = test_data_importer._get_path(__file__, "data/2017cmpmo_awards.json")
    with open(path, "r") as f:
        data = json.load(f)

    event = Event(
        event_short="cmpmo",
        event_type_enum=EventType.CMP_FINALS,
        year=2017,
    )
    awards = FMSAPIAwardsParser(event, valid_team_nums={2169}).parse(data)

    assert awards is not None
    assert len(awards) == 1

    award = awards[0]
    assert award is not None

    assert award.name_str == "Chairman's Award Finalist"
    assert award.award_type_enum == 69
    assert {"team_number": 2169, "awardee": None} in award.recipient_list
    assert not {"team_number": 1885, "awardee": None} in award.recipient_list
    assert not {"team_number": 2614, "awardee": None} in award.recipient_list


def test_parse_awards_valid_award_type_enum(test_data_importer, ndb_stub) -> None:
    path = test_data_importer._get_path(__file__, "data/2017cmpmo_awards_garbage.json")
    with open(path, "r") as f:
        data = json.load(f)

    event = Event(
        event_short="cmpmo",
        event_type_enum=EventType.CMP_FINALS,
        year=2017,
    )
    awards = FMSAPIAwardsParser(event).parse(data)

    assert awards is None


def test_parse_awards_awardee(test_data_importer, ndb_stub) -> None:
    path = test_data_importer._get_path(__file__, "data/2015waamv_staging_awards.json")
    with open(path, "r") as f:
        data = json.load(f)

    event = Event(
        event_short="waamv",
        event_type_enum=EventType.REGIONAL,
        year=2015,
    )
    awards = FMSAPIAwardsParser(event).parse(data)

    assert awards is not None
    assert len(awards) == 5

    for award in awards:
        if award.key.string_id() == "2015waamv_3":
            assert award.name_str == "Woodie Flowers Award"
            assert award.award_type_enum == 3
            assert {"team_number": None, "awardee": "Bob"} in award.recipient_list
        elif award.key.string_id() == "2015waamv_17":
            assert award.name_str == "Quality Award sponsored by Motorola"
            assert award.award_type_enum == 17
            assert {"team_number": 1318, "awardee": None} in award.recipient_list
        elif award.key.string_id() == "2015waamv_4":
            assert award.name_str == "FIRST Dean's List Award"
            assert award.award_type_enum == 4
            assert {
                "team_number": 123,
                "awardee": "Person Name 1",
            } in award.recipient_list
            assert {
                "team_number": 321,
                "awardee": "Person Name 2",
            } in award.recipient_list


def test_parse_awards_none(test_data_importer, ndb_stub) -> None:
    event = Event()

    path = test_data_importer._get_path(__file__, "data/2017cmpmo_no_awards.json")
    with open(path, "r") as f:
        data = json.load(f)

    awards = FMSAPIAwardsParser(event).parse(data)

    assert awards is None


def test_parse_awards_duplicate_teams(test_data_importer, ndb_stub) -> None:
    path = test_data_importer._get_path(__file__, "data/2021fimaw_awards.json")
    with open(path, "r") as f:
        data = json.load(f)

    event = Event(
        event_short="fimwa",
        event_type_enum=EventType.REMOTE,
        year=2021,
    )
    awards = FMSAPIAwardsParser(event).parse(data)

    # Expected outcome is Chairman's Awards should be de-duped but only a single
    # team should exist in the recipient_json

    assert awards is not None
    assert len(awards) == 2

    award = awards[0]
    assert award is not None

    assert award.name_str == "Regional Chairman's Award"
    assert award.award_type_enum == 0
    assert award.recipient_list == [{"awardee": None, "team_number": 503}]


def test_parse_awards_duplicate_teams2(test_data_importer, ndb_stub) -> None:
    event = Event(
        event_short="mnmi2",
        event_type_enum=EventType.REGIONAL,
        year=2022,
    )

    path = test_data_importer._get_path(__file__, "data/2022mnmi2_awards.json")
    with open(path, "r") as f:
        data = json.load(f)

    awards = FMSAPIAwardsParser(event).parse(data)
    assert awards is not None

    for award in awards:
        if award.award_type_enum == AwardType.DEANS_LIST:
            assert len(award.recipient_list) == 2
