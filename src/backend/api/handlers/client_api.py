import json

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.api.client_api_auth_helper import ClientApiAuthHelper
from backend.api.client_api_types import (
    BaseResponse,
    ListDevicesResponse,
    MediaSuggestionMessage,
    PingRequest,
    RegisteredMobileClient,
    RegistrationRequest,
    VoidRequest,
)
from backend.api.handlers.decorators import client_api_method
from backend.common.consts.client_type import (
    ENUMS as CLIENT_TYPE_MAP,
    NAMES as CLIENT_TYPE_NAMES,
)
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.models.mobile_client import MobileClient
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)


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
        ancestor=account_key,
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


@client_api_method(VoidRequest, ListDevicesResponse)
def list_mobile_clients(req: VoidRequest) -> ListDevicesResponse:
    current_user = ClientApiAuthHelper.get_current_user()
    if current_user is None:
        return ListDevicesResponse(
            code=401,
            message="Unauthorized to list devices",
            devices=[],
        )

    account_key = none_throws(current_user.account_key)
    mobile_clients = MobileClient.query(ancestor=account_key).fetch(1000)
    return ListDevicesResponse(
        code=200,
        message="",
        devices=[
            RegisteredMobileClient(
                name=d.display_name,
                operating_system=CLIENT_TYPE_NAMES[d.client_type].lower(),
                mobile_id=d.messaging_id,
                device_uuid=d.device_uuid,
            )
            for d in mobile_clients
        ],
    )


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


@client_api_method(PingRequest, BaseResponse)
def ping_mobile_client(req: PingRequest) -> BaseResponse:
    current_user = ClientApiAuthHelper.get_current_user()
    if current_user is None:
        return BaseResponse(code=401, message="Unauthorized to ping client")

    account_key = none_throws(current_user.account_key)
    gcm_id = req["mobile_id"]

    clients = MobileClient.query(
        MobileClient.messaging_id == gcm_id, ancestor=account_key
    ).fetch(1)
    if len(clients) == 0:
        return BaseResponse(
            code=404,
            message="Invalid push token for user",
        )
    else:
        client: MobileClient = clients[0]
        success = TBANSHelper.ping(client)
        if success:
            return BaseResponse(code=200, message="Ping sent")
        else:
            return BaseResponse(code=500, message="Failed to ping client")


@client_api_method(MediaSuggestionMessage, BaseResponse)
def suggest_team_media(request: MediaSuggestionMessage) -> BaseResponse:
    current_user = ClientApiAuthHelper.get_current_user()
    if current_user is None:
        return BaseResponse(code=401, message="Unauthorized to make suggestions")

    account_key = none_throws(current_user.account_key)

    # For now, only allow team media suggestions
    if request["reference_type"] != "team":
        # Trying to suggest a media for an invalid model type
        return BaseResponse(code=400, message="Bad model type")

    if request["year"] not in SeasonHelper.get_valid_years():
        return BaseResponse(code=400, message="Bad year")

    # Need to split deletehash out into its own private dict. Don't want that to be exposed via API...
    private_details_json = None
    if request["details_json"]:
        incoming_details = json.loads(request["details_json"])
        private_details = None
        if "deletehash" in incoming_details:
            private_details = {"deletehash": incoming_details.pop("deletehash")}
        private_details_json = json.dumps(private_details) if private_details else None

    (status, _) = SuggestionCreator.createTeamMediaSuggestion(
        author_account_key=account_key,
        media_url=request["media_url"],
        team_key=request["reference_key"],
        year_str=str(request["year"]),
        private_details_json=private_details_json,
    )

    if status == SuggestionCreationStatus.BAD_URL:
        return BaseResponse(code=400, message="Bad suggestion url")
    elif status == SuggestionCreationStatus.SUCCESS:
        return BaseResponse(code=200, message="Suggestion added")
    else:
        return BaseResponse(code=304, message="Suggestion already exists")
