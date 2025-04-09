from typing import List, TypedDict


class _TwitchAccessTokenApiResponse(TypedDict):
    access_token: str
    expires_in: int
    refresh_token: str
    token_type: str
    scope: List[str]


class _TwitchAccessTokenDerived(TypedDict):
    # We add these in ourselves
    client_id: str
    expires_at: int


class TwitchAccessToken(_TwitchAccessTokenApiResponse, _TwitchAccessTokenDerived):
    pass
