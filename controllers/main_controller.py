import os
import logging
import datetime

from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

from models import Team, Event

def render_static(page):
    memcache_key = "main_%s" % page
    html = memcache.get(memcache_key)
    
    if html is None:
        path = os.path.join(os.path.dirname(__file__), "../templates/main/%s.html" % page)
        html = template.render(path, {})
        memcache.set(memcache_key, html, 86400)
    
    return html

class MainHandler(webapp.RequestHandler):
    def get(self):
        memcache_key = "team_list"
        html = memcache.get(memcache_key)
        
        if html is None:
            upcoming_events = Event.all().filter("start_date >=", datetime.date.today() - datetime.timedelta(days=4))
            upcoming_events.order('start_date').fetch(20)
            
            # Only show events that are happening "the same week" as the first one
            first_start_date = upcoming_events[0].start_date            
            upcoming_events = [e for e in upcoming_events if ((e.start_date - datetime.timedelta(days=6)) < first_start_date)]
            
            template_values = {
                "upcoming_events": upcoming_events,
            }
            
            path = os.path.join(os.path.dirname(__file__), '../templates/main/index.html')
            html = template.render(path, template_values)
            memcache.set(memcache_key, html, 86400)
        
        self.response.out.write(html)

class ContactHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(render_static("contact"))
        
class ThanksHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(render_static("thanks"))

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

class PageNotFoundHandler(webapp.RequestHandler):
    def get(self):
        self.error(404)
        self.response.out.write(render_static("404"))
