import logging
import os
import json
import time

import datetime

from base_controller import CacheableHandler, LoggedInHandler
from consts.client_type import ClientType
from consts.playoff_type import PlayoffType
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from helpers.model_to_dict import ModelToDict
from helpers.mytba_helper import MyTBAHelper
from models.account import Account
from models.api_auth_access import ApiAuthAccess
from models.event import Event
from models.favorite import Favorite
from models.mobile_client import MobileClient
from models.sitevar import Sitevar
from models.typeahead_entry import TypeaheadEntry


class LiveEventHandler(CacheableHandler):
    """
    Returns the necessary details to render live components
    Uses timestamp for aggressive caching
    """
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "live-event:{}:{}"  # (event_key, timestamp)
    CACHE_HEADER_LENGTH = 60 * 10

    def __init__(self, *args, **kw):
        super(LiveEventHandler, self).__init__(*args, **kw)
        self._cache_expiration = self.CACHE_HEADER_LENGTH

    def get(self, event_key, timestamp):
        if int(timestamp) > time.time():
            self.abort(404)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(event_key, timestamp)
        super(LiveEventHandler, self).get(event_key, timestamp)

    def _render(self, event_key, timestamp):
        self.response.headers['content-type'] = 'application/json; charset="utf-8"'

        event = Event.get_by_id(event_key)

        matches = []
        for match in event.matches:
            matches.append({
                'name': match.short_name,
                'alliances': match.alliances,
                'order': match.play_order,
                'time_str': match.time_string,
            })

        event_dict = {
#             'rankings': event.rankings,
#             'matchstats': event.matchstats,
            'matches': matches,
        }

        return json.dumps(event_dict)


class EventRemapTeamsHandler(CacheableHandler):
    """
    Returns the current team remapping for an event
    """
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "remap_teams_{}"  # (event_key)
    CACHE_HEADER_LENGTH = 1

    def __init__(self, *args, **kw):
        super(EventRemapTeamsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 1

    def get(self, event_key):
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(event_key)
        super(EventRemapTeamsHandler, self).get(event_key)

    def _render(self, event_key):
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        event = Event.get_by_id(event_key)
        if not event:
            return json.dumps(None)

        return json.dumps(event.remap_teams)


class WebcastHandler(CacheableHandler):
    """
    Returns the HTML necessary to generate the webcast embed for a given event
    """
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "webcast_{}_{}"  # (event_key)
    CACHE_HEADER_LENGTH = 60 * 5

    def __init__(self, *args, **kw):
        super(WebcastHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def get(self, event_key, webcast_number):
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(event_key, webcast_number)
        super(WebcastHandler, self).get(event_key, webcast_number)

    def _render(self, event_key, webcast_number):
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')

        output = {}
        if not webcast_number.isdigit():
            return json.dumps(output)
        webcast_number = int(webcast_number) - 1

        event = Event.get_by_id(event_key)
        if event and event.webcast:
            webcast = event.webcast[webcast_number]
            if 'type' in webcast and 'channel' in webcast:
                output['player'] = self._renderPlayer(webcast)
        else:
            special_webcasts_future = Sitevar.get_by_id_async('gameday.special_webcasts')
            special_webcasts = special_webcasts_future.get_result()
            if special_webcasts:
                special_webcasts = special_webcasts.contents['webcasts']
            else:
                special_webcasts = []

            special_webcasts_dict = {}
            for webcast in special_webcasts:
                special_webcasts_dict[webcast['key_name']] = webcast

            if event_key in special_webcasts_dict:
                webcast = special_webcasts_dict[event_key]
                if 'type' in webcast and 'channel' in webcast:
                    output['player'] = self._renderPlayer(webcast)

        return json.dumps(output)

    def _renderPlayer(self, webcast):
        webcast_type = webcast['type']
        template_values = {'webcast': webcast}

        path = os.path.join(os.path.dirname(__file__), '../templates/webcast/' + webcast_type + '.html')
        return template.render(path, template_values)

    def memcacheFlush(self, event_key):
        keys = [self._render_cache_key(self.CACHE_KEY_FORMAT.format(event_key, n)) for n in range(10)]
        memcache.delete_multi(keys)
        return keys


class PlayoffTypeGetHandler(CacheableHandler):
    """
    Returns the possible playoff types, formatted for EventWizard dropdown
    """
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "playoff_types"
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def get(self):
        types = []
        for type_enum, type_name in PlayoffType.type_names.iteritems():
            types.append({'value': type_enum, 'label': type_name})
        self.response.out.write(json.dumps(types))
