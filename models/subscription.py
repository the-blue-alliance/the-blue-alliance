import json

from google.appengine.ext import ndb

from consts.client_type import ClientType
from consts.notification_type import NotificationType


class Subscription(ndb.Model):
    """
    In order to make strongly consistent DB requests, instances of this class
    should be created with a parent that is the associated Account key.
    """

    user_id = ndb.StringProperty(required=True)
    model_key = ndb.StringProperty(required=True)
    model_type = ndb.IntegerProperty(required=True)
    notification_types = ndb.IntegerProperty(repeated=True)
    client_types = ndb.IntegerProperty(repeated=True)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        self._settings = None
        super(Subscription, self).__init__(*args, **kw)

    # Since repeated and default are mutually exclusive
    # Make 'client_types' default to all
    @property
    def allowed_clients(self):
        if not self.client_types:
            return [ClientType.OS_ANDROID, ClientType.OS_IOS, ClientType.WEBHOOK]
        return self.client_types

    @property
    def notification_names(self):
        return [NotificationType.render_names[index] for index in self.notification_types]
