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


class AccountInfoHandler(LoggedInHandler):
    """
    For getting account info.
    Only provides logged in status for now.
    """
    def get(self):
        self.response.headers['content-type'] = 'application/json; charset="utf-8"'
        user = self.user_bundle.user
        self.response.out.write(json.dumps({
            'logged_in': True if user else False,
            'user_id': user.user_id() if user else None
        }))


class AccountRegisterFCMToken(LoggedInHandler):
    """
    For adding/updating an FCM token
    """
    def post(self):
        if not self.user_bundle.user:
            self.response.set_status(401)
            return

        user_id = self.user_bundle.user.user_id()
        fcm_token = self.request.get('fcm_token')
        uuid = self.request.get('uuid')
        display_name = self.request.get('display_name')
        client_type = ClientType.WEB

        query = MobileClient.query(
                MobileClient.user_id == user_id,
                MobileClient.device_uuid == uuid,
                MobileClient.client_type == client_type)
        if query.count() == 0:
            # Record doesn't exist yet, so add it
            MobileClient(
                parent=ndb.Key(Account, user_id),
                user_id=user_id,
                messaging_id=fcm_token,
                client_type=client_type,
                device_uuid=uuid,
                display_name=display_name).put()
        else:
            # Record already exists, update it
            client = query.fetch(1)[0]
            client.messaging_id = fcm_token
            client.display_name = display_name
            client.put()


class AccountFavoritesHandler(LoggedInHandler):
    """
    For getting an account's favorites
    """
    def get(self, model_type):
        if not self.user_bundle.user:
            self.response.set_status(401)
            return

        favorites = Favorite.query(
            Favorite.model_type==int(model_type),
            ancestor=ndb.Key(Account, self.user_bundle.user.user_id())).fetch()
        self.response.out.write(json.dumps([ModelToDict.favoriteConverter(fav) for fav in favorites]))


class AccountFavoritesAddHandler(LoggedInHandler):
    """
    For adding an account's favorites
    """
    def post(self):
        if not self.user_bundle.user:
            self.response.set_status(401)
            return

        model_type = int(self.request.get("model_type"))
        model_key = self.request.get("model_key")
        user_id = self.user_bundle.user.user_id()

        fav = Favorite(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            model_key=model_key,
            model_type=model_type
        )
        MyTBAHelper.add_favorite(fav)


class AccountFavoritesDeleteHandler(LoggedInHandler):
    """
    For deleting an account's favorites
    """
    def post(self):
        if not self.user_bundle.user:
            self.response.set_status(401)
            return

        model_key = self.request.get("model_key")
        model_type = int(self.request.get("model_type"))
        user_id = self.user_bundle.user.user_id()

        MyTBAHelper.remove_favorite(user_id, model_key, model_type)


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


class TypeaheadHandler(CacheableHandler):
    """
    Currently just returns a list of all teams and events
    Needs to be optimized at some point.
    Tried a trie but the datastructure was too big to
    fit into memcache efficiently
    """
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "typeahead_entries:{}"  # (search_key)
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(TypeaheadHandler, self).__init__(*args, **kw)
        self._cache_expiration = self.CACHE_HEADER_LENGTH

    def get(self, search_key):
        import urllib2
        search_key = urllib2.unquote(search_key)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(search_key)
        super(TypeaheadHandler, self).get(search_key)

    def _render(self, search_key):
        self.response.headers['content-type'] = 'application/json; charset="utf-8"'

        entry = TypeaheadEntry.get_by_id(search_key)
        if entry is None:
            return '[]'
        else:
            self._last_modified = entry.updated
            return entry.data_json


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


class YouTubePlaylistHandler(LoggedInHandler):
    """
    For Hitting the YouTube API to get a list of video keys associated with a playlist
    """
    def get(self):
        if not self.user_bundle.user:
            self.response.set_status(401)
            return

        playlist_id = self.request.get("playlist_id")
        if not playlist_id:
            self.response.set_status(400)
            return

        video_ids = []
        headers = {}
        yt_key = Sitevar.get_by_id("google.secrets")
        if not yt_key:
            self.response.set_status(500)
            return

        next_page_token = ""

        # format with playlist id, page token, api key
        url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={}&&pageToken={}&fields=items%2Fsnippet%2FresourceId%2Citems%2Fsnippet%2Ftitle%2CnextPageToken&key={}"

        while True:
            try:
                result = urlfetch.fetch(url.format(playlist_id, next_page_token, yt_key.contents["api_key"]),
                                        headers=headers,
                                        deadline=5)
            except Exception, e:
                self.response.set_status(500)
                return []

            if result.status_code != 200:
                self.response.set_status(result.status_code)
                return []

            video_result = json.loads(result.content)
            video_ids += [video for video in video_result["items"] if video["snippet"]["resourceId"]["kind"] == "youtube#video"]

            if "nextPageToken" not in video_result:
                break
            next_page_token = video_result["nextPageToken"]

        self.response.out.write(json.dumps(video_ids))


class AllowedApiWriteEventsHandler(LoggedInHandler):
    """
    Get the events the current user is allowed to edit via the trusted API
    """
    def get(self):
        if not self.user_bundle.user:
            self.response.out.write(json.dumps([]))
            return

        now = datetime.datetime.now()
        auth_tokens = ApiAuthAccess.query(ApiAuthAccess.owner == self.user_bundle.account.key,
                                          ndb.OR(ApiAuthAccess.expiration == None, ApiAuthAccess.expiration >= now)).fetch()
        event_keys = []
        for token in auth_tokens:
            event_keys.extend(token.event_list)

        events = ndb.get_multi(event_keys)
        details = []
        for event in events:
            details.append({'value': event.key_name, 'label': "{} {}".format(event.year, event.name)})
        self.response.out.write(json.dumps(details))


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
