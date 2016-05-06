import json
import logging
import re

from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup
from consts.media_type import MediaType


class MediaHelper(object):
    SOCIAL_SORT_ORDER = {
        MediaType.FACEBOOK_PROFILE: 0,
        MediaType.YOUTUBE_CHANNEL: 1,
        MediaType.TWITTER_PROFILE: 2,
        MediaType.GITHUB_PROFILE: 3,
    }

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

    @classmethod
    def get_images(cls, medias):
        return filter(lambda m: m.media_type_enum in MediaType.image_types, medias)

    @classmethod
    def get_socials(cls, medias):
        return filter(lambda m: m.media_type_enum in MediaType.social_types, medias)

    @classmethod
    def social_media_sorter(cls, media):
        return cls.SOCIAL_SORT_ORDER.get(media.media_type_enum, 1000)


class MediaParser(object):
    CD_PHOTO_THREAD_URL_PATTERNS = ['chiefdelphi.com/media/photos/']
    YOUTUBE_URL_PATTERNS = ['youtube.com', 'youtu.be']
    IMGUR_URL_PATTERNS = ['imgur.com/']

    # Dict that maps Social media types -> tuple of regex pattern and group # of foreign key
    SOCIAL_FOREIGN_KEY_PATTERNS = {
        MediaType.FACEBOOK_PROFILE: (r".*facebook.com\/(.*)(\/(.*))?", 1),
        MediaType.TWITTER_PROFILE: (r".*twitter.com\/(.*)(\/(.*))?", 1),
        MediaType.YOUTUBE_CHANNEL: (r".*youtube.com\/user\/(.*)(\/(.*))?", 1),
        MediaType.GITHUB_PROFILE: (r".*github.com\/(.*)(\/(.*))?", 1),
    }

    # Social profile URL patterns that map a URL -> Profile type
    SOCIAL_URL_PATTERNS = {
        'facebook.com/': MediaType.FACEBOOK_PROFILE,
        'twitter.com/': MediaType.TWITTER_PROFILE,
        'youtube.com/user': MediaType.YOUTUBE_CHANNEL,
        'github.com/': MediaType.GITHUB_PROFILE,
    }

    @classmethod
    def partial_media_dict_from_url(cls, url):
        """
        Takes a url, and turns it into a partial Media object dict
        """

        # Test social profile urls first
        # Because this YouTube URL is more strict than the video one
        for s, type in cls.SOCIAL_URL_PATTERNS.iteritems():
            if s in url:
                return cls._partial_social_dict(type, url)

        if any(s in url for s in cls.CD_PHOTO_THREAD_URL_PATTERNS):
            return cls._partial_media_dict_from_cd_photo_thread(url)
        elif any(s in url for s in cls.YOUTUBE_URL_PATTERNS):
            return cls._partial_media_dict_from_youtube(url)
        elif any(s in url for s in cls.IMGUR_URL_PATTERNS):
            return cls._partial_media_dict_from_imgur(url)
        else:
            logging.warning("Failed to determine media type from url: {}".format(url))
            return None

    @classmethod
    def _partial_social_dict(cls, social_type, url):
        social_dict = {'media_type_enum': social_type}
        foreign_key = cls._parse_social_foreign_key(social_type, url)
        if foreign_key is None:
            logging.warning("Failed to determine foreign_key from url: {}".format(url))
            return None
        social_dict['is_social'] = True
        social_dict['foreign_key'] = foreign_key
        social_dict['site_name'] = MediaType.type_names[social_type]
        social_dict['profile_url'] = MediaType.profile_urls[social_type].format(foreign_key)

        return social_dict

    @classmethod
    def _parse_social_foreign_key(cls, social_type, url):
        foreign_key = None
        regex = re.match(cls.SOCIAL_FOREIGN_KEY_PATTERNS[social_type][0], url)
        if regex is not None:
            foreign_key = regex.group(cls.SOCIAL_FOREIGN_KEY_PATTERNS[social_type][1])

        if foreign_key is None:
            return None
        else:
            # Remove trailing slashes in the URL if necessary
            return foreign_key.replace('/', '')

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
        media_dict['media_type_enum'] = MediaType.YOUTUBE_VIDEO
        foreign_key = cls._parse_youtube_foreign_key(url)
        if foreign_key is None:
            logging.warning("Failed to determine foreign_key from url: {}".format(url))
            return None
        media_dict['foreign_key'] = foreign_key

        return media_dict

    @classmethod
    def _partial_media_dict_from_imgur(cls, url):
        media_dict = {}
        media_dict['media_type_enum'] = MediaType.IMGUR
        foreign_key = cls._parse_imgur_foreign_key(url)
        if foreign_key is None:
            logging.warning("Failed to determine imgur foreign key from url {}".format(url))
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
        html = html.decode("utf-8", "replace")

        # parse html for the image url
        soup = BeautifulSoup(html,
                             convertEntities=BeautifulSoup.HTML_ENTITIES)

        # 2014-07-15: CD doesn't properly escape the photo title, which breaks the find() for cdmLargePic element below
        # Fix by removing all instances of the photo title from the HTML
        photo_title = soup.find('div', {'id': 'cdm_single_photo_title'}).text
        cleaned_soup = BeautifulSoup(html.replace(photo_title, ''),
                                     convertEntities=BeautifulSoup.HTML_ENTITIES)

        element = cleaned_soup.find('a', {'target': 'cdmLargePic'})
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

    @classmethod
    def _parse_imgur_foreign_key(cls, url):
        # Check imgur.com urls
        regex = re.match(r".*imgur.com\/(\w+)\/?\Z", url)

        if regex:
            return regex.group(1)

        # Check i.imgur.com/asdf.{jpg,png,whatever} direct image urls
        regex = re.match(r".*imgur.com\/(\w+)\.\w+\Z", url)
        return regex.group(1) if regex else None
