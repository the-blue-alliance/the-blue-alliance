import logging
import re
from typing import Any, cast, Dict, Generator, List, Optional, TypedDict
from urllib import parse as urlparse

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult


class YouTubePlaylistItem(TypedDict):
    video_title: str
    video_id: str
    guessed_match_partial: str


class YouTubeUpcomingStream(TypedDict):
    stream_id: str
    title: str
    scheduled_start_time: str


class YouTubeChannel(TypedDict):
    channel_id: str
    channel_name: str


class YouTubeVideoHelper(object):
    # Patterns to extract YouTube video ID from various URL formats
    VIDEO_ID_PATTERNS = [
        r".*youtu\.be\/([a-zA-Z0-9_-]*)",  # Short links: youtu.be/ID
        r".*v=([a-zA-Z0-9_-]*)",  # Standard: youtube.com/watch?v=ID
        r".*/embed/([a-zA-Z0-9_-]*)",  # Embed: youtube.com/embed/ID
        r".*/shorts/([a-zA-Z0-9_-]*)",  # Shorts: youtube.com/shorts/ID
    ]

    @classmethod
    def parse_id_from_url(cls, youtube_url: str) -> Optional[str]:
        """
        Attempts to parse a URL for the video ID and timestamp (if present)
        Returns None if parsing fails
        Otherwise, returns "<youtube_id>" or "<youtube_id>?t=<start_seconds>"
        """
        youtube_id = None

        # Try to parse for ID using each pattern
        for pattern in cls.VIDEO_ID_PATTERNS:
            match = re.match(pattern, youtube_url)
            if match is not None:
                youtube_id = match.group(1)
                break

        # Try to parse for time
        if youtube_id is not None:
            parsed = urlparse.urlparse(youtube_url)
            queries = urlparse.parse_qs(parsed.query)
            if "t" in queries:
                total_seconds = cls.time_to_seconds(queries["t"][0])
                youtube_id = "{}?t={}".format(youtube_id, total_seconds)
            elif parsed.fragment and "t=" in parsed.fragment:
                total_seconds = cls.time_to_seconds(parsed.fragment.split("t=")[1])
                youtube_id = "{}?t={}".format(youtube_id, total_seconds)

        return youtube_id

    @classmethod
    def time_to_seconds(cls, time_str: str) -> int:
        """
        Format time in seconds. Turns things like "3h17m30s" to "11850"
        """
        match = none_throws(
            re.match(r"((?P<hour>\d*?)h)?((?P<min>\d*?)m)?((?P<sec>\d*)s?)?", time_str)
        ).groupdict()
        hours = match["hour"] or 0
        minutes = match["min"] or 0
        seconds = match["sec"] or 0
        total_seconds = (int(hours) * 3600) + (int(minutes) * 60) + int(seconds)
        return total_seconds

    @classmethod
    def guessMatchPartial(cls, video_title: str) -> str:
        qual_match = re.search(r"[^\w\d]*(q|qm)(\d+).*", video_title, re.IGNORECASE)
        if qual_match is not None:
            return f"qm{qual_match.group(2)}"

        elim_match = re.search(
            r"[^\w\d]*(ef\d+m\d+|qf\d+m\d+|sf\d+m\d+|f\d+m\d+).*",
            video_title,
            re.IGNORECASE,
        )
        if elim_match is not None:
            return elim_match.group(1).lower()

        return ""

    @classmethod
    @typed_tasklet
    def get_scheduled_start_time(
        cls, video_id: str
    ) -> Generator[Any, Any, Optional[str]]:
        """
        Fetches the scheduledStartTime for a YouTube video from the YouTube API.
        Returns the date in YYYY-MM-DD format, or None if not available.
        """
        yt_secret = GoogleApiSecret.secret_key()
        if not yt_secret:
            logging.warning(
                "No Google API secret, unable to fetch YouTube video details"
            )
            raise ndb.Return(None)

        params = {
            "part": "liveStreamingDetails",
            "id": video_id,
            "key": yt_secret,
        }
        query_string = urlparse.urlencode(params)
        url = f"https://www.googleapis.com/youtube/v3/videos?{query_string}"

        try:
            ndb_context = ndb.get_context()
            urlfetch_response = yield ndb_context.urlfetch(url, deadline=10)
            urlfetch_result = URLFetchResult(url, urlfetch_response)

            if urlfetch_result.status_code != 200:
                # Sanitize URL for logging (remove API key)
                sanitized_url = url.replace(yt_secret, "***")
                logging.warning(
                    f"YouTube API returned status {urlfetch_result.status_code} for {sanitized_url}. Response: {urlfetch_result.content[:500] if urlfetch_result.content else 'No content'}"
                )
                raise ndb.Return(None)

            data = cast(Optional[dict], urlfetch_result.json())
            if not data or not data.get("items"):
                raise ndb.Return(None)

            live_details = data["items"][0].get("liveStreamingDetails", {})
            scheduled_start_time = live_details.get("scheduledStartTime")
            if not scheduled_start_time:
                raise ndb.Return(None)

            # Parse ISO 8601 datetime and return as YYYY-MM-DD
            raise ndb.Return(scheduled_start_time[:10])
        except ndb.Return:
            raise
        except Exception:
            logging.exception(
                "Failed to fetch YouTube video scheduled start time for %s", video_id
            )
            raise ndb.Return(None)

    @classmethod
    @typed_tasklet
    def resolve_channel_name(
        cls, channel_name: str
    ) -> Generator[Any, Any, Optional[YouTubeChannel]]:
        """
        Resolves a YouTube channel name to a channel ID.
        Returns channel metadata if found, else None.
        """
        yt_secret = GoogleApiSecret.secret_key()
        if not yt_secret:
            logging.warning("No Google API secret, unable to resolve YouTube channel")
            raise ndb.Return(None)

        params = {
            "part": "snippet",
            "type": "channel",
            "q": channel_name,
            "maxResults": "1",
            "key": yt_secret,
        }
        query_string = urlparse.urlencode(params)
        url = f"https://www.googleapis.com/youtube/v3/search?{query_string}"

        try:
            ndb_context = ndb.get_context()
            urlfetch_response = yield ndb_context.urlfetch(url, deadline=10)
            urlfetch_result = URLFetchResult(url, urlfetch_response)

            if urlfetch_result.status_code != 200:
                # Sanitize URL for logging (remove API key)
                sanitized_url = url.replace(yt_secret, "***")
                logging.warning(
                    f"YouTube API returned status {urlfetch_result.status_code} for {sanitized_url}. Response: {urlfetch_result.content[:500] if urlfetch_result.content else 'No content'}"
                )
                raise ndb.Return(None)

            data = cast(Optional[dict], urlfetch_result.json())
            if not data or not data.get("items"):
                raise ndb.Return(None)

            first_item = data["items"][0]
            resolved_channel_id = first_item.get("id", {}).get("channelId")
            resolved_channel_name = first_item.get("snippet", {}).get("title")

            if not resolved_channel_id:
                raise ndb.Return(None)

            raise ndb.Return(
                YouTubeChannel(
                    channel_id=resolved_channel_id,
                    channel_name=resolved_channel_name or channel_name,
                )
            )
        except ndb.Return:
            raise
        except Exception:
            sanitized_url = url.replace(yt_secret, "***")
            logging.exception(
                "Failed to resolve YouTube channel name '%s' at %s",
                channel_name,
                sanitized_url,
            )
            raise ndb.Return(None)

    @classmethod
    @typed_tasklet
    def videos_in_playlist(
        cls, playlist_id: str
    ) -> Generator[Any, Any, List[YouTubePlaylistItem]]:
        videos: List[Dict] = []
        yt_secret = GoogleApiSecret.secret_key()
        if not yt_secret:
            msg = "No Google API secret, unable to resolve playlist"
            logging.warning(msg)
            raise Exception(msg)

        next_page_token = ""
        base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
        i = 0

        while i < 10:  # Prevent runaway looping
            url = ""  # Initialize to avoid uninitialized variable error
            try:
                # Build URL with query parameters
                params = {
                    "playlistId": playlist_id,
                    "part": "id,snippet",
                    "maxResults": "50",
                    "key": yt_secret,
                }
                if next_page_token:
                    params["pageToken"] = next_page_token
                query_string = urlparse.urlencode(params)
                url = f"{base_url}?{query_string}"

                ndb_context = ndb.get_context()
                urlfetch_response = yield ndb_context.urlfetch(url, deadline=10)
                urlfetch_result = URLFetchResult(url, urlfetch_response)

                if urlfetch_result.status_code != 200:
                    # Sanitize URL for logging (remove API key)
                    sanitized_url = url.replace(yt_secret, "***")
                    error_msg = f"YouTube API returned status {urlfetch_result.status_code} for {sanitized_url}. Response: {urlfetch_result.content[:500] if urlfetch_result.content else 'No content'}"
                    logging.error(error_msg)
                    raise Exception(
                        f"Unable to call YouTube API for videos in playlist '{playlist_id}': status {urlfetch_result.status_code}"
                    )
            except Exception as e:
                sanitized_url = (
                    url.replace(yt_secret, "***")
                    if url and yt_secret
                    else url or base_url
                )
                logging.exception(
                    "Unable to call YouTube API for videos in playlist '%s' at %s: %s",
                    playlist_id,
                    sanitized_url,
                    str(e),
                )
                raise

            video_result = cast(Optional[dict], urlfetch_result.json())
            if video_result is None:
                logging.error("YouTube API returned no data")
                break

            videos += [
                video
                for video in video_result["items"]
                if video["snippet"]["resourceId"]["kind"] == "youtube#video"
            ]

            if "nextPageToken" not in video_result:
                break
            next_page_token = video_result["nextPageToken"]
            i += 1

        raise ndb.Return(
            [
                YouTubePlaylistItem(
                    video_id=video["snippet"]["resourceId"]["videoId"],
                    video_title=video["snippet"]["title"],
                    guessed_match_partial=cls.guessMatchPartial(
                        video["snippet"]["title"]
                    ),
                )
                for video in videos
            ]
        )

    @classmethod
    @typed_tasklet
    def get_upcoming_streams(
        cls, channel_id: str
    ) -> Generator[Any, Any, List[YouTubeUpcomingStream]]:
        """
        Fetches all upcoming live streams for a given YouTube channel.
        Returns a list of streams with stream_id, title, and scheduled_start_time.
        """
        yt_secret = GoogleApiSecret.secret_key()
        if not yt_secret:
            msg = "No Google API secret, unable to fetch upcoming streams"
            logging.warning(msg)
            raise Exception(msg)

        stream_basics: List[Dict[str, str]] = []
        next_page_token = ""
        base_url = "https://www.googleapis.com/youtube/v3/search"
        page_count = 0

        while page_count < 10:  # Prevent runaway looping
            url = ""  # Initialize to avoid uninitialized variable error
            try:
                params = {
                    "part": "snippet",
                    "channelId": channel_id,
                    "eventType": "upcoming",
                    "type": "video",
                    "order": "date",
                    "maxResults": "50",
                    "key": yt_secret,
                }
                if next_page_token:
                    params["pageToken"] = next_page_token
                query_string = urlparse.urlencode(params)
                url = f"{base_url}?{query_string}"

                ndb_context = ndb.get_context()
                urlfetch_response = yield ndb_context.urlfetch(url, deadline=10)
                urlfetch_result = URLFetchResult(url, urlfetch_response)

                if urlfetch_result.status_code != 200:
                    # Sanitize URL for logging (remove API key)
                    sanitized_url = url.replace(yt_secret, "***")
                    error_msg = f"YouTube API returned status {urlfetch_result.status_code} for {sanitized_url}. Response: {urlfetch_result.content[:500] if urlfetch_result.content else 'No content'}"
                    logging.error(error_msg)
                    raise Exception(
                        f"Unable to call YouTube API for upcoming streams in channel '{channel_id}': status {urlfetch_result.status_code}"
                    )
            except Exception as e:
                sanitized_url = (
                    url.replace(yt_secret, "***")
                    if url and yt_secret
                    else url or base_url
                )
                logging.exception(
                    "Unable to call YouTube API for upcoming streams in channel '%s' at %s: %s",
                    channel_id,
                    sanitized_url,
                    str(e),
                )
                raise

            search_result = cast(Optional[dict], urlfetch_result.json())
            if search_result is None:
                logging.error("YouTube API returned no data")
                break

            for item in search_result.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId")
                if video_id:
                    stream_basics.append(
                        {
                            "stream_id": video_id,
                            "title": snippet.get("title", ""),
                        }
                    )

            if "nextPageToken" not in search_result:
                break

            next_page_token = search_result["nextPageToken"]
            page_count += 1

        streams: List[YouTubeUpcomingStream] = []
        for batch_start in range(0, len(stream_basics), 50):
            batch = stream_basics[batch_start : batch_start + 50]
            video_ids = ",".join(stream["stream_id"] for stream in batch)
            params = {
                "part": "liveStreamingDetails",
                "id": video_ids,
                "key": yt_secret,
            }
            query_string = urlparse.urlencode(params)
            videos_url = f"https://www.googleapis.com/youtube/v3/videos?{query_string}"

            try:
                ndb_context = ndb.get_context()
                urlfetch_response = yield ndb_context.urlfetch(videos_url, deadline=10)
                urlfetch_result = URLFetchResult(videos_url, urlfetch_response)

                if urlfetch_result.status_code != 200:
                    # Sanitize URL for logging (remove API key)
                    sanitized_url = videos_url.replace(yt_secret, "***")
                    logging.warning(
                        f"YouTube API videos endpoint returned status {urlfetch_result.status_code} for {sanitized_url}. Response: {urlfetch_result.content[:500] if urlfetch_result.content else 'No content'}"
                    )
                    continue

                videos_result = cast(Optional[dict], urlfetch_result.json())
                if videos_result is None:
                    logging.warning("YouTube videos API returned no data")
                    continue

                scheduled_times: Dict[str, str] = {}
                for item in videos_result.get("items", []):
                    found_video_id = item.get("id")
                    live_details = item.get("liveStreamingDetails") or {}
                    scheduled_start = live_details.get("scheduledStartTime", "")
                    if found_video_id:
                        scheduled_times[found_video_id] = scheduled_start

                for stream in batch:
                    stream_id = stream["stream_id"]
                    streams.append(
                        YouTubeUpcomingStream(
                            stream_id=stream_id,
                            title=stream["title"],
                            scheduled_start_time=scheduled_times.get(stream_id, ""),
                        )
                    )
            except Exception:
                sanitized_url = (
                    videos_url.replace(yt_secret, "***") if yt_secret else videos_url
                )
                logging.exception(
                    "Unable to fetch video details from YouTube API at %s",
                    sanitized_url,
                )

        raise ndb.Return(streams)
