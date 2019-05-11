from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from database.dict_converters.match_converter import MatchConverter
from models.event import Event
from models.match import Match


class MatchQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'match_{}'  # (match_key)
    DICT_CONVERTER = MatchConverter

    @ndb.tasklet
    def _query_async(self):
        match_key = self._query_args[0]
        match = yield Match.get_by_id_async(match_key)
        raise ndb.Return(match)


class EventMatchesQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'event_matches_{}'  # (event_key)
    DICT_CONVERTER = MatchConverter

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        match_keys = yield Match.query(Match.event == ndb.Key(Event, event_key)).fetch_async(keys_only=True)
        matches = yield ndb.get_multi_async(match_keys)
        raise ndb.Return(filter(None, matches))


class TeamEventMatchesQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'team_event_matches_{}_{}'  # (team_key, event_key)
    DICT_CONVERTER = MatchConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        event_key = self._query_args[1]
        match_keys = yield Match.query(
            Match.team_key_names == team_key,
            Match.event == ndb.Key(Event, event_key)).fetch_async(keys_only=True)
        matches = yield ndb.get_multi_async(match_keys)
        raise ndb.Return(filter(None, matches))


class TeamYearMatchesQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'team_year_matches_{}_{}'  # (team_key, year)
    DICT_CONVERTER = MatchConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        year = self._query_args[1]
        match_keys = yield Match.query(
            Match.team_key_names == team_key,
            Match.year == year).fetch_async(keys_only=True)
        matches = yield ndb.get_multi_async(match_keys)
        raise ndb.Return(filter(None, matches))
