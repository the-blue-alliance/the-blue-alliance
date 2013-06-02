import json

from google.appengine.ext import ndb

from models.account import Account

class Suggestion(ndb.Model):
    """
    Sitevars represent site configuration parameters that should be adjustable
    without requiring a code push. They may be used to store secret information
    such as API keys and secrets since only app admins can read them.

    Code should assume sitevars may not come back from the datastore, in which
    case their value should be treated as dict(). Otherwise, sitevar should
    contain a json blob that contain one or more keys with values. They are
    manually edited by site administrators in the admin console.
    """
    MODELS = set(["event", "match"])
    
    accepted = ndb.BooleanProperty(default=False)
    accepted_at = ndb.DateTimeProperty()
    accepter = ndb.KeyProperty(kind=Account)
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
