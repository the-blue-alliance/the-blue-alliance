from typing import List, Optional

from google.cloud import ndb

from backend.common.consts.event_type import EventType
from backend.common.futures import TypedFuture
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import DistrictKey, EventKey, TeamKey
from backend.common.models.team import Team
from backend.common.queries.database_query import DatabaseQuery
from backend.common.queries.dict_converters.event_converter import EventConverter


class EventQuery(DatabaseQuery[Optional[Event]]):
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self, event_key: EventKey) -> TypedFuture[Optional[Event]]:
        event = yield Event.get_by_id_async(event_key)
        return event


class EventListQuery(DatabaseQuery[List[Event]]):
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self, year: int) -> TypedFuture[List[Event]]:
        events = yield Event.query(Event.year == year).fetch_async()
        return events


class DistrictEventsQuery(DatabaseQuery[List[Event]]):
    @ndb.tasklet
    def _query_async(self, district_key: DistrictKey) -> TypedFuture[List[Event]]:
        events = yield Event.query(
            Event.district_key == ndb.Key(District, district_key)
        ).fetch_async()
        return events


class DistrictChampsInYearQuery(DatabaseQuery[List[Event]]):
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self, year: int) -> List[Event]:
        all_cmp_event_keys = yield Event.query(
            Event.year == year, Event.event_type_enum == EventType.DISTRICT_CMP
        ).fetch_async(keys_only=True)
        events = yield ndb.get_multi_async(all_cmp_event_keys)
        return list(events)


class TeamEventsQuery(DatabaseQuery[List[Event]]):
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self, team_key: TeamKey) -> List[Event]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key)
        ).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        return list(events)


class TeamYearEventsQuery(DatabaseQuery[List[Event]]):
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self, team_key: TeamKey, year: int) -> List[Event]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key), EventTeam.year == year
        ).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        return list(events)


class TeamYearEventTeamsQuery(DatabaseQuery[List[EventTeam]]):
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(
        self, team_key: TeamKey, year: int
    ) -> TypedFuture[List[EventTeam]]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key), EventTeam.year == year
        ).fetch_async()
        return event_teams


class EventDivisionsQuery(DatabaseQuery[List[Event]]):
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self, event_key: EventKey) -> List[Event]:
        event = yield Event.get_by_id_async(event_key)
        if event is None:
            return []
        divisions = yield ndb.get_multi_async(event.divisions)
        return list(divisions)
