import json

from google.appengine.ext import ndb


class Subscription(ndb.Model):

    user_id = ndb.StringProperty(required=True)
    model_key = ndb.StringProperty(required=True)
    settings_json = ndb.StringProperty(required=True, indexed=True)  # JSON array of which individual notifications are subscribed to

    created = ndb.DateTimeProperty(auto_now_add=True)

    def __init__(self, *args, **kw):
        self._settings = None
        super(Subscription, self).__init__(*args, **kw)

    @property
    def settings(self):
        '''
        Lazy load settings_json
        '''
        if self._settings is None:
            self._settings = json.loads(self.settings_json)

        return self._settings
