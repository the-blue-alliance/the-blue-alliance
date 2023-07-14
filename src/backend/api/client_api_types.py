from typing import List, TypedDict


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
