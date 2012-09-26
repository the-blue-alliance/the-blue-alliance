import os
import logging
import datetime
import time
import json

from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template

import tba_config

from base_controller import BaseHandler

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

class MainHandler(BaseHandler):
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
                kickoff_countdown = False
            else:
                kickoff_countdown = True

            template_values = {
                "kickoff_countdown": kickoff_countdown,
                "events": upcoming_events,
            }
            
            path = os.path.join(os.path.dirname(__file__), '../templates/index.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400)
        
        self.response.out.write(html)

class ContactHandler(BaseHandler):
    def get(self):
        self.response.out.write(render_static("contact"))

class HashtagsHandler(BaseHandler):
    def get(self):
        self.response.out.write(render_static("hashtags"))
        
class AboutHandler(BaseHandler):
    def get(self):
        self.response.out.write(render_static("about"))

class ThanksHandler(BaseHandler):
    def get(self):
        self.response.out.write(render_static("thanks"))

class OprHandler(BaseHandler):
    def get(self):
        self.response.out.write(render_static("opr"))

class SearchHandler(BaseHandler):
    def get(self):
        try:
            q = self.request.get("q")
            logging.info("search query: %s" % q)
            if q.isdigit():
                team_key_name = "frc%s" % q
                team = Team.get_by_key_name(team_key_name)
                if team:
                    self.redirect(team.details_url)
                    return None
        except Exception, e:
            logging.warning("warning: %s" % e)
        finally:
            self.response.out.write(render_static("search"))
            
class KickoffHandler(BaseHandler):
    def get(self):
        memcache_key = "main_kickoff"
        html = memcache.get(memcache_key)
        
        if html is None:
            template_values = {}
            
            path = os.path.join(os.path.dirname(__file__), '../templates/kickoff.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400)
        
        self.response.out.write(html)        
            
class TypeaheadHandler(BaseHandler):
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
                results.append({'id': event.key().name(), 'name': '%s %s [%s]' % (event.year, event.name, event.event_short.upper())})
            for team in teams:
                results.append({'id': team.team_number, 'name': '%s | %s' % (team.team_number, team.nickname)})

            if tba_config.CONFIG["memcache"]: memcache.set(typeahead_key, results, 86400)
        return results

class ChannelHandler(BaseHandler):
    # This is required for the FB JSSDK
    def get(self):
        expires = 60*60*24*365
        self.response.headers.add_header("Pragma", "public")
        self.response.headers.add_header("Cache-Control", "max-age="+str(expires))
        expires_date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(expires + time.time()))
        self.response.headers.add_header("Expires", expires_date)
        self.response.out.write('<script src="//connect.facebook.net/en_US/all.js"></script>')

class PageNotFoundHandler(BaseHandler):
    def get(self):
        self.error(404)
        self.response.out.write(render_static("404"))
