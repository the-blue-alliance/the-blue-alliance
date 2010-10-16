import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from django.utils import simplejson

from models import Match, Event
from helpers.match_helper import MatchUpdater

class AdminMatchDashboard(webapp.RequestHandler):
    """
    Show stats about Matches
    """
    def get(self):
        match_count = Match.all().count()
        
        template_values = {
            "match_count": match_count
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/matches/dashboard.html')
        self.response.out.write(template.render(path, template_values))
        

class AdminMatchDetail(webapp.RequestHandler):
    """
    Show a Match.
    """
    def get(self, match_key):
        match = Match.get_by_key_name(match_key)
        
        template_values = {
            "match": match
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/matches/details.html')
        self.response.out.write(template.render(path, template_values))
        
class AdminMatchEdit(webapp.RequestHandler):
    """
    Edit a Match.
    """
    def get(self, match_key):
        match = Match.get_by_key_name(match_key)
        
        template_values = {
            "match": match
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/matches/edit.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self, match_key):        
        logging.info(self.request)
        
        alliances_json = self.request.get("alliances_json")
        alliances = simplejson.loads(alliances_json)
        team_key_names = list()
        
        for alliance in alliances:
            team_key_names.extend(alliances[alliance].get('teams', None))
        
        match = Match(
            key_name = match_key,
            event = Event.get_by_key_name(self.request.get("event_key_name")),
            game = self.request.get("game"),
            set_number = int(self.request.get("set_number")),
            match_number = int(self.request.get("match_number")),
            comp_level = self.request.get("comp_level"),
            team_key_names = team_key_names,
            alliances_json = alliances_json,
            #no_auto_update = str(self.request.get("no_auto_update")).lower() == "true", #TODO
        )
        match = MatchUpdater.createOrUpdate(match)
        
        self.redirect("/admin/match/" + match.get_key_name())
