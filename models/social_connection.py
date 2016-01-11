import json

from google.appengine.ext import ndb

from consts.social_connection_type import SocialConnectionType
from models.team import Team


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

    REFERENCE_MAP = {
        'team': Team
    }

    references = ndb.KeyProperty(repeated=True)  # Other models that are linked to this object
    social_type_enum = ndb.IntegerProperty(required=True)
    foreign_key = ndb.StringProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        super(SocialConnection, self).__init__(*args, **kw)

    @property
    def slug_name(self):
        return self.SLUG_NAMES[self.social_type_enum]

    @classmethod
    def create_reference(self, reference_type, reference_key):
        return ndb.Key(self.REFERENCE_MAP[reference_type], reference_key)

    @property
    def key_name(self):
        return self.render_key_name(self.social_type_enum, self.foreign_key)

    @property
    def profile_url(self):
        return SocialConnectionType.PROFILE_URLS[self.social_type_enum].format(self.foreign_key)

    @classmethod
    def render_key_name(self, social_type_enum, foreign_key):
        return '{}_{}'.format(self.SLUG_NAMES[social_type_enum], foreign_key)
