import abc
from typing import Any, Dict, List, Optional, TypeVar
from urllib.parse import urlencode

from backend.common.consts.webcast_type import WebcastType
from backend.common.models.webcast import Webcast, WebcastOnlineStatus
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.tasks_io.datafeeds.datafeed_base import DatafeedBase
from backend.tasks_io.datafeeds.parsers.youtube.youtube_playlist_items_parser import (
    ParsedPlaylistItem,
    YoutubePlaylistItemsParser,
)
from backend.tasks_io.datafeeds.parsers.youtube.youtube_search_parser import (
    ParsedSearchResult,
    YoutubeSearchParser,
)
from backend.tasks_io.datafeeds.parsers.youtube.youtube_stream_status_batch_parser import (
    YoutubeStreamStatusBatchParser,
)
from backend.tasks_io.datafeeds.parsers.youtube.youtube_video_details_parser import (
    ParsedVideoDetails,
    YoutubeVideoDetailsParser,
)
from backend.tasks_io.datafeeds.parsers.youtube.youtube_video_live_details_batch_parser import (
    YoutubeVideoLiveDetailsBatchParser,
)

TReturn = TypeVar("TReturn")


class YoutubeApiBase(DatafeedBase[Any, TReturn]):
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self) -> None:
        super().__init__()
        self.api_key = GoogleApiSecret.secret_key()
        if not self.api_key:
            raise ValueError("No Google API key! Configure GoogleApiSecret sitevar")

    @abc.abstractmethod
    def endpoint(self) -> str: ...

    @abc.abstractmethod
    def url_params(self) -> Dict[str, str]: ...

    def url(self) -> str:
        params = urlencode(self.url_params(), safe=",")
        return f"{self.BASE_URL}/{self.endpoint()}?{params}"

    def headers(self) -> Dict[str, str]:
        return {"X-goog-api-key": self.api_key}


class YoutubeWebcastStatusBatch(YoutubeApiBase[Dict[str, WebcastOnlineStatus]]):
    def __init__(self, webcasts: List[Webcast]) -> None:
        super().__init__()

        for webcast in webcasts:
            if webcast["type"] != WebcastType.YOUTUBE:
                raise ValueError(f"{webcast} is not youtube! Can't load status")

        self.webcasts = webcasts
        self.video_ids = [webcast["channel"] for webcast in webcasts]

    def endpoint(self) -> str:
        return "videos"

    def url_params(self) -> Dict[str, str]:
        return {
            "part": "snippet,liveStreamingDetails",
            "id": ",".join(self.video_ids),
        }

    def parser(self) -> YoutubeStreamStatusBatchParser:
        return YoutubeStreamStatusBatchParser(self.video_ids)


class YoutubeVideoDetailsDatafeed(YoutubeApiBase[Optional[ParsedVideoDetails]]):
    def __init__(
        self,
        video_id: str,
        parts: str = "snippet,liveStreamingDetails",
    ) -> None:
        super().__init__()
        self.video_id = video_id
        self.parts = parts

    def endpoint(self) -> str:
        return "videos"

    def url_params(self) -> Dict[str, str]:
        return {
            "part": self.parts,
            "id": self.video_id,
        }

    def parser(self) -> YoutubeVideoDetailsParser:
        return YoutubeVideoDetailsParser()


class YoutubeSearchDatafeed(YoutubeApiBase[List[ParsedSearchResult]]):
    def __init__(
        self,
        query: Optional[str] = None,
        search_type: str = "channel",
        max_results: int = 1,
        order: str = "relevance",
        page_token: str = "",
        channel_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.query = query
        self.search_type = search_type
        self.max_results = max_results
        self.order = order
        self.page_token = page_token
        self.channel_id = channel_id
        self.event_type = event_type

    def endpoint(self) -> str:
        return "search"

    def url_params(self) -> Dict[str, str]:
        params = {
            "part": "snippet",
            "type": self.search_type,
            "maxResults": str(self.max_results),
            "order": self.order,
        }
        if self.query is not None:
            params["q"] = self.query
        if self.channel_id is not None:
            params["channelId"] = self.channel_id
        if self.event_type is not None:
            params["eventType"] = self.event_type
        if self.page_token:
            params["pageToken"] = self.page_token
        return params

    def parser(self) -> YoutubeSearchParser:
        return YoutubeSearchParser()


class YoutubePlaylistItemsDatafeed(YoutubeApiBase[List[ParsedPlaylistItem]]):
    def __init__(
        self,
        playlist_id: str,
        max_results: int = 50,
        page_token: str = "",
    ) -> None:
        super().__init__()
        self.playlist_id = playlist_id
        self.max_results = max_results
        self.page_token = page_token

    def endpoint(self) -> str:
        return "playlistItems"

    def url_params(self) -> Dict[str, str]:
        params = {
            "part": "id,snippet",
            "playlistId": self.playlist_id,
            "maxResults": str(self.max_results),
        }
        if self.page_token:
            params["pageToken"] = self.page_token
        return params

    def parser(self) -> YoutubePlaylistItemsParser:
        return YoutubePlaylistItemsParser()


class YoutubeVideoLiveDetailsBatchDatafeed(YoutubeApiBase[Dict[str, str]]):
    def __init__(self, video_ids: List[str]) -> None:
        super().__init__()
        self.video_ids = video_ids

    def endpoint(self) -> str:
        return "videos"

    def url_params(self) -> Dict[str, str]:
        return {
            "part": "liveStreamingDetails",
            "id": ",".join(self.video_ids),
        }

    def parser(self) -> YoutubeVideoLiveDetailsBatchParser:
        return YoutubeVideoLiveDetailsBatchParser(self.video_ids)
