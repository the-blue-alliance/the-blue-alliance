from typing import List

from google.cloud import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.futures import TypedFuture
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.team import Team
from backend.common.queries.database_query import DatabaseQuery
from backend.common.queries.dict_converters.award_converter import AwardConverter


class EventAwardsQuery(DatabaseQuery[List[Award]]):
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(self, event_key: EventKey) -> TypedFuture[List[Award]]:
        awards = yield Award.query(
            Award.event == ndb.Key(Event, event_key)
        ).fetch_async()
        return awards


class TeamAwardsQuery(DatabaseQuery[List[Award]]):
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(self, team_key: TeamKey) -> TypedFuture[List[Award]]:
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key)
        ).fetch_async()
        return awards


class TeamYearAwardsQuery(DatabaseQuery[List[Award]]):
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(self, team_key: TeamKey, year: int) -> TypedFuture[List[Award]]:
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key), Award.year == year
        ).fetch_async()
        return awards


class TeamEventAwardsQuery(DatabaseQuery[List[Award]]):
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(
        self, team_key: TeamKey, event_key: EventKey
    ) -> TypedFuture[List[Award]]:
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key),
            Award.event == ndb.Key(Event, event_key),
        ).fetch_async()
        return awards


class TeamEventTypeAwardsQuery(DatabaseQuery[List[Award]]):
    DICT_CONVERTER = AwardConverter

    @ndb.tasklet
    def _query_async(
        self, team_key: TeamKey, event_type: EventType, award_type: AwardType
    ) -> TypedFuture[List[Award]]:
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key),
            Award.event_type_enum == event_type,
            Award.award_type_enum == award_type,
        ).fetch_async()
        return awards
