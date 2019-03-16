import json

from google.appengine.ext import ndb

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

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        self._settings = None
        super(Subscription, self).__init__(*args, **kw)

    @property
    def notification_names(self):
        return [NotificationType.render_names[index] for index in self.notification_types]

    @staticmethod
    def user_subscriptions(user_id):
        from models.account import Account
        return Subscription.query(ancestor=ndb.Key(Account, user_id)).fetch()
