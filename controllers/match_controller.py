import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import tba_config
from base_controller import BaseHandler
from models.event import Event
from models.match import Match

from helpers.template_wrapper import TemplateWrapper

class MatchDetail(BaseHandler):
    """
    Display a Match.
    """
    def get(self, match_key):
        
        if not match_key:
            return self.redirect("/")
        
        memcache_key = "match_detail_%s" % match_key
        html = memcache.get(memcache_key)
        
        if html is None:
            try:
                match_future = Match.get_by_id_async(match_key)
                event_future = Event.get_by_id_async(match_key.split("_")[0])
                match = match_future.get_result()
                event = event_future.get_result()
            except Exception, e:
                return self.redirect("/error/404")

            if not match:
                return self.redirect("/error/404")
            
            template_values = {
                "event": event,
                "match": match,
            }
            
            path = os.path.join(os.path.dirname(__file__), '../templates/match_details.html')
            html = TemplateWrapper.renderBasePage(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.add(memcache_key, html, 86400)
        
        self.response.out.write(html)
