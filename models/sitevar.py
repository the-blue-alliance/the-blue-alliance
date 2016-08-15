import json

from google.appengine.ext import ndb


class Sitevar(ndb.Model):
    """
    Sitevars represent site configuration parameters that should be adjustable
    without requiring a code push. They may be used to store secret information
    such as API keys and secrets since only app admins can read them.

    Code should assume sitevars may not come back from the datastore, in which
    case their value should be treated as dict(). Otherwise, sitevar should
    contain a json blob that contain one or more keys with values. They are
    manually edited by site administrators in the admin console.
    """
    description = ndb.StringProperty(indexed=False)
    values_json = ndb.StringProperty(indexed=False, default="{}")  # a json blob

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        self._contents = None
        super(Sitevar, self).__init__(*args, **kw)

    @property
    def contents(self):
        """
        Lazy load values_json
        """
        if self._contents is None and self.values_json is not None:
            self._contents = json.loads(self.values_json)
        return self._contents

    @contents.setter
    def contents(self, contents):
        self._contents = contents
        self.values_json = json.dumps(self._contents)
