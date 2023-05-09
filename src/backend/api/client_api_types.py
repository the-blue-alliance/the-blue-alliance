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
