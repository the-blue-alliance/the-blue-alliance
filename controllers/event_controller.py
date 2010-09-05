import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from models import Event

class EventList(webapp.RequestHandler):
    """
    List all Events.
    """
    def get(self):
        
        events = Event.all().order('start_date').fetch(10000)
        
        template_values = {
            "events": events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/events/list.html')
        self.response.out.write(template.render(path, template_values))
        
class EventDetail(webapp.RequestHandler):
    """
    Show an Event.
    """
    def get(self, year, event_short):
        
        event = Event.all().filter("year =", int(year)).filter("event_short = ", event_short)[0]
        
        event.red = event.teams.filter("alliance=", "red")
        event.blue = event.teams.filter("alliance=", "blue")
        event.redscore = event.scores.filter("alliance=", "red")
        event.bluescore = event.scores.filter("alliance=", "blue")
        
        path = os.path.join(os.path.dirname(__file__), '../templates/events/details.html')
        self.response.out.write(template.render(path, { 'event' : event }))