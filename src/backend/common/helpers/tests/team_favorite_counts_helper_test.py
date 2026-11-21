from typing import Any, cast, Dict

import pytest

from backend.common.consts.model_type import ModelType
from backend.common.helpers.team_favorite_counts_helper import TeamFavoriteCountsHelper
from backend.common.memcache import MemcacheClient
from backend.common.models.account import Account
from backend.common.models.favorite import Favorite
from backend.common.models.keys import TeamKey


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def add_favorite(account_id: str, team_key: TeamKey) -> None:
    account = Account(id=account_id)
    account.put()
    Favorite(
        parent=account.key,
        user_id=account_id,
        model_key=team_key,
        model_type=ModelType.TEAM,
    ).put()


def test_get_counts_queries_and_caches(ndb_stub, memcache_stub) -> None:
    add_favorite("a", "frc254")
    add_favorite("b", "frc254")
    add_favorite("c", "frc1114")

    counts = TeamFavoriteCountsHelper.get_counts({"frc254", "frc1114", "frc9999"})
    assert counts == {"frc254": 2, "frc1114": 1, "frc9999": 0}


def test_get_counts_shares_team_helper_namespace(ndb_stub, memcache_stub) -> None:
    # TeamHelper.getPopularTeamsEvents writes plain str keys into this namespace;
    # if we ever drift to bytes keys the cache silently stops being shared
    MemcacheClient.get().set_multi(
        cast(Dict[bytes, Any], {"frc254": 1234}),
        60,
        namespace=TeamFavoriteCountsHelper.CACHE_NAMESPACE,
    )

    counts = TeamFavoriteCountsHelper.get_counts({"frc254"})
    assert counts == {"frc254": 1234}
