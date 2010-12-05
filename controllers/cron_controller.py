import logging
import os

from django.utils import simplejson

from google.appengine.api.labs import taskqueue
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

from models import Event
from models import Team
from models import EventTeam

class EventTeamUpdater(webapp.RequestHandler):
    """
    Task that updates the EventTeam index for an Event.
    """
    def get(self, event_key):
        event = Event.get_by_key_name(event_key)
        matches = event.match_set
        eventteams = list()
        for m in matches:
            for team in m.team_key_names:
                et = EventTeam.get_or_insert(
                    key_name = m.event.key().name() + "_" + team,
                    event = m.event,
                    team = Team.get_by_key_name(team))
                eventteams.append(et)
                logging.info(et)
        
        template_values = {
            'eventteams': eventteams,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/cron/eventteam_update.html')
        self.response.out.write(template.render(path, template_values))