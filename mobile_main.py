import endpoints
import logging
import webapp2

from google.appengine.ext import ndb

from protorpc import remote
from protorpc import message_types

import tba_config

from consts.client_type import ClientType
from helpers.push_helper import PushHelper
from helpers.gcm_message_helper import GCMMessageHelper
from models.favorite import Favorite
from models.sitevar import Sitevar
from models.subscription import Subscription
from models.mobile_api_messages import BaseResponse, FavoriteCollection, FavoriteMessage, RegistrationRequest, \
                                       SubscriptionCollection, SubscriptionMessage
from models.mobile_client import MobileClient

client_id_sitevar = Sitevar.get_by_id('appengine.webClientId')
if client_id_sitevar is None:
    raise Exception("Sitevar appengine.webClientId is undefined. Can't process incoming requests")
WEB_CLIENT_ID = str(client_id_sitevar.values_json)
ANDROID_AUDIENCE = WEB_CLIENT_ID

android_id_sitevar = Sitevar.get_by_id('android.clientId')
if android_id_sitevar is None:
    raise Exception("Sitevar android.clientId is undefined. Can't process incoming requests")
ANDROID_CLIENT_ID = str(android_id_sitevar.values_json)

# To enable iOS access to the API, add another variable for the iOS client ID

client_ids = [WEB_CLIENT_ID, ANDROID_CLIENT_ID]
if tba_config.DEBUG:
    '''
    Only allow API Explorer access on dev versions
    '''
    client_ids.append(endpoints.API_EXPLORER_CLIENT_ID)

# To enable iOS access, add it's client ID here


@endpoints.api(name='tbaMobile', version='v8', description="API for TBA Mobile clients",
               allowed_client_ids=client_ids,
               audiences=[ANDROID_AUDIENCE],
               scopes=[endpoints.EMAIL_SCOPE])
