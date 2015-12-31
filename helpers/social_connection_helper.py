import logging
import re

from consts.social_connection_type import SocialConnectionType


class SocialConnectionHelper(object):
    @classmethod
    def group_by_type(cls, connections):
        conns_by_type = {}
        for conn in connections:
            slug_name = conn.slug_name
            if slug_name in conns_by_type:
                conns_by_type[slug_name].append(conn)
            else:
                conns_by_type[slug_name] = [conn]
        return conns_by_type


class SocialConnectionParser(object):
    FACEBOOK_URL_PATTERNS = ['facebook.com/']
    TWITTER_URL_PATTERNS = ['twitter.com/']
    YOUTUBE_URL_PATTERNS = ['youtube.com/user/']
    GITHUB_URL_PATTERNS = ['github.com/']

    @classmethod
    def partial_social_dict_from_url(cls, url):
        """
        Takes a url, and turns it into a partial Media object dict
        """
        if any(s in url for s in cls.FACEBOOK_URL_PATTERNS):
            return cls._partial_social_dict_from_facebook(url)
        elif any(s in url for s in cls.TWITTER_URL_PATTERNS):
            return cls._partial_social_dict_from_twitter(url)
        elif any(s in url for s in cls.YOUTUBE_URL_PATTERNS):
            return cls._partial_social_dict_from_youtube(url)
        elif any(s in url for s in cls.GITHUB_URL_PATTERNS):
            return cls._partial_social_dict_from_github(url)
        else:
            logging.warning("Failed to determine media type from url: {}".format(url))
            return None

    @classmethod
    def _partial_social_dict_from_facebook(cls, url):
        social_dict = {}
        social_dict['social_type_enum'] = SocialConnectionType.FACEBOOK
        foreign_key = cls._parse_facebook_foreign_key(url)
        if foreign_key is None:
            logging.warning("Failed to determine foreign_key from url: {}".format(url))
            return None
        social_dict['foreign_key'] = foreign_key

        return social_dict

    @classmethod
    def _partial_social_dict_from_twitter(cls, url):
        social_dict = {}
        social_dict['social_type_enum'] = SocialConnectionType.TWITTER
        foreign_key = cls._parse_twitter_foreign_key(url)
        if foreign_key is None:
            logging.warning("Failed to determine foreign_key from url: {}".format(url))
            return None
        social_dict['foreign_key'] = foreign_key

        return social_dict

    @classmethod
    def _partial_social_dict_from_youtube(cls, url):
        social_dict = {}
        social_dict['social_type_enum'] = SocialConnectionType.YOUTUBE
        foreign_key = cls._parse_youtube_foreign_key(url)
        if foreign_key is None:
            logging.warning("Failed to determine foreign_key from url: {}".format(url))
            return None
        social_dict['foreign_key'] = foreign_key

        return social_dict

    @classmethod
    def _partial_social_dict_from_github(cls, url):
        social_dict = {}
        social_dict['social_type_enum'] = SocialConnectionType.GITHUB
        foreign_key = cls._parse_github_foreign_key(url)
        if foreign_key is None:
            logging.warning("Failed to determine foreign_key from url: {}".format(url))
            return None
        social_dict['foreign_key'] = foreign_key

        return social_dict

    @classmethod
    def _parse_facebook_foreign_key(cls, url):
        facebook_profile = None
        regex = re.match(r".*facebook.com\/(.*)(\/(.*))?", url)
        if regex is not None:
            facebook_profile = regex.group(1)

        if facebook_profile is None:
            return None
        else:
            return facebook_profile

    @classmethod
    def _parse_twitter_foreign_key(cls, url):
        twitter_profile = None
        regex = re.match(r".*twitter.com\/(.*)(\/(.*))?", url)
        if regex is not None:
            twitter_profile = regex.group(1)

        if twitter_profile is None:
            return None
        else:
            return twitter_profile

    @classmethod
    def _parse_youtube_foreign_key(cls, url):
        youtube_profile = None
        regex = re.match(r".*youtube.com\/user\/(.*)(\/(.*))?", url)
        if regex is not None:
            youtube_profile = regex.group(1)

        if youtube_profile is None:
            return None
        else:
            return youtube_profile

    @classmethod
    def _parse_github_foreign_key(cls, url):
        github_profile = None
        regex = re.match(r".*github.com\/(.*)(\/(.*))?", url)
        if regex is not None:
            github_profile = regex.group(1)

        if github_profile is None:
            return None
        else:
            return github_profile
