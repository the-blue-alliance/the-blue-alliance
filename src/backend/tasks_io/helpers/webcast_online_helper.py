import datetime
from typing import Any, Dict, Generator, List, Optional

from pyre_extensions import none_throws

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.memcache_models.twitch_oauth_token_memcache import (
    TwitchOauthTokenMemcache,
)
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.twitch_access_token import TwitchAccessToken
from backend.common.models.webcast import Webcast
from backend.common.tasklets import typed_tasklet, typed_toplevel
from backend.tasks_io.datafeeds.datafeed_twitch import (
    TwitchGetAccessToken,
    TwitchWebcastStatus,
)
from backend.tasks_io.datafeeds.datafeed_youtube_batch import YoutubeWebcastStatusBatch


class WebcastOnlineHelper:
    @classmethod
    @typed_toplevel
    def add_online_status(cls, webcasts: List[Webcast]) -> Generator[Any, Any, None]:
        """Public API for updating webcast online status.

        Uses optimized batch processing internally to minimize API quota usage.
        """
        yield cls.add_online_status_batch_async(webcasts)

    @classmethod
    @typed_tasklet
    def _add_twitch_status_async(cls, webcast: Webcast) -> Generator[Any, Any, None]:
        token_mc = TwitchOauthTokenMemcache()
        maybe_twitch_token: Optional[TwitchAccessToken] = yield token_mc.get_async()
        if maybe_twitch_token is not None:
            now = datetime.datetime.now()
            token_expiration = datetime.datetime.fromtimestamp(
                maybe_twitch_token["expires_at"]
            )
            needs_refresh = now > token_expiration
        else:
            needs_refresh = True

        twitch_token: TwitchAccessToken
        refresh_token = None
        if maybe_twitch_token and needs_refresh:
            refresh_token = maybe_twitch_token.get("refresh_token")

        if needs_refresh:
            twitch_token = yield TwitchGetAccessToken(
                refresh_token=refresh_token
            ).fetch_async()
            token_mc.expires(twitch_token["expires_in"])
            yield token_mc.put_async(twitch_token)
        else:
            twitch_token = none_throws(maybe_twitch_token)

        yield TwitchWebcastStatus(twitch_token, webcast).fetch_async()

    @classmethod
    @typed_tasklet
    def _add_youtube_status_batch_async(
        cls, webcasts: List[Webcast]
    ) -> Generator[Any, Any, None]:
        """Batch multiple YouTube webcasts into a single API request.

        YouTube API v3 supports querying up to 50 video IDs in a single request.
        This batching significantly reduces quota usage and API calls.
        """
        if not webcasts:
            return

        # Batch into groups of 50 (YouTube API limit)
        batch_size = 50
        for i in range(0, len(webcasts), batch_size):
            batch = webcasts[i : i + batch_size]
            # Fetch status data from API (returns Dict[video_id, WebcastOnlineStatus])
            status_results: Dict[str, Any] = yield YoutubeWebcastStatusBatch(
                batch
            ).fetch_async()

            # Merge results into webcast models
            for webcast in batch:
                video_id = webcast["channel"]
                if video_id in status_results:
                    status_data = status_results[video_id]
                    webcast.update(status_data)

    @classmethod
    @typed_tasklet
    def add_online_status_batch_async(
        cls, webcasts: List[Webcast]
    ) -> Generator[Any, Any, None]:
        """Process webcasts with optimized batching for YouTube.

        Separates YouTube and non-YouTube webcasts, batches YouTube requests
        into a single API call, and processes other types individually.
        """
        if not webcasts:
            return

        # Separate by cache status and type
        youtube_webcasts: List[Webcast] = []
        other_webcasts: List[Webcast] = []
        webcast_status_futures: List[Any] = []

        # Check cache and separate webcasts
        cache_futures = [
            WebcastOnlineStatusMemcache(webcast).get_async() for webcast in webcasts
        ]
        cached_results: List[Optional[Webcast]] = yield cache_futures

        for webcast, cached_webcast in zip(webcasts, cached_results):
            if cached_webcast:
                # Apply cached status
                if "status" in cached_webcast:
                    webcast["status"] = cached_webcast.get(
                        "status", WebcastStatus.UNKNOWN
                    )
                if "stream_title" in cached_webcast:
                    webcast["stream_title"] = cached_webcast.get("stream_title")
                if "viewer_count" in cached_webcast:
                    webcast["viewer_count"] = cached_webcast.get("viewer_count")
            else:
                # Not cached - need to fetch
                webcast["status"] = WebcastStatus.UNKNOWN
                webcast["stream_title"] = None
                webcast["viewer_count"] = None

                if webcast["type"] == WebcastType.YOUTUBE:
                    youtube_webcasts.append(webcast)
                else:
                    other_webcasts.append(webcast)

        # Batch YouTube requests
        if youtube_webcasts:
            webcast_status_futures.append(
                cls._add_youtube_status_batch_async(youtube_webcasts)
            )

        # Process individual non-YouTube webcasts
        for webcast in other_webcasts:
            if webcast["type"] == WebcastType.TWITCH:
                webcast_status_futures.append(cls._add_twitch_status_async(webcast))

        # Wait for all fetches to complete
        if webcast_status_futures:
            yield webcast_status_futures

        # Cache all results
        cache_put_futures = [
            WebcastOnlineStatusMemcache(webcast).put_async(webcast)
            for webcast in webcasts
            if webcast.get("status") is not None
        ]
        if cache_put_futures:
            yield cache_put_futures

    """
    @classmethod
    @typed_tasklet
    def _add_ustream_status_async(cls, webcast: Webcast) -> Generator[Any, Any, None]:
        url = "https://api.ustream.tv/channels/{}.json".format(webcast["channel"])
        try:
            rpc = urlfetch.create_rpc()
            result = yield urlfetch.make_fetch_call(rpc, url)
        except Exception:
            logging.exception("URLFetch failed for: {}".format(url))
            return None

        if result.status_code == 200:
            response = json.loads(result.content)
            if response["channel"]:
                webcast["status"] = (
                    WebcastStatus.ONLINE
                    if response["channel"]["status"] == "live"
                    else WebcastStatus.OFFLINE
                )
                webcast["stream_title"] = response["channel"]["title"]
            else:
                webcast["status"] = WebcastStatus.OFFLINE
        else:
            logging.warning(
                "Ustream status failed with code: {}".format(result.status_code)
            )
            logging.warning(result.content)

        return None
    """

    """
    @classmethod
    @ndb.tasklet
    def _add_livestream_status_async(
        cls, webcast: Webcast
    ) -> Generator[Any, Any, None]:
        livestream_secrets = Sitevar.get_or_insert("livestream.secrets")
        api_key = None
        if livestream_secrets and livestream_secrets.contents:
            api_key = livestream_secrets.contents.get("api_key")
        if api_key:
            url = "https://livestreamapis.com/v2/accounts/{}/events/{}".format(
                webcast["channel"], webcast["file"]
            )
            try:
                base64string = base64.encodebytes("{}:".format(api_key).encode())
                headers = {"Authorization": "Basic {}".format(base64string)}
                rpc = urlfetch.create_rpc()
                result = yield urlfetch.make_fetch_call(rpc, url, headers=headers)
            except Exception:
                logging.exception("URLFetch failed for: {}".format(url))
                return None
        else:
            logging.warning("Must have Livestream API key")
            return None

        if result.status_code == 200:
            response = json.loads(result.content)
            if response["items"]:
                webcast["status"] = (
                    WebcastStatus.ONLINE
                    if response["items"][0]["snippet"]["liveBroadcastContent"] == "live"
                    else WebcastStatus.OFFLINE
                )
                webcast["stream_title"] = response["items"][0]["snippet"]["title"]
            else:
                webcast["status"] = WebcastStatus.OFFLINE
        else:
            logging.warning(
                "Livestream status failed with code: {}".format(result.status_code)
            )
            logging.warning(result.content)

        return None
    """
