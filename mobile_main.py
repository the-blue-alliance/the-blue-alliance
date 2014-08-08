import endpoints
import logging
import webapp2

from google.appengine.ext import ndb

from protorpc import remote
from protorpc import message_types

import tba_config

from helpers.gcm_helper import GCMHelper
from models.favorite import Favorite
from models.sitevar import Sitevar
from models.subscription import Subscription
from models.mobile_api_messages import BaseResponse, FavoriteCollection, FavoriteMessage, RegistrationRequest, \
                                       SubscriptionCollection, SubscriptionMessage
from models.mobile_client import MobileClient

client_id_sitevar = Sitevar.get_by_id('gcm.serverKey')
if client_id_sitevar is None:
    raise Exception("Sitevar gcm.serverKey is undefined. Can't process incoming requests")
WEB_CLIENT_ID = str(client_id_sitevar.values_json)
ANDROID_AUDIENCE = WEB_CLIENT_ID

android_id_sitevar = Sitevar.get_by_id('android.clientId')
if android_id_sitevar is None:
    raise Exception("Sitevar android.clientId is undefined. Can't process incoming requests")
ANDROID_CLIENT_ID = str(android_id_sitevar.values_json)

# To enable iOS access to the API, add another variable for the iOS client ID

@endpoints.api(name='tbaMobile', version='v4', description="API for TBA Mobile clients",
               allowed_client_ids=[WEB_CLIENT_ID, ANDROID_CLIENT_ID,
                                   # To enable iOS addess, add its client ID here
                                   endpoints.API_EXPLORER_CLIENT_ID],
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
        userId = current_user.user_id() 
        gcmId = request.mobile_id
        os = request.operating_system
        if MobileClient.query( MobileClient.messaging_id==gcmId ).count() == 0:
            # Record doesn't exist yet, so add it
            MobileClient(   messaging_id = gcmId,
                            user_id = userId,
                            operating_system = os ).put()        
            return BaseResponse(code=200, message="Registration successful")
        else:
            # Record already exists, don't bother updating it again
            return BaseResponse(code=304, message="Client already exists")

    @endpoints.method(FavoriteMessage, BaseResponse,
                      path='favorites/add', http_method='POST',
                      name='favorites.add')
    def add_favorite(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to add favorite")
        userId = current_user.user_id()
        modelKey = request.model_key

        if Favorite.query( Favorite.user_id == userId, Favorite.model_key == modelKey).count() == 0:
            # Favorite doesn't exist, add it
            Favorite( user_id = userId, model_key = modelKey).put()
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
        userId = current_user.user_id()
        modelKey = request.model_key

        to_delete = Favorite.query( Favorite.user_id == userId, Favorite.model_key == modelKey).fetch()
        if len(to_delete) > 0:
            ndb.delete_multi([m.key for m in to_delete])
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
        userId = current_user.user_id()

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
        userId = current_user.user_id()
        modelKey = request.model_key

        if Subscription.query( Subscription.user_id == userId, Subscription.model_key == modelKey).count() == 0:
            # Subscription doesn't exist, add it
            Subscription( user_id = userId, model_key = modelKey).put()
            return BaseResponse(code=200, message="Subscription added")
        else:
            # Subscription already exists. Don't add it again
            return BaseResponse(code=304, message="Subscription already exists")

    @endpoints.method(SubscriptionMessage, BaseResponse,
                      path='subscriptions/remove', http_method='POST',
                      name='subscriptions.remove')
    def remove_subscription(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to remove subscription")
        userId = current_user.user_id()
        modelKey = request.model_key

        to_delete = Subscription.query( Subscription.user_id == userId, Subscription.model_key == modelKey).fetch()
        if len(to_delete) > 0:
            ndb.delete_multi([m.key for m in to_delete])
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
        userId = current_user.user_id()

        subscriptions = Subscription.query( Subscription.user_id == userId ).fetch()
        output = []
        for subscription in subscriptions:
            output.append(SubscriptionMessage(model_key = subscription.model_key))
        return SubscriptionCollection(subscriptions = output)


app = endpoints.api_server([MobileAPI])
