import json
import logging
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
        logging.warning("Missing sitevar: google_analytics.id. Can't track API usage.")
    else:
        GOOGLE_ANALYTICS_ID = analytics_id.contents['GOOGLE_ANALYTICS_ID']
        params = urllib.urlencode({
            'v': 1,
            'tid': GOOGLE_ANALYTICS_ID,
            'cid': uuid.uuid3(uuid.NAMESPACE_X500, str(x_tba_app_id)),
            't': 'event',
            'ec': 'api',
            'ea': api_action,
            'el': api_details,
            'cd1': x_tba_app_id,  # custom dimension 1
            'ni': 1,
            'sc': 'end',  # forces tracking session to end
        })

        # Sets up the call
        analytics_url = 'http://www.google-analytics.com/collect?%s' % params
        urlfetch.fetch(
            url=analytics_url,
            method=urlfetch.GET,
            deadline=10,
        )


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
        deferred.defer(track_call, api_action, api_details, self.x_tba_app_id)

    def _validate_tba_app_id(self):
        """
        Tests the presence of a X-TBA-App-Id header or URL param.
        """
        self.x_tba_app_id = self.request.headers.get("X-TBA-App-Id")
        if self.x_tba_app_id is None:
            self.x_tba_app_id = self.request.get('X-TBA-App-Id')

        logging.info("X-TBA-App-ID: {}".format(self.x_tba_app_id))
        if not self.x_tba_app_id:
            self._errors = json.dumps({"Error": "X-TBA-App-Id is a required header or URL param. Please see http://www.thebluealliance.com/apidocs for more info."})
            self.abort(400)
        if len(self.x_tba_app_id.split(':')) != 3:
            self._errors = json.dumps({"Error": "X-TBA-App-Id must follow a specific format. Please see http://www.thebluealliance.com/apidocs for more info."})
            self.abort(400)


class ApiTeamsShow(MainApiHandler):
    """
    Information about teams.
    """
    def get(self):
        self._validate_tba_app_id()
        teams = []
        team_keys = self.request.get('teams').split(',')

        for team_key in team_keys:
            try:
                team_info = ApiHelper.getTeamInfo(team_key)
                teams.append(team_info)
            except IndexError:
                pass

        if teams:
            response_json = teams
        else:
            response_json = {"Property Error": "No teams found for any key given"}
            self.response.set_status(404)

        self.response.out.write(json.dumps(response_json))

        team_keys_sorted = sorted(team_keys)
        track_team_keys = ",".join(team_keys_sorted)
        self._track_call_defer('teams/show', track_team_keys)


class ApiTeamDetails(MainApiHandler):
    """
    Information about a Team in a particular year, including full Event and Match objects
    """
    def get(self):
        self._validate_tba_app_id()
        team_key = self.request.get('team')
        year = self.request.get('year')

        response_json = {}

        try:
            response_json = ApiHelper.getTeamInfo(team_key)
            if self.request.get('events'):
                response_json = ApiHelper.addTeamEvents(response_json, year)

            # TODO: matches

            self.response.out.write(json.dumps(response_json))

            track_team_key = team_key
            if year:
                track_team_key = track_team_key + ' (' + year + ')'
            self._track_call_defer('teams/details', track_team_key)

        except IndexError:
            response_json = {"Property Error": "No team found for the key given"}
            self.response.set_status(404)
            self.response.out.write(json.dumps(response_json))


class ApiEventsShow(MainApiHandler):
    """
    Information about events.
    Deprecation notice. Please use ApiEventList, or ApiEventDetails.
    """
    def get(self):
        self._validate_tba_app_id()
        response = {"API Method Removed": "ApiEventsShow is no longer available. Please use ApiEventDetails, and ApiEventList instead."}
        self.response.set_status(410)
        self.response.out.write(json.dumps(response))


class ApiEventList(MainApiHandler):
    """
    Returns a list of events for a year with top level information
    """

    def get(self):
        self._validate_tba_app_id()
        if self.request.get("year") is '':
            year = datetime.now().year
        else:
            year = int(self.request.get("year"))

        memcache_key = "api_event_list_%s" % year
        event_list = memcache.get(memcache_key)

        if event_list is None:
            event_list = []
            event_keys = Event.query(Event.year == year).fetch(500, keys_only=True)
            events = ndb.get_multi(event_keys)
            for event in events:
                event_dict = {}
                event_dict["key"] = event.key_name
                event_dict["name"] = event.name
                event_dict["short_name"] = event.short_name
                event_dict["official"] = event.official

                if event.start_date:
                    event_dict["start_date"] = event.start_date.isoformat()
                else:
                    event_dict["start_date"] = None
                if event.end_date:
                    event_dict["end_date"] = event.end_date.isoformat()
                else:
                    event_dict["end_date"] = None

                event_list.append(event_dict)

            if tba_config.CONFIG["memcache"]:
                memcache.set(memcache_key, event_list, (30 * ((60 * 60) * 24)))

        self.response.out.write(json.dumps(event_list))

        self._track_call_defer('events/list')


class ApiEventDetails(MainApiHandler):
    """
    Return a specific event with details.
    """

    def get(self):
        self._validate_tba_app_id()
        event_key = str(self.request.get("event"))
        if event_key is "" or event_key is None:
            error_message = {"Parameter Error": "'event' is a required parameter."}
            self.response.out.write(json.dumps(error_message))
            return False

        event_dict = ApiHelper.getEventInfo(event_key)

        self.response.out.write(json.dumps(event_dict))

        self._track_call_defer('events/details', event_key)


class ApiMatchDetails(MainApiHandler):
    """
    Returns specific matches with details.
    """
    def get(self):
        self._validate_tba_app_id()
        value = self.request.get('match') or self.request.get('matches')
        matches = []
        if value is not '':
            match_keys = value.split(',')
            match_keys_sorted = sorted(value.split(','))
            track_matches_keys = ",".join(match_keys_sorted)
            track_matches = value
            for match_key in match_keys:
                if match_key == '':
                    continue
                mjson = ApiHelper.getMatchDetails(match_key)
                if mjson is not None:
                    matches.append(mjson)

        if matches != []:
            response = matches
        else:
            response = {"Property Error": "No matches found for any key given"}
            self.response.set_status(404)

        self.response.out.write(json.dumps(response))

        self._track_call_defer('matches/details', track_matches)


class CsvTeamsAll(MainApiHandler):
    """
    Outputs a CSV of all team information in the database, designed for other apps to bulk-import data.
    """
    def get(self):
        self._validate_tba_app_id()
        memcache_key = "csv_teams_all"
        output = memcache.get(memcache_key)

        if output is None:
            team_keys = Team.query().order(Team.team_number).fetch(10000, keys_only=True)
            teams = ndb.get_multi(team_keys)

            template_values = {
                "teams": teams
            }

            path = os.path.join(os.path.dirname(__file__), '../templates/api/csv_teams_all.csv')
            output = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]:
                memcache.set(memcache_key, output, 86400)

        self.response.headers["content-type"] = "text/csv"
        self.response.out.write(output)

        self._track_call_defer('teams/list')
