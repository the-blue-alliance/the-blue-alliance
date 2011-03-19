import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

from models import Team

def render_static(page):
    memcache_key = "main_%s" % page
    html = memcache.get(memcache_key)
    
    if html is None:
        path = os.path.join(os.path.dirname(__file__), "../templates/main/%s.html" % page)
        html = template.render(path, {})
        memcache.set(memcache_key, html, 3600)
    
    return html

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(render_static("index"))

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


