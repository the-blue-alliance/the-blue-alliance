import datetime
import json


from google.appengine.ext import ndb

from backend.common.consts.event_type import CMP_EVENT_TYPES, EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.sitevars.cmp_registration_hacks import ChampsRegistrationHacks
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_event_list_parser import (
    FMSAPIEventListParser,
)


def test_parse_event_list(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2015_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2015).parse(data)

    assert isinstance(events, list)
    assert isinstance(districts, list)

    # File has 6 events, but we ignore CMP divisions (only subdivisions), so only 5 are expected back
    assert len(events) == 5
    assert len(districts) == 1


def test_parse_regional_event(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2015_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, _ = FMSAPIEventListParser(2015).parse(data)
    event = events[0]

    assert event.key_name == "2015nyny"
    assert event.name == "New York City Regional"
    assert event.short_name == "New York City"
    assert event.event_short == "nyny"
    assert event.official is True
    assert event.start_date == datetime.datetime(
        year=2015, month=3, day=12, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2015, month=3, day=15, hour=23, minute=59, second=59
    )
    assert event.venue == "Jacob K. Javits Convention Center"
    assert event.city == "New York"
    assert event.state_prov == "NY"
    assert event.country == "USA"
    assert event.year == 2015
    assert event.event_type_enum == EventType.REGIONAL
    assert event.district_key is None


def test_parse_regional_event_code_override(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2015_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, _ = FMSAPIEventListParser(2015, short="nyc").parse(data)
    event = events[0]

    assert event.key_name == "2015nyc"
    assert event.name == "New York City Regional"
    assert event.short_name == "New York City"
    assert event.event_short == "nyc"
    assert event.official is True
    assert event.start_date == datetime.datetime(
        year=2015, month=3, day=12, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2015, month=3, day=15, hour=23, minute=59, second=59
    )
    assert event.venue == "Jacob K. Javits Convention Center"
    assert event.city == "New York"
    assert event.state_prov == "NY"
    assert event.country == "USA"
    assert event.year == 2015
    assert event.event_type_enum == EventType.REGIONAL
    assert event.district_key is None


def test_parse_district_event(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2015_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2015).parse(data)
    event = events[1]
    district = districts[0]

    assert event.key_name == "2015cthar"
    assert event.name == "NE District - Hartford Event"
    assert event.short_name == "Hartford"
    assert event.event_short == "cthar"
    assert event.official is True
    assert event.start_date == datetime.datetime(
        year=2015, month=3, day=27, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2015, month=3, day=29, hour=23, minute=59, second=59
    )
    assert event.venue == "Hartford Public High School"
    assert event.city == "Hartford"
    assert event.state_prov == "CT"
    assert event.country == "USA"
    assert event.year == 2015
    assert event.event_type_enum == EventType.DISTRICT
    assert event.district_key == district.key

    assert district.key_name == "2015ne"
    assert district.abbreviation == "ne"
    assert district.year == 2015


def test_parse_district_cmp(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2015_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2015).parse(data)
    event = events[2]
    district = districts[0]

    assert event.key_name == "2015necmp"
    assert (
        event.name == "NE FIRST District Championship presented by United Technologies"
    )
    assert event.short_name == "NE"
    assert event.event_short == "necmp"
    assert event.official is True
    assert event.start_date == datetime.datetime(
        year=2015, month=4, day=8, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2015, month=4, day=11, hour=23, minute=59, second=59
    )
    assert event.venue == "Sports and Recreation Center, WPI"
    assert event.city == "Worcester"
    assert event.state_prov == "MA"
    assert event.country == "USA"
    assert event.year == 2015
    assert event.event_type_enum == EventType.DISTRICT_CMP
    assert event.district_key == district.key


def test_parse_cmp_subdivision(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2015_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, _ = FMSAPIEventListParser(2015).parse(data)
    event = events[3]

    assert event.key_name == "2015tes"
    assert event.name == "Tesla Division"
    assert event.short_name == "Tesla"
    assert event.event_short == "tes"
    assert event.official is True
    assert event.start_date == datetime.datetime(
        year=2015, month=4, day=22, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2015, month=4, day=25, hour=23, minute=59, second=59
    )
    assert event.venue == "Edward Jones Dome"
    assert event.city == "St. Louis"
    assert event.state_prov == "MO"
    assert event.country == "USA"
    assert event.year == 2015
    assert event.event_type_enum == EventType.CMP_DIVISION
    assert event.district_key is None


def test_parse_cmp_division(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2022gal.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, _ = FMSAPIEventListParser(2022).parse(data)
    event = events[0]

    assert event.key_name == "2022gal"
    assert event.name == "Galileo Division"
    assert event.short_name == "Galileo"
    assert event.event_short == "gal"
    assert event.official is True
    assert event.start_date == datetime.datetime(
        year=2022, month=4, day=20, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2022, month=4, day=23, hour=23, minute=59, second=59
    )
    assert event.venue == "George R. Brown Convention Center"
    assert event.city == "Houston"
    assert event.state_prov == "TX"
    assert event.country == "USA"
    assert event.year == 2022
    assert event.event_type_enum == EventType.CMP_DIVISION
    assert event.district_key is None


def test_parse_offseason(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2015_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, _ = FMSAPIEventListParser(2015).parse(data)
    event = events[4]

    assert event.key_name == "2015iri"
    assert event.name == "Indiana Robotics Invitational"
    assert event.short_name == "Indiana Robotics Invitational"
    assert event.event_short == "iri"
    assert event.official is False
    assert event.start_date == datetime.datetime(
        year=2015, month=7, day=17, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2015, month=7, day=18, hour=23, minute=59, second=59
    )
    assert event.venue == "Lawrence North HS"
    assert event.city == "Indianapolis"
    assert event.state_prov == "IN"
    assert event.country == "USA"
    assert event.year == 2015
    assert event.event_type_enum == EventType.OFFSEASON
    assert event.district_key is None


def test_parse_2017_event(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2017_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2017).parse(data)
    assert len(events) == 165
    assert len(districts) == 10
    event = events[16]

    assert event.key_name == "2017casj"
    assert event.name == "Silicon Valley Regional"
    assert event.short_name == "Silicon Valley"
    assert event.event_short == "casj"
    assert event.official is True
    assert event.start_date == datetime.datetime(
        year=2017, month=3, day=29, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2017, month=4, day=1, hour=23, minute=59, second=59
    )
    assert event.venue == "San Jose State University - The Event Center"
    assert event.city == "San Jose"
    assert event.state_prov == "CA"
    assert event.country == "USA"
    assert event.year == 2017
    assert event.event_type_enum == EventType.REGIONAL
    assert event.district_key is None

    # New in 2017
    assert event.website == "http://www.firstsv.org"


def test_parse_2017_events_with_cmp_hacks(test_data_importer):
    hack_sitevar = {
        "event_name_override": [
            {
                "event": "2017cmpmo",
                "name": "FIRST Championship Event",
                "short_name": "Championship",
            },
            {
                "event": "2017cmptx",
                "name": "FIRST Championship Event",
                "short_name": "Championship",
            },
        ],
        "set_start_to_last_day": ["2017cmptx", "2017cmpmo"],
        "divisions_to_skip": ["2017arc", "2017cars", "2017cur", "2017dal", "2017dar"],
    }
    ChampsRegistrationHacks.put(hack_sitevar)

    path = test_data_importer._get_path(__file__, "data/2017_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2017).parse(data)
    assert len(events) == 160
    assert len(districts) == 10

    non_einstein_types = CMP_EVENT_TYPES
    non_einstein_types.remove(EventType.CMP_FINALS)
    for key in hack_sitevar["divisions_to_skip"]:
        assert not list(filter(lambda e: e.key_name == key, events))

    einstein_stl = next(e for e in events if e.key_name == "2017cmpmo")
    assert einstein_stl is not None
    assert einstein_stl.name == "FIRST Championship Event (St. Louis)"
    assert einstein_stl.short_name == "Championship (St. Louis)"
    assert einstein_stl.start_date == datetime.datetime(
        year=2017, month=4, day=29, hour=0, minute=0, second=0
    )
    assert einstein_stl.end_date == datetime.datetime(
        year=2017, month=4, day=29, hour=23, minute=59, second=59
    )

    einstein_hou = next(e for e in events if e.key_name == "2017cmptx")
    assert einstein_hou is not None
    assert einstein_hou.name == "FIRST Championship Event (Houston)"
    assert einstein_hou.short_name == "Championship (Houston)"
    assert einstein_hou.start_date == datetime.datetime(
        year=2017, month=4, day=22, hour=0, minute=0, second=0
    )
    assert einstein_hou.end_date == datetime.datetime(
        year=2017, month=4, day=22, hour=23, minute=59, second=59
    )


def test_parse_2017_official_offseason(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2017_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2017).parse(data)
    assert len(events) == 165
    assert len(districts) == 10
    event = next(e for e in events if e.key_name == "2017iri")

    assert event.key_name == "2017iri"
    assert event.name == "Indiana Robotics Invitational"
    assert event.short_name == "Indiana Robotics Invitational"
    assert event.event_short == "iri"
    assert event.official is True
    assert event.start_date == datetime.datetime(
        year=2017, month=7, day=14, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2017, month=7, day=15, hour=23, minute=59, second=59
    )
    assert event.venue == "Lawrence North High School"
    assert event.city == "Indianapolis"
    assert event.state_prov == "IN"
    assert event.country == "USA"
    assert event.year == 2017
    assert event.event_type_enum == EventType.OFFSEASON
    assert event.district_key is None
    assert event.website == "http://indianaroboticsinvitational.org/"
    assert event.webcast == []


def test_parse_2018_event(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2018_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2018).parse(data)
    assert len(events) == 178
    assert len(districts) == 10
    event = events[18]

    assert event.key_name == "2018casj"
    assert event.name == "Silicon Valley Regional"
    assert event.short_name == "Silicon Valley"
    assert event.event_short == "casj"
    assert event.official is True
    assert event.start_date == datetime.datetime(
        year=2018, month=3, day=28, hour=0, minute=0, second=0
    )
    assert event.end_date == datetime.datetime(
        year=2018, month=3, day=31, hour=23, minute=59, second=59
    )
    assert event.venue == "San Jose State University - The Event Center"
    assert event.city == "San Jose"
    assert event.state_prov == "CA"
    assert event.country == "USA"
    assert event.year == 2018
    assert event.event_type_enum == EventType.REGIONAL
    assert event.district_key is None
    assert event.website == "http://www.firstsv.org"

    # New in 2018
    assert event.webcast == [
        {"type": "twitch", "channel": "firstinspires9"},
        {"type": "twitch", "channel": "firstinspires10"},
    ]


def test_parse_division_parent_2017(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2017_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2017).parse(data)
    assert len(events) == 165
    assert len(districts) == 10

    # Test division <-> parent associations
    for event in events:
        event_key = event.key.id()
        if event_key == "2017micmp":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2017micmp1"),
                ndb.Key("Event", "2017micmp2"),
                ndb.Key("Event", "2017micmp3"),
                ndb.Key("Event", "2017micmp4"),
            ]
        elif event_key in {"2017micmp1", "2017micmp2", "2017micmp3", "2017micmp4"}:
            assert event.parent_event == ndb.Key("Event", "2017micmp")
            assert event.divisions == []
        elif event_key == "2017cmptx":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2017carv"),
                ndb.Key("Event", "2017gal"),
                ndb.Key("Event", "2017hop"),
                ndb.Key("Event", "2017new"),
                ndb.Key("Event", "2017roe"),
                ndb.Key("Event", "2017tur"),
            ]
        elif event_key in {
            "2017carv",
            "2017gal",
            "2017hop",
            "2017new",
            "2017roe",
            "2017tur",
        }:
            assert event.parent_event == ndb.Key("Event", "2017cmptx")
            assert event.divisions == []
        elif event_key == "2017cmpmo":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2017arc"),
                ndb.Key("Event", "2017cars"),
                ndb.Key("Event", "2017cur"),
                ndb.Key("Event", "2017dal"),
                ndb.Key("Event", "2017dar"),
                ndb.Key("Event", "2017tes"),
            ]
        elif event_key in {
            "2017arc",
            "2017cars",
            "2017cur",
            "2017dal",
            "2017dar",
            "2017tes",
        }:
            assert event.parent_event == ndb.Key("Event", "2017cmpmo")
            assert event.divisions == []
        else:
            assert event.parent_event is None
            assert event.divisions == []


def test_parse_division_parent_2018(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2018_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)
    events, districts = FMSAPIEventListParser(2018).parse(data)
    assert len(events) == 178
    assert len(districts) == 10

    # Test division <-> parent associations
    for event in events:
        event_key = event.key.id()
        if event_key == "2018oncmp":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2018oncmp1"),
                ndb.Key("Event", "2018oncmp2"),
            ]
        elif event_key in {"2018oncmp1", "2018oncmp2"}:
            assert event.parent_event == ndb.Key("Event", "2018oncmp")
            assert event.divisions == []
        elif event_key == "2018micmp":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2018micmp1"),
                ndb.Key("Event", "2018micmp2"),
                ndb.Key("Event", "2018micmp3"),
                ndb.Key("Event", "2018micmp4"),
            ]
        elif event_key in {"2018micmp1", "2018micmp2", "2018micmp3", "2018micmp4"}:
            assert event.parent_event == ndb.Key("Event", "2018micmp")
            assert event.divisions == []
        elif event_key == "2018cmptx":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2018carv"),
                ndb.Key("Event", "2018gal"),
                ndb.Key("Event", "2018hop"),
                ndb.Key("Event", "2018new"),
                ndb.Key("Event", "2018roe"),
                ndb.Key("Event", "2018tur"),
            ]
        elif event_key in {
            "2018carv",
            "2018gal",
            "2018hop",
            "2018new",
            "2018roe",
            "2018tur",
        }:
            assert event.parent_event == ndb.Key("Event", "2018cmptx")
            assert event.divisions == []
        elif event_key == "2018cmpmi":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2018arc"),
                ndb.Key("Event", "2018cars"),
                ndb.Key("Event", "2018cur"),
                ndb.Key("Event", "2018dal"),
                ndb.Key("Event", "2018dar"),
                ndb.Key("Event", "2018tes"),
            ]
        elif event_key in {
            "2018arc",
            "2018cars",
            "2018cur",
            "2018dal",
            "2018dar",
            "2018tes",
        }:
            assert event.parent_event == ndb.Key("Event", "2018cmpmi")
            assert event.divisions == []
        else:
            assert event.parent_event is None
            assert event.divisions == []


