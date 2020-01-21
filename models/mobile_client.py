import urllib
from google.appengine.ext import ndb

from consts.client_type import ClientType


class MobileClient(ndb.Model):
    """
    This class repesents a mobile client that has registered with the server
    We store a messaging ID (e.g. Google Cloud Messaging sender ID) as well
    as a per-user unique key that is generated client side and sent up.

    In order to make strongly consistent DB requests, instances of this class
    should be created with a parent that is the associated Account key.
    """

    user_id = ndb.StringProperty(required=True, indexed=True)
    messaging_id = ndb.StringProperty(required=True)
    client_type = ndb.IntegerProperty(required=True)
    display_name = ndb.StringProperty(default="Unnamed Device")
    device_uuid = ndb.StringProperty(default='')
    secret = ndb.StringProperty(default="")  # Used to hash webhooks

    # Used to verify that webhooks are actually controlled by the account holder
    verification_code = ndb.StringProperty(default="")
    verified = ndb.BooleanProperty(default=True)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        super(MobileClient, self).__init__(*args, **kw)

    @property
    def type_string(self):
        return ClientType.names[self.client_type]

    @property
    def is_webhook(self):
        return self.client_type == ClientType.WEBHOOK

    @property
    def short_id(self):
        return self.messaging_id if len(self.messaging_id)<=50 else self.messaging_id[0:50]+'...'

    @staticmethod
    def clients(user_id, client_types=ClientType.names.keys()):
        """
        Get Mobile Clients for a given user.

        Args:
            user_id (string): The User ID to fetch clients for.
            client_types (list, ClientType): The client types to filter for.

        Returns:
            list (MobileClient): List of Mobile Clients for the user.
        """
        from models.account import Account
        return MobileClient.query(
            MobileClient.client_type.IN(client_types),
            ancestor=ndb.Key(Account, user_id)
        ).fetch()

    @staticmethod
    def fcm_messaging_ids(user_id):
        """
        Get messaging IDs for FCM clients for a given user.

        Args:
            user_id (string): The User ID to fetch device tokens for.

        Returns:
            list (string): List of device tokens for the user.
        """
        from models.account import Account
        clients = MobileClient.query(
            MobileClient.client_type.IN(ClientType.FCM_CLIENTS),
            ancestor=ndb.Key(Account, user_id)
        ).fetch(projection=[MobileClient.messaging_id])
        return [c.messaging_id for c in clients]

    @staticmethod
    def delete_for_messaging_id(messaging_id):
        """
        Delete the mobile client(s) with the associated messaging_id.
        Args:
            messaging_id (string): The messaging_id to filter for.
        """
        to_delete = MobileClient.query(MobileClient.messaging_id == messaging_id).fetch(keys_only=True)
        ndb.delete_multi(to_delete)
