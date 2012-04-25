import logging
import os

from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

from helpers.api_helper import ApiHelper
from models import Event, EventTeam, Match, Team

class ApiTeamsShow(webapp.RequestHandler):
    """
    Information about teams.
    """
    def get(self):
        teams = list()
        team_keys = self.request.get('teams').split(',')
        
        for team_key in team_keys:
            teams.append(ApiHelper.getTeamInfo(team_key))
        
        self.response.out.write(simplejson.dumps(teams))

class ApiTeamDetails(webapp.RequestHandler):
    """
    Information about a Team in a particular year, including full Event and Match objects
    """
    def get(self):
        team_key = self.request.get('team')
        year = self.request.get('year')
        
        team_dict = ApiHelper.getTeamInfo(team_key)
        if self.request.get('events'):
            team_dict = ApiHelper.addTeamEvents(team_dict, year)
        
        #TODO: matches
        
        self.response.out.write(simplejson.dumps(team_dict))

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
        
        self.response.out.write(simplejson.dumps(events))

class ApiEventList(webapp.RequestHandler):
    """
    List of teams for a year with key_name, team number, and name.
    """

    def get(self):
        try:
            year = int(self.request.get("year"))
        except ValueError:
            error_message = {"Parameter Error": "'year' is a required parameter."}
            self.response.out.write(simplejson.dumps(error_message))
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
                event_list.append(event_dict)
            memcache.set(memcache_key, event_list, 600)

        self.response.out.write(simplejson.dumps(event_list))

class ApiEventDetails(webapp.RequestHandler):
    """
    Return a specifc event with details.
    """

    def get(self):
        event_key = str(self.request.get("event"))
        if event_key is "" or event_key is None:
            error_message = {"Parameter Error": "'event' is a required parameter."}
            self.response.out.write(simplejson.dumps(error_message))
            return False


        event_dict = ApiHelper.getEventInfo(event_key)

        self.response.out.write(simplejson.dumps(event_dict))
