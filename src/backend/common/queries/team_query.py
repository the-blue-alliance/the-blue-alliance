from typing import List, Optional, Set

from google.cloud import ndb

from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import DistrictKey, EventKey, TeamKey, Year
from backend.common.models.team import Team
from backend.common.queries.database_query import DatabaseQuery
from backend.common.queries.dict_converters.team_converter import TeamConverter
from backend.common.tasklets import typed_tasklet


class TeamQuery(DatabaseQuery[Optional[Team]]):
    DICT_CONVERTER = TeamConverter

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> Optional[Team]:
        team = yield Team.get_by_id_async(team_key)
        return team


class TeamListQuery(DatabaseQuery[List[Team]]):
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
        return teams


class TeamListYearQuery(DatabaseQuery[List[Team]]):
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


class DistrictTeamsQuery(DatabaseQuery[List[Team]]):
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


class EventTeamsQuery(DatabaseQuery[List[Team]]):
    DICT_CONVERTER = TeamConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> List[Team]:
        event_teams = yield EventTeam.query(
            EventTeam.event == ndb.Key(Event, event_key)
        ).fetch_async()
        team_keys = map(lambda event_team: event_team.team, event_teams)
        teams = yield ndb.get_multi_async(team_keys)
        return list(teams)


class EventEventTeamsQuery(DatabaseQuery[List[EventTeam]]):
    DICT_CONVERTER = TeamConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> List[EventTeam]:
        event_teams = yield EventTeam.query(
            EventTeam.event == ndb.Key(Event, event_key)
        ).fetch_async()
        return event_teams


class TeamParticipationQuery(DatabaseQuery[Set[int]]):
    DICT_CONVERTER = TeamConverter

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> Set[int]:
        event_teams = yield EventTeam.query(
            EventTeam.team == ndb.Key(Team, team_key)
        ).fetch_async(keys_only=True)
        years = map(lambda event_team: int(event_team.id()[:4]), event_teams)
        return set(years)
