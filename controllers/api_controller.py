import logging
import os

from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

from helpers.api_helper import ApiHelper
from models import Event, EventTeam, Match, TBAVideo, Team

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
        team_dict = ApiHelper.addTeamMatches(team_dict, year)
        #TODO: Event objects
        #team_dict = ApiHelper.addTeamEvents(team_dict, year)
        
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
            
        event_keys = event_keys.union(set(self.request.get("events").split(',')))
        event_keys = filter(None, event_keys)
        
        events = list()
        
        for event_key in event_keys:
            memcache_key = "api_event_show_%s" % event_key
            event_dict = memcache.get(memcache_key)
            if event_dict is None:
                event = Event.get_by_key_name(event_key)
                if event is not None:
                    event_dict = dict()
                    event_dict["key"] = event.key().name()
                    event_dict["year"] = event.year
                    event_dict["event_code"] = event.event_short
                    event_dict["name"] = event.name
                    event_dict["short_name"] = event.short_name
                    event_dict["location"] = event.location
                    event_dict["official"] = event.official
                    event_dict["facebook_eid"] = event.facebook_eid

                    if event.start_date:
                        event_dict["start_date"] = event.start_date.isoformat()
                    else:
                        event_dict["start_date"] = None
                    if event.end_date:
                        event_dict["end_date"] = event.end_date.isoformat()
                    else:
                        event_dict["end_date"] = None
            
                    event_dict["teams"] = [a.team.key().name() for a in event.teams]
                    event_dict["matches"] = [a.key().name() for a in event.match_set]
                
                    memcache.set(memcache_key, event_dict, 300)
                    events.append(event_dict)
            else:
                events.append(event_dict)
        
        self.response.out.write(simplejson.dumps(events))
