import json
import logging
import re
from urllib import urlencode
from urlparse import urlparse

from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup
from consts.media_type import MediaType


class MediaHelper(object):
    SOCIAL_SORT_ORDER = {
        MediaType.FACEBOOK_PROFILE: 0,
        MediaType.YOUTUBE_CHANNEL: 1,
        MediaType.TWITTER_PROFILE: 2,
        MediaType.INSTAGRAM_PROFILE: 3,
        MediaType.GITHUB_PROFILE: 4,
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

    # Add MediaTypes to this list to indicate that they case case-sensitive (shouldn't be normalized to lower case)
    CASE_SENSITIVE_FOREIGN_KEYS = [MediaType.YOUTUBE_VIDEO, MediaType.IMGUR, MediaType.CD_PHOTO_THREAD]

    # Dict that maps media types -> list of tuple of regex pattern and group # of foreign key
    FOREIGN_KEY_PATTERNS = {
        MediaType.FACEBOOK_PROFILE: [(r".*facebook.com\/(.*)(\/(.*))?", 1)],
        MediaType.TWITTER_PROFILE: [(r".*twitter.com\/(.*)(\/(.*))?", 1)],
        MediaType.YOUTUBE_CHANNEL: [(r".*youtube.com\/user\/(.*)(\/(.*))?", 1),
                                    (r".*youtube.com\/c\/(.*)(\/(.*))?", 1),
                                    (r".*youtube.com\/(.*)(\/(.*))?", 1)],
        MediaType.GITHUB_PROFILE: [(r".*github.com\/(.*)(\/(.*))?", 1)],
        MediaType.YOUTUBE_VIDEO: [(r".*youtu\.be\/(.*)", 1), (r".*v=([a-zA-Z0-9_-]*)", 1)],
        MediaType.IMGUR: [(r".*imgur.com\/(\w+)\/?\Z", 1), (r".*imgur.com\/(\w+)\.\w+\Z", 1)],
        MediaType.INSTAGRAM_PROFILE: [(r".*instagram.com\/(.*)(\/(.*))?", 1)],
    }

    # Media URL patterns that map a URL -> Profile type (used to determine which type represents a given url)
    # This is a list because the order matters
    URL_PATTERNS = [
        ('facebook.com/', MediaType.FACEBOOK_PROFILE),
        ('twitter.com/', MediaType.TWITTER_PROFILE),
        ('youtube.com/user', MediaType.YOUTUBE_CHANNEL),
        ('youtube.com/c/', MediaType.YOUTUBE_CHANNEL),
        ('github.com/', MediaType.GITHUB_PROFILE),
        ('instagram.com/', MediaType.INSTAGRAM_PROFILE),
        ('chiefdelphi.com/media/photos/', MediaType.CD_PHOTO_THREAD),
        ('youtube.com/watch', MediaType.YOUTUBE_VIDEO),
        ('youtu.be', MediaType.YOUTUBE_VIDEO),
        ('imgur.com/', MediaType.IMGUR),

        # Keep this last, so it doesn't greedy match over other more specific youtube urls
        ('youtube.com/', MediaType.YOUTUBE_CHANNEL),
    ]

    # The default is to strip out all urlparams, but this is a white-list for exceptions
    ALLOWED_URLPARAMS = {
        MediaType.YOUTUBE_VIDEO: ['v'],
    }

    @classmethod
    def partial_media_dict_from_url(cls, url):
        """
        Takes a url, and turns it into a partial Media object dict
        """

        # Now, we can test for regular media type
        for s, media_type in cls.URL_PATTERNS:
            if s in url:
                if media_type == MediaType.CD_PHOTO_THREAD:
                    # CD images are special - they need to do an additional urlfetch because the given url
                    # doesn't contain the foreign key
                    return cls._partial_media_dict_from_cd_photo_thread(url)
                else:
                    return cls._create_media_dict(media_type, url)

        logging.warning("Failed to determine media type from url: {}".format(url))
        return None

    @classmethod
    def _create_media_dict(cls, media_type, url):
        """
        Build a media dict from the given url and media type
        This will parse the foreign key from the url and add other data about the media type
        """
        url = cls._sanitize_media_url(media_type, url)
        media_dict = {'media_type_enum': media_type}
        foreign_key = cls._parse_foreign_key(media_type, url)
        if foreign_key is None:
            logging.warning("Failed to determine {} foreign_key from url: {}".format(MediaType.type_names[media_type], url))
            return None
        foreign_key = foreign_key if media_type in cls.CASE_SENSITIVE_FOREIGN_KEYS else foreign_key.lower()
        media_dict['is_social'] = media_type in MediaType.social_types
        media_dict['foreign_key'] = foreign_key
        media_dict['site_name'] = MediaType.type_names[media_type]

        if media_type in MediaType.profile_urls:
            media_dict['profile_url'] = MediaType.profile_urls[media_type].format(foreign_key)

        return media_dict

    @classmethod
    def _parse_foreign_key(cls, media_type, url):
        """
        Uses FOREIGN_KEY_PATTERNS to extract the media foreign key from the given url
        Each index in the dict contains a list of valid patterns - tuples of (regex string, group #)
        """
        for pattern in cls.FOREIGN_KEY_PATTERNS[media_type]:
            regex = re.match(pattern[0], url)
            if regex is not None:
                foreign_key = regex.group(pattern[1])
                if foreign_key is not None:
                    # Remove trailing slashes in the URL if necessary
                    return foreign_key.replace('/', '')

        logging.warning("Failed to determine {} foreign_key from url: {}".format(MediaType.type_names[media_type], url))
        return None

    @classmethod
    def _sanitize_media_url(cls, media_type, url):
        media_url = url.strip()
        parsed = urlparse(media_url)
        clean_url = "{}://{}{}".format(parsed.scheme, parsed.netloc, parsed.path)

        # Add white-listed url params back in
        if media_type in cls.ALLOWED_URLPARAMS:
            whitelist = cls.ALLOWED_URLPARAMS[media_type]
            all_params = parsed.query.split('&')
            allowed_params = {}
            for param in all_params:
                if any(param.startswith(w+'=') for w in whitelist):
                    split = param.split('=')
                    allowed_params[split[0]] = split[1]

            clean_url += urlencode(allowed_params)
        return clean_url

    @classmethod
    def _partial_media_dict_from_cd_photo_thread(cls, url):
        media_dict = {'media_type_enum': MediaType.CD_PHOTO_THREAD}
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
