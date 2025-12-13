import time

from backend.common.models.twitch_access_token import TwitchAccessToken
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class TwitchAccessTokenParser(ParserBase[TwitchAccessToken]):
    """
    See: https://dev.twitch.tv/docs/api/reference/#get-streams
    """

    def __init__(self, client_id: str) -> None:
        super().__init__()
        self.client_id = client_id

    def parse(self, response: dict) -> TwitchAccessToken:
        current_time = time.time()
        expires_in = response["expires_in"]
        return TwitchAccessToken(
            access_token=response["access_token"],
            expires_in=expires_in,
            refresh_token=response.get("refresh_token"),
            scope=response.get("scope"),
            token_type=response["token_type"],
            client_id=self.client_id,
            expires_at=int(current_time) + expires_in,
        )
