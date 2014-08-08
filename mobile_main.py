import logging
import webapp2

import endpoints
from protorpc import remote

import tba_config

from helpers.gcm_helper import GCMHelper
from models.favorite import Favorite
from models.sitevar import Sitevar
from models.mobile_api_messages import BaseResponse, RegistrationRequest
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

@endpoints.api(name='tbaMobile', version='v1',
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

app = endpoints.api_server([MobileAPI])
