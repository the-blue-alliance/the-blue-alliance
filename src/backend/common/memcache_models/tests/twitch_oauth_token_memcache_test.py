from datetime import timedelta

import pytest

from backend.common.memcache_models.twitch_oauth_token_memcache import (
    TwitchOauthTokenMemcache,
)


def test_key() -> None:
    assert TwitchOauthTokenMemcache().key() == b"twitch_oauth_token"


def test_ttl_requires_expiration() -> None:
    with pytest.raises(ValueError, match="Must set expiration"):
        TwitchOauthTokenMemcache().ttl()


def test_ttl_doubles_expiration() -> None:
    assert TwitchOauthTokenMemcache().expires(30).ttl() == timedelta(seconds=60)
