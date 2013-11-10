import json

from google.appengine.ext import ndb

from consts.media_type import MediaType


class Media(ndb.Model):
    """
    """

    # Do not change! key_names are generated based on this
    SLUG_NAMES = {
        MediaType.YOUTUBE: 'youtube',
        MediaType.CD_PHOTO_THREAD: 'cdphotothread',
    }

    # media_type and foreign_key make up the key_name
    media_type_enum = ndb.IntegerProperty(required=True)
    foreign_key = ndb.StringProperty(required=True)  # Unique id for the particular media type. Ex: the Youtube Video key at the end of a YouTube url

    details_json = ndb.StringProperty()  # Additional details required for rendering
    year = ndb.IntegerProperty()  # None if year is not relevant
    references = ndb.KeyProperty(repeated=True)  # Other models that are linked to this object

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        self._details = None
        super(Media, self).__init__(*args, **kw)

    @property
    def details(self):
        if self._details is None:
            self._details = json.loads(self.details_json)
        return self._details

    @property
    def key_name(self):
        return self.render_key_name(self.media_type_enum, self.foreign_key)

    @property
    def slugname(self):
        return self.SLUG_NAMES[self.media_type_enum]

    @classmethod
    def render_key_name(self, media_type_enum, foreign_key):
        return "{}_{}".format(self.SLUG_NAMES[media_type_enum], foreign_key)

    # URL renderers
    @property
    def cdphotothread_image_url(self):
        return 'http://www.chiefdelphi.com/media/img/{}'.format(self.details['image_partial'])

    @property
    def cdphotothread_thread_url(self):
        return 'http://www.chiefdelphi.com/media/photos/{}'.format(self.foreign_key)

    @property
    def youtube_url(self):
        return 'http://www.youtube.com/embed/{}'.format(self.foreign_key)
