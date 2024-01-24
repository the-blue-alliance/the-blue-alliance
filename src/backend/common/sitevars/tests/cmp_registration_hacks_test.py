import datetime

import pytest
from freezegun import freeze_time
from google.appengine.ext import ndb

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.sitevars.cmp_registration_hacks import ChampsRegistrationHacks


def make_event(event_type: EventType, division_count: int) -> Event:
    return Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=event_type,
        divisions=[
            ndb.Key(Event, f"2023test{i}") for i in range(1, division_count + 1)
        ],
        start_date=datetime.datetime(2023, 4, 1),
        end_date=datetime.datetime(2023, 4, 4),
    )


def test_get_default() -> None:
    default_sitevar = ChampsRegistrationHacks.get()
    assert default_sitevar == {
        "set_start_to_last_day": [],
        "event_name_override": [],
        "divisions_to_skip": [],
        "skip_eventteams": [],
    }


def test_skip_eventteams_explicit_key() -> None:
    ChampsRegistrationHacks.put(
        {
            "set_start_to_last_day": [],
            "event_name_override": [],
            "divisions_to_skip": [],
            "skip_eventteams": ["2023test"],
        }
    )

    event = make_event(EventType.OFFSEASON, 0)
    assert ChampsRegistrationHacks.should_skip_eventteams(event) is True


@pytest.mark.parametrize(
    "event_type,division_count,date_str,should_skip",
    [
        # Live district CMP with divisions
        (EventType.DISTRICT_CMP, 2, "2023-04-01", True),
        # Live world CMP with divisions
        (EventType.CMP_FINALS, 4, "2023-04-01", True),
        # Past district CMP with divisions
        (EventType.DISTRICT_CMP, 2, "2023-05-01", True),
        # Past world CMP with divisions
        (EventType.CMP_FINALS, 2, "2023-05-01", True),
        # Future district CMP with divisions
        (EventType.DISTRICT_CMP, 2, "2023-03-01", False),
        # Future world CMP with divisions
        (EventType.CMP_FINALS, 2, "2023-03-01", False),
        # Live district CMP with no divisions
        (EventType.DISTRICT_CMP, 0, "2023-04-01", False),
        # Past district CMP with no divisions
        (EventType.DISTRICT_CMP, 0, "2023-05-01", False),
        # Bad event type
        (EventType.OFFSEASON, 2, "2023-04-01", False),
    ],
)
def test_automatically_skip_cases(
    event_type: EventType, division_count: int, date_str: str, should_skip: bool
) -> None:
    event = make_event(event_type, division_count)
    with freeze_time(date_str):
        assert ChampsRegistrationHacks.should_skip_eventteams(event) == should_skip
