import os, logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from models import Event, Match
from helpers.match_helper import MatchHelper

class EventList(webapp.RequestHandler):
    """
    List all Events.
    """
    def get(self, year=None):
        if not year: year = 2010 #fixme -gregmarra 17 Oct 2010
        
        events = Event.all().filter("year =", int(year)).order('start_date').fetch(1000)
        
        template_values = {
            "events": events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/events/list.html')
        self.response.out.write(template.render(path, template_values))
        
class EventDetail(webapp.RequestHandler):
    """
    Show an Event.
    event_code like "2010ct"
    """
    def get(self, event_code):
        
        year = event_code[0:4]
        event_short = event_code[4:]
        
        event = Event.get_by_key_name(year + event_short)
        matches = MatchHelper.organizeMatches(event.match_set)
        
        template_values = {
            "event": event,
            "matches": matches,
        }
                
        path = os.path.join(os.path.dirname(__file__), '../templates/events/details.html')
        self.response.out.write(template.render(path, template_values))