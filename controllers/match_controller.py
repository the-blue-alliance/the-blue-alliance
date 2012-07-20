import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

import tba_config
from models import Match
from helpers.tbavideo_helper import TBAVideoHelper

class MatchList(webapp.RequestHandler):
    """
    Display all Matches.
    """
    def get(self):
        matches = Match.all().order('event').fetch(100)
        
        template_values = {
            "matches": matches,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/matches/list.html')
        self.response.out.write(template.render(path, template_values))
        
class MatchDetail(webapp.RequestHandler):
    """
    Display a Match.
    """
    def get(self, match_key):
        
        if not match_key:
            return self.redirect("/")
        
        memcache_key = "match_detail_%s" % match_key
        html = memcache.get(memcache_key)
        
        if html is None:
            match = Match.get_by_key_name(match_key)
            
            if not match:
                return self.redirect("/error/404")
            
            match.unpack_json()

            tbavideo = None
            if len(match.tba_videos) > 0:
                tbavideo = TBAVideoHelper(match)
            
            template_values = {
                "match": match,
                "tbavideo": tbavideo,
            }
            
            path = os.path.join(os.path.dirname(__file__), '../templates/match_details.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.add(memcache_key, html, 86400)
        
        self.response.out.write(html)
        
