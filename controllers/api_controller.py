import json
import logging
import os

from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template

import tba_config
from helpers.api_helper import ApiHelper

from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

#Note: generally caching for the API happens in ApiHelper

class ApiTeamsShow(webapp.RequestHandler):
    """
    Information about teams.
    """
    def get(self):
        teams = list()
        team_keys = self.request.get('teams').split(',')
        
        for team_key in team_keys:
            teams.append(ApiHelper.getTeamInfo(team_key))
        
        self.response.out.write(json.dumps(teams))

class ApiTeamDetails(webapp.RequestHandler):
    """
    Information about a Team in a particular year, including full Event and Match objects
    """
    def get(self):
        team_key = self.request.get('team')
        year = self.request.get('year')

        try:
            team_dict = ApiHelper.getTeamInfo(team_key)
            if self.request.get('events'):
                team_dict = ApiHelper.addTeamEvents(team_dict, year)
            
            #TODO: matches
            
            self.response.out.write(json.dumps(team_dict))
        except Exception:
            return False

class ApiEventsShow(webapp.RequestHandler):
    """
    Information about events.
    Deprecation notice. Please use ApiEventList, or ApiEventDetails.
    """
    def get(self):
        logging.warning("Deprecation notice: ApiEventsShow.")

        event_keys = set()
        
        if self.request.get("year"):
            events = Event.all().filter("year =", int(self.request.get("year"))).fetch(500)
            event_keys = event_keys.union(set([event.key().name() for event in events]))
            
        event_keys = filter(None, event_keys.union(set(self.request.get("events").split(','))))        
        events = [ApiHelper.getEventInfo(event_key) for event_key in event_keys]
        
        self.response.out.write(json.dumps(events))

class ApiEventList(webapp.RequestHandler):
    """
    List of teams for a year with key_name, team number, and name.
    """

    def get(self):
        try:
            year = int(self.request.get("year"))
        except ValueError:
            error_message = {"Parameter Error": "'year' is a required parameter."}
            self.response.out.write(json.dumps(error_message))
            return False

        memcache_key = "api_event_list_%s" % year
        event_list = memcache.get(memcache_key)

        if event_list is None:
            event_list = []
            events = Event.all().filter("year =", year).fetch(500)
            for event in events:
                event_dict = dict()
                event_dict["key"] = event.key().name()
                event_dict["name"] = event.name
                event_dict["event_code"] = event.short_name
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
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, event_list, 600)

        self.response.out.write(json.dumps(event_list))

class ApiEventDetails(webapp.RequestHandler):
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

        self.response.out.write(json.dumps(event_dict))

class ApiMatchDetails(webapp.RequestHandler):
    """
    Returns a specific match with details.
    """

    def get(self):
        match_key = str(self.request.get("match"))
        if match_key is None or match_key is "":
            error = {'Error': "'match' is a required parameter."}
            self.response.headers.add_header('content-type', 'application/json')
            self.response.out.write(json.dumps(error))

        else:
            match_dict = ApiHelper.getMatchDetails(match_key)

            self.response.headers.add_header('content-type', 'application/json')
            self.response.out.write(json.dumps(match_dict))
