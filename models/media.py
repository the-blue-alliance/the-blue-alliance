import json

from google.appengine.ext import ndb

from consts.media_type import MediaType
from models.team import Team


class Media(ndb.Model):
    """
    The Media model represents different forms of media, such as YouTube Videos
    or ChiefDelphi photos, that are associated with other models, such as Teams.
    """

    # Do not change! key_names are generated based on this
    SLUG_NAMES = {
        MediaType.YOUTUBE: 'youtube',
        MediaType.CD_PHOTO_THREAD: 'cdphotothread',
    }

    REFERENCE_MAP = {
        'team': Team
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
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'references': set(),
            'year': set(),
        }
        self._details = None
        super(Media, self).__init__(*args, **kw)

    @property
    def details(self):
        if self._details is None and self.details_json is not None:
            self._details = json.loads(self.details_json)
        return self._details

    @classmethod
    def create_reference(self, reference_type, reference_key):
        return ndb.Key(self.REFERENCE_MAP[reference_type], reference_key)

    @property
    def key_name(self):
        return self.render_key_name(self.media_type_enum, self.foreign_key)

    @property
    def slug_name(self):
        return self.SLUG_NAMES[self.media_type_enum]

    @classmethod
    def render_key_name(self, media_type_enum, foreign_key):
        return "{}_{}".format(self.SLUG_NAMES[media_type_enum], foreign_key)

    # URL renderers
    @property
    def cdphotothread_image_url(self):
        return 'http://www.chiefdelphi.com/media/img/{}'.format(self.details['image_partial'])

    @property
    def cdphotothread_image_url_med(self):
        return self.cdphotothread_image_url.replace('_l', '_m')

    @property
    def cdphotothread_thread_url(self):
        return 'http://www.chiefdelphi.com/media/photos/{}'.format(self.foreign_key)

    @property
    def youtube_url(self):
        return 'http://www.youtube.com/embed/{}'.format(self.foreign_key)
