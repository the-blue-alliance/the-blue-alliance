from typing import TypedDict


class BaseResponse(TypedDict):
    code: int
    message: str


class _RegistrationRequestNotRequired(TypedDict, total=False):
    name: str


class RegistrationRequest(_RegistrationRequestNotRequired):
    operating_system: str
    mobile_id: str
    device_uuid: str
