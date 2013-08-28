
import json
import logging
import os
import webapp2
import urllib

from datetime import datetime

from google.appengine.api import memcache, urlfetch
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

import tba_config
from helpers.api_helper import ApiHelper

from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team
from models.sitevar import Sitevar

# Note: generally caching for the API happens in ApiHelper


class MainApiHandler(webapp2.RequestHandler):

    def __init__(self, request, response):
        # Need to initialize a webapp2 instance
        self.initialize(request, response)
        logging.info(request)

    def _track_call(self, api_category, api_type, api_details=''):
        # Creates asynchronous call
        rpc = urlfetch.create_rpc()

        analytics_id = Sitevar.get_by_id("analytics.id")
        if analytics_id == None:
            raise Exception("Missing sitevar: analytics.id. Can't track API usage.")
        ANALYTICS_ID = analytics_id.contents['ANALYTICS_ID']

        params = urllib.urlencode({
            'v': 1,
            'tid': ANALYTICS_ID,
            'cid': '1',
            't': 'event',
            'ec': 'api_' + api_category,
            'ea': api_type,
            'el': api_details,
            'ev': 1,
            'ni': 1
        })

        # Sets up the call
        analytics_url = 'http://www.google-analytics.com/collect'
        urlfetch.make_fetch_call(rpc=rpc,
            url=analytics_url,
            payload=params,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        try:
            result = rpc.get_result()
        except urlfetch.DownloadError:
            logging.error('API tracking error')


class ApiTeamsShow(MainApiHandler):
    """
    Information about teams.
    """
    def get(self):
        teams = []
        team_keys = self.request.get('teams').split(',')

        try:
            teams = [ApiHelper.getTeamInfo(team_key) for team_key in team_keys]
        except IndexError:
            self.response.set_status(404)
            response_json = {"Property Error": "No team found for key in %s" % str(teams)}

        track_team_keys = ",".join(team_keys)
        self._track_call('teams', 'show', track_team_keys)

        self.response.out.write(json.dumps(teams))


class ApiTeamDetails(MainApiHandler):
    """
    Information about a Team in a particular year, including full Event and Match objects
    """
    def get(self):

        team_key = self.request.get('team')
        year = self.request.get('year')

        response_json = {}
        try:
            response_json = ApiHelper.getTeamInfo(team_key)
            if self.request.get('events'):
                reponse_json = ApiHelper.addTeamEvents(response_json, year)

            # TODO: matches

            track_team_key = team_key
            if year:
                track_team_key = track_team_key + ' (' + year + ')'
            self._track_call('teams', 'details', track_team_key)

            self.response.out.write(json.dumps(response_json))

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
        response = {"API Method Removed": "ApiEventsShow is no longer available. Please use ApiEventDetails, and ApiEventList instead."}
        self.response.set_status(410)
        self.response.out.write(json.dumps(response))


class ApiEventList(MainApiHandler):
    """
    Returns a list of events for a year with top level information
    """

    def get(self):
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

        self._track_call('events', 'list')

        self.response.headers.add_header("content-type", "application/json")
        self.response.out.write(json.dumps(event_list))


class ApiEventDetails(MainApiHandler):
    """
    Return a specific event with details.
    """

    def get(self):
        event_key = str(self.request.get("event"))
        if event_key is "" or event_key is None:
            error_message = {"Parameter Error": "'event' is a required parameter."}
            self.response.out.write(json.dumps(error_message))
            return False

        event_dict = ApiHelper.getEventInfo(event_key)

        self.response.headers.add_header("content-type", "application/json")
        self._track_call('events', 'details', event_key)
        self.response.out.write(json.dumps(event_dict))


class ApiMatchDetails(MainApiHandler):
    """
    Returns specific matches with details.
    """
    def get(self):
        if self.request.get('match') is not '':
            match_keys = self.request.get('match').split(',')
            track_matches = self.request.get('match')

        if self.request.get('matches') is not '':
            match_keys = self.request.get('matches').split(',')
            track_matches = self.request.get('matches')

        match_json = []
        for match in match_keys:
            match_json.append(ApiHelper.getMatchDetails(match))

        self._track_call('matches', 'details', track_matches)

        self._track_call('matches', 'details', track_matches)

        self.response.headers.add_header("content-type", "application/json")
        self.response.out.write(json.dumps(match_json))


class CsvTeamsAll(MainApiHandler):
    """
    Outputs a CSV of all team information in the database, designed for other apps to bulk-import data.
    """
    def get(self):
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

        self._track_call('teams', 'list')

        self.response.out.write(output)
