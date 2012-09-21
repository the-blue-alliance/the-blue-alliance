import logging
import os

from google.appengine.api import taskqueue
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template

from models.event import Event
from models.event_team import EventTeam
from models.team import Team

class EventTeamUpdate(webapp.RequestHandler):
    """
    Task that updates the EventTeam index for an Event.
    """
    def get(self, event_key):
        event = Event.get_by_key_name(event_key)
        teams = set()
        
        # Add teams from Matches
        for m in event.match_set:
            for team in m.team_key_names:
                teams.add(team)
        
        # Add teams from existing EventTeams
        [teams.add(EventTeam.team.get_value_for_datastore(event_team).name()) for event_team in event.teams.fetch(5000)]
        
        eventteams_count = 0
        for team in teams:
            team_object = Team.get_or_insert(
                key_name = team,
                team_number = int(team[3:]), #"frc177"->"177"
                )
            
            et = EventTeam.get_or_insert(
                key_name = event_key + "_" + team,
                event = event,
                team = team_object,
                year = event.year)
            
            # Update if needed
            reput = False
            if not et.team:
                reput = True
                et.team = team_object
            elif et.team.key().name != team_object.key().name:
                reput = True
                et.team = team_object
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

class EventOprDo(webapp.RequestHandler):
    """
    Calculates the opr for an event
    """
    def get(self, event_key):
        opr = []
        teams = []
        oprs = []
        event = Event.get_by_key_name(event_key)
        if event.match_set.count() > 0:
            try:
                opr,teams = OprHelper.opr(event_key)
                oprs.append((opr,teams))
                event.oprs = opr
                event.opr_teams = teams
                event.put()
            except Exception, e:
                logging.error("OPR error on event %s. %s" % (event_key, e))

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
            events = events.filter('end_date <=', datetime.date.today() + datetime.timedelta(days=4))
            events = events.filter('end_date >=', datetime.date.today() - datetime.timedelta(days=1))
        else:
            events = events.filter('year =', int(when))
        
        events = events.fetch(500)
        
        for event in events:
            taskqueue.add(
                url='/math/do/event_opr/' + event.key_name,
                method='GET')
        
        template_values = {
            'event_count': events.count(),
            'year': year
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/math/event_opr_enqueue.html')
        self.response.out.write(template.render(path, template_values))
