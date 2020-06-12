from typing_extensions import TypedDict
from backend.common.consts.webcast_type import WebcastType


class _WebcastRequired(TypedDict, total=True):
    type: WebcastType
    channel: str


class _WebcastOptional(TypedDict, total=False):
    file: str
    date: str


class Webcast(_WebcastRequired, _WebcastOptional):
    pass
