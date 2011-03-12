import datetime
import os
import logging
import PyRSS2Gen

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from django.utils import simplejson


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
            explicit_year = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False
        
        memcache_key = "event_list_%s" % year
        html = memcache.get(memcache_key)
        
        if html is None:
            events = Event.all().filter("year =", int(year)).order('start_date').fetch(1000)
        
            template_values = {
                "explicit_year": explicit_year,
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
    def get(self, event_key):
        memcache_key = "event_detail_%s" % event_key
        html = memcache.get(memcache_key)
        
        if html is None:
            event = Event.get_by_key_name(event_key)
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

class EventRss(webapp.RequestHandler):
    """
    Generates a RSS feed for the matches in a event
    Created by: @brandondean, github.com/brandondean
    """
    def get(self, event_key):
        memcache_key = "event_rss_%s" % event_key
        html = memcache.get(memcache_key)
        
        if html is None:
            event = Event.get_by_key_name(event_key)
            matches = MatchHelper.organizeMatches(event.match_set)
            
            rss_items = []
            # Loop through and generate RSS items for each match
            for match in matches['f'] + matches['sf'] + matches['qf'] + matches['ef'] + matches['qm']:
                match.unpack_json()
                new_item = PyRSS2Gen.RSSItem(
                    title = str(match.verbose_name()),
                    link = 'http://www.thebluealliance.com/match/' + match.get_key_name() + '',
                    
                    # List the red and blue alliance teams and their score
                    # TODO: Make this generic in case there's ever not just red/blue -gregmarra 12 Mar 2011
                    description = "Red Alliance: " + ' '.join(match.alliances["red"]["teams"]) + " "
                                  + "Score: " + str(match.alliances["red"]["score"]) + " "
                                  + "Blue Alliance: " + ' '.join(match.alliances["blue"]["teams"]) + " "
                                  + "Score: " + str(match.alliances["blue"]["score"])
         
                )
                rss_items.append(new_item)
            
            # Create final rss document
            rss = PyRSS2Gen.RSS2(
                title = event.name + "-- " + str(event.year),
                link = 'http://www.thebluealliance.com/event/' + str(event.get_key_name()) + '',
                description = "RSS feed for the " + event.name + " provided by The Blue Alliance." ,
                lastBuildDate = datetime.datetime.now(),
                items = rss_items
            )
            html = rss.to_xml()
            memcache.set(memcache_key, html, 300)
        
        self.response.out.write(html)
