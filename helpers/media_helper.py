import logging
import re
import json

from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup
from consts.media_type import MediaType


class MediaHelper(object):
    @classmethod
    def partial_media_dict_from_url(self, url):
        """
        Takes a url, and turns it into a partial Media object dict
        """
        media_dict = {}

        if 'chiefdelphi.com/media/photos/' in url:
            media_dict['media_type_enum'] = MediaType.CD_PHOTO
            media_dict['media_id'] = re.match(r'.*chiefdelphi.com\/media\/photos\/(\d+)', url).group(1)

            urlfetch_result = urlfetch.fetch(url, deadline=10)
            if urlfetch_result.status_code != 200:
                logging.warning('Unable to retrieve url: {}'.format(url))
                return None

            # parse html for the image url
            soup = BeautifulSoup(urlfetch_result.content,
                                 convertEntities=BeautifulSoup.HTML_ENTITIES)
            image_url = "http://www.chiefdelphi.com{}".format(soup.find('a', {'target': 'cdmLargePic'})['href'])
            link_url = "http://www.chiefdelphi.com/media/photos/{}".format(media_dict['media_id'])
            details = {'image_url': image_url,
                       'link_url': link_url}
            media_dict['details_json'] = json.dumps(details)
        elif 'youtube.com' in url:
            media_dict['media_type_enum'] = MediaType.YOUTUBE

            youtube_id = None
            regex1 = re.match(r".*youtu\.be\/(.*)", url)
            if regex1 is not None:
                youtube_id = regex1.group(1)
            else:
                regex2 = re.match(r".*v=([a-zA-Z0-9_-]*)", url)
                if regex2 is not None:
                    youtube_id = regex2.group(1)
            if youtube_id is None:
                logging.warning("Unable to get YouTube id from url: {}".format(url))
            media_dict['media_id'] = youtube_id
        else:
            logging.warning("Failed to determine media type from url: ".format(url))
            return None

        return media_dict
