from typing import TypedDict

from backend.common.consts.webcast_type import WebcastType
from backend.common.sitevars.sitevar import Sitevar


class WebcastChannel(TypedDict):
    type: WebcastType
    channel: str
    channel_id: str


class ContentType(TypedDict):
    district_to_channels: dict[str, list[WebcastChannel]]


class DistrictWebcastChannels(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "district_webcast_channels"

    @staticmethod
    def description() -> str:
        return "Webcast channels for districts that don't publish them in advance"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(district_to_channels={})
