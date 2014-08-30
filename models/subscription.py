import json

from google.appengine.ext import ndb


class Subscription(ndb.Model):

    user_id = ndb.StringProperty(required=True)
    model_key = ndb.StringProperty(required=True)
    notification_types = ndb.IntegerProperty(repeated=True)

    created = ndb.DateTimeProperty(auto_now_add=True)

    def __init__(self, *args, **kw):
        self._settings = None
        super(Subscription, self).__init__(*args, **kw)
