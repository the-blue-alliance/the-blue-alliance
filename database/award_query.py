from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from database.dict_converters.award_converter import AwardConverter
from models.award import Award
from models.event import Event
from models.team import Team


class EventAwardsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_awards_{}'  # (event_key)
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        awards = yield Award.query(Award.event == ndb.Key(Event, event_key)).fetch_async()
        raise ndb.Return(awards)


class TeamAwardsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_awards_{}'  # (team_key)
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key)).fetch_async()
        raise ndb.Return(awards)


class TeamYearAwardsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_year_awards_{}_{}'  # (team_key, year)
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        year = self._query_args[1]
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key),
            Award.year == year).fetch_async()
        raise ndb.Return(awards)


class TeamEventAwardsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_event_awards_{}_{}'  # (team_key, event_key)
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        event_key = self._query_args[1]
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key),
            Award.event == ndb.Key(Event, event_key)).fetch_async()
        raise ndb.Return(awards)


class TeamEventTypeAwardsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_events_type_tag_awards_{}_{}_{}'  # (team_key, event_type_enum, award_type_enum)
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        event_type_enum = self._query_args[1]
        award_type_enum = self._query_args[2]
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key),
            Award.event_type_enum == event_type_enum,
            Award.award_type_enum == award_type_enum).fetch_async()
        raise ndb.Return(awards)
