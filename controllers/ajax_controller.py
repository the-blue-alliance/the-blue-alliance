import os
import json
import urllib2

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import BaseHandlerFB, CacheableHandler

from models.event import Event
from models.team import Team
from models.sitevar import Sitevar
from models.typeahead_entry import TypeaheadEntry
import tba_config


class TypeaheadHandler(CacheableHandler):
    """
    Currently just returns a list of all teams and events
    Needs to be optimized at some point.
    Tried a trie but the datastructure was too big to
    fit into memcache efficiently
    """
    def __init__(self, *args, **kw):
        super(TypeaheadHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24
        self._cache_key = "typeahead_entries:{}"
        self._cache_version = 1

    def get(self, search_key):
        search_key = urllib2.unquote(search_key)
        self._cache_key = self._cache_key.format(search_key)
        self.response.headers['Cache-Control'] = "public, max-age=%d" % (24*60*60)
        self.response.headers['Pragma'] = 'Public'
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        super(TypeaheadHandler, self).get(search_key)

    def _render(self, search_key):
        entry = TypeaheadEntry.get_by_id(search_key)
        if entry is None:
            return '[]'
        else:
            return entry.data_json


class WebcastHandler(CacheableHandler):
    """
    Returns the HTML necessary to generate the webcast embed for a given event
    """
    def __init__(self, *args, **kw):
        super(WebcastHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24
        self._cache_key = "webcast_{}_{}" # (event_key)
        self._cache_version = 1

    def get(self, event_key, webcast_number):
        webcast_number = int(webcast_number) - 1
        self._cache_key = self._cache_key.format(event_key, webcast_number)

        self.response.headers['Cache-Control'] = "public, max-age=%d" % (5*60)
        self.response.headers['Pragma'] = 'Public'
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')  

        super(WebcastHandler, self).get(event_key, webcast_number)
        
    def _render(self, event_key, webcast_number):
        event = Event.get_by_id(event_key)
        output = {}
        if event and event.webcast:
            webcast = event.webcast[webcast_number]
            if 'type' in webcast and 'channel' in webcast:
                output['player'] = self._renderPlayer(webcast)
        else:
            special_webcasts_future = Sitevar.get_by_id_async('gameday.special_webcasts')
            special_webcasts = special_webcasts_future.get_result()
            if special_webcasts:
                special_webcasts = special_webcasts.contents
            else:
                special_webcasts = {}
            if event_key in special_webcasts:
                webcast = special_webcasts[event_key]
                if 'type' in webcast and 'channel' in webcast:
                    output['player'] = self._renderPlayer(webcast)                   
                
        return json.dumps(output)
        
    def _renderPlayer(self, webcast):
        webcast_type = webcast['type']
        template_values = {'webcast': webcast}

        path = os.path.join(os.path.dirname(__file__), '../templates/webcast/' + webcast_type + '.html')
        return template.render(path, template_values)

    def memcacheFlush(self, event_key):
        keys = [self.cache_key.format(event_key, n) for n in range(10)]
        memcache.delete_multi(keys)
        return keys

