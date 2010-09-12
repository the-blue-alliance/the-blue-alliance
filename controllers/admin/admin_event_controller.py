import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from models import Event

class AdminEventList(webapp.RequestHandler):
    """
    List all Events.
    """
    def get(self):
        
        events = Event.all().order('year').order('start_date').fetch(10000)
        
        template_values = {
            "events": events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/events/list.html')
        self.response.out.write(template.render(path, template_values))
        
class AdminEventDetail(webapp.RequestHandler):
    """
    Show an Event.
    """
    def get(self, event_key):
        event = Event.get_by_key_name(event_key)
        
        template_values = {
            "event": event
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/events/details.html')
        self.response.out.write(template.render(path, { 'event' : event }))