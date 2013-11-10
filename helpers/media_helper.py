import logging
import re
import json

from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup
from consts.media_type import MediaType


class MediaParser(object):
    @classmethod
    def partial_media_dict_from_url(cls, url):
        """
        Takes a url, and turns it into a partial Media object dict
        """
        media_dict = {}

        if 'chiefdelphi.com/media/photos/' in url:
            media_dict['media_type_enum'] = MediaType.CD_PHOTO_THREAD
            media_id = cls._parse_cdphotothread_media_id(url)
            if media_id is None:
                logging.warning("Failed to determine media_id from url: {}".format(url))
                return None
            media_dict['media_id'] = media_id

            urlfetch_result = urlfetch.fetch(url, deadline=10)
            if urlfetch_result.status_code != 200:
                logging.warning('Unable to retrieve url: {}'.format(url))
                return None

            image_url = cls._parse_cdphotothread_image_url(urlfetch_result.content)
            if image_url is None:
                logging.warning("Failed to determine image_url from the page: {}".format(url))
                return None
            details = {'image_url': image_url,
                       'link_url': "http://www.chiefdelphi.com/media/photos/{}".format(media_dict['media_id'])}
            media_dict['details_json'] = json.dumps(details)
        elif 'youtube.com' in url:
            media_dict['media_type_enum'] = MediaType.YOUTUBE
            media_id = cls._parse_youtube_media_id(url)
            if media_id is None:
                logging.warning("Failed to determine media_id from url: {}".format(url))
                return None
            media_dict['media_id'] = media_id
        else:
            logging.warning("Failed to determine media type from url: {}".format(url))
            return None

        return media_dict

    @classmethod
    def _parse_cdphotothread_media_id(cls, url):
        regex1 = re.match(r'.*chiefdelphi.com\/media\/photos\/(\d+)', url)
        if regex1 is not None:
            return regex1.group(1)
        else:
            return None

    @classmethod
    def _parse_cdphotothread_image_url(cls, html):
        # parse html for the image url
        soup = BeautifulSoup(html,
                             convertEntities=BeautifulSoup.HTML_ENTITIES)
        element = soup.find('a', {'target': 'cdmLargePic'})
        if element is not None:
            partial_url = element['href']
        else:
            return None
        return "http://www.chiefdelphi.com{}".format(partial_url)

    @classmethod
    def _parse_youtube_media_id(cls, url):
        youtube_id = None
        regex1 = re.match(r".*youtu\.be\/(.*)", url)
        if regex1 is not None:
            youtube_id = regex1.group(1)
        else:
            regex2 = re.match(r".*v=([a-zA-Z0-9_-]*)", url)
            if regex2 is not None:
                youtube_id = regex2.group(1)

        if youtube_id is None:
            return None
        else:
            return youtube_id
