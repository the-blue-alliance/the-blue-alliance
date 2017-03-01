import json
import logging

from google.appengine.api import urlfetch
from models.sitevar import Sitevar


class WebcastOnlineHelper(object):
    @classmethod
    def add_online_status(cls, event):
        for webcast in event.webcast:
            webcast['status'] = 'unknown'
            if webcast['type'] == 'twitch':
                twitch_secrets = Sitevar.get_or_insert('twitch.secrets')
                client_id = None
                if twitch_secrets and twitch_secrets.contents:
                    client_id = twitch_secrets.contents.get('client_id')
                if client_id:
                    try:
                        url = 'https://api.twitch.tv/kraken/streams/{}?client_id={}'.format(webcast['channel'], client_id)
                        result = urlfetch.fetch(url)
                    except Exception, e:
                        logging.error("URLFetch failed for: {}".format(url))
                        continue
                else:
                    logging.warning("Must have Twitch Client ID")
                    continue

                if result.status_code == 200:
                    response = json.loads(result.content)
                    if response['stream']:
                        webcast['status'] = 'online'
                    else:
                        webcast['status'] = 'offline'
