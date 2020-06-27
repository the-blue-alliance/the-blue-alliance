import json
from datetime import datetime
from typing import Optional

import pytest
from freezegun import freeze_time
from google.cloud import ndb

from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_type import WebcastType
from backend.common.models.event import District
from backend.common.models.event import Event
from backend.common.models.tests.util import (
    CITY_STATE_COUNTRY_PARAMETERS,
    LOCATION_PARAMETERS,
)


@pytest.mark.parametrize("key", ["2010ct", "2014onto2"])
def test_valid_key_names(key: str) -> None:
    assert Event.validate_key_name(key) is True


@pytest.mark.parametrize("key", ["210c1", "frc2010ct", "2010 ct"])
def test_invalid_key_names(key: str) -> None:
    assert Event.validate_key_name(key) is False


@pytest.mark.parametrize(
    "starttime, timezone_id, output",
    [
        (datetime(2020, 2, 1), None, datetime(2020, 2, 1)),
        (datetime(2020, 2, 1), "America/New_York", datetime(2020, 2, 1, 5)),
        # A DST-ambiguous time, assert that we account for the extra hour
        (
            datetime(2009, 10, 31, 23, 30),
            "America/New_York",
            datetime(2009, 11, 1, 3, 30),
        ),
    ],
)
def test_time_as_utc(starttime: datetime, timezone_id: str, output: datetime) -> None:
    e = Event(timezone_id=timezone_id,)

    assert e.time_as_utc(starttime) == output


@pytest.mark.parametrize(
    "mock_time, timezone_id, output",
    [
        ("2020-02-01", None, datetime(2020, 2, 1)),
        ("2020-02-01", "America/New_York", datetime(2020, 1, 31, 19)),
        # A DST-ambiguous time, assert that we account for the extra hour
        ("2009-10-31 23:30", "America/New_York", datetime(2009, 10, 31, 19, 30)),
    ],
)
def test_local_time(
    mock_time: str, timezone_id: Optional[str], output: datetime
) -> None:
    e = Event(timezone_id=timezone_id,)

    with freeze_time(mock_time):
        assert e.local_time() == output


@pytest.mark.parametrize(
    "mock_time, event_start, event_end, days_before, days_after, is_within",
    [
        ("2020-01-01", datetime(2020, 2, 1), datetime(2020, 2, 5), -2, 2, False),
        ("2020-01-30", datetime(2020, 2, 1), datetime(2020, 2, 5), -2, 2, True),
        ("2020-02-02", datetime(2020, 2, 1), datetime(2020, 2, 5), -2, 2, True),
        ("2020-02-07", datetime(2020, 2, 1), datetime(2020, 2, 5), -2, 2, True),
        ("2020-03-02", datetime(2020, 2, 1), datetime(2020, 2, 5), -2, 2, False),
        ("2020-02-02", None, datetime(2020, 2, 5), -2, 2, False),
        ("2020-02-02", datetime(2020, 2, 1), None, -2, 2, False),
    ],
)
def test_within_days(
    mock_time: str,
    event_start: Optional[datetime],
    event_end: Optional[datetime],
    days_before: int,
    days_after: int,
    is_within: bool,
) -> None:
    e = Event(start_date=event_start, end_date=event_end,)

    with freeze_time(mock_time):
        assert e.withinDays(days_before, days_after) == is_within


@pytest.mark.parametrize(
    "mock_time, is_within",
    [
        ("2020-01-01", False),
        ("2020-01-31", True),
        ("2020-02-02", True),
        ("2020-02-06", True),
        ("2020-03-02", False),
    ],
)
def test_within_a_day(mock_time: str, is_within: bool,) -> None:
    e = Event(start_date=datetime(2020, 2, 1), end_date=datetime(2020, 2, 5),)

    with freeze_time(mock_time):
        assert e.within_a_day == is_within


