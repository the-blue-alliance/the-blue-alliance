import os, logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from models import Event, Match

class EventList(webapp.RequestHandler):
    """
    List all Events.
    """
    def get(self, year=None):
        if not year: year = 2010 #fixme -gregmarra 17 Oct 2010
        
        events = Event.all().order('start_date').fetch(10000)
        
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
        match_list = event.match_set.order("set_number").order("match_number").fetch(500)
        
        # Eh, this could be better. -gregmarra 17 oct 2010
        # todo: abstract this so we can use it in the team view.
        # todo: figure out how slow this is
        [match.unpack_json() for match in match_list]
        matches = dict([(comp_level, list()) for comp_level in Match.COMP_LEVELS])
        while len(match_list) > 0:
            match = match_list.pop(0)
            matches[match.comp_level].append(match)
        
        template_values = {
            "event": event,
            "matches": matches,
        }
                
        path = os.path.join(os.path.dirname(__file__), '../templates/events/details.html')
        self.response.out.write(template.render(path, template_values))