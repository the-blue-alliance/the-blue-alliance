from backend.common.models.team import Team
from backend.common.typed_future import TypedFuture
from backend.common.queries.database_query import DatabaseQuery
from backend.common.queries.dict_converters.team_converter import TeamConverter
from google.cloud import ndb
from typing import List


class TeamQuery(DatabaseQuery[Team]):
    DICT_CONVERTER = TeamConverter

    @ndb.tasklet
    def _query_async(self, team_key: str) -> TypedFuture[Team]:
        team = yield Team.get_by_id_async(team_key)
        raise ndb.Return(team)


class TeamListQuery(DatabaseQuery[List[Team]]):
    DICT_CONVERTER = TeamConverter
    PAGE_SIZE: int = 500

    @ndb.tasklet
    def _query_async(self, page: int) -> TypedFuture[List[Team]]:
        start = self.PAGE_SIZE * page
        end = start + self.PAGE_SIZE
        teams = (
            yield Team.query(Team.team_number >= start, Team.team_number < end)
            .order(Team.team_number)
            .fetch_async()
        )
        return teams
