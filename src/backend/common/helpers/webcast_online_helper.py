import json
import logging
from typing import Any, Generator, List, Optional

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.memcache import MemcacheClient
from backend.common.models.webcast import Webcast
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.sitevars.twitch_secrets import TwitchSecrets
from backend.common.tasklets import typed_tasklet, typed_toplevel


class WebcastOnlineHelper:
    @classmethod
    @typed_toplevel
    def add_online_status(cls, webcasts: List[Webcast]) -> Generator[Any, Any, None]:
        yield tuple(cls.add_online_status_async(webcast) for webcast in webcasts)

    @classmethod
    @typed_tasklet
    def add_online_status_async(cls, webcast: Webcast) -> Generator[Any, Any, None]:
        memcache = MemcacheClient.get()
        memcache_key = "webcast_status:{}:{}:{}".format(
            webcast["type"], webcast.get("channel"), webcast.get("file")
        ).encode()
        cached_webcast: Optional[Webcast] = memcache.get(memcache_key)
        if cached_webcast:
            if "status" in cached_webcast:
                webcast["status"] = cached_webcast.get("status", WebcastStatus.UNKNOWN)
            if "stream_title" in cached_webcast:
                webcast["stream_title"] = cached_webcast.get("stream_title")
            if "viewer_count" in cached_webcast:
                webcast["viewer_count"] = cached_webcast.get("viewer_count")

            return

        webcast["status"] = WebcastStatus.UNKNOWN
        webcast["stream_title"] = None
        webcast["viewer_count"] = None
        if webcast["type"] == WebcastType.TWITCH:
            yield cls._add_twitch_status_async(webcast)
        elif webcast["type"] == WebcastType.USTREAM:
            yield cls._add_ustream_status_async(webcast)
        elif webcast["type"] == WebcastType.YOUTUBE:
            yield cls._add_youtube_status_async(webcast)
        # Livestream charges for their API. Go figure.
        # elif webcast['type'] == 'livestream':
        #     yield cls._add_livestream_status_async(webcast)

        memcache.set(memcache_key, webcast, 60 * 5)

    @classmethod
    @typed_tasklet
    def _add_twitch_status_async(cls, webcast: Webcast) -> Generator[Any, Any, None]:
        client_id = TwitchSecrets.client_id()
        client_secret = TwitchSecrets.client_secret()
        if client_id and client_secret:
            # Get auth token
            auth_url = "https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials".format(
                client_id, client_secret
            )
            try:
                rpc = urlfetch.create_rpc()
                result = yield urlfetch.make_fetch_call(rpc, auth_url, method="POST")
            except Exception as e:
                logging.error("URLFetch failed when getting Twitch auth token.")
                logging.error(e)
                raise ndb.Return(None)

            if result.status_code == 200:
                response = json.loads(result.content)
                token = response["access_token"]
            else:
                logging.warning(
                    "Twitch auth failed with status code: {}".format(result.status_code)
                )
                logging.warning(result.content)
                raise ndb.Return(None)

            # Get webcast status
            status_url = "https://api.twitch.tv/helix/streams?user_login={}".format(
                webcast["channel"]
            )
            try:
                rpc = urlfetch.create_rpc()
                result = yield urlfetch.make_fetch_call(
                    rpc,
                    status_url,
                    headers={
                        "Authorization": "Bearer {}".format(token),
                        "Client-ID": client_id,
                    },
                )
            except Exception as e:
                logging.exception("URLFetch failed for: {}".format(status_url))
                logging.error(e)
                return None
        else:
            logging.warning("Must have Twitch Client ID & Secret")
            return None

        if result.status_code == 200:
            response = json.loads(result.content)
            if response["data"]:
                webcast["status"] = WebcastStatus.ONLINE
                webcast["stream_title"] = response["data"][0]["title"]
                webcast["viewer_count"] = response["data"][0]["viewer_count"]
            else:
                webcast["status"] = WebcastStatus.OFFLINE
        else:
            logging.warning(
                "Twitch status failed with code: {}".format(result.status_code)
            )
            logging.warning(result.content)

        return None

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

    @classmethod
    @typed_tasklet
    def _add_youtube_status_async(cls, webcast: Webcast) -> Generator[Any, Any, None]:
        api_key = GoogleApiSecret.secret_key()
        if api_key:
            url = "https://www.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}".format(
                webcast["channel"], api_key
            )
            try:
                rpc = urlfetch.create_rpc()
                result = yield urlfetch.make_fetch_call(rpc, url)
            except Exception:
                logging.exception("URLFetch failed for: {}".format(url))
                return None
        else:
            logging.warning("Must have Google API key")
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
                "YouTube status failed with code: {}".format(result.status_code)
            )
            logging.warning(result.content)

        return None

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
