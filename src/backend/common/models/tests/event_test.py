import json
from datetime import datetime, timedelta
from typing import Optional
from unittest import mock

import pytest
import pytz
from freezegun import freeze_time
from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_sync_type import EventSyncType
from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.models.alliance import EventAlliance
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_district_points import EventDistrictPoints
from backend.common.models.event_ranking import EventRanking
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import Year
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.models.tests.util import (
    CITY_STATE_COUNTRY_PARAMETERS,
    LOCATION_PARAMETERS,
)
from backend.conftest import clear_cached_queries  # noqa: ETBA0


@pytest.mark.parametrize("key", ["2010ct", "2014onto2", "202121fim", "2022dc305"])
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
    e = Event(
        timezone_id=timezone_id,
    )

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
    e = Event(
        timezone_id=timezone_id,
    )

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
    e = Event(
        start_date=event_start,
        end_date=event_end,
    )

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
def test_within_a_day(
    mock_time: str,
    is_within: bool,
) -> None:
    e = Event(
        start_date=datetime(2020, 2, 1),
        end_date=datetime(2020, 2, 5),
    )

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
def test_now(
    mock_time: str,
    timezone: Optional[str],
    is_now: bool,
) -> None:
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
    e = Event(
        start_date=datetime(2020, 2, 1),
        end_date=datetime(2020, 2, 5),
    )

    with freeze_time(mock_time):
        assert e.past == is_past
        assert e.future == is_future
        assert e.starts_today == start_today
        assert e.ends_today == end_today


def test_default_sync_overrides() -> None:
    e = Event()
    assert e.sync_overrides is None


def test_should_skip_eventteams_explicit_config() -> None:
    e = Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=EventType.OFFSEASON,
        sync_overrides={"skip_eventteams": True},
        start_date=datetime(2023, 4, 1),
        end_date=datetime(2023, 4, 4),
    )

    assert e.should_skip_eventteams() is True


@pytest.mark.parametrize(
    "event_type,division_count,date_str,should_skip",
    [
        (EventType.DISTRICT_CMP, 2, "2023-04-01", True),
        (EventType.CMP_FINALS, 4, "2023-04-01", True),
        (EventType.DISTRICT_CMP, 2, "2023-05-01", True),
        (EventType.CMP_FINALS, 2, "2023-05-01", True),
        (EventType.DISTRICT_CMP, 2, "2023-03-01", False),
        (EventType.CMP_FINALS, 2, "2023-03-01", False),
        (EventType.DISTRICT_CMP, 0, "2023-04-01", False),
        (EventType.DISTRICT_CMP, 0, "2023-05-01", False),
        (EventType.OFFSEASON, 2, "2023-04-01", False),
    ],
)
def test_should_skip_eventteams_automatic_cases(
    event_type: EventType, division_count: int, date_str: str, should_skip: bool
) -> None:
    e = Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=event_type,
        divisions=[
            ndb.Key(Event, f"2023test{i}") for i in range(1, division_count + 1)
        ],
        start_date=datetime(2023, 4, 1),
        end_date=datetime(2023, 4, 4),
    )

    with freeze_time(date_str):
        assert e.should_skip_eventteams() == should_skip


@pytest.mark.parametrize(
    "year, event_type, official, week, week_output, week_str",
    [
        # Don't forget that weeks are zero indexed :)
        (2020, EventType.REGIONAL, True, 2, 2, "Week 3"),
        (2016, EventType.REGIONAL, True, 0, 0, "Week 0.5"),
        (2016, EventType.REGIONAL, True, 1, 1, "Week 1"),
        (2020, EventType.OFFSEASON, False, 2, None, None),
        (2020, EventType.REGIONAL, False, 2, None, None),
        (2021, EventType.REGIONAL, True, 0, 0, "Participation"),
        (2021, EventType.DISTRICT, True, 0, 0, "Participation"),
        (2021, EventType.REMOTE, True, 6, 6, "FIRST Innovation Challenge"),
        (2021, EventType.REMOTE, True, 7, 7, "INFINITE RECHARGE At Home Challenge"),
        (2021, EventType.REMOTE, True, 8, 8, "Game Design Challenge"),
        (2021, EventType.REMOTE, True, 5, 5, "Awards"),
    ],
)
def test_week(
    year: Year,
    event_type: EventType,
    official: bool,
    week: int,
    week_output: int,
    week_str: str,
) -> None:
    e = Event(
        year=year,
        event_type_enum=event_type,
        official=official,
    )
    e._week = week

    assert e.week == week_output
    assert e.week_str == week_str


