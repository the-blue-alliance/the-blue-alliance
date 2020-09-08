import logging
import re
from typing import Dict, List, Optional
from urllib import parse as urlparse

import requests
from pyre_extensions import none_throws
from typing_extensions import TypedDict

from backend.common.sitevars.google_api_secret import GoogleApiSecret


class YouTubePlaylistItem(TypedDict):
    video_title: str
    video_id: str
    guessed_match_partial: str


class YouTubeVideoHelper(object):
    @classmethod
    def parse_id_from_url(cls, youtube_url: str) -> Optional[str]:
        """
        Attempts to parse a URL for the video ID and timestamp (if present)
        Returns None if parsing fails
        Otherwise, returns "<youtube_id>" or "<youtube_id>?t=<start_seconds>"
        """
        youtube_id = None

        # Try to parse for ID
        regex1 = re.match(r".*youtu\.be\/([a-zA-Z0-9_-]*)", youtube_url)
        if regex1 is not None:
            youtube_id = regex1.group(1)
        else:
            regex2 = re.match(r".*v=([a-zA-Z0-9_-]*)", youtube_url)
            if regex2 is not None:
                youtube_id = regex2.group(1)
            else:
                regex3 = re.match(r".*/embed/([a-zA-Z0-9_-]*)", youtube_url)
                if regex3 is not None:
                    youtube_id = regex3.group(1)

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
            r"[^\w\d]*(ef\dm\d|qf\dm\d|sf\dm\d|f\dm\d).*", video_title, re.IGNORECASE
        )
        if elim_match is not None:
            return elim_match.group(1).lower()

        return ""

    @classmethod
    def videos_in_playlist(cls, playlist_id: str) -> List[YouTubePlaylistItem]:
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
                result = requests.get(
                    base_url,
                    params={
                        "playlistId": playlist_id,
                        "part": "id,snippet",
                        "maxResults": 50,
                        "pageToken": next_page_token,
                        "key": yt_secret,
                    },
                )
                result.raise_for_status()
            except Exception:
                logging.exception("Unable to call Youtube API for videos in playlist")
                raise

            video_result = result.json()
            videos += [
                video
                for video in video_result["items"]
                if video["snippet"]["resourceId"]["kind"] == "youtube#video"
            ]

            if "nextPageToken" not in video_result:
                break
            next_page_token = video_result["nextPageToken"]
            i += 1

        return [
            YouTubePlaylistItem(
                video_id=video["snippet"]["resourceId"]["videoId"],
                video_title=video["snippet"]["title"],
                guessed_match_partial=cls.guessMatchPartial(video["snippet"]["title"]),
            )
            for video in videos
        ]
