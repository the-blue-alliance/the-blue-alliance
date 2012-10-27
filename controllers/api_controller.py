import json
import logging
import os

from datetime import datetime

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
            events = Event.query(Event.year == year).fetch(500)
            for event in events:
                event_dict = dict()
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

            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, event_list, (30 * ((60 * 60) * 24)))

        self.response.headers.add_header("content-type", "application/json")
        self.response.out.write(json.dumps(event_list))

class ApiEventDetails(webapp.RequestHandler):
    """
    Return a specifc event with details.
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
    Returns a specifc
    """
    def get(self):
        if self.request.get('match') is not '':
            match_key = self.request.get('match')

        if self.request.get('matches') is not '':
            match_keys = self.request.get('matches').split(',')

        if 'match_keys' in locals():
            match_json = list()
            for match in match_keys:
                match_json.append(ApiHelper.getMatchDetails(match))
        else:
            match_json = ApiHelper.getMatchDetails(match_key)

        self.response.headers.add_header("content-type", "application/json")
        self.response.out.write(json.dumps(match_json))
