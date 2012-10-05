import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from helpers.event_manipulator import EventManipulator
from models.event import Event

class AdminEventList(webapp.RequestHandler):
    """
    List all Events.
    """
    def get(self):
        
        events = Event.all().order('year').order('start_date').fetch(10000)
        
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
        event = Event.get_by_key_name(event_key)
        
        template_values = {
            "event": event,
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_details.html')
        self.response.out.write(template.render(path, template_values))
        
class AdminEventEdit(webapp.RequestHandler):
    """
    Edit an Event.
    """
    def get(self, event_key):
        event = Event.get_by_key_name(event_key)
        
        template_values = {
            "event": event
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_edit.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self, event_key):
        # Note, we don't actually use event_key.
        
        event = Event(
            end_date = None, #TODO
            event_short = self.request.get("event_short"),
            event_type = self.request.get("event_type"),
            location = self.request.get("location"),
            name = self.request.get("name"),
            short_name = self.request.get("short_name"),
            start_date = None, #TODO
            website = self.request.get("website"),
            year = int(self.request.get("year")),
            official = {"true": True, "false": False}.get(self.request.get("official").lower()),
            facebook_eid = self.request.get("facebook_eid"),
            webcast_json = self.request.get("webcast_json"),
            rankings_json = self.request.get("rankings_json"),
        )
        event = EventManipulator.createOrUpdate(event)
        
        self.redirect("/admin/event/" + event.key_name)
        
