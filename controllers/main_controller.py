import os
import logging
import datetime
import json

from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template

import tba_config

from models.event import Event
from models.team import Team

def render_static(page):
    memcache_key = "main_%s" % page
    html = memcache.get(memcache_key)
    
    if html is None:
        path = os.path.join(os.path.dirname(__file__), "../templates/%s.html" % page)
        html = template.render(path, {})
        if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400)
    
    return html

class MainHandler(webapp.RequestHandler):
    def get(self):
        memcache_key = "main_index"
        html = memcache.get(memcache_key)
        
        if html is None:
            upcoming_events = Event.all().filter("start_date >=", datetime.date.today() - datetime.timedelta(days=4))
            upcoming_events.order('start_date').fetch(20)
            
            # Only show events that are happening "the same week" as the first one
            if upcoming_events.count() > 0:
              first_start_date = upcoming_events[0].start_date            
              upcoming_events = [e for e in upcoming_events if ((e.start_date - datetime.timedelta(days=6)) < first_start_date)]
            
            template_values = {
                "upcoming_events": upcoming_events,
            }
            
            path = os.path.join(os.path.dirname(__file__), '../templates/index.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400)
        
        self.response.out.write(html)

class ContactHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(render_static("contact"))

class HashtagsHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(render_static("hashtags"))

class ThanksHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(render_static("thanks"))

class OprHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(render_static("opr"))

class SearchHandler(webapp.RequestHandler):
    def get(self):
        try:
            q = self.request.get("q")
            logging.info("search query: %s" % q)
            if q.isdigit():
                team_key_name = "frc%s" % q
                team = Team.get_by_key_name(team_key_name)
                if team:
                    self.redirect(team.details_url())
                    return None
        except Exception, e:
            logging.warning("warning: %s" % e)
        finally:
            self.response.out.write(render_static("search"))
            
class TypeaheadHandler(webapp.RequestHandler):
    def get(self):
        # Currently just returns a list of all teams and events
        # Needs to be optimized at some point.
        # Tried a trie but the datastructure was too big to
        # fit into memcache efficiently
        q = self.request.get_all('q')
        entries = self.typeahead_entries()

        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')        
        typeahead_list = json.dumps(entries)
        self.response.out.write(typeahead_list)
        
    def typeahead_entries(self):
        typeahead_key = "typeahead_entries"
        results = memcache.get(typeahead_key)
        
        if results is None:
            events = Event.all().order('-year').order('name')       
            teams = Team.all().order('team_number')

            results = []
            for event in events:
                results.append({'id': event.details_url(), 'name': '%s %s [%s]' % (event.year, event.name, event.event_short.upper())})
            for team in teams:
                results.append({'id': team.details_url(), 'name': '%s | %s' % (team.team_number, team.nickname)})

            if tba_config.CONFIG["memcache"]: memcache.set(typeahead_key, results, 86400)
        return results

class PageNotFoundHandler(webapp.RequestHandler):
    def get(self):
        self.error(404)
        self.response.out.write(render_static("404"))
