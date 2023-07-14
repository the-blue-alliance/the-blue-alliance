from typing import Optional

from google.appengine.ext import ndb

from backend.common.consts.model_type import ModelType
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.models.favorite import Favorite
from backend.common.models.subscription import Subscription


class MyTBAHelper:
    @staticmethod
    def add_favorite(fav: Favorite, device_key: Optional[str] = None) -> bool:
        """
        returns true if the favorite was successfully added,
        or false if it already existed
        """
        favorite_existence = Favorite.query(
            Favorite.model_key == fav.model_key,
            Favorite.model_type == fav.model_type,
            ancestor=fav.key.parent(),
        ).count()
        if favorite_existence == 0:
            # Favorite doesn't exist, add it
            fav.put()
            # Send updates to user's other devices
            TBANSHelper.update_favorites(fav.user_id, device_key)
            return True
        else:
            # Favorite already exists. Don't add it again
            return False

    @staticmethod
    def remove_favorite(
        account_key: ndb.Key,
        model_key: str,
        model_type: ModelType,
        device_key: Optional[str] = None,
    ) -> bool:
        """
        returns true if the favorite was deleted,
        or false if it didn't exist in the first place
        """
        to_delete = Favorite.query(
            Favorite.model_key == model_key,
            Favorite.model_type == model_type,
            ancestor=account_key,
        ).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            # Send updates to user's other devices
            TBANSHelper.update_favorites(str(account_key.id()), device_key)
            return True
        else:
            # Favorite doesn't exist. Can't delete it
            return False

    @staticmethod
    def add_subscription(sub: Subscription, device_key: Optional[str] = None) -> bool:
        """
        return true if the subscription was successfully added
        or false if it already existed
        """
        current = Subscription.query(
            Subscription.model_key == sub.model_key,
            Subscription.model_type == sub.model_type,
            ancestor=sub.key.parent(),
        ).get()
        if current is None:
            # Subscription doesn't exist, add it
            sub.put()
            # Send updates to user's other devices
            TBANSHelper.update_subscriptions(sub.user_id, device_key)
            return True
        else:
            if (
                len(
                    set(current.notification_types).symmetric_difference(
                        set(sub.notification_types)
                    )
                )
                == 0
            ):
                # Subscription already exists. Don't add it again
                return False
            else:
                # We're updating the settings
                current.notification_types = sub.notification_types
                current.put()
                # Send updates to user's other devices
                TBANSHelper.update_subscriptions(sub.user_id, device_key)
                return True

    @staticmethod
    def remove_subscription(
        parent_key: ndb.Key,
        model_key: str,
        model_type: ModelType,
        device_key: Optional[str] = None,
    ) -> bool:
        """
        return true if the subscription was successfully deleted
        or false if it didn't exist to begin with
        """
        to_delete = Subscription.query(
            Subscription.model_key == model_key,
            Subscription.model_type == model_type,
            ancestor=parent_key,
        ).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            # Send updates to user's other devices
            TBANSHelper.update_subscriptions(str(parent_key.id()), device_key)
            return True
        else:
            # Subscription doesn't exist. Can't delete it
            return False
