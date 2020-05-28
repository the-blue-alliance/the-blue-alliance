import logging
import re

from google.appengine.api import urlfetch


class WebcastParser(object):
    TWITCH_URL_PATTERNS = ['twitch.tv/']
    YOUTUBE_URL_PATTERNS = ['youtube.com/', 'youtu.be/']
    USTREAM_URL_PATTERNS = ['ustream.tv/']
    LIVESTREAM_URL_PATTERNS = ['livestream.com/']

    @classmethod
    def webcast_dict_from_url(cls, url):
        """
        Takes a url, and turns it into a webcast dict (as defined in models.event)
        """
        if any(s in url for s in cls.TWITCH_URL_PATTERNS):
            return cls._webcast_dict_from_twitch(url)
        elif any(s in url for s in cls.YOUTUBE_URL_PATTERNS):
            return cls._webcast_dict_from_youtube(url)
        elif any(s in url for s in cls.USTREAM_URL_PATTERNS):
            return cls._webcast_dict_from_ustream(url)
        elif any(s in url for s in cls.LIVESTREAM_URL_PATTERNS):
            return cls._webcast_dict_from_livestream(url)
        else:
            logging.warning("Failed to determine webcast type from url: {}".format(url))
            return None

    @classmethod
    def _webcast_dict_from_twitch(cls, url):
        channel = cls._parse_twitch_channel(url)
        if channel is None:
            logging.warning("Failed to determine channel from url: {}".format(url))
            return None
        webcast_dict = {
            'type': 'twitch',
            'channel': channel,
        }
        return webcast_dict

    @classmethod
    def _webcast_dict_from_youtube(cls, url):
        channel = cls._parse_youtube_channel(url)
        if channel is None:
            logging.warning("Failed to determine channel from url: {}".format(url))
            return None
        webcast_dict = {
            'type': 'youtube',
            'channel': channel,
        }
        return webcast_dict

    @classmethod
    def _webcast_dict_from_ustream(cls, url):
        urlfetch_result = urlfetch.fetch(url, deadline=10)
        if urlfetch_result.status_code != 200:
            logging.warning('Unable to retrieve url: {}'.format(url))
            return None

        channel = cls._parse_ustream_channel(urlfetch_result.content)
        if channel is None:
            logging.warning("Failed to determine channel from url: {}".format(url))
            return None
        webcast_dict = {
            'type': 'ustream',
            'channel': channel,
        }
        return webcast_dict

    @classmethod
    def _webcast_dict_from_livestream(cls, url):
        urlfetch_result = urlfetch.fetch(url, deadline=10)
        if urlfetch_result.status_code != 200:
            logging.warning('Unable to retrieve url: {}'.format(url))
            return None

        channel_and_file = cls._parse_livestream_channel(urlfetch_result.content)
        if channel_and_file is None:
            logging.warning("Failed to determine channel and file from url: {}".format(url))
            return None
        channel, file = channel_and_file
        webcast_dict = {
            'type': 'livestream',
            'channel': channel,
            'file': file,
        }
        return webcast_dict

    @classmethod
    def _parse_twitch_channel(cls, url):
        regex1 = re.match(r'.*twitch.tv\/(\w+)', url)
        if regex1 is not None:
            return regex1.group(1)
        else:
            return None

    @classmethod
    def _parse_youtube_channel(cls, url):
        youtube_id = None
        regex1 = re.match(r".*youtu\.be\/(.*)", url)
        if regex1 is not None:
            youtube_id = regex1.group(1)
        else:
            regex2 = re.match(r".*v=([a-zA-Z0-9_-]*)", url)
            if regex2 is not None:
                youtube_id = regex2.group(1)

        if not youtube_id:
            return None
        else:
            return youtube_id

    @classmethod
    def _parse_ustream_channel(cls, html):
        from bs4 import BeautifulSoup

        html = html.decode("utf-8", "replace")

        # parse html for the channel id
        soup = BeautifulSoup(html, "html.parser")
        el = soup.find('meta', {'name': 'ustream:channel_id'})
        if el is None:
            return None
        else:
            channel_id = el['content']
            if channel_id:
                return channel_id
            else:
                return None

    @classmethod
    def _parse_livestream_channel(cls, html):
        from bs4 import BeautifulSoup

        html = html.decode("utf-8", "replace")

        # parse html for the channel id
        soup = BeautifulSoup(html, "html.parser")
        el = soup.find('meta', {'name': 'twitter:player'})
        if el is None:
            return None
        else:
            regex1 = re.match(r'.*livestream.com\/accounts\/(\d+)\/events\/(\d+)', el['content'])
            if regex1 is not None:
                return regex1.group(1), regex1.group(2)
            else:
                return None
