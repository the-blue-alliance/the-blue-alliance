import csv
import json
import logging
import StringIO
import os
import urllib
import uuid
import webapp2

from datetime import datetime

from google.appengine.api import memcache, urlfetch
from google.appengine.ext import deferred, ndb
from google.appengine.ext.webapp import template

import tba_config
from helpers.api_helper import ApiHelper

from models.event import Event
from models.sitevar import Sitevar
from models.team import Team


# used for deferred call
def track_call(api_action, api_details, x_tba_app_id):
    analytics_id = Sitevar.get_by_id("google_analytics.id")
    if analytics_id is None:
        logging.warning(
            "Missing sitevar: google_analytics.id. Can't track API usage.")
    else:
        GOOGLE_ANALYTICS_ID = analytics_id.contents['GOOGLE_ANALYTICS_ID']
        params = urllib.urlencode({
            'v':
            1,
            'tid':
            GOOGLE_ANALYTICS_ID,
            'cid':
            uuid.uuid3(uuid.NAMESPACE_X500, str(x_tba_app_id)),
            't':
            'event',
            'ec':
            'api',
            'ea':
            api_action,
            'el':
            api_details,
            'cd1':
            x_tba_app_id,  # custom dimension 1
            'ni':
            1,
            'sc':
            'end',  # forces tracking session to end
        })

        # Sets up the call
        analytics_url = 'http://www.google-analytics.com/collect?%s' % params
        urlfetch.fetch(
            url=analytics_url,
            method=urlfetch.GET,
            deadline=10,
        )


class ApiDeprecatedController(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.response.headers.add_header("content-type", "application/json")

    def get(self, _):
        self.response.out.write(
            json.dumps({
                "Error":
                "As of Jan. 2 2015, v1 of the TBA API has been deprecated. Please see http://www.thebluealliance.com/apidocs for more info."
            }))
        self.response.headers['Cache-Control'] = "public, max-age=%d" % (
            60 * 60 * 24 * 7)  # 1 week
        self.response.headers['Pragma'] = 'Public'


# Note: generally caching for the API happens in ApiHelper
class MainApiHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        # Need to initialize a webapp2 instance
        self.initialize(request, response)
        self.response.headers.add_header("content-type", "application/json")
        self.response.headers['Access-Control-Allow-Origin'] = '*'

    def handle_exception(self, exception, debug):
        """
        Handle an HTTP exception and actually write out a response.
        Called by webapp when abort() is called, stops code excution.
        """
        logging.info(exception)
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
            self.response.out.write(self._errors)
        else:
            self.response.set_status(500)

    def _track_call_defer(self, api_action, api_details=''):
        deferred.defer(
            track_call,
            api_action,
            api_details,
            self.x_tba_app_id,
            _queue="api-track-call")

    def _validate_tba_app_id(self):
        """
        Tests the presence of a X-TBA-App-Id header or URL param.
        """
        self.x_tba_app_id = self.request.headers.get("X-TBA-App-Id")
        if self.x_tba_app_id is None:
            self.x_tba_app_id = self.request.get('X-TBA-App-Id')

        logging.info("X-TBA-App-ID: {}".format(self.x_tba_app_id))
        if not self.x_tba_app_id:
            self._errors = json.dumps({
                "Error":
                "X-TBA-App-Id is a required header or URL param. Please see http://www.thebluealliance.com/apidocs for more info."
            })
            self.abort(400)

        x_tba_app_id_parts = self.x_tba_app_id.split(':')

        if len(x_tba_app_id_parts) != 3 or any(
                len(part) == 0 for part in x_tba_app_id_parts):
            self._errors = json.dumps({
                "Error":
                "X-TBA-App-Id must follow a specific format. Please see http://www.thebluealliance.com/apidocs for more info."
            })
            self.abort(400)


class CsvTeamsAll(MainApiHandler):
    """
    Outputs a CSV of all team information in the database, designed for other apps to bulk-import data.
    """

    def get(self):
        self._validate_tba_app_id()
        memcache_key = "csv_teams_all"
        output = memcache.get(memcache_key)

        if output is None:
            team_keys = Team.query().order(Team.team_number).fetch(
                10000, keys_only=True)
            team_futures = ndb.get_multi_async(team_keys)

            sio = StringIO.StringIO()
            writer = csv.writer(sio, delimiter=',')
            writer.writerow(
                ['team_number', 'name', 'nickname', 'location', 'website'])

            for team_future in team_futures:
                team = team_future.get_result()
                row = [
                    team.team_number, team.name, team.nickname, team.location,
                    team.website
                ]
                row_utf8 = [unicode(e).encode('utf-8') for e in row]
                writer.writerow(row_utf8)

            output = sio.getvalue()

            if tba_config.CONFIG["memcache"]:
                memcache.set(memcache_key, output, 86400)

        self.response.headers["content-type"] = "text/csv"
        self.response.out.write(output)

        self._track_call_defer('teams/list')
