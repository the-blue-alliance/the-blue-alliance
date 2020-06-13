from google.cloud import ndb
from backend.common.queries.database_query import DatabaseQuery
from backend.common.models.event import Event
from backend.common.futures import TypedFuture
from typing import List, Optional


class EventQuery(DatabaseQuery[Optional[Event]]):
    @ndb.tasklet
    def _query_async(self, event_key: str) -> TypedFuture[Optional[Event]]:
        event = yield Event.get_by_id_async(event_key)
        return event


class EventListQuery(DatabaseQuery[List[Event]]):
    @ndb.tasklet
    def _query_async(self, year: int) -> TypedFuture[List[Event]]:
        events = yield Event.query(Event.year == year).fetch_async()
        return events


"""
class DistrictEventsQuery(DatabaseQuery[List[Event]]):

    @ndb.tasklet
    def _query_async(self, distict_key: str) -> TypedFuture[List[Event]]:
        events = yield Event.query(
            Event.district_key == ndb.Key(District, district_key)).fetch_async()
        return events


class TeamEventsQuery(DatabaseQuery[List[Event]]):

    @ndb.tasklet
    def _query_async(self, team_key: str) -> TypedFuture[List[Event]]:
        event_teams = yield EventTeam.query(EventTeam.team == ndb.Key(Team, team_key)).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        return events


class TeamYearEventsQuery(DatabaseQuery[List[Event]]):

    @ndb.tasklet
    def _query_async(self, team_key: str, year: int) -> TypedFuture[List[Event]]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key),
            EventTeam.year == year).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        return events


class TeamYearEventTeamsQuery(DatabaseQuery[List[EventTeam]]):

    @ndb.tasklet
    def _query_async(self, team_key: str, year: int) -> TypedFuture[List[EventTeam]]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key),
            EventTeam.year == year).fetch_async()
        return event_teams
"""


class EventDivisionsQuery(DatabaseQuery[List[TypedFuture[Event]]]):
    @ndb.tasklet
    def _query_async(self, event_key: str) -> List[TypedFuture[Event]]:
        event = yield Event.get_by_id_async(event_key)
        if event is None:
            return []
        divisions = yield ndb.get_multi_async(event.divisions)
        return list(divisions)
