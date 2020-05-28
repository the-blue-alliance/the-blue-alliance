from google.appengine.ext import ndb

from consts.district_type import DistrictType
from database.dict_converters.district_converter import DistrictConverter
from database.dict_converters.team_converter import TeamConverter
from database.database_query import DatabaseQuery
from models.district import District
from models.district_team import DistrictTeam
from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class TeamQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'team_{}'  # (team_key)
    DICT_CONVERTER = TeamConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        team = yield Team.get_by_id_async(team_key)
        raise ndb.Return(team)


class TeamListQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'team_list_{}'  # (page_num)
    PAGE_SIZE = 500
    DICT_CONVERTER = TeamConverter

    @ndb.tasklet
    def _query_async(self):
        page_num = self._query_args[0]
        start = self.PAGE_SIZE * page_num
        end = start + self.PAGE_SIZE
        teams = yield Team.query(Team.team_number >= start, Team.team_number < end).fetch_async()
        raise ndb.Return(teams)


class TeamListYearQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'team_list_year_{}_{}'  # (year, page_num)
    DICT_CONVERTER = TeamConverter

    @ndb.tasklet
    def _query_async(self):
        year = self._query_args[0]
        page_num = self._query_args[1]

        event_team_keys_future = EventTeam.query(EventTeam.year == year).fetch_async(keys_only=True)
        teams_future = TeamListQuery(page_num).fetch_async()

        year_team_keys = set()
        for et_key in event_team_keys_future.get_result():
            team_key = et_key.id().split('_')[1]
            year_team_keys.add(team_key)

        teams = filter(lambda team: team.key.id() in year_team_keys, teams_future.get_result())
        raise ndb.Return(teams)


class DistrictTeamsQuery(DatabaseQuery):
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = 'district_teams_{}'  # (district_key)
    DICT_CONVERTER = TeamConverter

    @ndb.tasklet
    def _query_async(self):
        district_key = self._query_args[0]
        district_teams = yield DistrictTeam.query(
            DistrictTeam.district_key == ndb.Key(District, district_key)).fetch_async()
        team_keys = map(lambda district_team: district_team.team, district_teams)
        teams = yield ndb.get_multi_async(team_keys)
        raise ndb.Return(teams)


class EventTeamsQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'event_teams_{}'  # (event_key)
    DICT_CONVERTER = TeamConverter

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        event_teams = yield EventTeam.query(EventTeam.event == ndb.Key(Event, event_key)).fetch_async()
        team_keys = map(lambda event_team: event_team.team, event_teams)
        teams = yield ndb.get_multi_async(team_keys)
        raise ndb.Return(teams)


class EventEventTeamsQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'event_eventteams_{}'  # (event_key)

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        event_teams = yield EventTeam.query(EventTeam.event == ndb.Key(Event, event_key)).fetch_async()
        raise ndb.Return(event_teams)


class TeamParticipationQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'team_participation_{}'  # (team_key)

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        event_teams = yield EventTeam.query(EventTeam.team == ndb.Key(Team, team_key)).fetch_async(keys_only=True)
        years = map(lambda event_team: int(event_team.id()[:4]), event_teams)
        raise ndb.Return(set(years))


class TeamDistrictsQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'team_districts_{}'  # (team_key)
    DICT_CONVERTER = DistrictConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        district_team_keys = yield DistrictTeam.query(DistrictTeam.team == ndb.Key(Team, team_key)).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async([ndb.Key(District, dtk.id().split('_')[0]) for dtk in district_team_keys])
        raise ndb.Return(filter(lambda x: x is not None, districts))
