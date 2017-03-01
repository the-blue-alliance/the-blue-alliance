import json
import logging

from google.appengine.ext import ndb
from google.appengine.api import urlfetch

from models.sitevar import Sitevar


class WebcastOnlineHelper(object):
    @classmethod
    @ndb.tasklet
    def add_online_status_async(cls, webcast):
        webcast['status'] = 'unknown'
        webcast['stream_title'] = None
        if webcast['type'] == 'twitch':
            cls._add_twitch_status_async(webcast)
        elif webcast['type'] == 'ustream':
            cls._add_ustream_status_async(webcast)

    @classmethod
    @ndb.tasklet
    def _add_twitch_status_async(cls, webcast):
        twitch_secrets = Sitevar.get_or_insert('twitch.secrets')
        client_id = None
        if twitch_secrets and twitch_secrets.contents:
            client_id = twitch_secrets.contents.get('client_id')
        if client_id:
            try:
                url = 'https://api.twitch.tv/kraken/streams/{}?client_id={}'.format(webcast['channel'], client_id)
                rpc = urlfetch.create_rpc()
                result = yield urlfetch.make_fetch_call(rpc, url)
            except Exception, e:
                logging.error("URLFetch failed for: {}".format(url))
                raise ndb.Return(None)
        else:
            logging.warning("Must have Twitch Client ID")
            raise ndb.Return(None)

        if result.status_code == 200:
            response = json.loads(result.content)
            if response['stream']:
                webcast['status'] = 'online'
                webcast['stream_title'] = response['stream']['channel']['status']
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
