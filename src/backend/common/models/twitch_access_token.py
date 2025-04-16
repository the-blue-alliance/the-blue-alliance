from typing import List, Optional, TypedDict


class _TwitchAccessTokenApiResponse(TypedDict):
    access_token: str
    expires_in: int
    refresh_token: Optional[str]
    token_type: str
    scope: Optional[List[str]]


class _TwitchAccessTokenDerived(TypedDict):
    # We add these in ourselves
    client_id: str
    expires_at: int


class TwitchAccessToken(_TwitchAccessTokenApiResponse, _TwitchAccessTokenDerived):
    pass
