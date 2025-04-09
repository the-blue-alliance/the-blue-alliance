from typing import NotRequired, Optional, TypedDict

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType


class Webcast(TypedDict):
    type: WebcastType
    channel: str
    file: NotRequired[str]
    date: NotRequired[str]

    # Online status, fetched from provider's API
    status: NotRequired[WebcastStatus]
    stream_title: NotRequired[Optional[str]]
    viewer_count: NotRequired[Optional[int]]
