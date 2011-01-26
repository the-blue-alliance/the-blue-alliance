import logging
import os

from django.utils import simplejson

from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

from models import Event, EventTeam, Match, TBAVideo, Team

class ApiTeamsShow(webapp.RequestHandler):
    """
    Information about teams.
    """
    def get(self):
        
        teams = list()
        team_keys = self.request.get('teams').split(',')
        
        for team_key in team_keys:
            team = Team.get_by_key_name(team_key)
            team_dict = dict()
            team_dict["key"] = team.key().name()
            team_dict["team_number"] = team.team_number
            team_dict["name"] = team.name
            team_dict["nickname"] = team.nickname
            team_dict["location"] = team.address
            team_dict["website"] = team.website
            
            team_dict["events"] = [a.event.key().name() for a in team.events]
            teams.append(team_dict)
        
        self.response.out.write(simplejson.dumps(teams))

class ApiEventsShow(webapp.RequestHandler):
    """
    Information about events.
    """
    def get(self):

        events = list()
        event_keys = self.request.get('events').split(',')

        for event_key in event_keys:
            event = Event.get_by_key_name(event_key)
            event_dict = dict()
            event_dict["key"] = event.key().name()
            event_dict["year"] = event.year
            event_dict["event_code"] = event.event_short
            event_dict["name"] = event.name
            event_dict["short_name"] = event.short_name
            event_dict["location"] = event.location
            event_dict["official"] = event.official

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
            events.append(event_dict)

        self.response.out.write(simplejson.dumps(events))
