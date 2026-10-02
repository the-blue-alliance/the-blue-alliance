from backend.common.models.twitch_access_token import TwitchAccessToken


def test_twitch_access_token() -> None:
    token = TwitchAccessToken(
        access_token="abc",
        expires_in=3600,
        refresh_token=None,
        token_type="bearer",
        scope=None,
        client_id="client",
        expires_at=1234,
    )
    assert token["access_token"] == "abc"
    assert token["client_id"] == "client"
