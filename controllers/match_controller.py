import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

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
    def get(self, key_name):
        
        memcache_key = "match_detail_%s" % key_name
        html = memcache.get(memcache_key)
        
        if html is None:
            match = Match.get_by_key_name(key_name)
            if not match:
                # TODO: Add real "match not found" template
                self.response.out.write("404.")
                return None
            
            match.unpack_json()
            
            tbavideo = None
            if len(match.tba_videos) > 0:
                tbavideo = TBAVideoHelper(match)
            
            #TODO: Remove this entirely, since the tbavideo class is being deprecated -gregmarra 31 Mar 2012
            try:
                if tbavideo is None:
                    if match.tbavideo_set.count() > 0:
                        tbavideo = match.tbavideo_set[0]
            except Exception, e:
                logging.error("Match didn't have tbavideo_set")
            
            template_values = {
                "match": match,
                "tbavideo": tbavideo,
            }
            
            path = os.path.join(os.path.dirname(__file__), '../templates/matches/details.html')
            html = template.render(path, template_values)
            memcache.add(memcache_key, html, 600)
        
        self.response.out.write(html)
        
