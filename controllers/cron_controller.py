import logging
import os

from django.utils import simplejson

from google.appengine.api import taskqueue
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

from models import Event
from models import Team
from models import EventTeam

class EventTeamUpdate(webapp.RequestHandler):
    """
    Task that updates the EventTeam index for an Event.
    """
    def get(self, event_key):
        event = Event.get_by_key_name(event_key)
        matches = event.match_set
        teams = set()
        
        # Add teams from Matches
        for m in matches:
            for team in m.team_key_names:
                teams.add(team)
        
        # Add teams from existing EventTeams
        for a in event.teams:
            teams.add("frc" + str(a.team.team_number))
        
        eventteams_count = 0
        for team in teams:
            team_object = Team.get_or_insert(
                key_name = team,
                team_number = int(team[3:]), #"frc177"->"177"
                )
            
            #TODO: If we don't always put these, we'll use less resources. -gregmarra 23 Jan 2010
            et = EventTeam.get_or_insert(key_name = event_key + "_" + team)
            et.event = event
            et.team = team_object
            et.year = event.year
            et.put()
            
            eventteams_count = eventteams_count + 1
        
        template_values = {
            'eventteams_count': eventteams_count,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/cron/eventteam_update.html')
        self.response.out.write(template.render(path, template_values))
        
class EventTeamUpdateEnqueue(webapp.RequestHandler):
    """
    Handles enqueing building attendance for Events.
    """
    def get(self):
        for event in Event.all().fetch(1000):
            logging.info(event.name)
            taskqueue.add(
                url='/tasks/eventteam_update/' + event.key().name(),
                method='GET')
        
        template_values = {
            'event_count': Event.all().count(),
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/cron/eventteam_update_enqueue.html')
        self.response.out.write(template.render(path, template_values))