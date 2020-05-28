from google.appengine.ext import ndb

from consts.district_type import DistrictType
from database.database_query import DatabaseQuery
from database.dict_converters.event_converter import EventConverter
from models.district import District
from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class EventQuery(DatabaseQuery):
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = 'event_{}'  # (event_key)
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        event = yield Event.get_by_id_async(event_key)
        raise ndb.Return(event)


class EventListQuery(DatabaseQuery):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = 'event_list_{}'  # (year)
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self):
        year = self._query_args[0]
        events = yield Event.query(Event.year == year).fetch_async()
        raise ndb.Return(events)


class DistrictEventsQuery(DatabaseQuery):
    CACHE_VERSION = 5
    CACHE_KEY_FORMAT = 'district_events_{}'  # (district_key)
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self):
        district_key = self._query_args[0]
        events = yield Event.query(
            Event.district_key == ndb.Key(District, district_key)).fetch_async()
        raise ndb.Return(events)


class TeamEventsQuery(DatabaseQuery):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = 'team_events_{}'  # (team_key)
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        event_teams = yield EventTeam.query(EventTeam.team == ndb.Key(Team, team_key)).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        raise ndb.Return(events)


class TeamYearEventsQuery(DatabaseQuery):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = 'team_year_events_{}_{}'  # (team_key, year)
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        year = self._query_args[1]
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key),
            EventTeam.year == year).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        raise ndb.Return(events)


class TeamYearEventTeamsQuery(DatabaseQuery):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = 'team_year_eventteams_{}_{}'  # (team_key, year)

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        year = self._query_args[1]
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key),
            EventTeam.year == year).fetch_async()
        raise ndb.Return(event_teams)


class EventDivisionsQuery(DatabaseQuery):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "event_divisions_{}"  # (event_key)
    DICT_CONVERTER = EventConverter

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        event = yield Event.get_by_id_async(event_key)
        divisions = yield ndb.get_multi_async(event.divisions)
        raise ndb.Return(divisions)
