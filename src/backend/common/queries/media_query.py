from typing import cast, List

from google.cloud import ndb

from backend.common.consts.media_tag import MediaTag
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, TeamKey, Year
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.media_converter import (
    MediaConverter,
    MediaDict,
)
from backend.common.tasklets import typed_tasklet


class TeamSocialMediaQuery(CachedDatabaseQuery[List[Media], List[MediaDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "team_social_media_{team_key}"
    DICT_CONVERTER = MediaConverter

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> List[Media]:
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key),
            Media.year == None,  # noqa: E711
        ).fetch_async()
        return medias


class TeamMediaQuery(CachedDatabaseQuery[List[Media], List[MediaDict]]):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "team_media_{team_key}"
    DICT_CONVERTER = MediaConverter

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> List[Media]:
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key)
        ).fetch_async()
        return medias


class TeamYearMediaQuery(CachedDatabaseQuery[List[Media], List[MediaDict]]):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "team_year_media_{team_key}_{year}"
    DICT_CONVERTER = MediaConverter

    def __init__(self, team_key: TeamKey, year: Year) -> None:
        super().__init__(team_key=team_key, year=year)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey, year: Year) -> List[Media]:
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key), Media.year == year
        ).fetch_async()
        return medias


class EventTeamsMediasQuery(CachedDatabaseQuery[List[Media], List[MediaDict]]):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "event_teams_medias_{event_key}"
    DICT_CONVERTER = MediaConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> List[Media]:
        year = int(event_key[:4])
        event_team_keys = yield EventTeam.query(
            EventTeam.event == ndb.Key(Event, event_key)
        ).fetch_async(keys_only=True)
        if not event_team_keys:
            return []
        team_keys = list(
            map(
                lambda event_team_key: ndb.Key(Team, event_team_key.id().split("_")[1]),
                event_team_keys,
            )
        )
        medias = yield Media.query(
            cast(ndb.KeyProperty, Media.references).IN(team_keys), Media.year == year
        ).fetch_async()
        return medias


class EventTeamsPreferredMediasQuery(CachedDatabaseQuery[List[Media], List[MediaDict]]):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "event_teams_medias_preferred_{event_key}"
    DICT_CONVERTER = MediaConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> List[Media]:
        year = int(event_key[:4])
        event_team_keys = yield EventTeam.query(
            EventTeam.event == ndb.Key(Event, event_key)
        ).fetch_async(keys_only=True)
        if not event_team_keys:
            return []
        team_keys = list(
            map(
                lambda event_team_key: ndb.Key(Team, event_team_key.id().split("_")[1]),
                event_team_keys,
            )
        )
        medias = yield Media.query(
            cast(ndb.KeyProperty, Media.preferred_references).IN(team_keys),
            Media.year == year,
        ).fetch_async()
        return medias


class EventMediasQuery(CachedDatabaseQuery[List[Media], List[MediaDict]]):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "event_medias_{event_key}"
    DICT_CONVERTER = MediaConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> List[Media]:
        medias = yield Media.query(
            Media.references == ndb.Key(Event, event_key)
        ).fetch_async()
        return medias


class TeamTagMediasQuery(CachedDatabaseQuery[List[Media], List[MediaDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "team_tag_medias_{team_key}_{media_tag}"
    DICT_CONVERTER = MediaConverter

    def __init__(self, team_key: TeamKey, media_tag: MediaTag) -> None:
        super().__init__(team_key=team_key, media_tag=media_tag)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey, media_tag: MediaTag) -> List[Media]:
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key),
            Media.media_tag_enum == media_tag,
        ).fetch_async()
        return medias


class TeamYearTagMediasQuery(CachedDatabaseQuery[List[Media], List[MediaDict]]):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "team_year_tag_medias_{team_key}_{year}_{media_tag}"
    DICT_CONVERTER = MediaConverter

    def __init__(self, team_key: TeamKey, year: Year, media_tag: MediaTag) -> None:
        super().__init__(team_key=team_key, year=year, media_tag=media_tag)

    @typed_tasklet
    def _query_async(
        self, team_key: TeamKey, year: Year, media_tag: MediaTag
    ) -> List[Media]:
        team_ndb_key = ndb.Key(Team, team_key)
        medias = yield Media.query(
            Media.references == team_ndb_key,
            Media.year == year,
            Media.media_tag_enum == media_tag,
        ).fetch_async()
        return medias
