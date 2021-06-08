import itertools
import math
from typing import List, Optional, Set

from google.cloud import ndb

from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import DistrictKey, EventKey, TeamKey, Year
from backend.common.models.team import Team
from backend.common.queries.database_query import CachedDatabaseQuery, DatabaseQuery
from backend.common.queries.dict_converters.team_converter import (
    TeamConverter,
    TeamDict,
)
from backend.common.tasklets import typed_tasklet


def get_team_page_num(team_key: str) -> int:
    return int(int(team_key[3:]) / TeamListQuery.PAGE_SIZE)


class TeamQuery(CachedDatabaseQuery[Optional[Team], Optional[TeamDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "team_{team_key}"
    MODEL_CACHING_ENABLED = False  # No need to cache a point query
    DICT_CONVERTER = TeamConverter

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> Optional[Team]:
        team = yield Team.get_by_id_async(team_key)
        return team


class TeamListQuery(CachedDatabaseQuery[List[Team], List[TeamDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "team_list_{page}"
    DICT_CONVERTER = TeamConverter
    PAGE_SIZE: int = 500

    def __init__(self, page: int) -> None:
        super().__init__(page=page)

    @typed_tasklet
    def _query_async(self, page: int) -> List[Team]:
        start = self.PAGE_SIZE * page
        end = start + self.PAGE_SIZE
        teams = (
            yield Team.query(Team.team_number >= start, Team.team_number < end)
            .order(Team.team_number)
            .fetch_async()
        )
        return list(teams)


class TeamListYearQuery(CachedDatabaseQuery[List[Team], List[TeamDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "team_list_year_{year}_{page}"
    DICT_CONVERTER = TeamConverter

    def __init__(self, year: Year, page: int) -> None:
        super().__init__(year=year, page=page)

    @typed_tasklet
    def _query_async(self, year: Year, page: int) -> List[Team]:
        event_team_keys_future = EventTeam.query(EventTeam.year == year).fetch_async(
            keys_only=True
        )
        teams_future = TeamListQuery(page=page).fetch_async()

        year_team_keys = set()
        for et_key in event_team_keys_future.get_result():
            team_key = et_key.id().split("_")[1]
            year_team_keys.add(team_key)

        teams = filter(
            lambda team: team.key.id() in year_team_keys, teams_future.get_result()
        )
        return list(teams)


# TODO: Paginate
class DistrictTeamsQuery(CachedDatabaseQuery[List[Team], List[TeamDict]]):
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "district_teams_{district_key}"
    DICT_CONVERTER = TeamConverter

    def __init__(self, district_key: DistrictKey) -> None:
        super().__init__(district_key=district_key)

    @typed_tasklet
    def _query_async(self, district_key: DistrictKey) -> List[Team]:
        district_teams = yield DistrictTeam.query(
            DistrictTeam.district_key == ndb.Key(District, district_key)
        ).fetch_async()
        team_keys = map(lambda district_team: district_team.team, district_teams)
        teams = yield ndb.get_multi_async(team_keys)
        return list(teams)


class EventTeamsQuery(PaginatedDatabaseQuery[List[ndb.Key], List[Team], List[TeamDict]]):

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    # # TODO: Do this with generics...
    # def _build_query(self, event_key: EventKey) -> ndb.query.Query:
    #     return EventTeam.query(
    #         EventTeam.event == ndb.Key(Event, event_key)
    #     )

    @typed_tasklet
    def _query_async(self, results: List[EventTeam]) -> List[Team]:
        event_team_keys = yield query.fetch_async(limit=self.PAGE_SIZE, offset=offset, keys_only=True)
        team_keys = map(
            lambda event_team_key: ndb.Key(Team, event_team_key.id().split("_")[1]),
            event_team_keys,
        )
        teams = yield ndb.get_multi_async(team_keys)
        return list(teams)


class _EventTeamsPageQuery(CachedDatabaseQuery[List[Team], List[TeamDict]]):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "event_teams_{event_key}_{page}"
    DICT_CONVERTER = TeamConverter
    PAGE_SIZE: int = 500

    def __init__(self, event_key: EventKey, page: int) -> None:
        super().__init__(event_key=event_key, page=page)


# TODO: Paginate
class EventEventTeamsQuery(CachedDatabaseQuery[List[EventTeam], List[TeamDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "event_event_teams_{event_key}"
    DICT_CONVERTER = TeamConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> List[EventTeam]:
        event_teams = yield EventTeam.query(
            EventTeam.event == ndb.Key(Event, event_key)
        ).fetch_async()
        return event_teams


class TeamParticipationQuery(CachedDatabaseQuery[Set[int], None]):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "team_participation_{team_key}"

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> Set[int]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key)
        ).fetch_async(keys_only=True)
        years = map(lambda event_team: int(event_team.id()[:4]), event_teams)
        return set(years)


"""
class TeamDistrictsQuery(CachedDatabaseQuery[List[District], List[TeamDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'team_districts_{}'  # (team_key)
    DICT_CONVERTER = DistrictConverter

    @ndb.tasklet
    def _query_async(self, team_key: str) -> List[District]:
        team_key = self._query_args[0]
        district_team_keys = yield DistrictTeam.query(DistrictTeam.team == ndb.Key(Team, team_key)).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async([ndb.Key(District, dtk.id().split('_')[0]) for dtk in district_team_keys])
        return filter(lambda x: x is not None, districts)
"""
