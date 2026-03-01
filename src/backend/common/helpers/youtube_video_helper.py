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

        url = f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={yt_secret}"
        try:
            ndb_context = ndb.get_context()
            urlfetch_response = yield ndb_context.urlfetch(url, deadline=10)
            urlfetch_result = URLFetchResult(url, urlfetch_response)

            if urlfetch_result.status_code != 200:
                logging.warning(
                    f"YouTube API returned status {urlfetch_result.status_code}"
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

        while i < 10:  # Precent runaway looping
            try:
                # Build URL with query parameters
                params = {
                    "playlistId": playlist_id,
                    "part": "id,snippet",
                    "maxResults": "50",
                    "pageToken": next_page_token,
                    "key": yt_secret,
                }
                query_string = "&".join(f"{k}={v}" for k, v in params.items() if v)
                url = f"{base_url}?{query_string}"

                ndb_context = ndb.get_context()
                urlfetch_response = yield ndb_context.urlfetch(url, deadline=10)
                urlfetch_result = URLFetchResult(url, urlfetch_response)

                if urlfetch_result.status_code != 200:
                    logging.error(
                        f"YouTube API returned status {urlfetch_result.status_code}"
                    )
                    raise Exception(
                        f"Unable to call Youtube API for videos in playlist: status {urlfetch_result.status_code}"
                    )
            except Exception:
                logging.exception("Unable to call Youtube API for videos in playlist")
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
