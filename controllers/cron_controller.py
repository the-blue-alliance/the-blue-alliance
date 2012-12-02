import datetime
import logging
import os

from google.appengine.api import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from helpers.opr_helper import OprHelper

from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

class EventTeamUpdate(webapp.RequestHandler):
    """
    Task that updates the EventTeam index for an Event.
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        teams = set()
        
        # Add teams from Matches
        for m in Match.query(Match.event == event.key).fetch(1000):
            for team in m.team_key_names:
                teams.add(team)
        
        # Add teams from existing EventTeams
        [teams.add(event_team.team.id()) for event_team in EventTeam.query(EventTeam.event == event.key).fetch(5000)]
        
        eventteams_count = 0
        for team in teams:
            team_object = Team.get_or_insert(
                team,
                team_number = int(team[3:]), #"frc177"->"177"
                )
            
            et = EventTeam.get_or_insert(
                event_key + "_" + team,
                event = event.key,
                team = team_object.key,
                year = event.year)
            
            # Update if needed
            reput = False
            if not et.team:
                reput = True
                et.team = team_object.key
            elif et.team != team_object.key:
                reput = True
                et.team = team_object.key
            if et.year != event.year:
                reput = True
                et.year = event.year
            if reput:
                logging.info("Had to re-put %s" % et.key().name)
                et.put()
                # TODO: This could be made MUCH more efficient with batching (gregmarra 14 Jan 2011)
            
            eventteams_count = eventteams_count + 1
        
        template_values = {
            'eventteams_count': eventteams_count,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/math/eventteam_update_do.html')
        self.response.out.write(template.render(path, template_values))
        
class EventTeamUpdateEnqueue(webapp.RequestHandler):
    """
    Handles enqueing building attendance for Events.
    """
    def get(self, when):
        if when == "all":
            event_keys = Event.query().fetch(10000, keys_only=True)
        else:
            event_keys = Event.query(Event.year == int(when)).fetch(10000, keys_only=True)
        
        for event_key in event_keys:
            taskqueue.add(
                url='/tasks/math/do/eventteam_update/' + event_key.id(),
                method='GET')
        
        template_values = {
            'event_keys': event_keys,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/math/eventteam_update_enqueue.html')
        self.response.out.write(template.render(path, template_values))

class EventOprDo(webapp.RequestHandler):
    """
    Calculates the opr for an event
    """
    def get(self, event_key):
        opr = []
        teams = []
        oprs = []
        event = Event.get_by_id(event_key)
        if Match.query(Match.event == event.key).count() > 0:
            try:
                opr,teams = OprHelper.opr(event_key)
                oprs.append((opr,teams))
                event.oprs = opr
                event.opr_teams = teams
                event.put()
            except Exception, e:
                logging.error("OPR error on event %s. %s" % (event_key, e))

        logging.info(oprs)

        template_values = {
            'oprs': oprs,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/math/event_opr_do.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        self.get()

class EventOprEnqueue(webapp.RequestHandler):
    """
    Enqueues OPR calculation
    """
    def get(self, when):
        if when == "now":
            events = Event.query(Event.end_date <= datetime.datetime.today() + datetime.timedelta(days=4))
            events = Event.query(Event.end_date >= datetime.datetime.today() - datetime.timedelta(days=1))
        else:
            events = Event.query(Event.year == int(when))
        
        events = events.fetch(500)
        
        for event in events:
            taskqueue.add(
                url='/tasks/math/do/event_opr/' + event.key_name,
                method='GET')
        
        template_values = {
            'event_count': len(events),
            'year': when
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/math/event_opr_enqueue.html')
        self.response.out.write(template.render(path, template_values))
