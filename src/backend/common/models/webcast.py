from typing import NotRequired, TypedDict

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType


class WebcastOnlineStatus(TypedDict):
    # Online status, fetched from provider's API
    status: NotRequired[WebcastStatus]
    stream_title: NotRequired[str | None]
    viewer_count: NotRequired[int | None]


class Webcast(WebcastOnlineStatus):
    type: WebcastType
    channel: str
    file: NotRequired[str]
    date: NotRequired[str]
