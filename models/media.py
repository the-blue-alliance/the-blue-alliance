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
        MediaType.YOUTUBE_VIDEO: 'youtube',
        MediaType.CD_PHOTO_THREAD: 'cdphotothread',
        MediaType.IMGUR: 'imgur',
        MediaType.FACEBOOK_PROFILE: 'facebook-profile',
        MediaType.YOUTUBE_CHANNEL: 'youtube-channel',
        MediaType.TWITTER_PROFILE: 'twitter-profile',
        MediaType.GITHUB_PROFILE: 'github-profile',
        MediaType.INSTAGRAM_PROFILE: 'instagram-profile',
    }

    REFERENCE_MAP = {
        'team': Team
    }

    MAX_PREFERRED = 3  # Loosely enforced. Not a big deal.

    # media_type and foreign_key make up the key_name
    media_type_enum = ndb.IntegerProperty(required=True)
    foreign_key = ndb.StringProperty(required=True)  # Unique id for the particular media type. Ex: the Youtube Video key at the end of a YouTube url

    details_json = ndb.StringProperty()  # Additional details required for rendering
    private_details_json = ndb.StringProperty()  # Additional properties we don't want to expose via API
    year = ndb.IntegerProperty()  # None if year is not relevant
    references = ndb.KeyProperty(repeated=True)  # Other models that are linked to this object
    preferred_references = ndb.KeyProperty(repeated=True)  # Other models for which this media is "Preferred". All preferred_references MUST also be in references

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'references': set(),
            'preferred_references': set(),
            'year': set(),
        }
        self._details = None
        self._private_details = None
        self._updated_attrs = []  # Used in MediaManipulator to track what changed
        super(Media, self).__init__(*args, **kw)

    @property
    def details(self):
        if self._details is None and self.details_json is not None:
            self._details = json.loads(self.details_json)
        return self._details

    @property
    def private_details(self):
        if self._private_details is None and self.private_details_json is not None:
            self._private_details = json.loads(self.private_details_json)
        return self._private_details

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
    def cdphotothread_image_url_sm(self):
        return self.cdphotothread_image_url.replace('_l', '_s')

    @property
    def cdphotothread_thread_url(self):
        return 'http://www.chiefdelphi.com/media/photos/{}'.format(self.foreign_key)

    @property
    def youtube_url(self):
        return 'https://www.youtube.com/embed/{}'.format(self.foreign_key)

    @property
    def imgur_url(self):
        return 'https://imgur.com/{}'.format(self.foreign_key)

    @property
    def imgur_direct_url(self):
        return 'https://i.imgur.com/{}h.jpg'.format(self.foreign_key)

    @property
    def imgur_direct_url_med(self):
        return 'https://i.imgur.com/{}m.jpg'.format(self.foreign_key)

    @property
    def imgur_direct_url_sm(self):
        return 'https://i.imgur.com/{}s.jpg'.format(self.foreign_key)

    @property
    def view_image_url(self):
        if self.media_type_enum == MediaType.CD_PHOTO_THREAD:
            return self.cdphotothread_image_url
        elif self.media_type_enum == MediaType.IMGUR:
            return self.imgur_url
        else:
            return ""

    @property
    def image_direct_url(self):
        # Largest image that isn't max resolution (which can be arbitrarily huge)
        if self.media_type_enum == MediaType.CD_PHOTO_THREAD:
            return self.cdphotothread_image_url_med
        elif self.media_type_enum == MediaType.IMGUR:
            return self.imgur_direct_url
        else:
            return ""

    @property
    def social_profile_url(self):
        if self.media_type_enum in MediaType.social_types:
            return MediaType.profile_urls[self.media_type_enum].format(self.foreign_key)
        return ""

    @property
    def type_name(self):
        return MediaType.type_names[self.media_type_enum]

    @property
    def image_direct_url_med(self):
        if self.media_type_enum == MediaType.CD_PHOTO_THREAD:
            return self.cdphotothread_image_url_med
        elif self.media_type_enum == MediaType.IMGUR:
            return self.imgur_direct_url_med
        else:
            return ""

    @property
    def image_direct_url_sm(self):
        if self.media_type_enum == MediaType.CD_PHOTO_THREAD:
            return self.cdphotothread_image_url_sm
        elif self.media_type_enum == MediaType.IMGUR:
            return self.imgur_direct_url_sm
        else:
            return ""
