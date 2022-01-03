from typing import Optional, TypedDict

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType


class _WebcastRequired(TypedDict, total=True):
    type: WebcastType
    channel: str


class _WebcastOptional(TypedDict, total=False):
    file: str
    date: str

    # Online status, fetched from provider's API
    status: WebcastStatus
    stream_title: Optional[str]
    viewer_count: Optional[int]


class Webcast(_WebcastRequired, _WebcastOptional):
    pass
