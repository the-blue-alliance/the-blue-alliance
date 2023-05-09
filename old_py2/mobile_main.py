import endpoints
import json
import logging

from google.appengine.ext import ndb

from protorpc import remote
from protorpc import message_types

import tba_config

from consts.client_type import ClientType
from helpers.media_helper import MediaParser
from helpers.push_helper import PushHelper
from helpers.notification_helper import NotificationHelper
from helpers.mytba_helper import MyTBAHelper
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
from models.favorite import Favorite
from models.media import Media
from models.sitevar import Sitevar
from models.subscription import Subscription
from models.mobile_api_messages import BaseResponse, FavoriteCollection, FavoriteMessage, RegistrationRequest, \
                                       SubscriptionCollection, SubscriptionMessage, ModelPreferenceMessage, \
                                       MediaSuggestionMessage, PingRequest
from models.mobile_client import MobileClient
from models.suggestion import Suggestion

WEB_CLIENT_ID = ""
ANDROID_AUDIENCE = ""
ANDROID_CLIENT_ID = ""
IOS_CLIENT_ID = ""

client_ids_sitevar = Sitevar.get_or_insert('mobile.clientIds')
if isinstance(client_ids_sitevar.contents, dict):
    WEB_CLIENT_ID = client_ids_sitevar.contents.get("web", "")
    ANDROID_AUDIENCE = client_ids_sitevar.contents.get("android-audience", "")
    ANDROID_CLIENT_ID = client_ids_sitevar.contents.get("android", "")
    IOS_CLIENT_ID = client_ids_sitevar.contents.get("ios", "")

if not WEB_CLIENT_ID:
    logging.error("Web client ID is not set, see /admin/authkeys")

if not ANDROID_CLIENT_ID:
    logging.error("Android client ID is not set, see /admin/authkeys")

if not ANDROID_AUDIENCE:
    logging.error("Android Audience is not set, see /admin/authkeys")

if not IOS_CLIENT_ID:
    logging.error("iOS client ID is not set, see /admin/authkeys")

client_ids = [WEB_CLIENT_ID, ANDROID_CLIENT_ID, ANDROID_AUDIENCE, IOS_CLIENT_ID]
if tba_config.DEBUG:
    '''
    Only allow API Explorer access on dev versions
    '''
    client_ids.append(endpoints.API_EXPLORER_CLIENT_ID)


@endpoints.api(
    name='tbaMobile',
    version='v9',
    description="API for TBA Mobile clients",
    allowed_client_ids=client_ids,
    audiences={
        'firebase': ['tbatv-prod-hrd'],
        'google_id_token': [ANDROID_AUDIENCE],
    },
    issuers={
        'firebase': endpoints.Issuer(
           'https://securetoken.google.com/tbatv-prod-hrd',
           'https://www.googleapis.com/service_accounts/v1/metadata/x509/securetoken@system.gserviceaccount.com'
        ),
        'google_id_token': endpoints.Issuer(
          'https://accounts.google.com',
          'https://www.googleapis.com/oauth2/v3/certs'
        ),
    }
)
class MobileAPI(remote.Service):

    @endpoints.method(RegistrationRequest, BaseResponse,
                      path='register', http_method='POST',
                      name='register')
    def register_client(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            return BaseResponse(code=401, message="Unauthorized to register")
        user_id = PushHelper.user_email_to_id(current_user.email())
        gcm_id = request.mobile_id
        os = ClientType.enums[request.operating_system]
        name = request.name
        uuid = request.device_uuid

        query = MobileClient.query(
                MobileClient.user_id == user_id,
                MobileClient.device_uuid == uuid,
                MobileClient.client_type == os)
        # trying to figure out an elusive dupe bug
        logging.info("DEBUGGING")
        logging.info("User ID: {}".format(user_id))
        logging.info("UUID: {}".format(uuid))
        logging.info("Count: {}".format(query.count()))
        if query.count() == 0:
            # Record doesn't exist yet, so add it
            MobileClient(
                parent=ndb.Key(Account, user_id),
                user_id=user_id,
                messaging_id=gcm_id,
                client_type=os,
                device_uuid=uuid,
                display_name=name).put()
            return BaseResponse(code=200, message="Registration successful")
        else:
            # Record already exists, update it
            client = query.fetch(1)[0]
            client.messaging_id = gcm_id
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
        user_id = PushHelper.user_email_to_id(current_user.email())
        gcm_id = request.mobile_id
        query = MobileClient.query(MobileClient.messaging_id == gcm_id, ancestor=ndb.Key(Account, user_id))\
            .fetch(keys_only=True)
        if len(query) == 0:
            # Record doesn't exist, so we can't remove it
            return BaseResponse(code=404, message="User doesn't exist. Can't remove it")
        else:
            ndb.delete_multi(query)
            return BaseResponse(code=200, message="User deleted")


app = endpoints.api_server([MobileAPI])
