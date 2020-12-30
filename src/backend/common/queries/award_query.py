from typing import List

from google.cloud import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, TeamKey, Year
from backend.common.models.team import Team
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.award_converter import (
    AwardConverter,
    AwardDict,
)
from backend.common.tasklets import typed_tasklet


class EventAwardsQuery(CachedDatabaseQuery[List[Award], List[AwardDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "event_awards_{event_key}"
    DICT_CONVERTER = AwardConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> List[Award]:
        awards = yield Award.query(
            Award.event == ndb.Key(Event, event_key)
        ).fetch_async()
        return awards


class TeamAwardsQuery(CachedDatabaseQuery[List[Award], List[AwardDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "team_awards_{team_key}"
    DICT_CONVERTER = AwardConverter

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> List[Award]:
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key)
        ).fetch_async()
        return awards


class TeamYearAwardsQuery(CachedDatabaseQuery[List[Award], List[AwardDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "team_year_awards_{team_key}_{year}"
    DICT_CONVERTER = AwardConverter

    def __init__(self, team_key: TeamKey, year: Year) -> None:
        super().__init__(team_key=team_key, year=year)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey, year: Year) -> List[Award]:
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key), Award.year == year
        ).fetch_async()
        return awards


class TeamEventAwardsQuery(CachedDatabaseQuery[List[Award], List[AwardDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "team_event_awards_{team_key}_{event_key}"
    DICT_CONVERTER = AwardConverter

    def __init__(self, team_key: TeamKey, event_key: EventKey) -> None:
        super().__init__(team_key=team_key, event_key=event_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey, event_key: EventKey) -> List[Award]:
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key),
            Award.event == ndb.Key(Event, event_key),
        ).fetch_async()
        return awards


class TeamEventTypeAwardsQuery(CachedDatabaseQuery[List[Award], List[AwardDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = (
        "team_events_type_tag_awards_{team_key}_{event_type}_{award_type}"
    )
    DICT_CONVERTER = AwardConverter

    def __init__(
        self, team_key: TeamKey, event_type: EventType, award_type: AwardType
    ) -> None:
        super().__init__(
            team_key=team_key, event_type=event_type, award_type=award_type
        )

    @typed_tasklet
    def _query_async(
        self, team_key: TeamKey, event_type: EventType, award_type: AwardType
    ) -> List[Award]:
        awards = yield Award.query(
            Award.team_list == ndb.Key(Team, team_key),
            Award.event_type_enum == event_type,
            Award.award_type_enum == award_type,
        ).fetch_async()
        return awards