def test_week_stored_in_context_cache() -> None:
    e = Event(
        id="2019test",
        year=2019,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(2019, 3, 1),
        event_short="test",
    )
    e.put()

    assert e.week == 0

    from backend.common.context_cache import context_cache

    assert context_cache.get("2019_season_start") == datetime(2019, 3, 4, 0, 0)


def test_week_falsy_zero_short_circuit() -> None:
    e = Event(
        year=2020,
        event_type_enum=EventType.REGIONAL,
        official=True,
    )
    e._week = 0

    from backend.common.context_cache import context_cache

    assert context_cache.get("2020_season_start") is None

    # Should return 0 immediately without computing or caching season_start
    assert e.week == 0
    assert context_cache.get("2020_season_start") is None


@pytest.mark.no_bypass_first_event_start_dates
def test_week_from_hardcoded_season_helper() -> None:
    # 2024 has start date hardcoded in SeasonHelper (2024-02-24, Saturday -> season_start = 2024-02-26)
    # Event starting on 2024-03-08 is Week 1 (11 days after 2024-02-26 -> 11 // 7 = 1)
    e = Event(
        id="2024test",
        year=2024,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(2024, 3, 8),
        event_short="test",
    )
    # e is NOT put into Datastore, demonstrating hardcoded date is used without querying Datastore

    assert e.week == 1

    from backend.common.context_cache import context_cache

    assert context_cache.get("2024_season_start") == datetime(2024, 2, 26, 0, 0)


def test_week_fallback_unlisted_year() -> None:
    # Year 2099 is not in SeasonHelper.FIRST_EVENT_START_DATES
    # It must fall back to querying Datastore
    e = Event(
        id="2099test",
        year=2099,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(2099, 3, 2),  # 2099-03-02 is a Monday
        event_short="test",
    )
    e.put()

    assert e.week == 0

    from backend.common.context_cache import context_cache

    assert context_cache.get("2099_season_start") == datetime(2099, 3, 2, 0, 0)


@pytest.mark.parametrize(LOCATION_PARAMETERS[0], LOCATION_PARAMETERS[1])
def test_location(
    city: str, state: str, country: str, postalcode: str, output: str
) -> None:
    event = Event(
        city=city,
        state_prov=state,
        country=country,
        postalcode=postalcode,
    )
    assert event.location == output


@pytest.mark.parametrize(
    CITY_STATE_COUNTRY_PARAMETERS[0], CITY_STATE_COUNTRY_PARAMETERS[1]
)
def test_city_state_country(city: str, state: str, country: str, output: str) -> None:
    event = Event(
        city=city,
        state_prov=state,
        country=country,
    )
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


def test_webcasts_sorted_chronologically() -> None:
    event = Event(
        start_date=datetime(2026, 3, 3),
        end_date=datetime(2026, 3, 5),
        webcast_json=json.dumps(
            [
                {"type": "twitch", "channel": "day2_stream", "date": "2026-03-04"},
                {"type": "twitch", "channel": "day3_stream", "date": "2026-03-05"},
                {"type": "twitch", "channel": "day1_stream", "date": "2026-03-03"},
                {"type": "twitch", "channel": "firstinspires", "date": "2026-03-05"},
                {"type": "youtube", "channel": "all_days"},
            ]
        ),
    )
    webcasts = event.webcast
    assert len(webcasts) == 5
    # firstinspires sorts first regardless of date
    assert webcasts[0]["channel"] == "firstinspires"
    # Then by date ascending
    assert webcasts[1]["channel"] == "day1_stream"
    assert webcasts[2]["channel"] == "day2_stream"
    assert webcasts[3]["channel"] == "day3_stream"
    # No-date webcasts sort last
    assert webcasts[4]["channel"] == "all_days"


