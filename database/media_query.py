from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from database.dict_converters.media_converter import MediaConverter
from models.event import Event
from models.event_team import EventTeam
from models.media import Media
from models.team import Team


class TeamSocialMediaQuery(DatabaseQuery):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = 'team_social_media_{}'  # (team_key)
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key),
            Media.year == None).fetch_async()
        raise ndb.Return(medias)


class TeamMediaQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'team_media_{}'  # (team_key)
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key)).fetch_async()
        raise ndb.Return(medias)


class TeamYearMediaQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'team_year_media_{}_{}'  # (team_key, year)
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        year = self._query_args[1]
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key),
            Media.year == year).fetch_async()
        raise ndb.Return(medias)


class EventTeamsMediasQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'event_teams_medias_{}'  # (event_key)
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        year = int(event_key[:4])
        event_team_keys = yield EventTeam.query(EventTeam.event == ndb.Key(Event, event_key)).fetch_async(keys_only=True)
        if not event_team_keys:
            raise ndb.Return([])
        team_keys = map(lambda event_team_key: ndb.Key(Team, event_team_key.id().split('_')[1]), event_team_keys)
        medias = yield Media.query(
            Media.references.IN(team_keys),
            Media.year == year).fetch_async()
        raise ndb.Return(medias)


class EventTeamsPreferredMediasQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'event_teams_medias_preferred_{}'  # (event_key)
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        year = int(event_key[:4])
        event_team_keys = yield EventTeam.query(EventTeam.event == ndb.Key(Event, event_key)).fetch_async(keys_only=True)
        if not event_team_keys:
            raise ndb.Return([])
        team_keys = map(lambda event_team_key: ndb.Key(Team, event_team_key.id().split('_')[1]), event_team_keys)
        medias = yield Media.query(
            Media.preferred_references.IN(team_keys),
            Media.year == year).fetch_async()
        raise ndb.Return(medias)


class EventMediasQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'event_medias_{}'  # (event_key)
    DICT_CONVERTER = None

    @ndb.tasklet
    def _query_async(self):
        event_key = ndb.Key(Event, self._query_args[0])
        medias = yield Media.query(Media.references == event_key).fetch_async()
        raise ndb.Return(medias)


class TeamTagMediasQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_tag_medias_{}_{}'  # (team_key, media_tag_enum)
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = ndb.Key(Team, self._query_args[0])
        media_tag_enum = self._query_args[1]
        medias = yield Media.query(
            Media.references == team_key,
            Media.media_tag_enum == media_tag_enum).fetch_async()
        raise ndb.Return(medias)


class TeamYearTagMediasQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_year_tag_medias_{}_{}_{}'  # (team_key, year, media_tag_enum)
    DICT_CONVERTER = MediaConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = ndb.Key(Team, self._query_args[0])
        year = self._query_args[1]
        media_tag_enum = self._query_args[2]
        medias = yield Media.query(
            Media.references == team_key,
            Media.year == year,
            Media.media_tag_enum == media_tag_enum).fetch_async()
        raise ndb.Return(medias)
