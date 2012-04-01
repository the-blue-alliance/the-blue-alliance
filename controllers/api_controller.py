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
    """
    def get(self):
        event_keys = set()
        
        if self.request.get("year"):
            events = Event.all().filter("year =", int(self.request.get("year"))).fetch(500)
            event_keys = event_keys.union(set([event.key().name() for event in events]))
            
        event_keys = filter(None, event_keys.union(set(self.request.get("events").split(','))))        
        events = [ApiHelper.getEventInfo(event_key) for event_key in event_keys]
        
        self.response.out.write(simplejson.dumps(events))
