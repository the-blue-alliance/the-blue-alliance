from google.appengine.ext import ndb

from consts.district_type import DistrictType
from database.database_query import DatabaseQuery
from helpers.model_to_dict import ModelToDict
from models.district_team import DistrictTeam
from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class TeamListQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'team_list_{}'  # (page_num)
    PAGE_SIZE = 500

    def __init__(self, page_num):
        self._query_args = (page_num, )

    @ndb.tasklet
    def _query_async(self, api_version):
        page_num = self._query_args[0]
        start = self.PAGE_SIZE * page_num
        end = start + self.PAGE_SIZE
        teams = yield Team.query(Team.team_number >= start, Team.team_number < end).fetch_async()
        if api_version:
            converter = ModelToDict.teamConverter(api_version)
            teams = map(converter, teams)
        raise ndb.Return(teams)


class TeamListYearQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'team_list_year_{}_{}'  # (year, page_num)

    def __init__(self, year, page_num):
        self._query_args = (year, page_num, )

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
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'district_teams_{}'  # (district_key)

    def __init__(self, district_key):
        self._query_args = (district_key, )

    @ndb.tasklet
    def _query_async(self):
        district_key = self._query_args[0]
        year = int(district_key[:4])
        district_abbrev = district_key[4:]
        district_type = DistrictType.abbrevs.get(district_abbrev, None)
        district_teams = yield DistrictTeam.query(
            DistrictTeam.year == year,
            DistrictTeam.district == district_type).fetch_async()
        team_keys = map(lambda district_team: district_team.team, district_teams)
        teams = yield ndb.get_multi_async(team_keys)
        raise ndb.Return(teams)


class EventTeamsQuery(DatabaseQuery):
    CACHE_VERSION = 1
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


class TeamParticipationQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_participation_{}'  # (team_key)

    def __init__(self, team_key):
        self._query_args = (team_key, )

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        event_teams = yield EventTeam.query(EventTeam.team == ndb.Key(Team, team_key)).fetch_async(keys_only=True)
        years = map(lambda event_team: int(event_team.id()[:4]), event_teams)
        raise ndb.Return(set(years))


class TeamDistrictsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_districts_{}'  # (team_key)

    def __init__(self, team_key):
        self._query_args = (team_key, )

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        district_team_keys = yield DistrictTeam.query(DistrictTeam.team == ndb.Key(Team, team_key)).fetch_async(keys_only=True)
        ret = {}
        for district_team_key in district_team_keys:
            district_key = district_team_key.id().split('_')[0]
            year = int(district_key[:4])
            ret[year] = district_key

        raise ndb.Return(ret)