class MobileAPI(remote.Service):

    @endpoints.method(RegistrationRequest, BaseResponse,
                      path='register', http_method='POST',
                      name='register')
    def register_client(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to register")
        userId = PushHelper.user_email_to_id(current_user.email())
        gcmId = request.mobile_id
        os = ClientType.enums[request.operating_system]
        if MobileClient.query( MobileClient.messaging_id==gcmId ).count() == 0:
            # Record doesn't exist yet, so add it
            MobileClient(   messaging_id = gcmId,
                            user_id = userId,
                            client_type = os ).put()
            return BaseResponse(code=200, message="Registration successful")
        else:
            # Record already exists, don't bother updating it again
            return BaseResponse(code=304, message="Client already exists")

    @endpoints.method(RegistrationRequest, BaseResponse,
                      path='unregister', http_method='POST',
                      name='unregister')
    def unregister_client(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to unregister")
        userID = PushHelper.user_email_to_id(current_user.email())
        gcmId = request.mobile_id
        query = MobileClient.query(MobileClient.messaging_id == gcmId, MobileClient.user_id == userID).fetch(keys_only=True)
        if len(query) == 0:
            # Record doesn't exist, so we can't remove it
            return BaseResponse(code=404, message="User doesn't exist. Can't remove it")
        else:
            ndb.delete_multi(query)
            return BaseResponse(code=200, message="User deleted")

    @endpoints.method(FavoriteMessage, BaseResponse,
                      path='favorites/add', http_method='POST',
                      name='favorites.add')
    def add_favorite(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to add favorite")
        userId = PushHelper.user_email_to_id(current_user.email())
        modelKey = request.model_key

        if Favorite.query( Favorite.user_id == userId, Favorite.model_key == modelKey).count() == 0:
            # Favorite doesn't exist, add it
            Favorite( user_id = userId, model_key = modelKey).put()
            if request.device_key:
                # Send updates to user's other devices
                logging.info("Sending favorite update to user other devices")
                GCMMessageHelper.send_favorite_update(userId, request.device_key)
            return BaseResponse(code=200, message="Favorite added")
        else:
            # Favorite already exists. Don't add it again
            return BaseResponse(code=304, message="Favorite already exists")

    @endpoints.method(FavoriteMessage, BaseResponse,
                      path='favorites/remove', http_method='POST',
                      name='favorites.remove')
    def remove_favorite(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to remove favorite")
        userId = PushHelper.user_email_to_id(current_user.email())
        modelKey = request.model_key

        to_delete = Favorite.query( Favorite.user_id == userId, Favorite.model_key == modelKey).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            if request.device_key:
                # Send updates to user's other devices
                GCMMessageHelper.send_favorite_update(userId, request.device_key)
            return BaseResponse(code=200, message="Favorites deleted")
        else:
            # Favorite doesn't exist. Can't delete it
            return BaseResponse(code=404, message="Favorite not found")

    @endpoints.method(message_types.VoidMessage, FavoriteCollection,
                      path='favorites/list', http_method='POST',
                      name='favorites.list')
    def list_favorites(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return FavoriteCollection(favorites = [])
        userId = PushHelper.user_email_to_id(current_user.email())

        favorites = Favorite.query( Favorite.user_id == userId ).fetch()
        output = []
        for favorite in favorites:
            output.append(FavoriteMessage(model_key = favorite.model_key))
        return FavoriteCollection(favorites = output)

    @endpoints.method(SubscriptionMessage, BaseResponse,
                      path='subscriptions/add', http_method='POST',
                      name='subscriptions.add')
    def add_subscription(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to add subscription")
        userId = PushHelper.user_email_to_id(current_user.email())
        modelKey = request.model_key

        sub = Subscription.query( Subscription.user_id == userId, Subscription.model_key == modelKey).get()
        if sub is None:
            # Subscription doesn't exist, add it
            Subscription( user_id = userId, model_key = modelKey, notification_types = PushHelper.notification_enums_from_string(request.notifications)).put()
            if request.device_key:
                # Send updates to user's other devices
                GCMMessageHelper.send_subscription_update(userId, request.device_key)
            return BaseResponse(code=200, message="Subscription added")
        else:
            if sub.notification_types == PushHelper.notification_enums_from_string(request.notifications):
                # Subscription already exists. Don't add it again
                return BaseResponse(code=304, message="Subscription already exists")
            else:
                # We're updating the settings
                sub.notification_types = PushHelper.notification_enums_from_string(request.notifications)
                sub.put()
                if request.device_key:
                    # Send updates to user's other devices
                    GCMMessageHelper.send_subscription_update(userId, request.device_key)
                return BaseResponse(code=200, message="Subscription updated")

    @endpoints.method(SubscriptionMessage, BaseResponse,
                      path='subscriptions/remove', http_method='POST',
                      name='subscriptions.remove')
    def remove_subscription(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to remove subscription")
        userId = PushHelper.user_email_to_id(current_user.email())
        modelKey = request.model_key

        to_delete = Subscription.query( Subscription.user_id == userId, Subscription.model_key == modelKey).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            if request.device_key:
                # Send updates to user's other devices
                GCMMessageHelper.send_subscription_update(userId, request.device_key)
            return BaseResponse(code=200, message="Subscriptions deleted")
        else:
            # Subscription doesn't exist. Can't delete it
            return BaseResponse(code=404, message="Subscription not found")

    @endpoints.method(message_types.VoidMessage, SubscriptionCollection,
                      path='subscriptions/list', http_method='POST',
                      name='subscriptions.list')
    def list_subscriptions(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return SubscriptionCollection(subscriptions = [])
        userId = PushHelper.user_email_to_id(current_user.email())

        subscriptions = Subscription.query( Subscription.user_id == userId ).fetch()
        output = []
        for subscription in subscriptions:
            output.append(SubscriptionMessage(model_key = subscription.model_key, notifications = PushHelper.notification_string_from_enums(subscription.notification_types)))
        return SubscriptionCollection(subscriptions = output)


app = endpoints.api_server([MobileAPI])
