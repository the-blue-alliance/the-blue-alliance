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

    parent_model = ndb.KeyProperty(required=True)
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

    @classmethod
    def render_key_name(self, parent_key_name, social_type_enum, foreign_key):
        return '{}_{}_{}'.format(parent_key_name, self.SLUG_NAMES[social_type_enum], foreign_key)