def test_linked_district() -> None:
    District(
        id="2019ne",
        display_name="New England",
        year=2019,
        abbreviation="ne",
    ).put()
    event = Event(
        district_key=ndb.Key(District, "2019ne"),
    )
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


def test_get_awards() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.awards == []

    a = Award(
        id="2019ct_1",
        year=2019,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2019ct"),
        name_str="Winner",
    )
    a.put()

    event._awards_future = None
    clear_cached_queries()
    assert event.awards == [a]

    event._awards_future = None
    clear_cached_queries()
    assert event.awards == [a]


def test_details() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.details is None

    d = EventDetails(
        id="2019ct",
    )
    d.put()

    event.clear_details()
    clear_cached_queries()
    assert event.details == d

    event.clear_details()
    clear_cached_queries()
    assert event.details == d


@pytest.mark.parametrize(
    "short_name, event_type_enum, expected",
    [
        # Normal case - suffix should be appended
        ("Archimedes", EventType.CMP_DIVISION, "Archimedes Division"),
        # 2002-style data where short_name already contains the suffix -
        # should not be duplicated. See #10206.
        ("Archimedes Division", EventType.CMP_DIVISION, "Archimedes Division"),
        (
            "Newton",
            EventType.DISTRICT_CMP_DIVISION,
            "Newton District Championship Division",
        ),
        (
            "Newton District Championship Division",
            EventType.DISTRICT_CMP_DIVISION,
            "Newton District Championship Division",
        ),
    ],
)
def test_normalized_name_division_suffix(
    short_name: str, event_type_enum: EventType, expected: str
) -> None:
    event = Event(
        id="2002cmp",
        year=2002,
        event_short="cmp",
        short_name=short_name,
        event_type_enum=event_type_enum,
    )
    assert event.normalized_name == expected


def test_first_api_code() -> None:
    # Pre-2023 regular event
    event = Event(id="2019ingre", year=2019, event_short="ingre")
    assert event.first_api_code == "ingre"

    # 2023 regular event
    event = Event(id="2023ingre", year=2023, event_short="ingre")
    assert event.first_api_code == "ingre"

    # Pre-2023 championship div
    event = Event(id="2022hop", year=2022, event_short="hop")
    assert event.first_api_code == "hopper"

    # 2023 championship div
    event = Event(id="2023hop", year=2023, event_short="hop")
    assert event.first_api_code == "hcmp"


def test_nexus_api_code() -> None:
    # Defaults to first_api_code
    event = Event(id="2023hop", year=2023, event_short="hop")
    assert event.nexus_api_code == "hcmp"

    # Inherits explicit FIRST override if Nexus override is unset
    event = Event(id="2019casj", year=2019, event_short="casj", first_code="caovr")
    assert event.nexus_api_code == "caovr"

    # Explicit Nexus override wins
    event = Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        first_code="caovr",
        nexus_code="nexovr",
    )
    assert event.nexus_api_code == "nexovr"


def test_get_alliances() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.alliance_selections is None

    teams = ["frc1", "frc2", "frc3"]
    alliances = [
        EventAlliance(picks=teams),
    ]
    EventDetails(
        id="2019ct",
        alliance_selections=alliances,
    ).put()

    event._details_future = None
    assert event.alliance_selections == alliances
    assert event.alliance_teams == teams


def test_get_alliances_with_backup() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.alliance_selections is None

    teams = ["frc1", "frc2", "frc3"]
    alliances = [
        EventAlliance(picks=teams, backup={"in": "frc4", "out": "frc3"}),
    ]
    EventDetails(
        id="2019ct",
        alliance_selections=alliances,
    ).put()

    event._details_future = None
    assert event.alliance_selections == alliances
    assert event.alliance_teams == (teams + ["frc4"])


def test_district_points() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.district_points is None

    points = EventDistrictPoints(points={}, tiebreakers={})
    EventDetails(
        id="2019ct",
        district_points=points,
    ).put()

    event._details_future = None
    assert event.district_points == points


