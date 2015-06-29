from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from models.award import Award
from models.cached_query_result import CachedQueryResult
from models.event import Event
from models.event_team import EventTeam
from models.match import Match


class EventListQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_list_{}'  # (year)

    def __init__(self, year):
        self._query_args = (year, )

    @ndb.tasklet
    def _query_async(self):
        year = self._query_args[0]
        events = yield Event.query(Event.year == year).fetch_async()
        raise ndb.Return(events)


class EventAwardsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_awards_{}'  # (event_key)

    def __init__(self, event_key):
        self._query_args = (event_key, )

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        awards = yield Award.query(Award.event == ndb.Key(Event, event_key)).fetch_async()
        raise ndb.Return(awards)


class EventMatchesQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_matches_{}'  # (event_key)

    def __init__(self, event_key):
        self._query_args = (event_key, )

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        matches = yield Match.query(Match.event == ndb.Key(Event, event_key)).fetch_async()
        raise ndb.Return(matches)


class EventTeamsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_teams_{}'  # (event_key)

    def __init__(self, event_key):
        self._query_args = (event_key, )

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        event_teams = yield EventTeam.query(EventTeam.event == ndb.Key(Event, event_key)).fetch_async()
        team_keys = map(lambda event_team: event_team.team, event_teams)
        teams = yield ndb.get_multi_async(team_keys)
        raise ndb.Return(teams)
