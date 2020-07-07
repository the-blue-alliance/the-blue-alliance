from backend.common.consts.model_type import ModelType
from backend.common.models.account import Account
from backend.common.models.favorite import Favorite
from backend.common.queries.favorite_query import FavoriteQuery


def test_no_favorites() -> None:
    account = Account(id="uid")
    favorites = FavoriteQuery(account=account).fetch()
    assert favorites == []


def test_favorites() -> None:
    account = Account(id="uid")
    favorite = Favorite(
        parent=account.key,
        user_id=account.key.id(),
        model_key="frc7332",
        model_type=ModelType.TEAM,
    )
    favorite.put()

    favorites = FavoriteQuery(account=account).fetch()
    assert favorites == [favorite]


def test_favorites_keys_only() -> None:
    account = Account(id="uid")
    favorite = Favorite(
        parent=account.key,
        user_id=account.key.id(),
        model_key="frc7332",
        model_type=ModelType.TEAM,
    )
    favorite.put()

    favorites = FavoriteQuery(account=account, keys_only=True).fetch()
    assert favorites == [favorite.key]
