from typing import Dict

from backend.common.consts.webcast_type import WebcastType
from backend.common.models.webcast import Webcast
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.tasks_io.datafeeds.datafeed_base import DatafeedBase
from backend.tasks_io.datafeeds.parsers.youtube.youtube_stream_stauts_parser import (
    YoutubeStreamStatusParser,
)


class YoutubeWebcastStatus(DatafeedBase[Webcast]):
    def __init__(self, webcast: Webcast) -> None:
        super().__init__()
        self.api_key = GoogleApiSecret.secret_key()
        if not self.api_key:
            raise ValueError("No Google API key! Configure GoogleApiSecret sitevar")

        self.webcast = webcast
        if self.webcast["type"] != WebcastType.YOUTUBE:
            raise ValueError(f"{webcast} is not youtube! Can't load status")

    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def url(self) -> str:
        channel = self.webcast["channel"]
        return f"https://www.googleapis.com/youtube/v3/videos?part=snippet,liveStreamingDetails&id={channel}"

    def parser(self) -> YoutubeStreamStatusParser:
        return YoutubeStreamStatusParser(self.webcast)
