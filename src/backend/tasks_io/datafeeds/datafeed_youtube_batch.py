from typing import Any, Dict, List

from backend.common.consts.webcast_type import WebcastType
from backend.common.models.webcast import Webcast, WebcastOnlineStatus
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.tasks_io.datafeeds.datafeed_base import DatafeedBase
from backend.tasks_io.datafeeds.parsers.youtube.youtube_stream_status_batch_parser import (
    YoutubeStreamStatusBatchParser,
)


class YoutubeWebcastStatusBatch(DatafeedBase[Any, Dict[str, WebcastOnlineStatus]]):
    """
    Fetches status for multiple YouTube webcasts in a single API request.
    YouTube API v3 supports querying multiple video IDs in one request.

    Returns a dictionary mapping video IDs to their online status (without mutating models).
    The caller is responsible for merging these results into the webcast models.
    """

    def __init__(self, webcasts: List[Webcast]) -> None:
        super().__init__()
        self.api_key = GoogleApiSecret.secret_key()
        if not self.api_key:
            raise ValueError("No Google API key! Configure GoogleApiSecret sitevar")

        # Validate all are YouTube webcasts
        for webcast in webcasts:
            if webcast["type"] != WebcastType.YOUTUBE:
                raise ValueError(f"{webcast} is not youtube! Can't load status")

        self.webcasts = webcasts
        # Extract video IDs for the parser
        self.video_ids = [webcast["channel"] for webcast in webcasts]

    def url(self) -> str:
        # Batch up to 50 video IDs per request (YouTube API limit)
        video_ids = ",".join(self.video_ids)
        return f"https://www.googleapis.com/youtube/v3/videos?part=snippet,liveStreamingDetails&id={video_ids}&key={self.api_key}"

    def parser(self) -> YoutubeStreamStatusBatchParser:
        return YoutubeStreamStatusBatchParser(self.video_ids)