def test_matches() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.matches == []

    event._matches_future = None
    assert event.matches == []

    m = Match(
        id="2019ct_qm1",
        event=ndb.Key(Event, "2019ct"),
        year=2019,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json="",
    )
    m.put()

    event._matches_future = None
    clear_cached_queries()
    assert event.matches == [m]


def test_teams() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.teams == []

    EventTeam(
        id="2019ct_frc1",
        event=ndb.Key(Event, "2019ct"),
        team=ndb.Key(Team, "frc1"),
        year=2019,
    ).put()
    t = Team(
        id="frc1",
        team_number=1,
    )
    t.put()

    event._teams_future = None
    clear_cached_queries()
    assert event.teams == [t]


def test_rankings() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.rankings is None

    rankings = [
        EventRanking(
            rank=1,
            team_key="frc1",
            record=None,
            qual_average=None,
            matches_played=1,
            dq=0,
            sort_orders=[],
        )
    ]

    EventDetails(id="2019ct", rankings2=rankings).put()

    event._details_future = None
    assert event.rankings == rankings


def test_venue_address():
    event = Event(
        id="2024cc",
        year=2024,
        event_short="cc",
        venue="Bellarmine College Preparatory",
        venue_address="Bellarmine College Preparatory\n960 W. Hedding St.\nSan Jose, CA, USA",
        city="San Jose",
        state_prov="CA",
        country="USA",
    )
    assert event.venue_or_venue_from_address == "Bellarmine College Preparatory"
    assert (
        event.venue_address_safe
        == "Bellarmine College Preparatory\n960 W. Hedding St.\nSan Jose, CA, USA"
    )

    event = Event(
        id="2024cabe",
        year=2024,
        event_short="cabe",
        venue="Berkeley High School",
        venue_address="1980 Allston Way",
        city="Berkeley",
        state_prov="CA",
        country="USA",
    )
    assert event.venue_or_venue_from_address == "Berkeley High School"
    assert (
        event.venue_address_safe
        == "Berkeley High School\n1980 Allston Way\nBerkeley, CA, USA"
    )


def test_sync_never_enabled_when_unofficial() -> None:
    event = Event(
        id="2024cc",
        year=2024,
        event_short="cc",
        official=False,
    )

    for sync_type in EventSyncType:
        assert (
            event.is_sync_enabled(sync_type) is False
        ), f"Sync should not be enabled for {sync_type} when not official"


def test_sync_always_enabled_with_null_mask() -> None:
    event = Event(
        id="2024cc",
        year=2024,
        event_short="cc",
        official=True,
        disable_sync_flags=None,
    )

    for sync_type in EventSyncType:
        assert (
            event.is_sync_enabled(sync_type) is True
        ), f"Sync should be enabled for {sync_type} when official"


def test_sync_always_enabled_with_zero_mask() -> None:
    event = Event(
        id="2024cc",
        year=2024,
        event_short="cc",
        official=True,
        disable_sync_flags=0,
    )

    for sync_type in EventSyncType:
        assert (
            event.is_sync_enabled(sync_type) is True
        ), f"Sync should be enabled for {sync_type} when official"


def test_disable_sync_by_mask() -> None:
    event = Event(
        id="2024cc",
        year=2024,
        event_short="cc",
        official=True,
        disable_sync_flags=(0 | EventSyncType.EVENT_ALLIANCES),
    )

    for sync_type in EventSyncType:
        expected = sync_type != EventSyncType.EVENT_ALLIANCES
        assert (
            event.is_sync_enabled(sync_type) == expected
        ), f"Sync should be {expected} for {sync_type} when official"


def test_time_as_utc_retries_out_of_nonexistent_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # pytz only raises for a DST gap when asked to disambiguate; simulate that
    # and make sure we fall back to the offset an hour later.
    tz = mock.Mock()
    tz.utcoffset.side_effect = [pytz.NonExistentTimeError(), timedelta(hours=-4)]
    monkeypatch.setattr(pytz, "timezone", lambda _: tz)

    e = Event(timezone_id="America/New_York")
    gap_time = datetime(2020, 3, 8, 2, 30)
    assert e.time_as_utc(gap_time) == datetime(2020, 3, 8, 6, 30)
    assert tz.utcoffset.call_args_list == [
        mock.call(gap_time),
        mock.call(gap_time + timedelta(hours=1)),
    ]


