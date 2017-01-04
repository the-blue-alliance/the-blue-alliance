from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from helpers.model_to_dict import ModelToDict
from models.event import Event
from models.match import Match


class EventMatchesQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_matches_{}'  # (event_key)

    def __init__(self, event_key):
        self._query_args = (event_key, )

    @ndb.tasklet
    def _query_async(self, dict_version):
        event_key = self._query_args[0]
        match_keys = yield Match.query(Match.event == ndb.Key(Event, event_key)).fetch_async(keys_only=True)
        matches = yield ndb.get_multi_async(match_keys)
        raise ndb.Return(matches)


class TeamEventMatchesQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_event_matches_{}_{}'  # (team_key, event_key)

    def __init__(self, team_key, event_key):
        self._query_args = (team_key, event_key, )

    @ndb.tasklet
    def _query_async(self, dict_version):
        team_key = self._query_args[0]
        event_key = self._query_args[1]
        match_keys = yield Match.query(
            Match.team_key_names == team_key,
            Match.event == ndb.Key(Event, event_key)).fetch_async(keys_only=True)
        matches = yield ndb.get_multi_async(match_keys)
        if dict_version:
            matches = ModelToDict.convertMatches(matches, dict_version)
        raise ndb.Return(matches)


class TeamYearMatchesQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_year_matches_{}_{}'  # (team_key, year)

    def __init__(self, team_key, year):
        self._query_args = (team_key, year, )

    @ndb.tasklet
    def _query_async(self, dict_version):
        team_key = self._query_args[0]
        year = self._query_args[1]
        match_keys = yield Match.query(
            Match.team_key_names == team_key,
            Match.year == year).fetch_async(keys_only=True)
        matches = yield ndb.get_multi_async(match_keys)
        if dict_version:
            matches = ModelToDict.convertMatches(matches, dict_version)
        raise ndb.Return(matches)
