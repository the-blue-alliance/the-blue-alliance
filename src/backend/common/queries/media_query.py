from typing import List, Union

from google.cloud import ndb

from backend.common.consts.media_tag import MediaTag
from backend.common.futures import TypedFuture
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, TeamKey, Year
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.database_query import DatabaseQuery
from backend.common.queries.dict_converters.media_converter import MediaConverter


class TeamSocialMediaQuery(DatabaseQuery[List[Media]]):
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self, team_key: TeamKey) -> TypedFuture[List[Media]]:
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key),
            Media.year == None,  # noqa: E711
        ).fetch_async()
        return medias


class TeamMediaQuery(DatabaseQuery[List[Media]]):
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self, team_key: TeamKey) -> TypedFuture[List[Media]]:
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key)
        ).fetch_async()
        return medias


class TeamYearMediaQuery(DatabaseQuery[List[Media]]):
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self, team_key: TeamKey, year: Year) -> TypedFuture[List[Media]]:
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key), Media.year == year
        ).fetch_async()
        return medias


class EventTeamsMediasQuery(DatabaseQuery[List[Media]]):
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(
        self, event_key: EventKey
    ) -> Union[List[Media], TypedFuture[List[Media]]]:
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
            Media.references.IN(team_keys), Media.year == year
        ).fetch_async()
        return medias


class EventTeamsPreferredMediasQuery(DatabaseQuery[List[Media]]):
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(
        self, event_key: EventKey
    ) -> Union[List[Media], TypedFuture[List[Media]]]:
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
            Media.preferred_references.IN(team_keys), Media.year == year
        ).fetch_async()
        return medias


class EventMediasQuery(DatabaseQuery[List[Media]]):
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self, event_key: EventKey) -> TypedFuture[List[Media]]:
        medias = yield Media.query(
            Media.references == ndb.Key(Event, event_key)
        ).fetch_async()
        return medias


class TeamTagMediasQuery(DatabaseQuery[List[Media]]):
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self, team_key: TeamKey, media_tag: MediaTag):
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key),
            Media.media_tag_enum == media_tag,
        ).fetch_async()
        return medias


class TeamYearTagMediasQuery(DatabaseQuery[List[Media]]):
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(
        self, team_key: TeamKey, year: Year, media_tag: MediaTag
    ) -> TypedFuture[List[Media]]:
        team_ndb_key = ndb.Key(Team, team_key)
        medias = yield Media.query(
            Media.references == team_ndb_key,
            Media.year == year,
            Media.media_tag_enum == media_tag,
        ).fetch_async()
        return medias
