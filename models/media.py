import json

from google.appengine.ext import ndb

from consts.media_type import MediaType


class Media(ndb.Model):
    """
    """

    # Do not change! key_names are generated based on this
    SLUG_NAMES = {
        MediaType.YOUTUBE: 'youtube',
        MediaType.CD_PHOTO: 'cdphoto',
    }

    # media_type and media_id make up the key_name
    media_type_enum = ndb.IntegerProperty(required=True)
    media_id = ndb.StringProperty(required=True)  # Unique id for the particular media type. Ex: the "random" string at the end of a YouTube url

    details_json = ndb.StringProperty()  # Additional details required for rendering
    year = ndb.IntegerProperty()  # None if year is not relevant
    references = ndb.KeyProperty(repeated=True)  # Other models that are linked to this object

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    @property
    def key_name(self):
        return self.render_key_name(self.media_type_enum, self.media_id)

    @classmethod
    def render_key_name(self, media_type_enum, media_id):
        return "{}_{}".format(self.SLUG_NAMES[media_type_enum], media_id)
