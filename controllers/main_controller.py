import os

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

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
        self.response.out.write(render_static("search"))
