from datetime import datetime, timedelta

import pytest
from pytz import timezone, UTC

from backend.common.consts.event_type import EventType
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event


EST = timezone("US/Eastern")


def test_kickoff_datetime() -> None:
    # 2021 - Saturday the 9th, 12:00am EST (https://www.firstinspires.org/robotics/frc/blog/2021-kickoff)
    kickoff_2021 = datetime(2021, 1, 9, 12, 00, 00, tzinfo=EST)
    kickoff_2021_utc = kickoff_2021.astimezone(UTC)
    assert SeasonHelper.kickoff_datetime_est(year=2021) == kickoff_2021
    assert SeasonHelper.kickoff_datetime_utc(year=2021) == kickoff_2021_utc

    # 2020 - Saturday the 4th, 10:30am EST (https://www.firstinspires.org/robotics/frc/blog/2020-kickoff-downloads)
    kickoff_2020 = datetime(2020, 1, 4, 10, 30, 00, tzinfo=EST)
    kickoff_2020_utc = kickoff_2020.astimezone(UTC)
    assert SeasonHelper.kickoff_datetime_est(year=2020) == kickoff_2020
    assert SeasonHelper.kickoff_datetime_utc(year=2020) == kickoff_2020_utc

    # 2019 - Saturday the 5th, 10:30am EST (https://en.wikipedia.org/wiki/Logo_Motion)
    kickoff_2019 = datetime(2019, 1, 5, 10, 30, 00, tzinfo=EST)
    kickoff_2019_utc = kickoff_2019.astimezone(UTC)
    assert SeasonHelper.kickoff_datetime_est(year=2019) == kickoff_2019
    assert SeasonHelper.kickoff_datetime_utc(year=2019) == kickoff_2019_utc

    # 2010 - Saturday the 9th, 10:30am EST (https://en.wikipedia.org/wiki/Breakaway_(FIRST))
    kickoff_2010 = datetime(2010, 1, 9, 10, 30, 00, tzinfo=EST)
    kickoff_2010_utc = kickoff_2010.astimezone(UTC)
    assert SeasonHelper.kickoff_datetime_est(year=2010) == kickoff_2010
    assert SeasonHelper.kickoff_datetime_utc(year=2010) == kickoff_2010_utc


@pytest.mark.parametrize(
    "date, expected",
    [
        (datetime(2020, 1, 3, 14, 30, 00, tzinfo=UTC), False),  # False - over one day
        (datetime(2020, 1, 3, 15, 30, 00, tzinfo=UTC), True),  # True - exactly one day
        (datetime(2020, 1, 4, 15, 30, 00, tzinfo=UTC), True),  # True - same time
        (
            datetime(2020, 2, 4, 15, 30, 00, tzinfo=UTC),
            True,
        ),  # True - very far away in the future
    ],
)
def test_is_kickoff_at_least_one_day_away(date, expected) -> None:
    at_least_one_day_away = SeasonHelper.is_kickoff_at_least_one_day_away(date, 2020)
    assert at_least_one_day_away == expected


def test_effective_season_year_no_events(ndb_stub) -> None:
    now = datetime.now()
    effective_season_year = SeasonHelper.effective_season_year()

    assert effective_season_year == now.year


def test_effective_season_year_this_year(ndb_stub) -> None:
    # Effective season should be this year
    today = datetime.today()
    Event(
        id="{}testendstomorrow".format(today.year),
        event_short="Ends Tomorrow",
        start_date=today,
        end_date=today + timedelta(days=1),
        event_type_enum=EventType.REGIONAL,
        year=today.year,
    ).put()
    effective_season_year = SeasonHelper.effective_season_year()

    assert effective_season_year == today.year


def test_effective_season_year_next_year(ndb_stub) -> None:
    # Effective season should be next year
    today = datetime.today()
    Event(
        id="{}testended".format(today.year),
        event_short="Test Ended",
        start_date=today - timedelta(days=2),
        end_date=today - timedelta(days=1),
        event_type_enum=EventType.REGIONAL,
        year=today.year,
    ).put()
    effective_season_year = SeasonHelper.effective_season_year()

    assert effective_season_year == today.year + 1


def test_effective_season_year_next_year_ignore_non_official(
    ndb_stub,
) -> None:
    # Effective season should be next year
    today = datetime.today()
    # Insert an event that has already happened - otherwise we'll default to the current season
    # This is to simulate offseason
    Event(
        id="{}testended".format(today.year),
        event_short="Test Ended",
        start_date=today - timedelta(days=2),
        end_date=today - timedelta(days=1),
        event_type_enum=EventType.REGIONAL,
        year=today.year,
    ).put()
    Event(
        id="{}testendstomorrow".format(today.year),
        event_short="testendstomorrow",
        start_date=today,
        end_date=today + timedelta(days=1),
        event_type_enum=EventType.OFFSEASON,
        year=today.year,
    ).put()
    effective_season_year = SeasonHelper.effective_season_year()

    assert effective_season_year == today.year + 1


def test_first_event_datetime_no_events(ndb_stub) -> None:
    first_event_datetime = SeasonHelper.first_event_datetime_utc()

    assert first_event_datetime is None


def test_first_event_datetime_one_event(ndb_stub) -> None:
    start_date = datetime(2020, 3, 1)
    Event(
        id="{}testfirst".format(start_date.year),
        event_short="First Event",
        start_date=start_date,
        end_date=start_date + timedelta(days=1),
        event_type_enum=EventType.REGIONAL,
        year=start_date.year,
    ).put()
    first_event_datetime = SeasonHelper.first_event_datetime_utc(start_date.year)

    assert first_event_datetime == start_date


def test_first_event_datetime_multiple_events(ndb_stub) -> None:
    start_date = datetime(2020, 3, 1)
    Event(
        id="{}testfirst".format(start_date.year),
        event_short="First Event",
        start_date=start_date,
        end_date=start_date + timedelta(days=1),
        event_type_enum=EventType.REGIONAL,
        year=start_date.year,
    ).put()
    Event(
        id="{}testsecond".format(start_date.year),
        event_short="Second Event",
        start_date=start_date + timedelta(days=1),
        end_date=start_date + timedelta(days=2),
        event_type_enum=EventType.REGIONAL,
        year=start_date.year,
    ).put()
    first_event_datetime = SeasonHelper.first_event_datetime_utc(start_date.year)

    assert first_event_datetime == start_date
