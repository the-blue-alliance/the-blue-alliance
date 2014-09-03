import logging
from google.appengine.ext import ndb

from consts.client_type import ClientType


class MobileClient(ndb.Model):
    """
    This class repesents a mobile client that has registered with the server
    We store a messaging ID (e.g. Google Cloud Messaging sender ID) as well
    as a per-user unique key that is generated client side and sent up.
    """

    user_id = ndb.StringProperty(required=True, indexed=True)
    messaging_id = ndb.StringProperty(required=True)
    client_type = ndb.IntegerProperty(required=True)
    secret = ndb.StringProperty(default="")  # Used to hash webhooks

    created = ndb.DateTimeProperty(auto_now_add=True)

    def __init__(self, *args, **kw):
        super(MobileClient, self).__init__(*args, **kw)

    @property
    def type_string(self):
        return ClientType.names[self.client_type]

    @property
    def is_webhook(self):
        logging.info(str(self.client_type == ClientType.WEBHOOK))
        return self.client_type == ClientType.WEBHOOK
