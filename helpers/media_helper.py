import logging
import re
import json

from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup
from consts.media_type import MediaType


class MediaParser(object):
    CD_PHOTO_THREAD_URL_PATTERN = 'chiefdelphi.com/media/photos/'
    YOUTUBE_URL_PATTERN = 'youtube.com'

    @classmethod
    def partial_media_dict_from_url(cls, url):
        """
        Takes a url, and turns it into a partial Media object dict
        """
        media_dict = {}

        if cls.CD_PHOTO_THREAD_URL_PATTERN in url:
            media_dict['media_type_enum'] = MediaType.CD_PHOTO_THREAD
            foreign_key = cls._parse_cdphotothread_foreign_key(url)
            if foreign_key is None:
                logging.warning("Failed to determine foreign_key from url: {}".format(url))
                return None
            media_dict['foreign_key'] = foreign_key

            urlfetch_result = urlfetch.fetch(url, deadline=10)
            if urlfetch_result.status_code != 200:
                logging.warning('Unable to retrieve url: {}'.format(url))
                return None

            image_partial = cls._parse_cdphotothread_image_partial(urlfetch_result.content)
            if image_partial is None:
                logging.warning("Failed to determine image_partial from the page: {}".format(url))
                return None
            media_dict['details_json'] = json.dumps({'image_partial': image_partial})
        elif cls.YOUTUBE_URL_PATTERN in url:
            media_dict['media_type_enum'] = MediaType.YOUTUBE
            foreign_key = cls._parse_youtube_foreign_key(url)
            if foreign_key is None:
                logging.warning("Failed to determine foreign_key from url: {}".format(url))
                return None
            media_dict['foreign_key'] = foreign_key
        else:
            logging.warning("Failed to determine media type from url: {}".format(url))
            return None

        return media_dict

    @classmethod
    def _parse_cdphotothread_foreign_key(cls, url):
        regex1 = re.match(r'.*chiefdelphi.com\/media\/photos\/(\d+)', url)
        if regex1 is not None:
            return regex1.group(1)
        else:
            return None

    @classmethod
    def _parse_cdphotothread_image_partial(cls, html):
        # parse html for the image url
        soup = BeautifulSoup(html,
                             convertEntities=BeautifulSoup.HTML_ENTITIES)
        element = soup.find('a', {'target': 'cdmLargePic'})
        if element is not None:
            partial_url = element['href']
        else:
            return None

        # partial_url looks something like: "/media/img/774/774d98c80dcf656f2431b2e9186f161a_l.jpg"
        # we want "774/774d98c80dcf656f2431b2e9186f161a_l.jpg"
        image_partial = re.match(r'\/media\/img\/(.*)', partial_url)
        if image_partial is not None:
            return image_partial.group(1)
        else:
            return None

    @classmethod
    def _parse_youtube_foreign_key(cls, url):
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
