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
    # Foreign key patterns
    # Dict that maps SocialConnectionType -> tuple of regex pattern and group # of foreign key
    FOREIGN_KEY_PATTERNS = {
        SocialConnectionType.FACEBOOK: (r".*facebook.com\/(.*)(\/(.*))?", 1),
        SocialConnectionType.TWITTER: (r".*twitter.com\/(.*)(\/(.*))?", 1),
        SocialConnectionType.YOUTUBE: (r".*youtube.com\/user\/(.*)(\/(.*))?", 1),
        SocialConnectionType.GITHUB: (r".*github.com\/(.*)(\/(.*))?", 1),
    }

    # Social profile URL patterns that map a URL -> Profile type
    URL_PATTERNS = {
        'facebook.com/': SocialConnectionType.FACEBOOK,
        'twitter.com/': SocialConnectionType.TWITTER,
        'youtube.com/user': SocialConnectionType.YOUTUBE,
        'github.com/': SocialConnectionType.GITHUB
    }

    @classmethod
    def partial_social_dict_from_url(cls, url):
        """
        Takes a url, and turns it into a partial social connection object dict
        """
        for s, type in cls.URL_PATTERNS.iteritems():
            if s in url:
                return cls._partial_social_dict(type, url)
        logging.warning("Failed to determine media type from url: {}".format(url))
        return None

    @classmethod
    def _partial_social_dict(cls, social_type, url):
        social_dict = {}
        social_dict['social_type_enum'] = social_type
        foreign_key = cls._parse_foreign_key(social_type, url)
        if foreign_key is None:
            logging.warning("Failed to determine foreign_key from url: {}".format(url))
            return None
        social_dict['foreign_key'] = foreign_key

        return social_dict

    @classmethod
    def _parse_foreign_key(cls, social_type, url):
        foreign_key = None
        regex = re.match(cls.FOREIGN_KEY_PATTERNS[social_type][0], url)
        if regex is not None:
            foreign_key = regex.group(cls.FOREIGN_KEY_PATTERNS[social_type][1])

        if foreign_key is None:
            return None
        else:
            return foreign_key
