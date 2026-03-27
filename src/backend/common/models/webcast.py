from typing import NotRequired, Optional, TypedDict

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType


class WebcastOnlineStatus(TypedDict):
    # Online status, fetched from provider's API
    status: NotRequired[WebcastStatus]
    stream_title: NotRequired[Optional[str]]
    viewer_count: NotRequired[Optional[int]]
    scheduled_start_time_utc: NotRequired[Optional[str]]


class Webcast(WebcastOnlineStatus):
    type: WebcastType
    channel: str
    file: NotRequired[str]
    date: NotRequired[str]


class WebcastChannel(TypedDict):
    type: WebcastType
    channel: str
    channel_id: str
