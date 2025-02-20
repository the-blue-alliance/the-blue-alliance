from typing import Any, Generator, List

from backend.common.models.account import Account
from backend.common.models.favorite import Favorite
from backend.common.queries.database_query import DatabaseQuery
from backend.common.tasklets import typed_tasklet


class FavoriteQuery(DatabaseQuery[List[Favorite], None]):
    DICT_CONVERTER = None

    def __init__(self, account: Account, keys_only: bool = False) -> None:
        super().__init__(account=account, keys_only=keys_only)

    @typed_tasklet
    def _query_async(
        self, account: Account, keys_only: bool = False
    ) -> Generator[Any, Any, List[Favorite]]:
        favorite_query = Favorite.query(ancestor=account.key)
        return (yield (favorite_query.fetch_async(keys_only=keys_only)))
