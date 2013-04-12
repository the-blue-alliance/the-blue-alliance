import os
import json
import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import BaseHandler, CacheableHandler

from models.event import Event
from models.team import Team
from models.sitevar import Sitevar
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
        self._cache_key = "typeahead_entries"
        self._cache_version = 1

    def get(self):
        self.response.headers['Cache-Control'] = "public, max-age=%d" % (6*60*60)
        self.response.headers['Pragma'] = 'Public'
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')        
        super(TypeaheadHandler, self).get()
        
    @ndb.tasklet
    def get_events_async(self):
        event_keys = yield Event.query().order(-Event.year).order(Event.name).fetch_async(keys_only=True)
        events = yield ndb.get_multi_async(event_keys)
        raise ndb.Return(events)
        
    @ndb.tasklet
    def get_teams_async(self):
        team_keys = yield Team.query().order(Team.team_number).fetch_async(keys_only=True)
        teams = yield ndb.get_multi_async(team_keys)
        raise ndb.Return(teams)
        
    @ndb.toplevel
    def get_events_and_teams(self):
        events, teams = yield self.get_events_async(), self.get_teams_async()
        raise ndb.Return((events, teams))

    def _render(self):
        events, teams = self.get_events_and_teams()
        
        results = []
        for event in events:
            results.append({'id': event.key_name, 'name': '%s %s [%s]' % (event.year, event.name, event.event_short.upper())})
        for team in teams:
            if not team.nickname:
                nickname = "Team %s" % team.team_number
            else:
                nickname = team.nickname
            results.append({'id': team.team_number, 'name': '%s | %s' % (team.team_number, nickname)})
            
        return json.dumps(results)

    
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

