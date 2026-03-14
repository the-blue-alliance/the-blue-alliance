import logging
import re
from typing import Any, cast, Dict, Generator, List, Optional, TypedDict
from urllib import parse as urlparse

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.datafeeds.datafeed_youtube import (
    YoutubeChannelListForHandleDatafeed,
    YoutubePlaylistItemsDatafeed,
    YoutubeUpcomingStreamsDatafeed,
    YoutubeVideoDetailsDatafeed,
    YoutubeVideoLiveDetailsBatchDatafeed,
)
from backend.common.tasklets import typed_tasklet


class YouTubePlaylistItem(TypedDict):
    video_title: str
    video_id: str
    guessed_match_partial: str


class YouTubeUpcomingStream(TypedDict):
    stream_id: str
    title: str
    description: str
    scheduled_start_time: str
    live_broadcast_content: str


class YouTubeChannel(TypedDict):
    channel_id: str
    channel_name: str


class YouTubeVideoHelper(object):
    """
    Helper class for YouTube URL parsing and YouTube API access.
    """

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
        try:
            datafeed = YoutubeVideoDetailsDatafeed(
                video_id,
                parts="liveStreamingDetails",
            )
            response = yield datafeed._fetch()

            if response.status_code != 200:
                raise ndb.Return(None)

            raw_data = cast(Optional[dict], response.json())
            if not raw_data or not raw_data.get("items"):
                raise ndb.Return(None)

            parsed_data = datafeed.parser().parse(raw_data)
            scheduled_start_time = (
                parsed_data.get("scheduled_start_time") if parsed_data else None
            )

            if not scheduled_start_time:
                raise ndb.Return(None)

            raise ndb.Return(scheduled_start_time)
        except ValueError:
            logging.warning(
                "No Google API secret, unable to fetch YouTube video details"
            )
            raise ndb.Return(None)
        except ndb.Return:
            raise
        except Exception:
            logging.exception(
                "Failed to fetch YouTube video scheduled start time for %s", video_id
            )
            raise ndb.Return(None)

    @classmethod
    @typed_tasklet
    def resolve_channel_id(
        cls, channel_username: str
    ) -> Generator[Any, Any, Optional[YouTubeChannel]]:
        """
        Resolves a YouTube channel username/handle to a channel ID.
        Returns channel metadata if found, else None.
        """
        normalized_handle = channel_username.strip().lstrip("@")
        if not normalized_handle:
            raise ndb.Return(None)

        try:
            datafeed = YoutubeChannelListForHandleDatafeed(normalized_handle)
            response = yield datafeed._fetch()

            if response.status_code != 200:
                raise ndb.Return(None)

            raw_data = cast(Optional[dict], response.json())
            if not raw_data or not raw_data.get("items"):
                raise ndb.Return(None)

            parsed_data = datafeed.parser().parse(raw_data)
            if not parsed_data:
                raise ndb.Return(None)

            first_item = parsed_data[0]
            resolved_channel_id = first_item.get("channel_id")
            resolved_channel_name = first_item.get("channel_name")
            if not resolved_channel_id:
                raise ndb.Return(None)

            raise ndb.Return(
                YouTubeChannel(
                    channel_id=resolved_channel_id,
                    channel_name=resolved_channel_name or channel_username,
                )
            )
        except ValueError:
            logging.warning("No Google API secret, unable to resolve YouTube channel")
            raise ndb.Return(None)
        except ndb.Return:
            raise
        except Exception:
            logging.exception(
                "Failed to resolve YouTube channel handle '%s'",
                channel_username,
            )
            raise ndb.Return(None)

    @classmethod
    @typed_tasklet
    def resolve_channel_name(
        cls, channel_name: str
    ) -> Generator[Any, Any, Optional[YouTubeChannel]]:
        """Backward-compatible wrapper around handle-based channel resolution."""
        resolved_channel = yield cls.resolve_channel_id(channel_name)
        raise ndb.Return(resolved_channel)

    @classmethod
    @typed_tasklet
    def videos_in_playlist(
        cls, playlist_id: str
    ) -> Generator[Any, Any, List[YouTubePlaylistItem]]:
        videos: List[YouTubePlaylistItem] = []

        next_page_token = ""
        i = 0

        while i < 10:  # Prevent runaway looping
            try:
                datafeed = YoutubePlaylistItemsDatafeed(
                    playlist_id,
                    max_results=50,
                    page_token=next_page_token,
                )
            except ValueError:
                msg = "No Google API secret, unable to resolve playlist"
                logging.warning(msg)
                raise Exception(msg)

            try:
                response = yield datafeed._fetch()

                if response.status_code != 200:
                    error_msg = f"YouTube API returned status {response.status_code} for {response.url}. Response: {response.content[:500] if response.content else 'No content'}"
                    logging.error(error_msg)
                    raise Exception(
                        f"Unable to call YouTube API for videos in playlist '{playlist_id}': status {response.status_code}"
                    )
            except Exception as e:
                logging.exception(
                    "Unable to call YouTube API for videos in playlist '%s': %s",
                    playlist_id,
                    str(e),
                )
                raise

            video_result = cast(Optional[dict], response.json())
            if video_result is None:
                logging.error("YouTube API returned no data")
                break

            for video in datafeed.parser().parse(video_result):
                video_id = video.get("video_id")
                if not video_id:
                    continue
                video_title = video.get("title", "")
                videos.append(
                    YouTubePlaylistItem(
                        video_id=video_id,
                        video_title=video_title,
                        guessed_match_partial=cls.guessMatchPartial(video_title),
                    )
                )

            if "nextPageToken" not in video_result:
                break
            next_page_token = video_result["nextPageToken"]
            i += 1

        raise ndb.Return(videos)

    @classmethod
    @typed_tasklet
    def get_upcoming_streams(
        cls, channel_id: str
    ) -> Generator[Any, Any, List[YouTubeUpcomingStream]]:
        """
        Fetches all upcoming live streams for a given YouTube channel.
        Returns a list of streams with stream_id, title, and scheduled_start_time.
        """
        stream_basics: List[Dict[str, str]] = []
        try:
            search_datafeed = YoutubeUpcomingStreamsDatafeed(
                channel_id=channel_id,
                max_results=50,
                order="date",
            )
            parsed_search_results = yield search_datafeed.fetch_all_pages_async()
        except ValueError:
            msg = "No Google API secret, unable to fetch upcoming streams"
            logging.warning(msg)
            raise Exception(msg)
        except Exception as e:
            logging.exception(
                "Unable to call YouTube API for upcoming streams in channel '%s': %s",
                channel_id,
                str(e),
            )
            raise Exception(
                f"Unable to call YouTube API for upcoming streams in channel '{channel_id}': {str(e)}"
            ) from e

        for item in parsed_search_results:
            video_id = item.get("video_id")
            if video_id:
                stream_basics.append(
                    {
                        "stream_id": video_id,
                        "title": item.get("title", ""),
                        "live_broadcast_content": item.get(
                            "live_broadcast_content", ""
                        ),
                        "description": item.get("description", ""),
                    }
                )

        streams: List[YouTubeUpcomingStream] = []
        for batch_start in range(0, len(stream_basics), 50):
            batch = stream_basics[batch_start : batch_start + 50]
            batch_datafeed = YoutubeVideoLiveDetailsBatchDatafeed(
                [stream["stream_id"] for stream in batch]
            )

            try:
                videos_response = yield batch_datafeed._fetch()

                if videos_response.status_code != 200:
                    logging.warning(
                        f"YouTube API videos endpoint returned status {videos_response.status_code} for {videos_response.url}. Response: {videos_response.content[:500] if videos_response.content else 'No content'}"
                    )
                    continue

                videos_result = cast(Optional[dict], videos_response.json())
                if videos_result is None:
                    logging.warning("YouTube videos API returned no data")
                    continue

                scheduled_times = batch_datafeed.parser().parse(videos_result)

                for stream in batch:
                    stream_id = stream["stream_id"]
                    streams.append(
                        YouTubeUpcomingStream(
                            stream_id=stream_id,
                            title=stream["title"],
                            description=stream["description"],
                            scheduled_start_time=scheduled_times.get(stream_id, ""),
                            live_broadcast_content=stream.get(
                                "live_broadcast_content", ""
                            ),
                        )
                    )
            except Exception:
                logging.exception("Unable to fetch video details from YouTube API")

        raise ndb.Return(streams)