def test_parse_division_parent_2023(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2023_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)
    events, districts = FMSAPIEventListParser(2023).parse(data)
    assert len(events) == 186
    assert len(districts) == 11

    # Test division <-> parent associations
    for event in events:
        event_key = event.key.id()
        if event_key == "2023oncmp":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2023oncmp1"),
                ndb.Key("Event", "2023oncmp2"),
            ]
        elif event_key in {"2023oncmp1", "2023oncmp2"}:
            assert event.parent_event == ndb.Key("Event", "2023oncmp")
            assert event.divisions == []
        elif event_key == "2023micmp":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2023micmp1"),
                ndb.Key("Event", "2023micmp2"),
                ndb.Key("Event", "2023micmp3"),
                ndb.Key("Event", "2023micmp4"),
            ]
        elif event_key in {"2023micmp1", "2023micmp2", "2023micmp3", "2023micmp4"}:
            assert event.parent_event == ndb.Key("Event", "2023micmp")
            assert event.divisions == []
        elif event_key == "2023necmp":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2023necmp1"),
                ndb.Key("Event", "2023necmp2"),
            ]
        elif event_key in {"2023necmp1", "2023necmp2"}:
            assert event.parent_event == ndb.Key("Event", "2023necmp")
            assert event.divisions == []
        elif event_key == "2023txcmp":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2023txcmp1"),
                ndb.Key("Event", "2023txcmp2"),
            ]
        elif event_key in {"2023txcmp1", "2023txcmp2"}:
            assert event.parent_event == ndb.Key("Event", "2023txcmp")
            assert event.divisions == []
        elif event_key == "2023cmptx":
            assert event.parent_event is None
            assert event.divisions == [
                ndb.Key("Event", "2023arc"),
                ndb.Key("Event", "2023cur"),
                ndb.Key("Event", "2023dal"),
                ndb.Key("Event", "2023gal"),
                ndb.Key("Event", "2023hop"),
                ndb.Key("Event", "2023joh"),
                ndb.Key("Event", "2023mil"),
                ndb.Key("Event", "2023new"),
            ]
        elif event_key in {
            "2023arc",
            "2023cur",
            "2023dal",
            "2023gal",
            "2023hop",
            "2023joh",
            "2023mil",
            "2023new",
        }:
            assert event.parent_event == ndb.Key("Event", "2023cmptx")
            assert event.divisions == []
        else:
            assert event.parent_event is None
            assert event.divisions == []


def test_parse_2022_one_day_event(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2022on305.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2022).parse(data)
    assert len(events) == 1
    assert len(districts) == 1

    event = events[0]
    assert event.playoff_type == PlayoffType.BRACKET_4_TEAM


def test_parse_2022_two_alliance_dcmp(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2022txcmp.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, districts = FMSAPIEventListParser(2022).parse(data)
    assert len(events) == 1
    assert len(districts) == 1

    event = events[0]
    assert event.playoff_type == PlayoffType.BRACKET_2_TEAM


def test_parse_weeks(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2025_event_list.json")
    with open(path, "r") as f:
        data = json.load(f)

    events, _ = FMSAPIEventListParser(2025).parse(data)
    event = events[0]

    assert event.key_name == "2025alhu"
    assert event.name == "Rocket City Regional"
    assert event.week == 2
