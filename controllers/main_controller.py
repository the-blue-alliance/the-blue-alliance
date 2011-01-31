import os

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util


class MainHandler(webapp.RequestHandler):
    def get(self):
        memcache_key = "main_index"
        html = memcache.get(memcache_key)
        
        if html is None:
            path = os.path.join(os.path.dirname(__file__), '../templates/main/index.html')
            html = template.render(path, {})
            memcache.set(memcache_key, html, 3600)
        
        self.response.out.write(html)

class ThanksHandler(webapp.RequestHandler):
    def get(self):
        memcache_key = "main_thanks"
        html = memcache.get(memcache_key)
        
        if html is None:
            path = os.path.join(os.path.dirname(__file__), '../templates/main/thanks.html')
            html = template.render(path, {})
            memcache.set(memcache_key, html, 3600)
        
        self.response.out.write(html)
