from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.api.client_api_auth_helper import ClientApiAuthHelper
from backend.api.client_api_types import BaseResponse, RegistrationRequest
from backend.api.handlers.decorators import client_api_method
from backend.common.consts.client_type import ENUMS as CLIENT_TYPE_MAP
from backend.common.models.mobile_client import MobileClient


@client_api_method(RegistrationRequest, BaseResponse)
def register_mobile_client(req: RegistrationRequest) -> BaseResponse:
    current_user = ClientApiAuthHelper.get_current_user()
    if current_user is None:
        return BaseResponse(code=401, message="Unauthorized to register")

    # TODO should this be stringified?
    account_key = none_throws(current_user.account_key)
    user_id = str(account_key.id())

    gcm_id = req["mobile_id"]
    os = CLIENT_TYPE_MAP[req["operating_system"]]
    name = req.get("name", "Unnamed Device")
    uuid = req["device_uuid"]

    query = MobileClient.query(
        MobileClient.user_id == user_id,
        MobileClient.device_uuid == uuid,
        MobileClient.client_type == os,
    )

    # trying to figure out an elusive dupe bug
    if query.count() == 0:
        # Record doesn't exist yet, so add it
        MobileClient(
            parent=account_key,
            user_id=user_id,
            messaging_id=gcm_id,
            client_type=os,
            device_uuid=uuid,
            display_name=name,
        ).put()
        return BaseResponse(code=200, message="Registration successful")
    else:
        # Record already exists, update it
        client = query.fetch(1)[0]
        client.messaging_id = gcm_id
        client.display_name = name
        client.put()
        return BaseResponse(code=304, message="Client already exists")


@client_api_method(RegistrationRequest, BaseResponse)
def unregister_mobile_client(req: RegistrationRequest) -> BaseResponse:
    current_user = ClientApiAuthHelper.get_current_user()
    if current_user is None:
        return BaseResponse(code=401, message="Unauthorized to unregister")

    account_key = none_throws(current_user.account_key)

    gcm_id = req["mobile_id"]
    query = MobileClient.query(
        MobileClient.messaging_id == gcm_id,
        ancestor=account_key,
    ).fetch(keys_only=True)
    if len(query) == 0:
        # Record doesn't exist, so we can't remove it
        return BaseResponse(code=404, message="User doesn't exist. Can't remove it")
    else:
        ndb.delete_multi(query)
        return BaseResponse(code=200, message="User deleted")