def test_local_time_retries_out_of_ambiguous_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tz = mock.Mock()
    tz.utcoffset.side_effect = [pytz.AmbiguousTimeError(), timedelta(hours=-5)]
    monkeypatch.setattr(pytz, "timezone", lambda _: tz)

    e = Event(timezone_id="America/New_York")
    with freeze_time("2020-11-01 01:30"):
        assert e.local_time() == datetime(2020, 10, 31, 20, 30)
    assert tz.utcoffset.call_args_list == [
        mock.call(datetime(2020, 11, 1, 1, 30)),
        mock.call(datetime(2020, 11, 1, 2, 30)),
    ]


def test_week_before_2018_starts_on_wednesday() -> None:
    # 2017-03-01 is a Wednesday, so it is the season start as-is (a Monday
    # based season would have snapped to 2017-02-27)
    e = Event(
        id="2017test",
        year=2017,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(2017, 3, 1),
        event_short="test",
    )
    e.put()

    assert e.week == 0

    from backend.common.context_cache import context_cache

    assert context_cache.get("2017_season_start") == datetime(2017, 3, 1, 0, 0)

    later = Event(
        id="2017later",
        year=2017,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(2017, 3, 10),
        event_short="later",
    )
    assert later.week == 1


def _webcast_status_event() -> Event:
    return Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        start_date=datetime(2020, 2, 1),
        end_date=datetime(2020, 2, 3),
        webcast_json=json.dumps(
            [
                {"type": "twitch", "channel": "one"},
                {"type": "twitch", "channel": "two"},
            ]
        ),
    )


@freeze_time("2020-02-02")
def test_webcast_status_offline() -> None:
    event = _webcast_status_event()
    assert event.webcast_status == "offline"


@freeze_time("2020-02-02")
def test_webcast_status_unknown() -> None:
    event = _webcast_status_event()
    event.webcast[0]["status"] = WebcastStatus.UNKNOWN
    assert event.webcast_status == "unknown"


@freeze_time("2020-02-02")
def test_webcast_status_online_wins() -> None:
    event = _webcast_status_event()
    event.webcast[0]["status"] = WebcastStatus.UNKNOWN
    event.webcast[1]["status"] = WebcastStatus.ONLINE
    assert event.webcast_status == "online"


@freeze_time("2020-02-02")
def test_webcast_status_skips_missing_webcasts() -> None:
    event = _webcast_status_event()
    with (
        mock.patch.object(Event, "_patch_webcast_online_status", return_value=None),
        mock.patch.object(
            Event,
            "current_webcasts",
            new_callable=mock.PropertyMock,
            return_value=[
                None,
                {"type": "twitch", "channel": "two", "status": "online"},
            ],
        ),
    ):
        assert event.webcast_status == "online"


def test_division_keys_json() -> None:
    event = Event(
        id="2019cmptx",
        divisions=[ndb.Key(Event, "2019carv"), ndb.Key(Event, "2019gal")],
    )
    assert event.division_keys_json == '["2019carv", "2019gal"]'
    assert Event(id="2019nyny").division_keys_json == "[]"


def test_urls() -> None:
    event = Event(id="2019nyny", year=2019, event_short="nyny", facebook_eid="12345")
    assert event.facebook_event_url == "http://www.facebook.com/event.php?eid=12345"
    assert event.details_url == "/event/2019nyny"


def test_gameday_url() -> None:
    no_webcast = Event(id="2019nyny", year=2019, event_short="nyny")
    assert no_webcast.gameday_url is None

    with_webcast = Event(
        id="2019nyny",
        year=2019,
        event_short="nyny",
        webcast_json=json.dumps([{"type": "twitch", "channel": "one"}]),
    )
    assert with_webcast.gameday_url == "/gameday/2019nyny"


