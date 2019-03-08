import MySQLdb
import MySQLdb.cursors
import logging
import os

from google.appengine.ext import ndb

import tba_config
from database.database_query import DatabaseQuery
from models.cached_query_result import CachedQueryResult
from models.sitevar import Sitevar


class BaseCloudSqlQuery(DatabaseQuery):

    SCRUB_SQL_COLUMNS = []
    FETCH_CHUCK_SIZE = 50

    # Based on the GAE/CloudSQL documentation:
    # https://cloud.google.com/appengine/docs/standard/python/cloud-sql/using-cloud-sql-mysql
    def _connect_to_cloudsql(self):
        secrets_sitevar = Sitevar.get_by_id('google.secrets')
        cloudsql_connection = secrets_sitevar.contents.get('sql_connection', '')
        cloudsql_db = secrets_sitevar.contents.get('sql_db', '')
        cloudsql_user = secrets_sitevar.contents.get('sql_user', '')
        cloudsql_pass = secrets_sitevar.contents.get('sql_pass', '')
        # When deployed to App Engine, the `SERVER_SOFTWARE` environment variable
        # will be set to 'Google App Engine/version'.
        if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
            # Connect using the unix socket located at
            # /cloudsql/cloudsql-connection-name.
            cloudsql_unix_socket = os.path.join(
                '/cloudsql', cloudsql_connection)

            db = MySQLdb.connect(
                unix_socket=cloudsql_unix_socket,
                user=cloudsql_user,
                passwd=cloudsql_pass,
                cursorclass=MySQLdb.cursors.SSDictCursor,
                db=cloudsql_db)

        # If the unix socket is unavailable, then try to connect using TCP. This
        # will work if you're running a local MySQL server or using the Cloud SQL
        # proxy, for example:
        #
        #   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
        #
        else:
            db = MySQLdb.connect(
                host='127.0.0.1',
                user=cloudsql_user,
                passwd=cloudsql_pass,
                cursorclass=MySQLdb.cursors.SSDictCursor,
                db=cloudsql_db)

        return db

    def _query_cloud_sql(self, connection, query):
        cursor = connection.cursor()
        cursor.execute(query)

        while True:
            result = cursor.fetchmany(self.FETCH_CHUCK_SIZE)
            if not result:
                break

            # Filter out wall_time because it won't be consistent if we backfill, etc
            for r in result:
                if 'wall_time' in r:
                    del r['wall_time']
                yield r

        cursor.close()

    def _query_async(self):
        db = None
        rows = []
        query_result = []
        try:
            query = self._build_query()
            db = self._connect_to_cloudsql()
            rows = self._query_cloud_sql(db, query)

            result_to_cache = None
            for row_dict in rows:
                for column in self.SCRUB_SQL_COLUMNS:
                    del row_dict[column]
                query_result.append(row_dict)
        except Exception:
            logging.info("Error querying CloudSQL")
        finally:
            if db:
                db.close()
        result_future = ndb.Future()
        result_future.set_result(query_result)
        return result_future


class MatchGdcvDataQuery(BaseCloudSqlQuery):
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = 'match_timeseries_{}'

    def _build_query(self):
        match_key = self._query_args[0]
        event_key = match_key.split('_')[0]
        match_id = match_key.split('_')[1]
        year = int(event_key[:4])
        query = """SELECT * FROM {}_matches
            WHERE event_key = '{}' AND match_id = '{}' AND (mode = 'auto' OR mode = 'teleop')
            ORDER BY wall_time ASC""".format(year, event_key, match_id)

        return query


class EventMatchesGdcvDataQuery(BaseCloudSqlQuery):
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = 'event_matches_timeseries_{}'

    def _build_query(self):
        event_key = self._query_args[0]
        year = int(event_key[:4])
        query = """SELECT event_key, match_id, COUNT(*) FROM {}_matches
            WHERE event_key = '{}' AND (mode = 'auto' OR mode = 'teleop')
            GROUP BY event_key, match_id""".format(year, event_key)

        return query
