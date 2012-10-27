from datetime import datetime
import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from helpers.award_manipulator import AwardManipulator
from helpers.event_manipulator import EventManipulator
from models.award import Award
from models.event import Event
from models.team import Team

class AdminEventList(webapp.RequestHandler):
    """
    List all Events.
    """
    def get(self):
        events = Event.query().order(Event.year).order(Event.start_date).fetch(10000)
        
        template_values = {
            "events": events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_list.html')
        self.response.out.write(template.render(path, template_values))
        
class AdminEventDetail(webapp.RequestHandler):
    """
    Show an Event.
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        event.prepAwards()
        event.prepMatches()
        event.prepTeams()

        template_values = {
            "event": event
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_details.html')
        self.response.out.write(template.render(path, template_values))

class AdminEventCreate(webapp.RequestHandler):
    """
    Create an Event. POSTs to AdminEventEdit.
    """
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_create.html')
        self.response.out.write(template.render(path, {}))

class AdminEventEdit(webapp.RequestHandler):
    """
    Edit an Event.
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        
        template_values = {
            "event": event
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_edit.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self, event_key):
        # Note, we don't actually use event_key.

        start_date = None        
        if self.request.get("start_date"):
            start_date = datetime.strptime(self.request.get("start_date"), "%Y-%m-%d")
        
        end_date = None
        if self.request.get("end_date"):
            end_date = datetime.strptime(self.request.get("end_date"), "%Y-%m-%d")
        
        event = Event(
            id = str(self.request.get("year")) + str.lower(str(self.request.get("event_short"))),
            end_date = end_date,
            event_short = self.request.get("event_short"),
            event_type = self.request.get("event_type"),
            location = self.request.get("location"),
            name = self.request.get("name"),
            short_name = self.request.get("short_name"),
            start_date = start_date,
            website = self.request.get("website"),
            year = int(self.request.get("year")),
            official = {"true": True, "false": False}.get(self.request.get("official").lower()),
            facebook_eid = self.request.get("facebook_eid"),
            webcast_json = self.request.get("webcast_json"),
            rankings_json = self.request.get("rankings_json"),
        )
        event = EventManipulator.createOrUpdate(event)
        
        self.redirect("/admin/event/" + event.key_name)
        
class AdminAwardEdit(webapp.RequestHandler):
    """
    Edit an Award.
    """
    def get(self, award_key):
        award = Award.get_by_id(award_key)
                
        template_values = {
            "award": award
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/award_edit.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self, award_key):
        event_key_name = self.request.get('event_key_name')
        award = Award(
            id = award_key,
            name = self.request.get('award_name'),
            event = Event.get_by_id(event_key_name),
            official_name = self.request.get('official_name'),
            team = Team.get_by_id('frc' + str(self.request.get('team_number', 0))),
            awardee = self.request.get('awardee'),
        )
        award = AwardManipulator.createOrUpdate(award)
        self.redirect("/admin/event/" + event_key_name)
