import json

from google.appengine.ext import ndb

from models.account import Account

class Suggestion(ndb.Model):
    """
    Suggestions are generic containers for user-submitted data corrections to
    the site. The generally store a model, a key, and then a json blob of
    fields to append or ammend in the model.
    """
    MODELS = set(["event", "match"])
    REVIEW_ACCEPTED = 1
    REVIEW_PENDING = 0
    REVIEW_REJECTED = -1
    
    review_state = ndb.IntegerProperty(default=0)
    reviewed_at = ndb.DateTimeProperty()
    reviewer = ndb.KeyProperty(kind=Account)
    author = ndb.KeyProperty(kind=Account, required=True)
    contents_json = ndb.StringProperty(indexed=False) #a json blob
    target_key = ndb.StringProperty(required=True) # "2012cmp"
    target_model = ndb.StringProperty(choices=MODELS, required=True) # "event"
    
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
