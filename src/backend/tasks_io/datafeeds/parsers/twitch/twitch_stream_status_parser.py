from typing import Any, cast, List, TypedDict

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.models.webcast import Webcast
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class _StreamDataResponse(TypedDict):
    title: str
    viewer_count: int


class _StreamStatusResponse(TypedDict):
    data: List[_StreamDataResponse]


class TwitchStreamStatusParser(ParserBase[Webcast]):
    """
    See: https://dev.twitch.tv/docs/api/reference/#get-streams
    """

    def __init__(self, webcast: Webcast) -> None:
        super().__init__()
        self.webcast = webcast

    def parse(self, response: Any) -> Webcast:
        response_data = cast(_StreamStatusResponse, response)

        if not response_data["data"]:
            self.webcast["status"] = WebcastStatus.OFFLINE
            return self.webcast

        stream_data = response_data["data"][0]
        self.webcast["status"] = WebcastStatus.ONLINE
        self.webcast["stream_title"] = stream_data["title"]
        self.webcast["viewer_count"] = stream_data["viewer_count"]
        return self.webcast
