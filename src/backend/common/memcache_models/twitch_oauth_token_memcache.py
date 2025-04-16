from datetime import timedelta

from backend.common.memcache_models.memcache_model import MemcacheModel
from backend.common.models.twitch_access_token import TwitchAccessToken


class TwitchOauthTokenMemcache(MemcacheModel[TwitchAccessToken]):
    """
    Store a twitch oauth token, for its validity
    https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow
    """

    def __init__(self) -> None:
        super().__init__()
        self.expires_in = None

    def expires(self, expires_in: int) -> "TwitchOauthTokenMemcache":
        self.expires_in = expires_in
        return self

    def key(self) -> bytes:
        return b"twitch_oauth_token"

    def ttl(self) -> timedelta:
        # Double the returned validity window, so we can refresh upon expiration
        if not self.expires_in:
            raise ValueError("Must set expiration before writing Twitch Oauth token!!")

        return timedelta(seconds=self.expires_in * 2)
