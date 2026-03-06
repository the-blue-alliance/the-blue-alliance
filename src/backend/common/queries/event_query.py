from typing import Any, Generator, List, Optional

from google.appengine.ext import ndb

from backend.common.consts.event_type import (
    EventType,
    SEASON_EVENT_TYPES,
)
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import DistrictKey, EventKey, TeamKey, Year
from backend.common.models.team import Team
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.event_converter import (
    EventConverter,
    EventDict,
)
from backend.common.tasklets import typed_tasklet


class EventQuery(CachedDatabaseQuery[Optional[Event], Optional[EventDict]]):
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "event_{event_key}"
    MODEL_CACHING_ENABLED = False  # No need to cache a point query
    DICT_CONVERTER = EventConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> Generator[Any, Any, Optional[Event]]:
        event = yield Event.get_by_id_async(event_key)
        return event


class EventListQuery(CachedDatabaseQuery[List[Event], List[EventDict]]):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "event_list_{year}"
    DICT_CONVERTER = EventConverter

    def __init__(self, year: Year) -> None:
        super().__init__(year=year)

    @typed_tasklet
    def _query_async(self, year: Year) -> Generator[Any, Any, List[Event]]:
        events = yield Event.query(Event.year == year).fetch_async()
        return events


class DistrictEventsQuery(CachedDatabaseQuery[List[Event], List[EventDict]]):
    CACHE_VERSION = 5
    CACHE_KEY_FORMAT = "district_events_{district_key}"
    DICT_CONVERTER = EventConverter

    def __init__(self, district_key: DistrictKey) -> None:
        super().__init__(district_key=district_key)

    @typed_tasklet
    def _query_async(
        self, district_key: DistrictKey
    ) -> Generator[Any, Any, List[Event]]:
        events = yield Event.query(
            Event.district_key == ndb.Key(District, district_key)
        ).fetch_async()
        return events


class RegionalEventsQuery(CachedDatabaseQuery[List[Event], List[EventDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "regional_events_{year}"
    DICT_CONVERTER = EventConverter

    def __init__(self, year: Year) -> None:
        super().__init__(year=year)

    @typed_tasklet
    def _query_async(self, year: Year) -> Generator[Any, Any, List[Event]]:
        events = yield Event.query(
            Event.event_type_enum == EventType.REGIONAL, Event.year == year
        ).fetch_async()
        return events


class DistrictChampsInYearQuery(CachedDatabaseQuery[List[Event], List[EventDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "district_list_{year}"
    DICT_CONVERTER = EventConverter

    def __init__(self, year: Year) -> None:
        super().__init__(year=year)

    @typed_tasklet
    def _query_async(self, year: Year) -> Generator[Any, Any, List[Event]]:
        all_cmp_event_keys = yield Event.query(
            Event.year == year, Event.event_type_enum == EventType.DISTRICT_CMP
        ).fetch_async(keys_only=True)
        events = yield ndb.get_multi_async(all_cmp_event_keys)
        return list(events)


class CmpDivisionsInYearQuery(CachedDatabaseQuery[List[Event], List[EventDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "cmp_division_events_{year}"
    DICT_CONVERTER = EventConverter

    def __init__(self, year: Year) -> None:
        super().__init__(year=year)

    @typed_tasklet
    def _query_async(self, year: Year) -> Generator[Any, Any, List[Event]]:
        all_cmp_event_keys = yield Event.query(
            Event.year == year, Event.event_type_enum == EventType.CMP_DIVISION
        ).fetch_async(keys_only=True)
        events = yield ndb.get_multi_async(all_cmp_event_keys)
        return list(events)


class TeamEventsQuery(CachedDatabaseQuery[List[Event], List[EventDict]]):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "team_events_{team_key}"
    DICT_CONVERTER = EventConverter

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> Generator[Any, Any, List[Event]]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key)
        ).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        return list(events)


class TeamYearEventsQuery(CachedDatabaseQuery[List[Event], List[EventDict]]):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "team_year_events_{team_key}_{year}"
    DICT_CONVERTER = EventConverter

    def __init__(self, team_key: TeamKey, year: Year) -> None:
        super().__init__(team_key=team_key, year=year)

    @typed_tasklet
    def _query_async(
        self, team_key: TeamKey, year: Year
    ) -> Generator[Any, Any, List[Event]]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key), EventTeam.year == year
        ).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        return list(events)


class TeamYearEventTeamsQuery(CachedDatabaseQuery[List[EventTeam], None]):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "team_year_eventteams_{team_key}_{year}"
    DICT_CONVERTER = None

    def __init__(self, team_key: TeamKey, year: Year) -> None:
        super().__init__(team_key=team_key, year=year)

    @typed_tasklet
    def _query_async(
        self, team_key: TeamKey, year: Year
    ) -> Generator[Any, Any, List[EventTeam]]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key), EventTeam.year == year
        ).fetch_async()
        return event_teams


class EventDivisionsQuery(CachedDatabaseQuery[List[Event], List[EventDict]]):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "event_divisions_{event_key}"
    DICT_CONVERTER = EventConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> Generator[Any, Any, List[Event]]:
        event = yield Event.get_by_id_async(event_key)
        if event is None:
            return []
        divisions = yield ndb.get_multi_async(event.divisions)
        return list(divisions)


class LastSeasonEventQuery(CachedDatabaseQuery[Optional[Event], Optional[EventDict]]):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "last_season_event_list_{year}"
    DICT_CONVERTER = EventConverter

    def __init__(self, year: Year) -> None:
        super().__init__(year=year)

    @typed_tasklet
    def _query_async(self, year: Year) -> Generator[Any, Any, Optional[Event]]:
        events = (
            yield Event.query(
                Event.year == year, Event.event_type_enum.IN(SEASON_EVENT_TYPES)
            )
            .order(-Event.end_date)
            .fetch_async(1)
        )
        events = list(events)
        if not events:
            return None
        return events[0]