@pytest.mark.parametrize(
    "mock_time, timezone, is_now",
    [
        ("2020-01-01", "UTC", False),
        ("2020-01-31", "UTC", False),
        ("2020-01-31", None, True),
        ("2020-02-01", "UTC", True),
        ("2020-02-02", "UTC", True),
        ("2020-02-05", "UTC", True),
        ("2020-02-06", None, True),
        ("2020-02-06", "UTC", False),
        ("2020-03-02", "UTC", False),
    ],
)
def test_now(mock_time: str, timezone: Optional[str], is_now: bool,) -> None:
    e = Event(
        timezone_id=timezone,
        start_date=datetime(2020, 2, 1),
        end_date=datetime(2020, 2, 5),
    )

    with freeze_time(mock_time):
        assert e.now == is_now


@pytest.mark.parametrize(
    "mock_time, is_past, is_future, start_today, end_today",
    [
        ("2020-01-01", False, True, False, False),
        ("2020-02-01", False, False, True, False),
        ("2020-02-03", False, False, False, False),
        ("2020-02-05", False, False, False, True),
        ("2020-02-10", True, False, False, False),
    ],
)
def test_past_future_start_end_today(
    mock_time: str, is_past: bool, is_future: bool, start_today: bool, end_today: bool
) -> None:
    e = Event(start_date=datetime(2020, 2, 1), end_date=datetime(2020, 2, 5),)

    with freeze_time(mock_time):
        assert e.past == is_past
        assert e.future == is_future
        assert e.starts_today == start_today
        assert e.ends_today == end_today


@pytest.mark.parametrize(
    "year, event_type, official, week, week_output, week_str",
    [
        # Don't forget that weeks are zero indexed :)
        (2020, EventType.REGIONAL, True, 2, 2, "Week 3"),
        (2016, EventType.REGIONAL, True, 0, 0, "Week 0.5"),
        (2016, EventType.REGIONAL, True, 1, 1, "Week 1"),
        (2020, EventType.OFFSEASON, False, 2, None, None),
        (2020, EventType.REGIONAL, False, 2, None, None),
    ],
)
def test_week(
    year: int,
    event_type: EventType,
    official: bool,
    week: int,
    week_output: int,
    week_str: str,
) -> None:
    e = Event(year=year, event_type_enum=event_type, official=official,)
    e._week = week

    assert e.week == week_output
    assert e.week_str == week_str


@pytest.mark.parametrize(*LOCATION_PARAMETERS)
def test_location(
    city: str, state: str, country: str, postalcode: str, output: str
) -> None:
    event = Event(city=city, state_prov=state, country=country, postalcode=postalcode,)
    assert event.location == output


@pytest.mark.parametrize(*CITY_STATE_COUNTRY_PARAMETERS)
def test_city_state_country(city: str, state: str, country: str, output: str) -> None:
    event = Event(city=city, state_prov=state, country=country,)
    assert event.city_state_country == output


@freeze_time("2020-02-01")
def test_webcasts() -> None:
    event = Event(
        start_date=datetime(2020, 2, 1),
        end_date=datetime(2020, 2, 3),
        webcast_json=json.dumps(
            [
                {"type": "youtube", "channel": "meow", "date": "2020-02-01"},
                {"type": "twitch", "channel": "firstinspires"},
            ]
        ),
    )
    webcasts = event.webcast
    assert webcasts is not None
    assert len(webcasts) == 2
    assert webcasts[0] == {
        "type": WebcastType.TWITCH,
        "channel": "firstinspires",
    }
    assert webcasts[1] == {
        "type": WebcastType.YOUTUBE,
        "channel": "meow",
        "date": "2020-02-01",
    }

    assert len(event.current_webcasts) == 2
    with freeze_time("2020-02-02"):
        # go to some other time where the first webcast is not active
        assert len(event.current_webcasts) == 1

    assert event.has_first_official_webcast is True


def test_linked_district() -> None:
    District(id="2019ne", display_name="New England",).put()
    event = Event(district_key=ndb.Key(District, "2019ne"),)
    assert event.event_district_abbrev == "ne"
    assert event.event_district_key == "2019ne"
    assert event.event_district_str == "New England"


def test_no_linked_district() -> None:
    event = Event(district_key=None)
    assert event.event_district_abbrev is None
    assert event.event_district_key is None
    assert event.event_district_str is None


def test_nonexistent_linked_district() -> None:
    event = Event(district_key=ndb.Key(District, "2019ne"))
    assert event.event_district_abbrev == "ne"
    assert event.event_district_key == "2019ne"
    assert event.event_district_str is None
