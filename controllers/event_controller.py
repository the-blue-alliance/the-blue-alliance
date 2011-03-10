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

class EventRss(webapp.RequestHandler):
    """
    Feed!
    """
    def get(self, event_code):
          year = event_code[0:4]
          event_short = event_code[4:]

          event = Event.get_by_key_name(year + event_short)
          matches = MatchHelper.organizeMatches(event.match_set)
          
          ["qm", "ef", "qf", "sf", "f"]
          rss_items = []
          for match in matches['qm'] + matches['ef'] + matches['qf'] + matches['sf'] + matches['f']:
              match.unpack_json()
              new_item = PyRSS2Gen.RSSItem(
                  title = str(match.verbose_name()),
                  link = 'http://www.thebluealliance.com/match/' + match.get_key_name() + '',
                  
                  # This seems really sad to me. There has to be a better way of doing this, but I no idea what that
                  # might look like. Please, if you know, make the changes ASAP.
                  # FIXME: meh. -- @brandondean 10 March 2011
                  description = "Red Alliance: " + str().join(match.alliances["red"]["teams"][0]) + " "
                                + str().join(match.alliances["red"]["teams"][1]) + " "
                                + str().join(match.alliances["red"]["teams"][2]) + " "
                                + "Score: " + str(match.alliances["red"]["score"]) + " "
                                + "Blue Alliance: " + str().join(match.alliances["blue"]["teams"][0]) + " " 
                                + str().join(match.alliances["blue"]["teams"][1]) + " "
                                + str().join(match.alliances["blue"]["teams"][2]) + " "
                                + "Score: " + str(match.alliances["blue"]["score"]) + " "

              )
          
              rss_items.append(new_item)
          
          rss = PyRSS2Gen.RSS2(
              title = event.name + "-- " + str(event.short_name),
              link = 'http://www.thebluealliance.com/event/' + str(event.get_key_name()) + '',
              description = "RSS feed provided by " + event.name + " by The Blue Alliance." ,

              lastBuildDate = datetime.datetime.now(),
              
              items = rss_items
          )
          
          
          self.response.out.write(rss.to_xml())
