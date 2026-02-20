import logging
import re
from typing import Any, Generator, Optional, Tuple

from google.appengine.ext import ndb

from backend.common.consts.webcast_type import WebcastType
from backend.common.frc_api.types import WebcastDetailModelExtV33
from backend.common.models.webcast import Webcast
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult


class WebcastParser:
    TWITCH_URL_PATTERNS = ["twitch.tv/"]
    YOUTUBE_URL_PATTERNS = ["youtube.com/", "youtu.be/"]
    USTREAM_URL_PATTERNS = ["ustream.tv/"]
    LIVESTREAM_URL_PATTERNS = ["livestream.com/"]

    @classmethod
    def webcast_dict_from_api_response(
        cls, api_webcast: WebcastDetailModelExtV33
    ) -> Optional[Webcast]:
        webcast_type: WebcastType | None = None
        channel: str | None = None

        match api_webcast["provider"]:
            case "Twitch":
                webcast_type = WebcastType.TWITCH
                channel = api_webcast["channel"]
            case "Youtube":
                webcast_type = WebcastType.YOUTUBE
                channel = api_webcast["slug"]
            case _:
                pass

        if not webcast_type:
            logging.warning(f"Unknown webcast provider: {api_webcast['provider']}")
            return None

        if not channel:
            logging.warning(f"Missing channel information for webcast: {api_webcast}")
            return None

        w = Webcast(
            type=webcast_type,
            channel=channel,
        )
        if date := api_webcast.get("date"):
            w["date"] = date

        return w

    @classmethod
    @typed_tasklet
    def webcast_dict_from_url(cls, url: str) -> Generator[Any, Any, Optional[Webcast]]:
        """
        Takes a url, and turns it into a webcast dict (as defined in models.event)
        """
        if any(s in url for s in cls.TWITCH_URL_PATTERNS):
            result = cls._webcast_dict_from_twitch(url)
            raise ndb.Return(result)
        elif any(s in url for s in cls.YOUTUBE_URL_PATTERNS):
            result = cls._webcast_dict_from_youtube(url)
            raise ndb.Return(result)
        elif any(s in url for s in cls.USTREAM_URL_PATTERNS):
            result = yield cls._webcast_dict_from_ustream(url)
            raise ndb.Return(result)
        elif any(s in url for s in cls.LIVESTREAM_URL_PATTERNS):
            result = yield cls._webcast_dict_from_livestream(url)
            raise ndb.Return(result)
        else:
            logging.warning("Failed to determine webcast type from url: {}".format(url))
            raise ndb.Return(None)

    @classmethod
    def _webcast_dict_from_twitch(cls, url: str) -> Optional[Webcast]:
        channel = cls._parse_twitch_channel(url)
        if channel is None:
            logging.warning("Failed to determine channel from url: {}".format(url))
            return None
        webcast_dict: Webcast = {
            "type": WebcastType.TWITCH,
            "channel": channel,
        }
        return webcast_dict

    @classmethod
    def _webcast_dict_from_youtube(cls, url: str) -> Optional[Webcast]:
        channel = cls._parse_youtube_channel(url)
        if channel is None:
            logging.warning("Failed to determine channel from url: {}".format(url))
            return None
        webcast_dict: Webcast = {
            "type": WebcastType.YOUTUBE,
            "channel": channel,
        }
        return webcast_dict

    @classmethod
    @typed_tasklet
    def _webcast_dict_from_ustream(
        cls, url: str
    ) -> Generator[Any, Any, Optional[Webcast]]:
        ndb_context = ndb.get_context()
        urlfetch_result_future = ndb_context.urlfetch(url, deadline=10)
        urlfetch_result: URLFetchResult = yield urlfetch_result_future
        if urlfetch_result.status_code != 200:
            logging.warning("Unable to retrieve url: {}".format(url))
            raise ndb.Return(None)

        channel = cls._parse_ustream_channel(urlfetch_result.content)
        if channel is None:
            logging.warning("Failed to determine channel from url: {}".format(url))
            raise ndb.Return(None)
        webcast_dict: Webcast = {
            "type": WebcastType.USTREAM,
            "channel": channel,
        }
        raise ndb.Return(webcast_dict)

    @classmethod
    @typed_tasklet
    def _webcast_dict_from_livestream(
        cls, url: str
    ) -> Generator[Any, Any, Optional[Webcast]]:
        ndb_context = ndb.get_context()
        urlfetch_result_future = ndb_context.urlfetch(url, deadline=10)
        urlfetch_result: URLFetchResult = yield urlfetch_result_future
        if urlfetch_result.status_code != 200:
            logging.warning("Unable to retrieve url: {}".format(url))
            raise ndb.Return(None)

        channel_and_file = cls._parse_livestream_channel(urlfetch_result.content)
        if channel_and_file is None:
            logging.warning(
                "Failed to determine channel and file from url: {}".format(url)
            )
            raise ndb.Return(None)
        channel, file = channel_and_file
        webcast_dict: Webcast = {
            "type": WebcastType.LIVESTREAM,
            "channel": channel,
            "file": file,
        }
        raise ndb.Return(webcast_dict)

    @classmethod
    def _parse_twitch_channel(cls, url: str) -> Optional[str]:
        regex1 = re.match(r".*twitch.tv\/(\w+)", url)
        if regex1 is not None:
            return regex1.group(1)
        else:
            return None

    @classmethod
    def _parse_youtube_channel(cls, url: str) -> Optional[str]:
        youtube_id = None
        # youtu.be/video-id or youtube.com/live/video-id
        regex1 = re.match(
            r"(?:https?:\/\/)?(?:www.)?(?:youtu\.be|youtube.com\/live)\/([a-zA-Z0-9_-]{11})",
            url,
        )
        if regex1 is not None:
            youtube_id = regex1.group(1)
        else:
            # youtube.com/watch?v=video-id
            regex2 = re.match(r".*v=([a-zA-Z0-9_-]*)", url)
            if regex2 is not None:
                youtube_id = regex2.group(1)

        if not youtube_id:
            return None
        else:
            return youtube_id

    @classmethod
    def _parse_ustream_channel(cls, html: str) -> Optional[str]:
        from bs4 import BeautifulSoup

        content = html

        # parse html for the channel id
        soup = BeautifulSoup(content, "html.parser")
        el = soup.find("meta", {"name": "ustream:channel_id"})
        if el is None:
            return None
        else:
            channel_id = el["content"]
            if channel_id:
                return channel_id
            else:
                return None

    @classmethod
    def _parse_livestream_channel(cls, html: str) -> Optional[Tuple[str, str]]:
        from bs4 import BeautifulSoup

        content = html

        # parse html for the channel id
        soup = BeautifulSoup(content, "html.parser")
        el = soup.find("meta", {"name": "twitter:player"})
        if el is None:
            return None
        else:
            regex1 = re.match(
                r".*livestream.com\/accounts\/(\d+)\/events\/(\d+)", el["content"]
            )
            if regex1 is not None:
                return regex1.group(1), regex1.group(2)
            else:
                return None
