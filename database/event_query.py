from google.appengine.ext import ndb

from consts.district_type import DistrictType
from database.database_query import DatabaseQuery
from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class EventListQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'event_list_{}'  # (year)

    def __init__(self, year):
        self._query_args = (year, )

    @ndb.tasklet
    def _query_async(self, dict_version):
        year = self._query_args[0]
        events = yield Event.query(Event.year == year).fetch_async()
        raise ndb.Return(events)


class DistrictEventsQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'district_events_{}'  # (district_key)

    def __init__(self, district_key):
        self._query_args = (district_key, )

    @ndb.tasklet
    def _query_async(self, dict_version):
        district_key = self._query_args[0]
        year = int(district_key[:4])
        district_abbrev = district_key[4:]
        district_type = DistrictType.abbrevs.get(district_abbrev, None)
        events = yield Event.query(
            Event.event_district_enum == district_type,
            Event.year == year).fetch_async()
        raise ndb.Return(events)


class TeamEventsQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'team_events_{}'  # (team_key)

    def __init__(self, team_key):
        self._query_args = (team_key, )

    @ndb.tasklet
    def _query_async(self, dict_version):
        team_key = self._query_args[0]
        event_teams = yield EventTeam.query(EventTeam.team == ndb.Key(Team, team_key)).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        raise ndb.Return(events)


class TeamYearEventsQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'team_year_events_{}_{}'  # (team_key, year)

    def __init__(self, team_key, year):
        self._query_args = (team_key, year, )

    @ndb.tasklet
    def _query_async(self, dict_version):
        team_key = self._query_args[0]
        year = self._query_args[1]
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key),
            EventTeam.year == year).fetch_async()
        event_keys = map(lambda event_team: event_team.event, event_teams)
        events = yield ndb.get_multi_async(event_keys)
        raise ndb.Return(events)
