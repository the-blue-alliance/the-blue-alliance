import abc
import logging
from typing import Any, cast, Dict, Generator, List, Optional, TypeVar
from urllib.parse import urlencode

from google.appengine.ext import ndb

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

    @ndb.tasklet
    def fetch_all_pages_async(
        self,
        max_pages: int = 10,
    ) -> Generator[Any, Any, List[ParsedSearchResult]]:
        """Fetch and parse all pages for this search request.

        Follows YouTube's `nextPageToken` chain up to `max_pages` pages.
        """
        all_results: List[ParsedSearchResult] = []
        next_page_token = self.page_token
        page_count = 0

        while page_count < max_pages:
            page_datafeed = YoutubeSearchDatafeed(
                query=self.query,
                search_type=self.search_type,
                max_results=self.max_results,
                order=self.order,
                page_token=next_page_token,
                channel_id=self.channel_id,
                event_type=self.event_type,
            )
            response = yield page_datafeed._fetch()

            if response.status_code != 200:
                error_msg = f"YouTube API returned status {response.status_code} for {response.url}. Response: {response.content[:500] if response.content else 'No content'}"
                logging.error(error_msg)
                raise Exception(
                    f"Unable to call YouTube API for search: status {response.status_code}"
                )

            response_data = cast(Optional[Dict[str, Any]], response.json())
            if response_data is None:
                logging.error("YouTube API returned no data")
                break

            parsed_results = page_datafeed.parser().parse(response_data)
            if not parsed_results:
                parsed_results = page_datafeed._fallback_parse_items(response_data)
            all_results.extend(parsed_results)

            next_page_token = cast(str, response_data.get("nextPageToken", ""))
            if not next_page_token:
                break

            page_count += 1

        raise ndb.Return(all_results)

    def _fallback_parse_items(
        self, response_data: Dict[str, Any]
    ) -> List[ParsedSearchResult]:
        """Fallback parser for partial API responses that omit some expected fields."""
        parsed_results: List[ParsedSearchResult] = []

        for item_any in response_data.get("items", []):
            item = cast(Dict[str, Any], item_any)
            item_id = cast(Dict[str, Any], item.get("id", {}))
            snippet = cast(Dict[str, Any], item.get("snippet", {}))

            title = snippet.get("title")
            if not isinstance(title, str) or not title:
                continue

            parsed: ParsedSearchResult = {
                "kind": str(item_id.get("kind", "")),
                "title": title,
            }

            video_id = item_id.get("videoId")
            if isinstance(video_id, str) and video_id:
                parsed["video_id"] = video_id

            channel_id = item_id.get("channelId")
            if isinstance(channel_id, str) and channel_id:
                parsed["channel_id"] = channel_id
            else:
                snippet_channel_id = snippet.get("channelId")
                if isinstance(snippet_channel_id, str) and snippet_channel_id:
                    parsed["channel_id"] = snippet_channel_id

            playlist_id = item_id.get("playlistId")
            if isinstance(playlist_id, str) and playlist_id:
                parsed["playlist_id"] = playlist_id

            description = snippet.get("description")
            if isinstance(description, str) and description:
                parsed["description"] = description

            if any(key in parsed for key in ["video_id", "channel_id", "playlist_id"]):
                parsed_results.append(parsed)

        return parsed_results


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