@pytest.mark.parametrize(
    "event_type, expected",
    [
        (EventType.OFFSEASON, None),
        (EventType.PRESEASON, None),
        (
            EventType.CMP_DIVISION,
            "https://www.firstinspires.org/hubfs/web/event/2019/cmp/frc/public-schedule.pdf",
        ),
        (
            EventType.CMP_FINALS,
            "https://www.firstinspires.org/hubfs/web/event/2019/cmp/frc/public-schedule.pdf",
        ),
        (
            EventType.REGIONAL,
            "https://info.firstinspires.org/hubfs/web/event/frc/2019/2019_NYNY_Agenda.pdf",
        ),
        (
            EventType.DISTRICT,
            "https://info.firstinspires.org/hubfs/web/event/frc/2019/2019_NYNY_Agenda.pdf",
        ),
    ],
)
def test_public_agenda_url(event_type: EventType, expected: Optional[str]) -> None:
    event = Event(
        id="2019nyny", year=2019, event_short="nyny", event_type_enum=event_type
    )
    assert event.public_agenda_url == expected


def test_hashtag() -> None:
    event = Event(id="2019nyny", year=2019, event_short="nyny")
    assert event.hashtag == "frcnyny"
    event.custom_hashtag = "NYCRegional"
    assert event.hashtag == "NYCRegional"


def test_display_name() -> None:
    event = Event(id="2019nyny", name="New York City Regional")
    assert event.display_name == "New York City Regional"
    event.short_name = "New York City"
    assert event.display_name == "New York City"


@pytest.mark.parametrize(
    "year, expected",
    [(2016, "Championship"), (2017, "Houston Championship")],
)
def test_normalized_name_cmp_finals(year: int, expected: str) -> None:
    event = Event(
        id=f"{year}cmptx",
        year=year,
        event_short="cmptx",
        city="Houston",
        name="FIRST Championship - Einstein",
        event_type_enum=EventType.CMP_FINALS,
    )
    assert event.normalized_name == expected


def test_normalized_name_offseason_short_name() -> None:
    event = Event(
        id="2019iri",
        year=2019,
        event_short="iri",
        name="Indiana Robotics Invitational",
        short_name="IRI",
        event_type_enum=EventType.OFFSEASON,
    )
    assert event.normalized_name == "IRI"


def test_alliance_teams_no_alliances() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.alliance_teams == []


def test_details_passthrough_properties_without_details() -> None:
    event = Event(
        id="2019ct", year=2019, event_short="ct", event_type_enum=EventType.REGIONAL
    )
    assert event.regional_champs_pool_points is None
    assert event.playoff_advancement is None
    assert event.playoff_bracket is None
    assert event.matchstats is None
    assert event.coprs is None


def test_details_passthrough_properties_with_details() -> None:
    EventDetails(
        id="2019ct",
        regional_champs_pool_points={"points": {}, "tiebreakers": {}},
        matchstats={"oprs": {"254": 10.0}},
        coprs={"Total Points": {"254": 10.0}},
        playoff_advancement={"advancement": {"sf": []}, "bracket": {"sf": {}}},
    ).put()
    event = Event(
        id="2019ct", year=2019, event_short="ct", event_type_enum=EventType.REGIONAL
    )
    assert event.regional_champs_pool_points == {"points": {}, "tiebreakers": {}}
    assert event.playoff_advancement == {"sf": []}
    assert event.playoff_bracket == {"sf": {}}
    assert event.matchstats == {"oprs": {"254": 10.0}}
    assert event.coprs == {"Total Points": {"254": 10.0}}

    district_event = Event(
        id="2019ct", year=2019, event_short="ct", event_type_enum=EventType.DISTRICT
    )
    assert district_event.regional_champs_pool_points is None


def test_playoff_advancement_empty() -> None:
    EventDetails(id="2019ct").put()
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.playoff_advancement is None
    assert event.playoff_bracket is None


def test_clear_futures() -> None:
    event = Event(id="2019ct", year=2019, event_short="ct")
    assert event.matches == []
    assert event.awards == []
    assert event.teams == []
    event.clear_matches()
    event.clear_awards()
    event.clear_teams()
    assert event._matches_future is None
    assert event._awards_future is None
    assert event._teams_future is None


