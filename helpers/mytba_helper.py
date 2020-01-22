from google.appengine.ext import ndb

from helpers.tbans_helper import TBANSHelper
from models.account import Account
from models.favorite import Favorite
from models.subscription import Subscription


class MyTBAHelper(object):
    @classmethod
    def add_favorite(cls, fav, device_key=None):
        if Favorite.query(Favorite.model_key == fav.model_key, Favorite.model_type == fav.model_type,
                          ancestor=ndb.Key(Account, fav.user_id)).count() == 0:
            # Favorite doesn't exist, add it
            fav.put()
            # Send updates to user's other devices
            TBANSHelper.update_favorites(fav.user_id, device_key)
            return 200
        else:
            # Favorite already exists. Don't add it again
            return 304

    @classmethod
    def remove_favorite(cls, user_id, model_key, model_type, device_key=None):
        to_delete = Favorite.query(Favorite.model_key == model_key, Favorite.model_type == model_type,
                                   ancestor=ndb.Key(Account, user_id)).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            # Send updates to user's other devices
            TBANSHelper.update_favorites(user_id, device_key)
            return 200
        else:
            # Favorite doesn't exist. Can't delete it
            return 404

    @classmethod
    def add_subscription(cls, sub, device_key=None):
        current = Subscription.query(Subscription.model_key == sub.model_key, Subscription.model_type == sub.model_type,
                                     ancestor=ndb.Key(Account, sub.user_id)).get()
        if current is None:
            # Subscription doesn't exist, add it
            sub.put()
            # Send updates to user's other devices
            TBANSHelper.update_subscriptions(sub.user_id, device_key)
            return 200
        else:
            if len(set(current.notification_types).symmetric_difference(set(sub.notification_types))) == 0:
                # Subscription already exists. Don't add it again
                return 304
            else:
                # We're updating the settings
                current.notification_types = sub.notification_types
                current.put()
                # Send updates to user's other devices
                TBANSHelper.update_subscriptions(sub.user_id, device_key)
                return 200

    @classmethod
    def remove_subscription(cls, user_id, model_key, model_type, device_key=None):
        to_delete = Subscription.query(Subscription.model_key == model_key, Subscription.model_type == model_type,
                                       ancestor=ndb.Key(Account, user_id)).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            # Send updates to user's other devices
            TBANSHelper.update_subscriptions(user_id, device_key)
            return 200
        else:
            # Subscription doesn't exist. Can't delete it
            return 404
