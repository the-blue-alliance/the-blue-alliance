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
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)
    values_json = ndb.StringProperty(indexed=False) #a json blob
    
    def __init__(self, *args, **kw):
        self._values = None
        super(Sitevar, self).__init__(*args, **kw)
    
    @property
    def values(self):
        """
        Lazy load values_json
        """
        if self._values is None:
            self._values = json.loads(self.values_json)
        return self._values

    @values.setter
    def values(self, value):
        self._values = value
        self.values_json = json.puts(self._values)