@pytest.mark.parametrize(
    "mock_time, divisions, expected",
    [
        ("2020-02-02", [], True),
        ("2020-01-26", [], False),
        ("2020-01-26", [ndb.Key(Event, "2020div1")], True),
        ("2020-01-20", [ndb.Key(Event, "2020div1")], False),
    ],
)
def test_should_use_short_cache(
    mock_time: str, divisions: list[ndb.Key], expected: bool
) -> None:
    event = Event(
        start_date=datetime(2020, 2, 1),
        end_date=datetime(2020, 2, 3),
        divisions=divisions,
    )
    with freeze_time(mock_time):
        assert event.should_use_short_cache is expected


def test_should_use_short_cache_parent_event() -> None:
    event = Event(
        start_date=datetime(2020, 2, 1),
        end_date=datetime(2020, 2, 3),
        parent_event=ndb.Key(Event, "2020cmp"),
    )
    with freeze_time("2020-01-26"):
        assert event.should_use_short_cache is True


def test_week_no_season_start() -> None:
    # No hardcoded start date for 1992 and no events in the datastore
    e = Event(
        id="1992test",
        year=1992,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(1992, 3, 1),
        event_short="test",
    )
    assert e.week is None


def test_venue_or_venue_from_address_without_venue() -> None:
    event = Event(venue_address="Some Gym\r\n1 Main St")
    assert event.venue_or_venue_from_address == "Some Gym"

    # No venue and no address: the AttributeError is swallowed
    assert Event().venue_or_venue_from_address is None


def test_venue_address_safe_without_venue_address() -> None:
    assert Event(city="Berkeley").venue_address_safe is None
    assert Event(venue="Some Gym").venue_address_safe is None


def test_bug_31_venue_address_safe_is_plain_text() -> None:
    """
    Bug #31: with no venue_address, Event.venue_address_safe formats the
    results of Python 2 era `.encode("utf-8")` calls, so the string contains
    bytes reprs: "b'Some Gym'\\nb'Berkeley, CA, USA'".

    Correct: plain text, "Some Gym\\nBerkeley, CA, USA".
    """
    event = Event(venue="Some Gym", city="Berkeley", state_prov="CA", country="USA")
    assert event.venue_address_safe == "Some Gym\nBerkeley, CA, USA"


@freeze_time("2020-02-02")
def test_webcast_status_patched_from_memcache() -> None:
    from backend.common.memcache_models.webcast_online_status_memcache import (
        WebcastOnlineStatusMemcache,
    )

    event = _webcast_status_event()
    WebcastOnlineStatusMemcache(event.webcast[0]).put(
        {
            "type": WebcastType.TWITCH,
            "channel": "one",
            "status": WebcastStatus.ONLINE,
            "stream_title": "Qualifications",
            "viewer_count": 100,
            "scheduled_start_time_utc": "2020-02-02T12:00:00Z",
        }
    )

    assert event.webcast_status == "online"
    assert event.webcast[0]["stream_title"] == "Qualifications"
    assert event.webcast[0]["viewer_count"] == 100
    assert event.webcast[0]["scheduled_start_time_utc"] == "2020-02-02T12:00:00Z"


@freeze_time("2020-02-02")
def test_webcast_status_patched_from_memcache_partial() -> None:
    from backend.common.memcache_models.webcast_online_status_memcache import (
        WebcastOnlineStatusMemcache,
    )

    event = _webcast_status_event()
    WebcastOnlineStatusMemcache(event.webcast[1]).put(
        {"type": WebcastType.TWITCH, "channel": "two"}
    )

    assert event.webcast_status == "offline"
    assert "status" not in event.webcast[1]


def test_render_key_name() -> None:
    assert Event.render_key_name(2019, "NYNY") == "2019nyny"


@pytest.mark.parametrize(
    "nexus_code, expected",
    [
        ("2026demo0755", "2026demo0755"),
        ("demo0755", "demo0755"),
        ("DEMO0755", "DEMO0755"),
        ("test", "2026test"),
    ],
)
def test_nexus_code_for_api(nexus_code: str, expected: str) -> None:
    event = Event(year=2026, event_short="test", nexus_code=nexus_code)
    assert event.nexus_code_for_api == expected
