from typing import Dict, Optional

from backend.common.consts.webcast_type import WebcastType
from backend.common.models.twitch_access_token import TwitchAccessToken
from backend.common.models.webcast import Webcast
from backend.common.sitevars.twitch_secrets import TwitchSecrets
from backend.common.urlfetch import URLFetchMethod
from backend.tasks_io.datafeeds.datafeed_base import DatafeedBase
from backend.tasks_io.datafeeds.parsers.twitch.twitch_access_token_parser import (
    TwitchAccessTokenParser,
)
from backend.tasks_io.datafeeds.parsers.twitch.twitch_stream_status_parser import (
    TwitchStreamStatusParser,
)


class TwitchGetAccessToken(DatafeedBase[TwitchAccessToken]):

    def __init__(self, refresh_token: Optional[str]) -> None:
        super().__init__()
        self.client_id = TwitchSecrets.client_id()
        self.client_secret = TwitchSecrets.client_secret()
        self.refresh_token = refresh_token

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Missing twitch client ID & secret! Configure TwitchSecrets sitevar"
            )

    def url(self) -> str:
        return "https://id.twitch.tv/oauth2/token"

    @property
    def method(self) -> URLFetchMethod:
        return URLFetchMethod.POST

    def payload(self) -> Dict[str, str]:
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        if self.refresh_token is not None:
            payload["grant_type"] = "refresh_token"
            payload["refresh_token"] = self.refresh_token

        return payload

    def parser(self) -> TwitchAccessTokenParser:
        return TwitchAccessTokenParser(self.client_id)


class TwitchWebcastStatus(DatafeedBase[Webcast]):

    def __init__(self, access_token: TwitchAccessToken, webcast: Webcast) -> None:
        super().__init__()
        self.access_token = access_token
        self.webcast = webcast

        if self.webcast["type"] != WebcastType.TWITCH:
            raise ValueError(f"{webcast} is not twitch! Can't load status")

    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token['access_token']}",
            "Client-ID": self.access_token["client_id"],
        }

    def url(self) -> str:
        channel = self.webcast["channel"]
        return f"https://api.twitch.tv/helix/streams?user_login={channel}"

    def parser(self) -> TwitchStreamStatusParser:
        return TwitchStreamStatusParser(self.webcast)
