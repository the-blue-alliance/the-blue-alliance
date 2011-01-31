import datetime
import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from models import Event, Match
from helpers.match_helper import MatchHelper
from helpers.team_helper import TeamHelper

class EventList(webapp.RequestHandler):
    """
    List all Events.
    """
    def get(self, year=None):
        if year:
            year = int(year)
        else:
            year = datetime.datetime.now().year
        
        memcache_key = "event_list_%s" % year
        html = memcache.get(memcache_key)
        
        if html is None:
            events = Event.all().filter("year =", int(year)).order('start_date').fetch(1000)
        
            template_values = {
                "year": year,
                "events": events,
            }
        
            path = os.path.join(os.path.dirname(__file__), '../templates/events/list.html')
            html = template.render(path, template_values)
            memcache.set(memcache_key, html, 3600)
        
        self.response.out.write(html)
        
class EventDetail(webapp.RequestHandler):
    """
    Show an Event.
    event_code like "2010ct"
    """
    def get(self, event_code):
        
        memcache_key = "event_detail_%s" % event_code
        html = memcache.get(memcache_key)
        
        if html is None:
            year = event_code[0:4]
            event_short = event_code[4:]
        
            event = Event.get_by_key_name(year + event_short)
            matches = MatchHelper.organizeMatches(event.match_set)
            teams = TeamHelper.sortTeams([a.team for a in event.teams])
        
            template_values = {
                "event": event,
                "matches": matches,
                "teams": teams,
            }
                
            path = os.path.join(os.path.dirname(__file__), '../templates/events/details.html')
            html = template.render(path, template_values)
            memcache.set(memcache_key, html, 300)
        
        self.response.out.write(html)