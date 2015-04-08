from google.appengine.ext import ndb

from helpers.notification_helper import NotificationHelper
from models.account import Account
from models.favorite import Favorite
from models.subscription import Subscription


class MyTBAHelper(object):
    @classmethod
    def add_favorite(cls, fav, device_key=""):
        if Favorite.query(Favorite.model_key == fav.model_key, ancestor=ndb.Key(Account, fav.user_id)).count() == 0:
            # Favorite doesn't exist, add it
            fav.put()
            # Send updates to user's other devices
            NotificationHelper.send_favorite_update(fav.user_id, device_key)
            return 200
        else:
            # Favorite already exists. Don't add it again
            return 304

    @classmethod
    def remove_favorite(cls, userId, modelKey, device_key=""):
        to_delete = Favorite.query(Favorite.model_key == modelKey, ancestor=ndb.Key(Account, userId)).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            # Send updates to user's other devices
            NotificationHelper.send_favorite_update(userId, device_key)
            return 200
        else:
            # Favorite doesn't exist. Can't delete it
            return 404

    @classmethod
    def add_subscription(cls, sub, device_key=""):
        current = Subscription.query(Subscription.model_key == sub.model_key, ancestor=ndb.Key(Account, sub.user_id)).get()
        if current is None:
            # Subscription doesn't exist, add it
            sub.put()
            # Send updates to user's other devices
            NotificationHelper.send_subscription_update(sub.user_id, device_key)
            return 200
        else:
            if current.notification_types == sub.notification_types:
                # Subscription already exists. Don't add it again
                return 304
            else:
                # We're updating the settings
                current.notification_types = sub.notification_types
                current.put()
                # Send updates to user's other devices
                NotificationHelper.send_subscription_update(sub.user_id, device_key)
                return 200

    @classmethod
    def remove_subscription(cls, userId, modelKey, device_key=""):
        to_delete = Subscription.query(Subscription.model_key == modelKey, ancestor=ndb.Key(Account, userId)).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            # Send updates to user's other devices
            NotificationHelper.send_subscription_update(userId, device_key)
            return 200
        else:
            # Subscription doesn't exist. Can't delete it
            return 404
