import json

from google.appengine.ext import ndb

from consts.social_connection_type import SocialConnectionType


class SocialConnection(ndb.Model):
    """
    This class represents a social networking account associated with
    another model.
    key_name is formatted like: <model_key>_<social_type_str>_<foreign_key>
    """

    # Do not change! key_names are generated based on this
    SLUG_NAMES = {
        SocialConnectionType.FACEBOOK: 'facebook',
        SocialConnectionType.GITHUB: 'github',
        SocialConnectionType.TWITTER: 'twitter',
        SocialConnectionType.YOUTUBE: 'youtube'
    }

    references = ndb.KeyProperty(repeated=True)  # Other models that are linked to this object
    social_type_enum = ndb.IntegerProperty(required=True)
    profile_url = ndb.StringProperty(required=True)
    foreign_key = ndb.StringProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        super(SocialConnection, self).__init__(*args, **kw)

    @property
    def slug_name(self):
        return self.SLUG_NAMES[self.social_type_enum]

    # URL Renderers
    @property
    def facebook_profile_url(self):
        return "https://www.facebook.com/{}".format(self.foreign_key)

    @property
    def github_profile_url(self):
        return "https://github.com/{}".format(self.foreign_key)

    @property
    def twitter_profile_url(self):
        return "https://twitter.com/{}".format(self.foreign_key)

    @property
    def youtube_profile_url(self):
        return "https://www.youtube.com/user/{}".format(self.foreign_key)

    @classmethod
    def render_key_name(self, social_type_enum, foreign_key):
        return '{}_{}'.format(self.SLUG_NAMES[social_type_enum], foreign_key)
