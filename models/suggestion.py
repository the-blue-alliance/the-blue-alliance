import json

from google.appengine.ext import ndb

from models.account import Account


class Suggestion(ndb.Model):
    """
    Suggestions are generic containers for user-submitted data corrections to
    the site. The generally store a model, a key, and then a json blob of
    fields to append or ammend in the model.
    """
    MODELS = set(["event", "match", "media"])
    REVIEW_ACCEPTED = 1
    REVIEW_PENDING = 0
    REVIEW_REJECTED = -1

    review_state = ndb.IntegerProperty(default=0)
    reviewed_at = ndb.DateTimeProperty()
    reviewer = ndb.KeyProperty(kind=Account)
    author = ndb.KeyProperty(kind=Account, required=True)
    contents_json = ndb.StringProperty(indexed=False)  # a json blob
    target_key = ndb.StringProperty()  # "2012cmp"
    target_model = ndb.StringProperty(choices=MODELS, required=True)  # "event"

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        self._contents = None
        super(Suggestion, self).__init__(*args, **kw)

    @property
    def contents(self):
        """
        Lazy load contents_json
        """
        if self._contents is None:
            self._contents = json.loads(self.contents_json)
        return self._contents

    @contents.setter
    def contents(self, contents):
        self._contents = contents
        self.contents_json = json.dumps(self._contents)

    @property
    def youtube_video(self):
        if "youtube_videos" in self.contents:
            return self.contents["youtube_videos"][0]

    @classmethod
    def render_media_key_name(cls, year, target_model, target_key, foreign_type, foreign_key):
        """
        Keys aren't required for this model. This is only necessary if checking
        for duplicate suggestions is desired.
        """
        return 'media_{}_{}_{}_{}_{}'.format(year, target_model, target_key, foreign_type, foreign_key)

    @classmethod
    def render_webcast_key_name(cls, event_key, webcast_dict):
        """
        Keys aren't required for this model. This is only necessary if checking
        for duplicate suggestions is desired.
        """
        return 'webcast_{}_{}_{}_{}'.format(
            event_key,
            webcast_dict.get('type', None),
            webcast_dict.get('channel', None),
            webcast_dict.get('file', None))
