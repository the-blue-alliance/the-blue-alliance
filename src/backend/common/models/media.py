import json
from typing import cast, Dict, List, Optional

from google.cloud import ndb
from pyre_extensions import none_throws, safe_cast

from backend.common.consts import media_tag, media_type
from backend.common.consts.media_tag import MediaTag
from backend.common.consts.media_type import MediaType
from backend.common.models.event import Event
from backend.common.models.keys import MediaKey, Year
from backend.common.models.team import Team


class Media(ndb.Model):
    """
    The Media model represents different forms of media, such as YouTube Videos
    or ChiefDelphi photos, that are associated with other models, such as Teams.
    """

    REFERENCE_MAP = {
        "team": Team,
        "event": Event,
    }

    MAX_PREFERRED = 3  # Loosely enforced. Not a big deal.

    # media_type and foreign_key make up the key_name
    media_type_enum: MediaType = safe_cast(
        MediaType, ndb.IntegerProperty(required=True, choices=media_type.MEDIA_TYPES)
    )
    media_tag_enum: List[MediaTag] = cast(
        List[MediaTag], ndb.IntegerProperty(repeated=True, choices=media_tag.MEDIA_TAGS)
    )
    # Unique id for the particular media type. Ex: the Youtube Video key at the end of a YouTube url
    foreign_key = ndb.StringProperty(required=True)

    details_json = ndb.TextProperty()  # Additional details required for rendering
    private_details_json = (
        ndb.TextProperty()
    )  # Additional properties we don't want to expose via API
    year: Year = ndb.IntegerProperty()  # None if year is not relevant
    references = ndb.KeyProperty(
        repeated=True
    )  # Other models that are linked to this object
    preferred_references = ndb.KeyProperty(
        repeated=True
    )  # Other models for which this media is "Preferred". All preferred_references MUST also be in references

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "references": set(),
            "preferred_references": set(),
            "year": set(),
            "media_tag_enum": set(),
        }
        self._details: Optional[Dict] = None
        self._private_details: Optional[Dict] = None
        self._updated_attrs = []  # Used in MediaManipulator to track what changed
        super(Media, self).__init__(*args, **kw)

    @property
    def details(self) -> Dict:
        # TODO add better typing
        if self._details is None and self.details_json is not None:
            self._details = json.loads(self.details_json)
        return none_throws(self._details)

    @property
    def private_details(self) -> Optional[Dict]:
        # TODO add better typing
        if self._private_details is None and self.private_details_json is not None:
            self._private_details = json.loads(self.private_details_json)
        return self._private_details

    @classmethod
    def create_reference(self, reference_type: str, reference_key: str) -> ndb.Key:
        return ndb.Key(self.REFERENCE_MAP[reference_type], reference_key)

    @property
    def key_name(self) -> MediaKey:
        return self.render_key_name(self.media_type_enum, self.foreign_key)

    @property
    def slug_name(self) -> str:
        return media_type.SLUG_NAMES[self.media_type_enum]

    @classmethod
    def render_key_name(cls, media_type_enum: MediaType, foreign_key: str) -> MediaKey:
        return "{}_{}".format(media_type.SLUG_NAMES[media_type_enum], foreign_key)

    @classmethod
    def validate_key_name(cls, key: str) -> bool:
        split = key.split("_")
        return (
            len(split) == 2
            and split[0] in media_type.SLUG_NAMES.values()
            and len(split[1]) > 0
        )

    # URL renderers
    @property
    def cdphotothread_image_url(self) -> str:
        return "https://web.archive.org/web/0im_/https://www.chiefdelphi.com/media/img/{}".format(
            self.details["image_partial"]
        )

    @property
    def cdphotothread_image_url_med(self) -> str:
        return self.cdphotothread_image_url.replace("_l", "_m")

    @property
    def cdphotothread_image_url_sm(self) -> str:
        return self.cdphotothread_image_url.replace("_l", "_s")

    @property
    def cdphotothread_thread_url(self) -> str:
        return "https://web.archive.org/web/https://www.chiefdelphi.com/media/photos/{}".format(
            self.foreign_key
        )

    @property
    def external_link(self) -> str:
        return self.foreign_key

    @property
    def youtube_url(self) -> str:
        return "https://www.youtube.com/embed/{}".format(self.foreign_key)

    @property
    def youtube_url_link(self) -> str:
        return "https://youtu.be/{}".format(self.foreign_key)

    @property
    def imgur_url(self) -> str:
        return "https://imgur.com/{}".format(self.foreign_key)

    @property
    def imgur_direct_url(self) -> str:
        return "https://i.imgur.com/{}h.jpg".format(self.foreign_key)

    @property
    def imgur_direct_url_med(self) -> str:
        return "https://i.imgur.com/{}m.jpg".format(self.foreign_key)

    @property
    def imgur_direct_url_sm(self) -> str:
        return "https://i.imgur.com/{}s.jpg".format(self.foreign_key)

    @property
    def instagram_url(self) -> str:
        return "https://www.instagram.com/p/{}".format(self.foreign_key)

    @property
    def instagram_direct_url(self) -> str:
        return self.instagram_url_helper("l")

    @property
    def instagram_direct_url_med(self) -> str:
        return self.instagram_url_helper("m")

    @property
    def instagram_direct_url_sm(self) -> str:
        return self.instagram_url_helper("t")

    def instagram_url_helper(self, size) -> str:
        # Supported size values are t (thumbnail), m (medium), l (large)
        # See the Instagram developer docs for more information:
        # https://www.instagram.com/developer/embedding/#media_redirect!
        return "{}/media/?size={}".format(self.instagram_url, size)

    @property
    def view_image_url(self) -> str:
        if self.media_type_enum == MediaType.CD_PHOTO_THREAD:
            return self.cdphotothread_image_url
        elif self.media_type_enum == MediaType.IMGUR:
            return self.imgur_url
        elif self.media_type_enum == MediaType.GRABCAD:
            return "https://grabcad.com/library/{}".format(self.foreign_key)
        elif self.media_type_enum == MediaType.ONSHAPE:
            return "https://cad.onshape.com/documents/{}".format(self.foreign_key)
        elif self.media_type_enum == MediaType.INSTAGRAM_IMAGE:
            return self.instagram_url
        else:
            return ""

    @property
    def image_direct_url(self) -> str:
        # Largest image that isn't max resolution (which can be arbitrarily huge)
        if self.media_type_enum == MediaType.CD_PHOTO_THREAD:
            return self.cdphotothread_image_url_med
        elif self.media_type_enum == MediaType.IMGUR:
            return self.imgur_direct_url
        elif self.media_type_enum == MediaType.GRABCAD:
            return self.details["model_image"].replace("card.jpg", "large.png")
        elif self.media_type_enum == MediaType.ONSHAPE:
            return self.details["model_image"].replace("300x300", "600x340")
        elif self.media_type_enum == MediaType.INSTAGRAM_IMAGE:
            return self.instagram_direct_url
        else:
            return ""

    @property
    def social_profile_url(self) -> str:
        if self.media_type_enum in media_type.SOCIAL_TYPES:
            return media_type.PROFILE_URLS[self.media_type_enum].format(
                self.foreign_key
            )
        return ""

    @property
    def type_name(self) -> str:
        return media_type.TYPE_NAMES[self.media_type_enum]

    @property
    def tag_names(self) -> List[str]:
        return [media_tag.TAG_NAMES[t] for t in self.media_tag_enum]

    @property
    def is_image(self) -> bool:
        return self.media_type_enum in media_type.IMAGE_TYPES

    @property
    def image_direct_url_med(self) -> str:
        if self.media_type_enum == MediaType.CD_PHOTO_THREAD:
            return self.cdphotothread_image_url_med
        elif self.media_type_enum == MediaType.IMGUR:
            return self.imgur_direct_url_med
        elif self.media_type_enum == MediaType.GRABCAD:
            return self.details["model_image"]
        elif self.media_type_enum == MediaType.ONSHAPE:
            return self.details["model_image"]
        elif self.media_type_enum == MediaType.INSTAGRAM_IMAGE:
            return self.instagram_direct_url_med
        else:
            return ""

    @property
    def image_direct_url_sm(self) -> str:
        if self.media_type_enum == MediaType.CD_PHOTO_THREAD:
            return self.cdphotothread_image_url_sm
        elif self.media_type_enum == MediaType.IMGUR:
            return self.imgur_direct_url_sm
        elif self.media_type_enum == MediaType.GRABCAD:
            return self.details["model_image"].replace("large.jpg", "tiny.jpg")
        elif self.media_type_enum == MediaType.ONSHAPE:
            return self.details["model_image"].replace("300x300", "300x170")
        elif self.media_type_enum == MediaType.INSTAGRAM_IMAGE:
            return self.instagram_direct_url_sm
        else:
            return ""

    @property
    def avatar_image_source(self) -> str:
        image = json.loads(self.details_json)
        return "data:image/png;base64, {}".format(image["base64Image"])
