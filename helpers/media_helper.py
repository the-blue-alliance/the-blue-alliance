import json
import logging
import re

from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup
from consts.media_type import MediaType


class MediaHelper(object):
    @classmethod
    def group_by_slugname(cls, medias):
        medias_by_slugname = {}
        for media in medias:
            slugname = media.slug_name
            if slugname in medias_by_slugname:
                medias_by_slugname[slugname].append(media)
            else:
                medias_by_slugname[slugname] = [media]
        return medias_by_slugname


class MediaParser(object):
    CD_PHOTO_THREAD_URL_PATTERNS = ['chiefdelphi.com/media/photos/']
    YOUTUBE_URL_PATTERNS = ['youtube.com', 'youtu.be']

    @classmethod
    def partial_media_dict_from_url(cls, url):
        """
        Takes a url, and turns it into a partial Media object dict
        """
        if any(s in url for s in cls.CD_PHOTO_THREAD_URL_PATTERNS):
            return cls._partial_media_dict_from_cd_photo_thread(url)
        elif any(s in url for s in cls.YOUTUBE_URL_PATTERNS):
            return cls._partial_media_dict_from_youtube(url)
        else:
            logging.warning("Failed to determine media type from url: {}".format(url))
            return None

    @classmethod
    def _partial_media_dict_from_cd_photo_thread(cls, url):
        media_dict = {}
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

        return media_dict

    @classmethod
    def _partial_media_dict_from_youtube(cls, url):
        media_dict = {}
        media_dict['media_type_enum'] = MediaType.YOUTUBE
        foreign_key = cls._parse_youtube_foreign_key(url)
        if foreign_key is None:
            logging.warning("Failed to determine foreign_key from url: {}".format(url))
            return None
        media_dict['foreign_key'] = foreign_key

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
        """
        Input: the HTML from the thread page
        ex: http://www.chiefdelphi.com/media/photos/38464,

        returns the url of the image in the thread
        ex: http://www.chiefdelphi.com/media/img/3f5/3f5db241521ae5f2636ff8460f277997_l.jpg
        """
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
