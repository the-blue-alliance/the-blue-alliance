from typing import List, TypedDict

from backend.common.consts.model_type import ModelType


class VoidRequest(TypedDict):
    pass


class BaseResponse(TypedDict):
    code: int
    message: str


class _RegistrationRequestNotRequired(TypedDict, total=False):
    name: str


class RegistrationRequest(_RegistrationRequestNotRequired):
    operating_system: str
    mobile_id: str
    device_uuid: str


class RegisteredMobileClient(TypedDict):
    name: str
    operating_system: str
    mobile_id: str
    device_uuid: str


class ListDevicesResponse(BaseResponse):
    devices: List[RegisteredMobileClient]


class PingRequest(TypedDict):
    mobile_id: str


class MediaSuggestionMessage(TypedDict):
    reference_key: str
    reference_type: str
    year: int
    media_url: str
    details_json: str


class FavoriteMessage(TypedDict):
    model_key: str
    model_type: ModelType


class FavoriteCollection(BaseResponse):
    favorites: List[FavoriteMessage]


class SubscriptionMessage(TypedDict):
    model_key: str
    notifications: List[str]  # stringified NotificationType.TYPE_NAMES
    model_type: ModelType


class SubscriptionCollection(BaseResponse):
    subscriptions: List[SubscriptionMessage]


class ModelPreferenceMessage(TypedDict):
    model_key: str
    model_type: ModelType
    device_key: str  # so we know which device NOT to push sync notifications to
    notifications: List[str]  # stringified NotificationType.TYPE_NAMES
    favorite: bool


class UpdatePreferencesInternalResponse(TypedDict):
    """
    Because this API contract is horrible, this is the JSON-serialized object
    that will be in the `message` field in the overall response
    """

    favorite: BaseResponse
    subscription: BaseResponse
