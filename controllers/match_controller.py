import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import tba_config
from base_controller import BaseHandler, CacheableHandler
from models.event import Event
from models.match import Match

class MatchDetail(CacheableHandler):
    """
    Display a Match.
    """
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24
        self._cache_key = "match_detail_{}" # (match_key)
        self._cache_version = 1

    def get(self, match_key):
        if not match_key:
            return self.redirect("/")

        self._cache_key = self._cache_key.format(match_key)
        super(MatchDetail, self).get(match_key)
    
    def _render(self, match_key):
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
        return template.render(path, template_values)
