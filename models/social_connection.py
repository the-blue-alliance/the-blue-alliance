import json

from google.appengine.ext import ndb


class SocialConnection(ndb.Model):
    """
    This class represents a social networking account associated with
    another model.
    key_name is formatted like: <model_key>_<social_type_str>_<foreign_key>
    """

    parent_model = ndb.KeyProperty(required=True)
    social_type_enum = ndb.IntegerProperty(required=True)
    foreign_key = ndb.StringProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        super(SocialConnection, self).__init__(*args, **kw)

    @classmethod
    def render_key_name(self, parent_key_name, social_type_enum, foreign_key):
        return '{}_{}_{}'.format(parent_key_name, social_type_enum, foreign_key)
