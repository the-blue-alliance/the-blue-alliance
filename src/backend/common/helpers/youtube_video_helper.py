import re
from typing import Optional, TypedDict
from urllib import parse as urlparse

from pyre_extensions import none_throws


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
    """
    Helper class for YouTube URL parsing and simple utilities.
    For methods that interact with YouTube API/datafeeds, see:
    - backend.tasks_io.helpers.youtube_helper.YouTubeTasksIOHelper
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
