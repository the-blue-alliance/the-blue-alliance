import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from models import Match

class MatchList(webapp.RequestHandler):
    """
    Display all Matches.
    """
    def get(self):
        
        matches = Match.all().order('event').fetch(100)
        
        template_values = {
            "matches": matches,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/matches/list.html')
        self.response.out.write(template.render(path, template_values))
        
class MatchDetail(webapp.RequestHandler):
    """
    Display a Match.
    """
    def get(self, key_name):
        
        match = Match.all().get_by_key_name(key_name)
        
        if match:
            path = os.path.join(os.path.dirname(__file__), '../templates/events/details.html')
            self.response.out.write(template.render(path, { 'event' : event }))
        else:
            # TODO: Add real "match not found" template
            self.response.out.write("404.")

