import endpoints
import json
import logging
import webapp2

from google.appengine.ext import ndb

from protorpc import remote
from protorpc import message_types

import tba_config

from consts.client_type import ClientType
from helpers.push_helper import PushHelper
from helpers.mytba_helper import MyTBAHelper
from helpers.notification_helper import NotificationHelper
from models.account import Account
from models.favorite import Favorite
from models.sitevar import Sitevar
from models.subscription import Subscription
from models.mobile_api_messages import BaseResponse, FavoriteCollection, FavoriteMessage, RegistrationRequest, \
                                       SubscriptionCollection, SubscriptionMessage, ModelPreferenceMessage
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
        name = request.name
        uuid = request.device_uuid

        query = MobileClient.query( MobileClient.user_id == userId, MobileClient.device_uuid == uuid, MobileClient.client_type == os )
        # trying to figure out an elusive dupe bug
        logging.info("DEBUGGING")
        logging.info("User ID: {}".format(userId))
        logging.info("UUID: {}".format(uuid))
        logging.info("Count: {}".format(query.count()))
        if query.count() == 0:
            # Record doesn't exist yet, so add it
            MobileClient(
                parent = ndb.Key(Account, userId),
                user_id = userId,
                messaging_id = gcmId,
                client_type = os,
                device_uuid = uuid,
                display_name = name ).put()
            return BaseResponse(code=200, message="Registration successful")
        else:
            # Record already exists, update it
            client = query.fetch(1)[0]
            client.messaging_id = gcmId,
            client.display_name = name
            client.put()
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
        query = MobileClient.query(MobileClient.messaging_id == gcmId, ancestor=ndb.Key(Account, userID)).fetch(keys_only=True)
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

        fav = Favorite( user_id = userId, model_key = modelKey)
        result = MyTBAHelper.add_favorite(fav, request.device_key)
        if result == 200:
            return BaseResponse(code=200, message="Favorite added")
        elif result == 304:
            return BaseResponse(code=304, message="Favorite already exists")
        else:
            return BaseResponse(code=500, message="Unknown error adding favorite")

    @endpoints.method(FavoriteMessage, BaseResponse,
                      path='favorites/remove', http_method='POST',
                      name='favorites.remove')
    def remove_favorite(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to remove favorite")
        userId = PushHelper.user_email_to_id(current_user.email())
        modelKey = request.model_key
        result = MyTBAHelper.remove_favorite(userId, modelKey, request.device_key)
        if result == 200:
            return BaseResponse(code=200, message="Favorite deleted")
        elif result == 404:
            return BaseResponse(code=404, message="Favorite not found")
        else:
            return BaseResponse(code=500, message="Unknown error removing favorite")

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

        sub = Subscription( user_id = userId, model_key = modelKey, notification_types = PushHelper.notification_enums_from_string(request.notifications))
        result = MyTBAHelper.add_subscription(sub, request.device_key)
        if result == 200:
            return BaseResponse(code=200, message="Subscription updated")
        elif result == 304:
            return BaseResponse(code=304, message="Subscription already exists")
        else:
            return BaseResponse(code=500, message="Unknown error adding favorite")

    @endpoints.method(SubscriptionMessage, BaseResponse,
                      path='subscriptions/remove', http_method='POST',
                      name='subscriptions.remove')
    def remove_subscription(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to remove subscription")
        userId = PushHelper.user_email_to_id(current_user.email())
        modelKey = request.model_key
        result = MyTBAHelper.remove_subscription(userId, modelKey, request.device_key)
        if result == 200:
            return BaseResponse(code=200, message="Subscription removed")
        elif result == 404:
            return BaseResponse(code=404, message="Subscription not found")
        else:
            return BaseResponse(code=500, message="Unknown error removing subscription")

    @endpoints.method(ModelPreferenceMessage, BaseResponse,
                      path="model/setPreferences", http_method="POST",
                      name="model.setPreferences")
    def update_model_preferences(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to update model preferences")
        userId = PushHelper.user_email_to_id(current_user.email())
        modelKey = request.model_key
        output = {}
        code = 0

        if request.favorite:
            fav = Favorite( user_id = userId, model_key = modelKey)
            result = MyTBAHelper.add_favorite(fav, request.device_key)
            if result == 200:
                output['favorite'] = {"code"   : 200,
                                      "message": "Favorite added"}
                code += 100
            elif result == 304:
                output['favorite'] = {"code"   : 304,
                                      "message": "Favorite already exists"}
                code += 304
            else:
                output['favorite'] = {"code"   : 500,
                                      "message": "Unknown error adding favorite"}
                code += 500
        else:
            result = MyTBAHelper.remove_favorite(userId, modelKey, request.device_key)
            if result == 200:
                output['favorite'] = {"code"    : 200,
                                      "message" : "Favorite deleted"}
                code += 100
            elif result == 404:
                output['favorite'] = {"code"    : 404,
                                      "message" : "Favorite not found"}
                code += 404
            else:
                output['favorite'] = {"code"    : 500,
                                      "message" : "Unknown error removing favorite"}
                code += 500

        if request.notifications:
            sub = Subscription( user_id = userId, model_key = modelKey, notification_types = PushHelper.notification_enums_from_string(request.notifications))
            result = MyTBAHelper.add_subscription(sub, request.device_key)
            if result == 200:
                output['subscription'] = {"code"    : 200,
                                          "message" : "Subscription updated"}
                code += 100
            elif result == 304:
                output['subscription'] = {"code"    : 304,
                                          "message" : "Subscription already exists"}
                code += 304
            else:
                output['subscription'] = {"code"    : 500,
                                          "message" : "Unknown error adding favorite"}
                code += 500
        else:
            result = MyTBAHelper.remove_subscription(userId, modelKey, request.device_key)
            if result == 200:
                output['subscription'] = {"code:"   : 200,
                                          "message" : "Subscription removed"}
                code += 100
            elif result == 404:
                output['subscription'] = {"code"    : 404,
                                          "message" : "Subscription not found"}
                code += 404
            else:
                output['subscription'] = {"code"    : 500,
                                          "message" : "Unknown error removing subscription"}
                code += 500

        return BaseResponse(code=code, message=json.dumps(output))

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
