import json

from google.appengine.ext import ndb

from consts.notification_type import NotificationType


class Subscription(ndb.Model):

    user_id = ndb.StringProperty(required=True)
    model_key = ndb.StringProperty(required=True)
    notification_types = ndb.IntegerProperty(repeated=True)
    model_type = ndb.IntegerProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True)

    def __init__(self, *args, **kw):
        self._settings = None
        super(Subscription, self).__init__(*args, **kw)

    @property
    def notification_names(self):
        return [NotificationType.render_names[index] for index in self.notification_types]
