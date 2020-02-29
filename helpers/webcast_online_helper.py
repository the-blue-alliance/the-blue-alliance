import base64
import json
import logging
import tba_config

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

from models.sitevar import Sitevar


class WebcastOnlineHelper(object):
    @classmethod
    @ndb.toplevel
    def add_online_status(cls, webcasts):
        for webcast in webcasts:
            cls.add_online_status_async(webcast)

    @classmethod
    @ndb.tasklet
    def add_online_status_async(cls, webcast):
        memcache_key = 'webcast_status:{}:{}:{}'.format(webcast['type'], webcast.get('channel'), webcast.get('file'))
        cached_webcast = memcache.get(memcache_key)
        if cached_webcast:
            if 'status' in cached_webcast:
                webcast['status'] = cached_webcast['status']
            if 'stream_title' in cached_webcast:
                webcast['stream_title'] = cached_webcast['stream_title']
            if 'viewer_count' in cached_webcast:
                webcast['viewer_count'] = cached_webcast['viewer_count']

            return

        webcast['status'] = 'unknown'
        webcast['stream_title'] = None
        webcast['viewer_count'] = None
        if not tba_config.CONFIG['update-webcast-online-status']:
            return
        if webcast['type'] == 'twitch':
            yield cls._add_twitch_status_async(webcast)
        elif webcast['type'] == 'ustream':
            yield cls._add_ustream_status_async(webcast)
        elif webcast['type'] == 'youtube':
            yield cls._add_youtube_status_async(webcast)
        # Livestream charges for their API. Go figure.
        # elif webcast['type'] == 'livestream':
        #     yield cls._add_livestream_status_async(webcast)

        memcache.set(memcache_key, webcast, 60*5)

    @classmethod
    @ndb.tasklet
    def _add_twitch_status_async(cls, webcast):
        twitch_secrets = Sitevar.get_or_insert('twitch.secrets')
        client_id = None
        if twitch_secrets and twitch_secrets.contents:
            client_id = twitch_secrets.contents.get('client_id')
        if client_id:
            try:
                url = 'https://api.twitch.tv/helix/streams?user_login={}'.format(webcast['channel'])
                rpc = urlfetch.create_rpc()
                result = yield urlfetch.make_fetch_call(rpc, url, headers={
                    'Client-ID': client_id,
                })
            except Exception, e:
                logging.error("URLFetch failed for: {}".format(url))
                raise ndb.Return(None)
        else:
            logging.warning("Must have Twitch Client ID")
            raise ndb.Return(None)

        if result.status_code == 200:
            response = json.loads(result.content)
            if response['data']:
                webcast['status'] = 'online'
                webcast['stream_title'] = response['data'][0]['title']
                webcast['viewer_count'] = response['data'][0]['viewer_count']
            else:
                webcast['status'] = 'offline'
        else:
            logging.warning("Twitch status failed with code: {}".format(result.status_code))
            logging.warning(result.content)

        raise ndb.Return(None)

    @classmethod
    @ndb.tasklet
    def _add_ustream_status_async(cls, webcast):
        try:
            url = 'https://api.ustream.tv/channels/{}.json'.format(webcast['channel'])
            rpc = urlfetch.create_rpc()
            result = yield urlfetch.make_fetch_call(rpc, url)
        except Exception, e:
            logging.error("URLFetch failed for: {}".format(url))
            raise ndb.Return(None)

        if result.status_code == 200:
            response = json.loads(result.content)
            if response['channel']:
                webcast['status'] = 'online' if response['channel']['status'] == 'live' else 'offline'
                webcast['stream_title'] = response['channel']['title']
            else:
                webcast['status'] = 'offline'
        else:
            logging.warning("Ustream status failed with code: {}".format(result.status_code))
            logging.warning(result.content)

        raise ndb.Return(None)

    @classmethod
    @ndb.tasklet
    def _add_youtube_status_async(cls, webcast):
        google_secrets = Sitevar.get_or_insert('google.secrets')
        api_key = None
        if google_secrets and google_secrets.contents:
            api_key = google_secrets.contents.get('api_key')
        if api_key:
            try:
                url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}'.format(webcast['channel'], api_key)
                rpc = urlfetch.create_rpc()
                result = yield urlfetch.make_fetch_call(rpc, url)
            except Exception, e:
                logging.error("URLFetch failed for: {}".format(url))
                raise ndb.Return(None)
        else:
            logging.warning("Must have Google API key")
            raise ndb.Return(None)

        if result.status_code == 200:
            response = json.loads(result.content)
            if response['items']:
                webcast['status'] = 'online' if response['items'][0]['snippet']['liveBroadcastContent'] == 'live' else 'offline'
                webcast['stream_title'] = response['items'][0]['snippet']['title']
            else:
                webcast['status'] = 'offline'
        else:
            logging.warning("YouTube status failed with code: {}".format(result.status_code))
            logging.warning(result.content)

        raise ndb.Return(None)

    @classmethod
    @ndb.tasklet
    def _add_livestream_status_async(cls, webcast):
        livestream_secrets = Sitevar.get_or_insert('livestream.secrets')
        api_key = None
        if livestream_secrets and livestream_secrets.contents:
            api_key = livestream_secrets.contents.get('api_key')
        if api_key:
            try:
                url = 'https://livestreamapis.com/v2/accounts/{}/events/{}'.format(webcast['channel'], webcast['file'])
                base64string = base64.encodestring('{}:'.format(api_key)).replace('\n','')
                headers = {
                    'Authorization': 'Basic {}'.format(base64string)
                }
                rpc = urlfetch.create_rpc()
                result = yield urlfetch.make_fetch_call(rpc, url, headers=headers)
            except Exception, e:
                logging.error("URLFetch failed for: {}".format(url))
                raise ndb.Return(None)
        else:
            logging.warning("Must have Livestream API key")
            raise ndb.Return(None)

        if result.status_code == 200:
            response = json.loads(result.content)
            if response['items']:
                webcast['status'] = 'online' if response['items'][0]['snippet']['liveBroadcastContent'] == 'live' else 'offline'
                webcast['stream_title'] = response['items'][0]['snippet']['title']
            else:
                webcast['status'] = 'offline'
        else:
            logging.warning("Livestream status failed with code: {}".format(result.status_code))
            logging.warning(result.content)

        raise ndb.Return(None)
