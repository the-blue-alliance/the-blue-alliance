from typing import List, Optional

from google.cloud import ndb

from backend.common.models.event import Event
from backend.common.models.keys import EventKey, MatchKey, TeamKey, Year
from backend.common.models.match import Match
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.match_converter import (
    MatchConverter,
    MatchDict,
)
from backend.common.tasklets import typed_tasklet


class MatchQuery(CachedDatabaseQuery[Optional[Match], Optional[MatchDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "match_{match_key}"
    MODEL_CACHING_ENABLED = False  # No need to cache a point query
    DICT_CONVERTER = MatchConverter

    def __init__(self, match_key: MatchKey) -> None:
        super().__init__(match_key=match_key)

    @typed_tasklet
    def _query_async(self, match_key: MatchKey) -> Optional[Match]:
        match = yield Match.get_by_id_async(match_key)
        return match


class EventMatchesQuery(CachedDatabaseQuery[List[Match], List[MatchDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "event_matches_{event_key}"
    DICT_CONVERTER = MatchConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> List[Match]:
        match_keys = yield Match.query(
            Match.event == ndb.Key(Event, event_key)
        ).fetch_async(keys_only=True)
        matches = yield ndb.get_multi_async(match_keys)
        return list(filter(None, matches))


class TeamEventMatchesQuery(CachedDatabaseQuery[List[Match], List[MatchDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "team_event_matches_{team_key}_{event_key}"
    DICT_CONVERTER = MatchConverter

    def __init__(self, team_key: TeamKey, event_key: EventKey) -> None:
        super().__init__(team_key=team_key, event_key=event_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey, event_key: EventKey) -> List[Match]:
        match_keys = yield Match.query(
            Match.team_key_names == team_key, Match.event == ndb.Key(Event, event_key)
        ).fetch_async(keys_only=True)
        matches = yield ndb.get_multi_async(match_keys)
        return list(filter(None, matches))


class TeamYearMatchesQuery(CachedDatabaseQuery[List[Match], List[MatchDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "team_year_matches_{team_key}_{year}"
    DICT_CONVERTER = MatchConverter

    def __init__(self, team_key: TeamKey, year: Year) -> None:
        super().__init__(team_key=team_key, year=year)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey, year: Year) -> List[Match]:
        match_keys = yield Match.query(
            Match.team_key_names == team_key, Match.year == year
        ).fetch_async(keys_only=True)
        matches = yield ndb.get_multi_async(match_keys)
        return list(filter(None, matches))
