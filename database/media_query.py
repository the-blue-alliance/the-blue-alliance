from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from models.media import Media
from models.team import Team


class TeamYearMediaQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_year_media_{}_{}'  # (team_key, year)

    def __init__(self, team_key, year):
        self._query_args = (team_key, year, )

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        year = self._query_args[1]
        medias = yield Media.query(
            Media.references == ndb.Key(Team, team_key),
            Media.year == year).fetch_async()
        raise ndb.Return(medias)
